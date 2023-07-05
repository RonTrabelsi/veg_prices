from fastapi import FastAPI

from src.config import settings
from src.database import create_indexes
from src.loggers import load_loggers_conf
from src.routers.market_prices_router import market_prices_router
from src.routers.statistical_data_router import statistical_data_router
from src.utils import load_default_market_prices

# Load loggers configuration
load_loggers_conf()

# Create elasticsearch indexes
create_indexes()

# If needed, load default market prices
if(settings.load_default_market_prices):
    load_default_market_prices()

app = FastAPI(debug=settings.debug, openapi_prefix="/openapi")
app.include_router(market_prices_router, prefix="/market_prices")
app.include_router(statistical_data_router, prefix="/statistical_data")
