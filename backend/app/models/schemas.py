from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class TravelStyle(str, Enum):
    budget = "budget"
    comfort = "comfort"
    heritage = "heritage"
    luxury = "luxury"


class AccommodationPreference(str, Enum):
    budget_hostel = "budget_hostel"
    guesthouse = "guesthouse"
    hotel = "hotel"
    heritage = "heritage"
    resort = "resort"


class BudgetFeasibility(str, Enum):
    feasible = "FEASIBLE"
    tight = "TIGHT"
    over_budget = "OVER_BUDGET"


# ─── Request Schema ───────────────────────────────────────────────────────────

class TripRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=100, example="Hyderabad")
    destinations: list[str] = Field(..., min_length=1, max_items=10, example=["Jaipur", "Jodhpur", "Udaipur"])
    duration_days: int = Field(..., ge=1, le=30, example=7)
    budget_inr: float = Field(..., ge=5000, le=5000000, example=80000)
    group_size: int = Field(..., ge=1, le=10, example=2)
    travel_style: TravelStyle = Field(..., example="heritage")
    interests: list[str] = Field(..., min_length=1, example=["street food", "architecture", "photography"])
    accommodation_preference: AccommodationPreference = Field(..., example="heritage")
    trip_start_date: date = Field(..., example="2026-06-15")

    @field_validator("destinations")
    @classmethod
    def destinations_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Destinations must be unique")
        return v

    @field_validator("interests")
    @classmethod
    def interests_must_be_unique(cls, v):
        return list(set(v))


# ─── Response Sub-schemas ─────────────────────────────────────────────────────

class TimeBlock(BaseModel):
    time: str
    activity: str
    duration_minutes: int
    cost_inr: float
    tip: str


class DayItinerary(BaseModel):
    day: int
    date: str
    city: str
    theme: str
    morning: Optional[TimeBlock] = None
    afternoon: Optional[TimeBlock] = None
    evening: Optional[TimeBlock] = None
    accommodation: str
    daily_food_budget_inr: float


class BudgetBreakdown(BaseModel):
    accommodation_inr: float
    food_inr: float
    transport_inr: float
    activities_inr: float
    shopping_buffer_inr: float
    contingency_inr: float
    total_inr: float

    @field_validator("total_inr")
    @classmethod
    def total_must_match_sum(cls, v, values):
        fields = ["accommodation_inr", "food_inr", "transport_inr",
                  "activities_inr", "shopping_buffer_inr", "contingency_inr"]
        calculated = sum(values.data.get(f, 0) for f in fields)
        if abs(calculated - v) > 1:  # allow ₹1 rounding tolerance
            raise ValueError(f"Budget total {v} does not match sum {calculated}")
        return v


class WeatherInfo(BaseModel):
    temp: str
    condition: str
    rain_risk: str
    tip: str


class LocalTips(BaseModel):
    food_spots: list[str]
    cultural_etiquette: list[str]
    common_mistakes: list[str]
    packing_list: list[str]
    safety_tips: list[str]


class TripSummary(BaseModel):
    origin: str
    destinations: list[str]
    duration_days: int
    total_budget_inr: float
    budget_feasibility: BudgetFeasibility
    best_season: str


# ─── Full Response Schema ─────────────────────────────────────────────────────

class TripResponse(BaseModel):
    trip_id: str
    trip_summary: TripSummary
    itinerary: list[DayItinerary]
    budget_breakdown: BudgetBreakdown
    weather_info: dict[str, WeatherInfo]
    local_tips: LocalTips
    processing_time_seconds: float


# ─── History Schemas ──────────────────────────────────────────────────────────

class TripHistoryItem(BaseModel):
    trip_id: str
    origin: str
    destinations: list[str]
    duration_days: int
    budget_inr: float
    budget_feasibility: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    environment: str
    faiss_index_loaded: bool