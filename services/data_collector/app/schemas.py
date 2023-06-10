""" Define schemas for REST requests and responses """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

from app.utils import DEFAULT_START_DATE


class MarketPricesRequest(BaseModel):
    """ Describe a market prices request necessary data """
    vegetable_name: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime]
    
    @validator('end_date', pre=True, always=True)
    def set_end_date(cls, end_date_value):
        """ Set now as default value for end_date """
        return end_date_value or datetime.now()
