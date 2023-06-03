""" Define schemas for REST requests and responses """

from asyncio import DefaultEventLoopPolicy
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

DEFAULT_START_DATE = datetime(2000,1,1)
DEFAULT_END_DATE = datetime.now()

class MarketPricesRequest(BaseModel):
    vegetable_name: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime] = DEFAULT_END_DATE
    