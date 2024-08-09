from typing import List

from pydantic import BaseModel, Field, FutureDatetime


class BusArrivalData(BaseModel):
    line_number: int = Field(alias="lineNumber")
    line_ref: int = Field(alias="lineRef")
    real_time_arrives_at: FutureDatetime = Field(alias="realTimeArrivalDate")
    real_time_arrives_in: float = Field(alias="realTimeArrivalFromNow")
    real_time_arrival_delay: int = Field(alias="realTimeArrivalDelay")
    is_real_time: bool = Field(alias="isRealTime")
    destination: str
    agency: str


class BusResponse(BaseModel):
    station_id: int = Field(alias="station")
    station_name: str = Field(alias="stationName")
    bus_data: List[BusArrivalData] = Field(alias="businformation")
