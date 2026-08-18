from typing import Literal
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    sku_id: str = Field(min_length=1)
    region: str = "All"
    periods: int = Field(default=4, ge=1, le=12)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    records: int

