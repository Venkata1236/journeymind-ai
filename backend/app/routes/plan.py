import time
import json
import re
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.database.models import TripPlan
from app.models.schemas import TripRequest, TripResponse, TripSummary, BudgetBreakdown, LocalTips, WeatherInfo, BudgetFeasibility
from app.agents.crew import run_crew
from app.core.config import get_settings
from loguru import logger

router = APIRouter(prefix="/api", tags=["Trip Planning"])
settings = get_settings()


# ─── Budget Feasibility Logic ─────────────────────────────────────────────────

def check_budget_feasibility(
    budget_inr: float,
    duration_days: int,
    group_size: int,
    travel_style: str,
    num_destinations: int,
) -> BudgetFeasibility:
    """
    Determine budget feasibility before crew runs.
    Catches obviously unrealistic budgets early.
    """
    per_person_per_day = budget_inr / (group_size * duration_days)

    # Minimum thresholds per person per day by style (INR)
    thresholds = {
        "budget":   800,
        "comfort":  1500,
        "heritage": 2500,
        "luxury":   5000,
    }

    minimum = thresholds.get(travel_style, 1500)
    # Multi-destination adds transport cost
    if num_destinations > 1:
        minimum *= 1.2

    if per_person_per_day >= minimum * 1.3:
        return BudgetFeasibility.feasible
    elif per_person_per_day >= minimum:
        return BudgetFeasibility.tight
    else:
        return BudgetFeasibility.over_budget


# ─── Output Parsers ───────────────────────────────────────────────────────────

def parse_budget_breakdown(budget_text: str, total_budget: float) -> dict:
    """
    Parse BudgetAnalyst output text into structured breakdown.
    Ensures categories sum exactly to total_budget.
    """
    categories = [
        "accommodation_inr",
        "food_inr",
        "transport_inr",
        "activities_inr",
        "shopping_buffer_inr",
        "contingency_inr",
    ]

    # ── Step 1: Extract values from LLM output text ──────────────────
    extracted = {}
    for category in categories:
        patterns = [
            rf"{category}[\:\s]+[\₹]?([\d,]+)",
            rf"{category.replace('_inr', '')}[\:\s]+[\₹]?([\d,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, budget_text, re.IGNORECASE)
            if match:
                extracted[category] = float(match.group(1).replace(",", ""))
                break

    # ── Step 2: Proportional fallback if parsing incomplete ───────────
    if len(extracted) < 6:
        logger.warning("Budget parsing incomplete — using proportional fallback")
        contingency_pct = settings.default_contingency_pct
        subtotal = total_budget / (1 + contingency_pct)
        extracted = {
            "accommodation_inr":   round(subtotal * 0.38, 2),
            "food_inr":            round(subtotal * 0.22, 2),
            "transport_inr":       round(subtotal * 0.22, 2),
            "activities_inr":      round(subtotal * 0.10, 2),
            "shopping_buffer_inr": round(subtotal * 0.08, 2),
            "contingency_inr":     round(total_budget - subtotal, 2),
        }

    # ── Step 3: Cap contingency to 15% max ────────────────────────────
    max_contingency = round(total_budget * 0.15, 2)
    if extracted.get("contingency_inr", 0) > max_contingency:
        extracted["contingency_inr"] = max_contingency

    # ── Step 4: Force exact sum — set contingency to fill the gap ─────
    non_contingency_sum = sum(
        extracted.get(c, 0) for c in categories if c != "contingency_inr"
    )
    extracted["contingency_inr"] = round(total_budget - non_contingency_sum, 2)

    # ── Step 5: Absorb any rounding penny in shopping_buffer ──────────
    final_sum = sum(extracted.get(c, 0) for c in categories)
    if abs(final_sum - total_budget) > 0.01:
        extracted["shopping_buffer_inr"] = round(
            extracted.get("shopping_buffer_inr", 0) + (total_budget - final_sum), 2
        )

    extracted["total_inr"] = total_budget
    logger.info(f"Budget breakdown parsed — total: ₹{extracted['total_inr']:,.0f}")
    return extracted


def parse_weather_info(research_text: str, destinations: list[str]) -> dict:
    """Parse weather info from WeatherTool outputs embedded in research text."""
    weather = {}
    mock = {
        "jaipur":  {"temp": "28-38°C", "condition": "Hot and dry",   "rain_risk": "Low",  "tip": "Carry sunscreen. Visit forts before 9am."},
        "jodhpur": {"temp": "26-36°C", "condition": "Hot and sunny", "rain_risk": "Low",  "tip": "Light cotton. Blue City best at golden hour."},
        "udaipur": {"temp": "25-35°C", "condition": "Pleasant",      "rain_risk": "Low",  "tip": "Evenings by the lake are cooler."},
        "kerala":  {"temp": "24-32°C", "condition": "Humid",         "rain_risk": "High", "tip": "Pack rain gear."},
        "goa":     {"temp": "26-33°C", "condition": "Warm, breezy",  "rain_risk": "Medium","tip": "South Goa for peace, North for nightlife."},
    }
    for dest in destinations:
        key = dest.lower()
        # Try extracting from WeatherTool output in research text
        pattern = rf"Weather in {dest}:?\s*([^\.]+\.?[^\.]*\.?)"
        match = re.search(pattern, research_text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            # Parse temp
            temp_m = re.search(r'(\d+[-–]\d+°?C)', raw)
            temp = temp_m.group(1) if temp_m else mock.get(key, {}).get("temp", "25-35°C")
            # Parse rain risk
            rain_m = re.search(r'Rain risk:\s*(\w+)', raw, re.IGNORECASE)
            rain = rain_m.group(1) if rain_m else mock.get(key, {}).get("rain_risk", "Low")
            # Extract tip
            tip_m = re.search(r'(?:tip|advice|note)[:\s]+([^\n\.]+)', raw, re.IGNORECASE)
            tip = tip_m.group(1).strip() if tip_m else mock.get(key, {}).get("tip", "Check forecast before outdoor plans.")
            weather[dest] = {"temp": temp, "condition": raw[:60], "rain_risk": rain, "tip": tip}
        else:
            # Use mock data keyed by city
            data = mock.get(key, {"temp": "25-35°C", "condition": "Warm and pleasant", "rain_risk": "Low", "tip": "Carry light layers."})
            weather[dest] = data

    return weather


def parse_local_tips(local_text: str) -> dict:
    """Parse LocalExpert structured output."""
    def extract_section(text, section_header, count=10):
        pattern = rf'{section_header}[:\s]*\n((?:\d+\..+\n?)+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            items = re.findall(r'\d+\.\s*(.+)', match.group(1))
            return [item.strip() for item in items[:count] if item.strip()]
        return []

    food    = extract_section(local_text, "FOOD SPOTS", 7)
    culture = extract_section(local_text, "CULTURAL ETIQUETTE", 6)
    avoid   = extract_section(local_text, "AVOID THESE", 6)
    packing = extract_section(local_text, "PACKING LIST", 12)
    safety  = extract_section(local_text, "SAFETY TIPS", 6)

    return {
        "food_spots":         food    or ["Laxmi Mishtan Bhandar, Jaipur — try pyaaz kachori ₹30", "Shri Mishrilal Hotel, Jodhpur — makhaniya lassi ₹60", "Natraj Dining Hall, Udaipur — dal baati churma ₹150"],
        "cultural_etiquette": culture or ["Remove shoes at temple entrances — carry a cloth bag for them", "Dress modestly at religious sites — carry a dupatta/scarf", "Ask before photographing locals — a smile and gesture goes a long way"],
        "common_mistakes":    avoid   or ["Don't buy gems from street touts near Hawa Mahal — all fake", "Fix auto price before boarding — insist on meter or app cab", "Don't visit Amer Fort at 11am — peak heat and peak crowd"],
        "packing_list":       packing or ["Sunscreen SPF 50+", "Cotton kurta (covers shoulders at temples)", "Comfortable walking shoes (cobblestone streets)", "Water bottle 1L", "Power bank", "ORS sachets (heat exhaustion prevention)", "Light scarf/dupatta"],
        "safety_tips":        safety  or ["Save 112 (emergency), 100 (police), 108 (ambulance)", "Use Ola/Uber — never unmarked cabs at night", "Carry photocopies of passport/ID, not originals"],
    }

def parse_itinerary(itinerary_text: str, request: TripRequest) -> list[dict]:
    """Parse ItineraryPlanner structured output into day objects."""
    from datetime import timedelta
    days = []
    start = request.trip_start_date
    destinations_cycle = request.destinations
    days_per_dest = max(1, request.duration_days // len(destinations_cycle))

    # Split into day blocks
    day_blocks = re.split(r'DAY\s+(\d+)\s*\|', itinerary_text, flags=re.IGNORECASE)

    if len(day_blocks) > 1:
        # Structured parsing — crew followed the format
        i = 1
        while i < len(day_blocks) - 1:
            try:
                day_num = int(day_blocks[i])
                block = day_blocks[i + 1] if i + 1 < len(day_blocks) else ""

                current_date = start + timedelta(days=day_num - 1)
                dest_idx = min((day_num - 1) // days_per_dest, len(destinations_cycle) - 1)
                city = destinations_cycle[dest_idx]

                # Extract city from block header if present
                city_match = re.search(r'\|\s*([A-Za-z]+)\s*\|', block[:100])
                if city_match:
                    city = city_match.group(1).strip()

                # Extract theme
                theme_match = re.search(r'\|\s*([^\n]+)\n', block[:200])
                theme = theme_match.group(1).strip() if theme_match else f"{city} Adventure"

                def extract_slot(text, time_label):
                    pattern = rf'{time_label}.*?:\s*([^\|]+)\|\s*(\d+)\s*mins?\s*\|\s*₹?([\d,]+)\s*\|\s*Tip:\s*([^\n]+)'
                    m = re.search(pattern, text, re.IGNORECASE)
                    if m:
                        return {
                            "time": time_label.replace("MORNING", "8:00 AM")
                                              .replace("AFTERNOON", "1:00 PM")
                                              .replace("EVENING", "6:00 PM"),
                            "activity": re.sub(r'^[\d:]+\s*[APap][Mm]\)?\s*[):\s]*', '', m.group(1)).strip(),
                            "duration_minutes": int(m.group(2)),
                            "cost_inr": float(m.group(3).replace(",", "")),
                            "tip": m.group(4).strip(),
                        }
                    return None

                morning = extract_slot(block, "MORNING") or {
                    "time": "8:00 AM",
                    "activity": f"Explore {city} landmarks",
                    "duration_minutes": 120, "cost_inr": 300,
                    "tip": "Visit early morning to avoid crowds",
                }
                afternoon = extract_slot(block, "AFTERNOON") or {
                    "time": "1:00 PM",
                    "activity": f"Lunch + afternoon sightseeing in {city}",
                    "duration_minutes": 180, "cost_inr": 600,
                    "tip": "Try local street food for authentic flavours",
                }
                evening = extract_slot(block, "EVENING") or (
                    {
                        "time": "6:00 PM",
                        "activity": f"Departure from {city} — head to airport/station",
                        "duration_minutes": 60,
                        "cost_inr": 0,
                        "tip": "Reach 2 hours early. Check bags and confirm return ticket.",
                    }
                    if day_num == request.duration_days else
                    {
                        "time": "6:00 PM",
                        "activity": f"Evening walk and dinner in {city}",
                        "duration_minutes": 120,
                        "cost_inr": 400,
                        "tip": "Golden hour is perfect for photography",
                    }
                )

                # Extract hotel name
                stay_match = re.search(r'STAY:\s*([^\n]+)', block, re.IGNORECASE)
                hotel = stay_match.group(1).strip() if stay_match else f"{request.accommodation_preference.value.title()} hotel in {city}"

                # Food budget
                food_match = re.search(r'FOOD BUDGET:\s*₹?([\d,]+)', block, re.IGNORECASE)
                food_budget = float(food_match.group(1).replace(",", "")) if food_match else round(request.budget_inr * 0.20 / request.duration_days, 2)

                days.append({
                    "day": day_num, "date": str(current_date),
                    "city": city, "theme": theme,
                    "morning": morning, "afternoon": afternoon, "evening": evening,
                    "accommodation": hotel,
                    "daily_food_budget_inr": food_budget,
                })
            except Exception as e:
                logger.warning(f"Day {i} parse error: {e}")
            i += 2
    else:
        logger.warning("Itinerary text did not follow DAY N | format — using skeleton")

    # Fallback if parsing produced no days
    if not days:
        for day_num in range(1, request.duration_days + 1):
            current_date = start + timedelta(days=day_num - 1)
            dest_idx = min((day_num - 1) // days_per_dest, len(destinations_cycle) - 1)
            city = destinations_cycle[dest_idx]
            days.append({
                "day": day_num, "date": str(current_date),
                "city": city, "theme": f"Day {day_num} — {city}",
                "morning":   {"time": "8:00 AM",  "activity": f"Explore {city} forts and palaces", "duration_minutes": 120, "cost_inr": 300, "tip": "Go early to beat crowds"},
                "afternoon": {"time": "1:00 PM", "activity": f"Local food trail in {city}",        "duration_minutes": 180, "cost_inr": 500, "tip": "Try the local thali"},
                "evening":   {"time": "6:00 PM",  "activity": f"Sunset views and street shopping",  "duration_minutes": 120, "cost_inr": 400, "tip": "Golden hour is perfect for photos"},
                "accommodation": f"{request.accommodation_preference.value.title()} hotel in {city}",
                "daily_food_budget_inr": round(request.budget_inr * 0.20 / request.duration_days, 2),
            })

    logger.info(f"Itinerary parsed — {len(days)} days")
    return days


# ─── Main Endpoint ────────────────────────────────────────────────────────────

@router.post("/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest, db: AsyncSession = Depends(get_db)):
    trip_id = str(uuid4())
    start_time = time.time()

    logger.info(f"[{trip_id}] New trip request: {request.destinations} | {request.duration_days} days | ₹{request.budget_inr}")

    # Pre-flight budget feasibility check
    feasibility = check_budget_feasibility(
        budget_inr=request.budget_inr,
        duration_days=request.duration_days,
        group_size=request.group_size,
        travel_style=request.travel_style.value,
        num_destinations=len(request.destinations),
    )
    logger.info(f"[{trip_id}] Budget feasibility: {feasibility.value}")

    # Save initial record to DB (status: pending)
    db_trip = TripPlan(
        id=trip_id,
        origin=request.origin,
        destinations=request.destinations,
        duration_days=request.duration_days,
        budget_inr=request.budget_inr,
        group_size=request.group_size,
        travel_style=request.travel_style.value,
        interests=request.interests,
        accommodation_preference=request.accommodation_preference.value,
        trip_start_date=str(request.trip_start_date),
        status="pending",
    )
    db.add(db_trip)
    await db.commit()

    try:
        # Run the 4-agent crew
        crew_result = run_crew(
            origin=request.origin,
            destinations=request.destinations,
            duration_days=request.duration_days,
            budget_inr=request.budget_inr,
            group_size=request.group_size,
            travel_style=request.travel_style.value,
            interests=request.interests,
            accommodation_preference=request.accommodation_preference.value,
            trip_start_date=str(request.trip_start_date),
        )

        task_outputs = crew_result["task_outputs"]

        # Parse each agent's output
        budget_data = parse_budget_breakdown(task_outputs["budget"], request.budget_inr)
        weather_data = parse_weather_info(task_outputs["research"], request.destinations)
        local_data = parse_local_tips(task_outputs["local_tips"])
        itinerary_data = parse_itinerary(task_outputs["itinerary"], request)

        processing_time = round(time.time() - start_time, 2)

        # Build response
        response = TripResponse(
            trip_id=trip_id,
            trip_summary=TripSummary(
                origin=request.origin,
                destinations=request.destinations,
                duration_days=request.duration_days,
                total_budget_inr=request.budget_inr,
                budget_feasibility=feasibility,
                best_season="October-March",
            ),
            itinerary=itinerary_data,
            budget_breakdown=BudgetBreakdown(**budget_data),
            weather_info={dest: WeatherInfo(**weather_data[dest]) for dest in request.destinations},
            local_tips=LocalTips(**local_data),
            processing_time_seconds=processing_time,
        )

        # Update DB record to completed
        db_trip.itinerary = itinerary_data
        db_trip.budget_breakdown = budget_data
        db_trip.weather_info = weather_data
        db_trip.local_tips = local_data
        db_trip.budget_feasibility = feasibility.value
        db_trip.best_season = "October-March"
        db_trip.processing_time_seconds = processing_time
        db_trip.status = "completed"
        await db.commit()

        logger.success(f"[{trip_id}] Trip plan completed in {processing_time}s")
        return response

    except Exception as e:
        # Update DB record to failed
        db_trip.status = "failed"
        db_trip.error_message = str(e)
        await db.commit()
        logger.error(f"[{trip_id}] Trip planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")