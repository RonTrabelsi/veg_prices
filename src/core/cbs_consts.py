""" Implement client to CBS api """

from enum import Enum


CBS_WEBSITE_URL: str = "https://apis.cbs.gov.il"
CBS_DATA_PATH: str = "/series/data/path"

# Request query params
class RequestParams(Enum):
    SERIES_ID = "id"
    START_DATE = "startperiod"
    END_DATE = "endperiod"
    LANGUAGE = "lang"
    DATA_FORMAT = "format"
    DOWNLOAD = "download"
    PAGE_SIZE = "pagesize"


# Default query params values
ENGLISH_LANGUAGE_CODE: str = "en"
JSON_FORMAT: str = "json"
SHOULD_DOWNLOAD: bool = False
DEFAULT_PAGE_SIZE: int = 1000

# Date format for the dates in the request
REQUEST_DATE_FORMAT: str = "%m-%Y"

# Response content's fields
class ResponseFields(Enum):
    API_ERR_MSG = "Message"
    CONTENT = "DataSet"
    SERIES_DATA = "Series"
    CHUNK_DATA = "obs"
    DATE = "TimePeriod"
    VALUE = "Value"
    PAGING_DATA = "paging"
    NEXT_URL = "next_url"


# CBS API Error Message
API_ERR_MSG: str = 'Error: Series Path Data'

# Date format in the response
RESPONSE_DATE_FORMAT: str = "%Y-%m"

# Identifiers amount in series id
CBS_SERIES_IDENTIFIERS_AMOUNT: int = 5

# General date format
GENERAL_DATE_FORMAT: str = "%d/%m/%Y"
