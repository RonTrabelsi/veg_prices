from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers.analytics_router import analytics_router
from src.routers.holidays_router import holidays_router
from src.routers.market_prices_router import market_prices_router
from src.routers.statistical_data_router import statistical_data_router
from src.routers.weather_router import weather_router

app = FastAPI(debug=settings.debug, openapi_prefix="/openapi")
# The web app is served by nginx which proxies /api to this service; CORS is only needed for `vite dev`
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(market_prices_router, prefix="/market_prices")
app.include_router(statistical_data_router, prefix="/statistical_data")
app.include_router(weather_router, prefix="/weather")
app.include_router(holidays_router, prefix="/holidays")
app.include_router(analytics_router, prefix="/analytics")
