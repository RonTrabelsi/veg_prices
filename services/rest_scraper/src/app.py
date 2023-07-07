from fastapi import FastAPI

from src.config import settings
from src.routers.market_prices_router import market_prices_router
from src.routers.statistical_data_router import statistical_data_router

app = FastAPI(debug=settings.debug, openapi_prefix="/openapi")
app.include_router(market_prices_router, prefix="/market_prices")
app.include_router(statistical_data_router, prefix="/statistical_data")
