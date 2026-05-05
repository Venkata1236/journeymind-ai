from crewai import Task
from app.agents.agents import (
    get_destination_researcher,
    get_itinerary_planner,
    get_budget_analyst,
    get_local_expert,
)
from loguru import logger


def create_tasks(
    origin: str,
    destinations: list[str],
    duration_days: int,
    budget_inr: float,
    group_size: int,
    travel_style: str,
    interests: list[str],
    accommodation_preference: str,
    trip_start_date: str,
):
    """
    Create all 4 tasks with proper context passing.
    Each task receives the previous task's output via context=[].
    This is the sequential crew's backbone.
    """
    destinations_str = ", ".join(destinations)
    interests_str = ", ".join(interests)

    researcher = get_destination_researcher()
    planner = get_itinerary_planner()
    analyst = get_budget_analyst()
    expert = get_local_expert()

    logger.info(f"Creating tasks for {destinations_str} | {duration_days} days | ₹{budget_inr}")

    # ─── Task 1: Destination Research ────────────────────────────────────────
    task_research = Task(
        description=(
            f"Research each destination for a {duration_days}-day trip from {origin} "
            f"to {destinations_str}.\n\n"
            f"Traveler profile:\n"
            f"- Travel style: {travel_style}\n"
            f"- Interests: {interests_str}\n"
            f"- Group size: {group_size} people\n"
            f"- Accommodation preference: {accommodation_preference}\n\n"
            f"For EACH destination in [{destinations_str}], use AttractionTool to research:\n"
            f"1. Top 5 must-visit attractions (use interests to prioritize)\n"
            f"2. Top 3 hidden gems not on standard tourist itineraries\n"
            f"3. Best neighbourhoods to stay in\n"
            f"4. Local transport options within the city\n"
            f"5. Inter-city travel options and travel time to the next destination\n\n"
            f"Use WeatherTool to get weather for each destination.\n"
            f"Format your output clearly per destination with numbered lists."
        ),
        expected_output=(
            f"A detailed research report for each of [{destinations_str}] containing: "
            f"top attractions, hidden gems, best neighbourhoods, local transport, "
            f"inter-city travel options, and weather summary. "
            f"Clearly labeled per destination."
        ),
        agent=researcher,
    )

    # ─── Task 2: Itinerary Planning ───────────────────────────────────────────
    # context=[task_research] passes Task 1's output to this task
    task_itinerary = Task(
        description=(
            f"Using the destination research provided, create a detailed day-by-day "
            f"itinerary for {duration_days} days starting {trip_start_date}.\n\n"
            f"Trip details:\n"
            f"- Origin: {origin}\n"
            f"- Destinations: {destinations_str}\n"
            f"- Travel style: {travel_style}\n"
            f"- Interests: {interests_str}\n"
            f"- Accommodation preference: {accommodation_preference}\n\n"
            f"Rules you MUST follow:\n"
            f"1. Maximum 4 activities per day — quality over quantity\n"
            f"2. Day 1 must be light — arrival, check-in, one nearby attraction, dinner\n"
            f"3. Last day must be light — breakfast, one activity, travel to airport/station\n"
            f"4. Always include morning (8-12pm), afternoon (12-5pm), evening (5-9pm) blocks\n"
            f"5. Include meal recommendations at each time block\n"
            f"6. Account for travel time between attractions\n"
            f"7. Include accommodation name per day (matching {accommodation_preference} preference)\n"
            f"8. Include estimated cost in INR per activity\n\n"
            f"Use AttractionTool to validate specific activity recommendations."
        ),
        expected_output=(
            f"A complete {duration_days}-day itinerary with morning, afternoon, and evening "
            f"blocks for each day. Each block must include: time, activity name, duration, "
            f"estimated cost in INR, and one insider tip. Each day must include accommodation "
            f"name and daily food budget estimate."
        ),
        agent=planner,
        context=[task_research],  # ← Task 1 output flows into Task 2
    )

    # ─── Task 3: Budget Analysis ──────────────────────────────────────────────
    # context=[task_research, task_itinerary] passes both Task 1 and Task 2 outputs
    task_budget = Task(
        description=(
            f"Using the itinerary provided, create a realistic budget breakdown for "
            f"the full trip.\n\n"
            f"Budget constraints:\n"
            f"- Total budget: ₹{budget_inr:,.0f}\n"
            f"- Group size: {group_size} people\n"
            f"- Duration: {duration_days} days\n"
            f"- Travel style: {travel_style}\n"
            f"- Accommodation preference: {accommodation_preference}\n\n"
            f"Rules you MUST follow:\n"
            f"1. Break down budget into EXACTLY these 6 categories:\n"
            f"   - accommodation_inr\n"
            f"   - food_inr\n"
            f"   - transport_inr\n"
            f"   - activities_inr\n"
            f"   - shopping_buffer_inr\n"
            f"   - contingency_inr (MUST be exactly 10% of subtotal)\n"
            f"2. All 6 categories MUST sum to exactly ₹{budget_inr:,.0f}\n"
            f"3. Use CurrencyTool to convert ₹{budget_inr:,.0f} to USD/EUR for reference\n"
            f"4. Provide budget feasibility rating:\n"
            f"   - FEASIBLE: budget is comfortable for the requested style\n"
            f"   - TIGHT: doable but requires discipline and trade-offs\n"
            f"   - OVER_BUDGET: budget is unrealistic — state exactly why and suggest minimum needed\n"
            f"5. If OVER_BUDGET, do NOT silently adjust — explicitly state the shortfall amount\n"
            f"6. Include per-person cost (total / {group_size})\n"
            f"7. Include best_season recommendation for {destinations_str}"
        ),
        expected_output=(
            f"A budget breakdown with exactly 6 categories summing to ₹{budget_inr:,.0f}. "
            f"Must include: feasibility rating (FEASIBLE/TIGHT/OVER_BUDGET), "
            f"per-person cost, currency conversion, and best season. "
            f"If OVER_BUDGET, include specific shortfall amount and adjustments needed."
        ),
        agent=analyst,
        context=[task_research, task_itinerary],  # ← Task 1 + Task 2 outputs flow into Task 3
    )

    # ─── Task 4: Local Expert Tips ────────────────────────────────────────────
    # context=[task_research, task_itinerary, task_budget] — receives ALL previous outputs
    task_local = Task(
        description=(
            f"Using all the research, itinerary, and budget information provided, "
            f"add the essential human layer to this trip plan.\n\n"
            f"Trip context:\n"
            f"- Destinations: {destinations_str}\n"
            f"- Travel style: {travel_style}\n"
            f"- Interests: {interests_str}\n"
            f"- First-time visitors to these destinations\n\n"
            f"Provide ALL of the following — be specific, not generic:\n\n"
            f"1. FOOD SPOTS (5 per destination):\n"
            f"   - Specific restaurant/stall name + what to order\n"
            f"   - Use AttractionTool with 'food' category to ground recommendations\n\n"
            f"2. CULTURAL ETIQUETTE (5 tips):\n"
            f"   - Specific dos and don'ts for {destinations_str}\n"
            f"   - Dress codes at religious sites\n\n"
            f"3. COMMON MISTAKES TO AVOID (5 tips):\n"
            f"   - Tourist traps specific to {destinations_str}\n"
            f"   - Scams to watch for\n\n"
            f"4. PACKING LIST (10 items):\n"
            f"   - Based on WeatherTool data for {destinations_str}\n"
            f"   - Specific to {travel_style} travel style\n\n"
            f"5. SAFETY TIPS (5 tips):\n"
            f"   - Destination-specific safety advice\n"
            f"   - Emergency contacts format"
        ),
        expected_output=(
            f"Five sections: food_spots (5 per destination), cultural_etiquette (5 tips), "
            f"common_mistakes (5 tips), packing_list (10 items), safety_tips (5 tips). "
            f"Every tip must be specific to {destinations_str} — no generic travel advice."
        ),
        agent=expert,
        context=[task_research, task_itinerary, task_budget],  # ← All 3 previous outputs
    )

    logger.info("All 4 tasks created with context passing configured")
    return task_research, task_itinerary, task_budget, task_local