from crewai import Crew, Process
from app.agents.tasks import create_tasks
from loguru import logger


def assemble_crew(
    origin: str,
    destinations: list[str],
    duration_days: int,
    budget_inr: float,
    group_size: int,
    travel_style: str,
    interests: list[str],
    accommodation_preference: str,
    trip_start_date: str,
) -> Crew:
    """
    Assemble the JourneyMind sequential crew.
    Tasks and agents are created fresh per request — no state bleed between trips.
    """
    logger.info(f"Assembling JourneyMind crew for {destinations} | {duration_days} days")

    task_research, task_itinerary, task_budget, task_local = create_tasks(
        origin=origin,
        destinations=destinations,
        duration_days=duration_days,
        budget_inr=budget_inr,
        group_size=group_size,
        travel_style=travel_style,
        interests=interests,
        accommodation_preference=accommodation_preference,
        trip_start_date=trip_start_date,
    )

    crew = Crew(
        agents=[
            task_research.agent,
            task_itinerary.agent,
            task_budget.agent,
            task_local.agent,
        ],
        tasks=[
            task_research,
            task_itinerary,
            task_budget,
            task_local,
        ],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("JourneyMind crew assembled — process: sequential")
    return crew


def run_crew(
    origin: str,
    destinations: list[str],
    duration_days: int,
    budget_inr: float,
    group_size: int,
    travel_style: str,
    interests: list[str],
    accommodation_preference: str,
    trip_start_date: str,
) -> dict:
    """
    Run the crew and return raw outputs per task.
    CrewAI 1.14.4: result.tasks_output is the list of TaskOutput objects.
    """
    crew = assemble_crew(
        origin=origin,
        destinations=destinations,
        duration_days=duration_days,
        budget_inr=budget_inr,
        group_size=group_size,
        travel_style=travel_style,
        interests=interests,
        accommodation_preference=accommodation_preference,
        trip_start_date=trip_start_date,
    )

    logger.info("Starting JourneyMind crew execution...")
    result = crew.kickoff()

    # CrewAI 1.14.4 — result.tasks_output is list[TaskOutput]
    task_names = ["research", "itinerary", "budget", "local_tips"]
    task_outputs = {}

    for i, task_name in enumerate(task_names):
        if i < len(result.tasks_output):
            raw = result.tasks_output[i].raw or ""
        else:
            raw = ""
        task_outputs[task_name] = raw
        logger.info(f"Task '{task_name}' output: {len(raw)} chars")
        logger.debug(f"Task '{task_name}' preview: {raw[:200]}")

    logger.success("JourneyMind crew execution complete")

    return {
        "final_output": result.raw,
        "task_outputs": task_outputs,
    }