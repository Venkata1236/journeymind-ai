from crewai import Task
from pydantic import BaseModel
from loguru import logger


# ─── Output Schemas for Structured JSON ──────────────────────────────────────

class ResearchOutput(BaseModel):
    destinations: dict  # {city: {attractions, hidden_gems, transport, weather}}

class ItineraryOutput(BaseModel):
    days: list  # list of day objects

class BudgetOutput(BaseModel):
    accommodation_inr: float
    food_inr: float
    transport_inr: float
    activities_inr: float
    shopping_buffer_inr: float
    contingency_inr: float
    total_inr: float
    feasibility: str
    notes: str

class LocalOutput(BaseModel):
    food_spots: list
    cultural_etiquette: list
    common_mistakes: list
    packing_list: list
    safety_tips: list


def get_destination_research_task(agent, destinations, travel_style, interests):
    logger.info("Creating destination research task")
    dest_str = ", ".join(destinations)
    interests_str = ", ".join(interests)

    return Task(
        description=f"""
Research each destination in this list: {dest_str}

Travel style: {travel_style}
Traveler interests: {interests_str}

For EACH destination, use AttractionTool with format "city|category" to find attractions.
Use WeatherTool for each city to get actual weather data.

For every destination provide:
1. Top 3 specific named attractions (real places, not generic descriptions)
2. 2 hidden gems (off the beaten path, authentic experiences)
3. Best neighbourhoods to stay in
4. Local transport options (auto, cab, bike rental, costs)
5. Inter-city travel from previous destination (train/bus/flight, duration, approx cost)
6. Weather summary from WeatherTool

Be specific. "Hawa Mahal" not "a famous palace". "Sardar Market" not "a local market".
""",
        expected_output=f"""
A detailed research report for each destination in {dest_str}.
For each city: named attractions, hidden gems, transport options, weather data, and inter-city travel info.
Format as clear sections per city with specific names and costs.
""",
        agent=agent,
    )


def get_itinerary_task(agent, destinations, duration_days, travel_style, trip_start_date, context_tasks):
    logger.info("Creating itinerary planning task")
    dest_str = ", ".join(destinations)

    return Task(
        description=f"""
Using the destination research provided, create a day-by-day itinerary.

Trip: {dest_str} | {duration_days} days | Style: {travel_style} | Start: {trip_start_date}

STRICT RULES:
- Maximum 4 activities per day (morning, afternoon, evening, optional night)
- Each activity must be a SPECIFIC named place from the research (not generic)
- Include realistic travel time between attractions
- Day 1: Light schedule — arrival, check-in, one nearby attraction, dinner
- Last day: Half-day only — morning activity, checkout, departure
- Include meal recommendations at each time block (specific restaurant/dhaba name)
- Distribute days across destinations: {dest_str}

For EACH day output this exact structure:
DAY [N] | [DATE] | [CITY] | [THEME]
MORNING (8:00 AM): [specific activity name] | [duration mins] | ₹[cost] | Tip: [insider tip]
AFTERNOON (1:00 PM): [specific activity name] | [duration mins] | ₹[cost] | Tip: [insider tip]
EVENING (6:00 PM): [specific activity name] | [duration mins] | ₹[cost] | Tip: [insider tip]
STAY: [specific hotel name matching {travel_style} style]
FOOD BUDGET: ₹[amount]
""",
        expected_output=f"""
A complete {duration_days}-day itinerary with specific named activities, timings, costs, and accommodation for each day.
Each day clearly labeled with DAY N | DATE | CITY | THEME format.
Maximum 4 activities per day. Realistic timing and costs.
""",
        agent=agent,
        context=context_tasks,
    )


def get_budget_task(agent, budget_inr, group_size, duration_days, travel_style, context_tasks):
    logger.info("Creating budget analysis task")

    return Task(
        description=f"""
Based on the itinerary provided, create a detailed budget breakdown.

Total budget: ₹{budget_inr:,.0f}
Group size: {group_size} people
Duration: {duration_days} days
Style: {travel_style}

Use CurrencyTool with "{budget_inr}" to show international equivalent.

RULES:
- Categories: accommodation, food, transport, activities, shopping_buffer, contingency
- Contingency = exactly 10% of total budget
- All categories MUST sum to exactly ₹{budget_inr:,.0f} — no exceptions
- Per person per day = ₹{budget_inr / (group_size * duration_days):,.0f}

FEASIBILITY CHECK:
- Heritage style minimum: ₹2,500/person/day
- If per_person_per_day >= ₹3,250 → FEASIBLE
- If per_person_per_day >= ₹2,500 → TIGHT
- If per_person_per_day < ₹2,500 → OVER_BUDGET

Output this exact format:
BUDGET BREAKDOWN:
accommodation_inr: [amount]
food_inr: [amount]
transport_inr: [amount]
activities_inr: [amount]
shopping_buffer_inr: [amount]
contingency_inr: [amount]
total_inr: {budget_inr}
FEASIBILITY: [FEASIBLE/TIGHT/OVER_BUDGET]
NOTES: [1-2 sentences on budget adequacy and key cost drivers]
INTERNATIONAL: [CurrencyTool output]
""",
        expected_output=f"""
A complete budget breakdown with all 6 categories summing exactly to ₹{budget_inr:,.0f}.
Feasibility verdict and brief notes on budget adequacy.
""",
        agent=agent,
        context=context_tasks,
    )


def get_local_expert_task(agent, destinations, interests, context_tasks):
    logger.info("Creating local expert task")
    dest_str = ", ".join(destinations)
    interests_str = ", ".join(interests)

    return Task(
        description=f"""
Using all research and itinerary provided, add the authentic local layer.

Destinations: {dest_str}
Traveler interests: {interests_str}

Use AttractionTool for "city|food" queries to find authentic food spots.
Use WeatherTool for each city to add weather-specific packing advice.

Provide SPECIFIC recommendations — not generic advice.
"Laxmi Mishtan Bhandar on Johari Bazaar for dal baati churma" not "try local food".

Output these exact sections:

FOOD SPOTS:
1. [Specific restaurant/stall name] — [city] — [what to order] — ₹[cost]
2. [repeat for 5 spots minimum]

CULTURAL ETIQUETTE:
1. [Specific actionable tip]
[5 tips minimum]

AVOID THESE:
1. [Specific tourist trap or mistake to avoid]
[5 mistakes minimum]

PACKING LIST:
1. [Item specific to this trip's weather and activities]
[10 items minimum]

SAFETY TIPS:
1. [Specific safety tip for these destinations]
[5 tips minimum]
""",
        expected_output=f"""
Authentic, specific local tips for {dest_str} covering food spots (with names and costs),
cultural etiquette, tourist mistakes to avoid, packing list, and safety tips.
All recommendations must be specific — no generic travel advice.
""",
        agent=agent,
        context=context_tasks,
    )