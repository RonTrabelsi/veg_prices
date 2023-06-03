""" Implement the endpoints for the app """

from datetime import datetime

from app.config import settings
from app.logic.veg_council_scraper import veg_council_scraper
from app.schemas import MarketPricesRequest

from fastapi import Body, FastAPI

# Loading the loggers configuration
from app.loggers import load_loggers_conf
load_loggers_conf()

app = FastAPI(debug=settings.debug)


@app.post("/load_market_prices")
def load_market_prices(market_prices_request: MarketPricesRequest) -> int:
    saved_dates_amount = veg_council_scraper.save_historic_prices(
        vegetable_name=market_prices_request.vegetable_name,
        start_date=market_prices_request.start_date,
        end_date=market_prices_request.end_date,
    )
    return saved_dates_amount
