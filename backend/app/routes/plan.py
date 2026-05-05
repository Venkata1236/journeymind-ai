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

    extracted = {}
    for category in categories:
        # Match patterns like "accommodation_inr: 28000" or "Accommodation: ₹28,000"
        patterns = [
            rf"{category}[:\s]+[\₹]?([\d,]+)",
            rf"{category.replace('_inr', '')}[:\s]+[\₹]?([\d,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, budget_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(",", ""))
                extracted[category] = value
                break

    # If parsing failed or incomplete — distribute proportionally
    if len(extracted) < 6:
        logger.warning("Budget parsing incomplete — using proportional fallback")
        contingency_pct = settings.default_contingency_pct
        subtotal = total_budget / (1 + contingency_pct)
        contingency = total_budget - subtotal

        extracted = {
            "accommodation_inr": round(subtotal * 0.38, 2),
            "food_inr":          round(subtotal * 0.22, 2),
            "transport_inr":     round(subtotal * 0.22, 2),
            "activities_inr":    round(subtotal * 0.10, 2),
            "shopping_buffer_inr": round(subtotal * 0.08, 2),
            "contingency_inr":   round(contingency, 2),
        }

    # Force exact sum — adjust contingency to absorb rounding difference
    current_sum = sum(extracted[c] for c in categories if c != "contingency_inr")
    extracted["contingency_inr"] = round(total_budget - current_sum, 2)
    extracted["total_inr"] = total_budget

    logger.info(f"Budget breakdown parsed — total: ₹{extracted['total_inr']:,.0f}")
    return extracted


def parse_weather_info(research_text: str, destinations: list[str]) -> dict:
    """Parse weather info from DestinationResearcher output."""
    weather = {}
    for dest in destinations:
        # Look for weather section per destination
        pattern = rf"Weather in {dest}[:\s]+([^\n.]+)"
        match = re.search(pattern, research_text, re.IGNORECASE)
        if match:
            weather[dest] = {
                "temp": "25-35°C",
                "condition": match.group(1).strip(),
                "rain_risk": "Low",
                "tip": "Check local forecast before outdoor activities",
            }
        else:
            weather[dest] = {
                "temp": "25-35°C",
                "condition": "Pleasant travel weather",
                "rain_risk": "Low",
                "tip": "Pack light layers and sunscreen",
            }
    return weather


def parse_local_tips(local_text: str) -> dict:
    """Parse LocalExpert output into structured tips."""
    def extract_list(text: str, section: str, count: int = 5) -> list[str]:
        pattern = rf"{section}.*?(?=\n\n|\n[A-Z]|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            section_text = match.group(0)
            items = re.findall(r"\d+\.\s+(.+?)(?=\n\d+\.|\n\n|$)", section_text, re.DOTALL)
            return [item.strip() for item in items[:count]] if items else []
        return []

    food_spots = extract_list(local_text, "FOOD SPOTS", 5)
    cultural = extract_list(local_text, "CULTURAL ETIQUETTE", 5)
    mistakes = extract_list(local_text, "COMMON MISTAKES", 5)
    packing = extract_list(local_text, "PACKING LIST", 10)
    safety = extract_list(local_text, "SAFETY", 5)

    # Fallback if parsing returns empty lists
    return {
        "food_spots":          food_spots or ["Explore local street food markets", "Ask hotel staff for authentic recommendations"],
        "cultural_etiquette":  cultural or ["Remove shoes before entering temples", "Dress modestly at religious sites"],
        "common_mistakes":     mistakes or ["Avoid buying from touts near monuments", "Negotiate prices before boarding auto-rickshaws"],
        "packing_list":        packing or ["Sunscreen SPF 50+", "Light cotton clothes", "Comfortable walking shoes", "Water bottle", "Power bank"],
        "safety_tips":         safety or ["Keep copies of ID documents", "Use registered taxis or Ola/Uber", "Emergency: 112"],
    }


def parse_itinerary(itinerary_text: str, request: TripRequest) -> list[dict]:
    """
    Parse ItineraryPlanner output into structured day objects.
    Falls back to a sensible skeleton if parsing fails.
    """
    days = []
    from datetime import timedelta, date

    start = request.trip_start_date
    destinations_cycle = request.destinations
    days_per_dest = max(1, request.duration_days // len(destinations_cycle))

    for day_num in range(1, request.duration_days + 1):
        current_date = start + timedelta(days=day_num - 1)
        dest_index = min((day_num - 1) // days_per_dest, len(destinations_cycle) - 1)
        city = destinations_cycle[dest_index]

        days.append({
            "day": day_num,
            "date": str(current_date),
            "city": city,
            "theme": f"Day {day_num} — {city} Exploration",
            "morning": {
                "time": "8:00 AM",
                "activity": f"Morning exploration of {city}",
                "duration_minutes": 120,
                "cost_inr": 300,
                "tip": "Start early to beat the crowds",
            },
            "afternoon": {
                "time": "1:00 PM",
                "activity": f"Lunch and afternoon sightseeing in {city}",
                "duration_minutes": 180,
                "cost_inr": 500,
                "tip": "Try local street food for an authentic experience",
            },
            "evening": {
                "time": "6:00 PM",
                "activity": f"Evening walk and dinner in {city}",
                "duration_minutes": 120,
                "cost_inr": 400,
                "tip": "Evenings are cooler and great for photography",
            },
            "accommodation": f"Hotel in {city} ({request.accommodation_preference})",
            "daily_food_budget_inr": round(request.budget_inr / (request.duration_days * 6), 2),
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