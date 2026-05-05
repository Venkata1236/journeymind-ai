from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.connection import get_db
from app.database.models import TripPlan
from app.models.schemas import TripHistoryItem
from loguru import logger

router = APIRouter(prefix="/api", tags=["History"])


@router.get("/history", response_model=list[TripHistoryItem])
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of all past trip plans.
    Returns most recent first.
    """
    logger.info(f"Fetching history — limit: {limit}, offset: {offset}")

    result = await db.execute(
        select(TripPlan)
        .order_by(desc(TripPlan.created_at))
        .limit(limit)
        .offset(offset)
    )
    trips = result.scalars().all()

    logger.info(f"Returning {len(trips)} trip records")

    return [
        TripHistoryItem(
            trip_id=str(trip.id),
            origin=trip.origin,
            destinations=trip.destinations,
            duration_days=trip.duration_days,
            budget_inr=trip.budget_inr,
            budget_feasibility=trip.budget_feasibility,
            status=trip.status,
            created_at=str(trip.created_at),
        )
        for trip in trips
    ]


@router.get("/history/{trip_id}", response_model=dict)
async def get_trip_by_id(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full details of a single past trip plan by ID.
    """
    logger.info(f"Fetching trip: {trip_id}")

    result = await db.execute(
        select(TripPlan).where(TripPlan.id == trip_id)
    )
    trip = result.scalar_one_or_none()

    if not trip:
        logger.warning(f"Trip not found: {trip_id}")
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

    logger.info(f"Returning trip: {trip_id} | status: {trip.status}")

    return {
        "trip_id":                  str(trip.id),
        "origin":                   trip.origin,
        "destinations":             trip.destinations,
        "duration_days":            trip.duration_days,
        "budget_inr":               trip.budget_inr,
        "group_size":               trip.group_size,
        "travel_style":             trip.travel_style,
        "interests":                trip.interests,
        "accommodation_preference": trip.accommodation_preference,
        "trip_start_date":          trip.trip_start_date,
        "itinerary":                trip.itinerary,
        "budget_breakdown":         trip.budget_breakdown,
        "weather_info":             trip.weather_info,
        "local_tips":               trip.local_tips,
        "budget_feasibility":       trip.budget_feasibility,
        "best_season":              trip.best_season,
        "processing_time_seconds":  trip.processing_time_seconds,
        "status":                   trip.status,
        "error_message":            trip.error_message,
        "created_at":               str(trip.created_at),
    }


@router.delete("/history/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a trip plan by ID.
    """
    logger.info(f"Deleting trip: {trip_id}")

    result = await db.execute(
        select(TripPlan).where(TripPlan.id == trip_id)
    )
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

    await db.delete(trip)
    await db.commit()

    logger.info(f"Trip deleted: {trip_id}")