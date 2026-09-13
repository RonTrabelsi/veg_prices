""" Consts for the weather fetcher (Open-Meteo, free, no API key) """

from datetime import datetime

# Historical daily reanalysis (ERA5) - complete history, usually up to date within a day or two
OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
# Forecast endpoint - used to fill the last days and the coming week
OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"

DAILY_VARIABLES: str = "temperature_2m_max,temperature_2m_min,precipitation_sum"
TIMEZONE: str = "Asia/Jerusalem"
REQUEST_DATE_FORMAT: str = "%Y-%m-%d"

# Default start of weather history - matches the earliest prices data
DEFAULT_START_DATE: datetime = datetime(2005, 1, 1)
# Days back / forward fetched by the daily refresh
REFRESH_PAST_DAYS: int = 14
REFRESH_FORECAST_DAYS: int = 7

# Main vegetable growing regions of Israel. The Arava is the winter greenhouse region (Sep-May harvest),
# Beit She'an valley and the Besor / western Negev cover the rest of the year.
GROWING_REGIONS = {
    "arava": {"name_he": "הערבה", "latitude": 30.78, "longitude": 35.25},
    "beit_shean": {"name_he": "עמק בית שאן", "latitude": 32.50, "longitude": 35.50},
    "besor": {"name_he": "הבשור", "latitude": 31.25, "longitude": 34.45},
}
# Region used for the price/weather signal in analytics
PRIMARY_REGION: str = "arava"

# Daily max temperature above which tomato fruit-set suffers
HEAT_STRESS_TMAX: float = 38.0
# Daily min temperature below which ripening slows down
COLD_STRESS_TMIN: float = 5.0

SOURCE_ARCHIVE: str = "archive"
SOURCE_FORECAST: str = "forecast"
