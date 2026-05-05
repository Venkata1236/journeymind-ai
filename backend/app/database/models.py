from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base
from datetime import datetime, timezone
import uuid


class TripPlan(Base):
    __tablename__ = "trip_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Trip inputs
    origin = Column(String(100), nullable=False)
    destinations = Column(JSON, nullable=False)        # ["Jaipur", "Jodhpur", "Udaipur"]
    duration_days = Column(Integer, nullable=False)
    budget_inr = Column(Float, nullable=False)
    group_size = Column(Integer, nullable=False)
    travel_style = Column(String(50), nullable=False)
    interests = Column(JSON, nullable=False)           # ["street food", "architecture"]
    accommodation_preference = Column(String(50), nullable=False)
    trip_start_date = Column(String(20), nullable=False)

    # Trip outputs
    itinerary = Column(JSON, nullable=True)            # Full day-by-day plan
    budget_breakdown = Column(JSON, nullable=True)     # Category-wise breakdown
    weather_info = Column(JSON, nullable=True)         # Per-city weather
    local_tips = Column(JSON, nullable=True)           # Food, culture, packing
    budget_feasibility = Column(String(20), nullable=True)  # FEASIBLE/TIGHT/OVER_BUDGET
    best_season = Column(String(100), nullable=True)

    # Metadata
    processing_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="pending")     # pending / completed / failed
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<TripPlan id={self.id} destinations={self.destinations} status={self.status}>"