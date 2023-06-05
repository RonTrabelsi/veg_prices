""" Define schemas for REST requests and responses """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.utils import DEFAULT_START_DATE


class MarketPricesRequest(BaseModel):
    vegetable_name: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime] = Field(default_factory=lambda: datetime.now())
