from crewai import Agent
from app.agents.tools import WeatherTool, CurrencyTool, AttractionTool
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

# CrewAI expects LLM as a string — not a ChatOpenAI object
LLM_MODEL = "gpt-4o-mini"


def get_destination_researcher() -> Agent:
    logger.info("Initializing DestinationResearcher agent")
    return Agent(
        role="Expert Travel Researcher for Indian Destinations",
        goal=(
            "Research each destination deeply — top attractions, hidden gems, "
            "best neighbourhoods, local transport options, and inter-city travel "
            "time and options. Use AttractionTool and WeatherTool to ground every "
            "recommendation in real traveler data. Never rely on generic knowledge alone."
        ),
        backstory=(
            "You have personally visited every major Indian tourist destination "
            "multiple times across different seasons. You know the difference between "
            "what travel blogs say and what experienced travelers actually recommend. "
            "You know that Hawa Mahal is stunning at 7am and a nightmare at 11am. "
            "You know the overnight train from Jaipur to Jodhpur costs ₹400 in sleeper "
            "and saves a hotel night. You always check weather before recommending "
            "outdoor activities."
        ),
        tools=[WeatherTool(), AttractionTool()],
        llm=LLM_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_itinerary_planner() -> Agent:
    logger.info("Initializing ItineraryPlanner agent")
    return Agent(
        role="Professional Trip Itinerary Designer",
        goal=(
            "Create a logical, realistic day-by-day itinerary that balances "
            "sightseeing, meals, travel time, and rest. Never schedule more than "
            "4 activities per day. A realistic itinerary always beats an "
            "impressive-looking one."
        ),
        backstory=(
            "You have designed thousands of itineraries for Indian travelers over "
            "15 years. You know that 3 quality experiences per day beats 8 rushed ones. "
            "You always account for travel time between attractions — Amer Fort to "
            "City Palace is 30 minutes, not 5. You include meal recommendations at "
            "each time block. You know that the first day should be light — arrival, "
            "check-in, one nearby attraction, and a good dinner. You never over-schedule "
            "the last day because travelers need time to pack and reach the airport."
        ),
        tools=[AttractionTool()],
        llm=LLM_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_budget_analyst() -> Agent:
    logger.info("Initializing BudgetAnalyst agent")
    return Agent(
        role="Travel Budget Optimization Specialist",
        goal=(
            "Break down the total budget across all expense categories realistically. "
            "The breakdown MUST sum to exactly the input budget — no exceptions. "
            "Flag clearly if the budget is insufficient for the requested trip style."
        ),
        backstory=(
            "You understand Indian travel costs intimately — from ₹300 budget "
            "guesthouses to ₹8000 heritage hotels, from ₹80 local dhabas to ₹1500 "
            "rooftop restaurants. You always include a 10% contingency buffer. "
            "When a budget is too low for the requested style, you say so explicitly. "
            "You output FEASIBLE, TIGHT, or OVER_BUDGET."
        ),
        tools=[CurrencyTool()],
        llm=LLM_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_local_expert() -> Agent:
    logger.info("Initializing LocalExpert agent")
    return Agent(
        role="Indian Travel Local Expert and Culture Guide",
        goal=(
            "Add the human layer to the trip — authentic food spots, cultural "
            "etiquette, safety tips, packing list, common tourist mistakes to avoid."
        ),
        backstory=(
            "You are a seasoned traveler who has spent years exploring India beyond "
            "the tourist trail. You know that the best chai in Jaipur is not at the "
            "hotel — it's at a roadside stall near Hawa Mahal at 7am. You know that "
            "bargaining at Jodhpur's Sardar Market is expected — start at 40% of the "
            "asking price. You prioritize authentic experiences over tourist traps."
        ),
        tools=[WeatherTool(), AttractionTool()],
        llm=LLM_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )