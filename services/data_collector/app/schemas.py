""" Define schemas for REST requests and responses """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.utils import DEFAULT_START_DATE, DEFAULT_END_DATE


class MarketPricesRequest(BaseModel):
    vegetable_name: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime] = DEFAULT_END_DATE
