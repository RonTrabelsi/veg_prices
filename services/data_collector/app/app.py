from fastapi import FastAPI

from app.config import settings
from app.market_prices_router import market_prices_router

from app.loggers import load_loggers_conf
from app.utils import load_default_market_prices
from app.database import create_market_prices_index

# Load loggers configuration
load_loggers_conf()

# Create market prices index 
create_market_prices_index()

# If needed, load default market prices
if(settings.load_default_market_prices):
    load_default_market_prices()

app = FastAPI(debug=settings.debug, openapi_prefix="/openapi")
app.include_router(market_prices_router, prefix="/market_prices")
