"""Data models for Israeli Public Transport API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BusArrival(BaseModel):
    """Model for a single bus arrival."""

    line_number: str = Field(alias="lineNumber")
    line_ref: int = Field(alias="lineRef")
    destination: str
    agency: str
    real_time_arrives_at: datetime = Field(alias="realTimeArrivalDate")
    real_time_arrives_in: float = Field(alias="realTimeArrivalFromNow")
    real_time_arrival_delay: int = Field(alias="realTimeArrivalDelay")
    is_real_time: bool = Field(alias="isRealTime")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class BusResponse(BaseModel):
    """Model for bus API response."""

    station_id: str = Field(alias="station")
    station_name: str = Field(alias="stationName")
    bus_data: list[BusArrival] = Field(alias="businformation")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class TrainArrival(BaseModel):
    """Model for a single train arrival."""

    arrival_time: datetime = Field(alias="arrivalTime")
    departure_time: datetime = Field(alias="departureTime")
    platform: str | None = Field(default=None, alias="platform")
    train_number: str | None = Field(default=None, alias="trainNumber")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class TrainResponse(BaseModel):
    """Model for train API response."""

    trains: list[TrainArrival]
    from_station: str | None = Field(default=None, alias="fromStation")
    to_station: str | None = Field(default=None, alias="toStation")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
