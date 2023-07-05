""" Define schemas for REST requests and responses """

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

from src.core.cbs_consts import CBS_SERIES_IDENTIFIERS_AMOUNT
from src.utils import DEFAULT_START_DATE


class MarketPricesRequest(BaseModel):
    """ Describe a market prices request """
    vegetable_name: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime]

    @validator('end_date', pre=True, always=True)
    def set_end_date(cls, end_date_value):
        """ Set now as default value for end_date """
        return end_date_value or datetime.now()


class StatisticalDataRequest(BaseModel):
    """ Describe a statistical data request """
    series_id: str
    start_date: Optional[datetime] = DEFAULT_START_DATE
    end_date: Optional[datetime]

    @validator("end_date", pre=True, always=True)
    def set_end_date(cls, end_date_value):
        """ Set now as default value for end_date """
        return end_date_value or datetime.now()

    @validator("series_id")
    def validate_series_id(cls, series_id_value: str):
        """ Validate that the series id is valid """
        series_identifiers = series_id_value.split(",")

        if len(series_identifiers) != CBS_SERIES_IDENTIFIERS_AMOUNT:
            raise ValueError("Invalid series id")
        if not all(map(lambda x: x.isdigit(), series_identifiers)):
            raise ValueError("Invalid series id")

        return series_id_value
