from contextlib import suppress
from datetime import datetime, timedelta
from logging import getLogger
from sched import scheduler
from time import sleep
from typing import Dict, List

from common.holidays_client import HolidaysClient
from common.plants_council_scraper import PlantsCouncilScraper
from common.weather_client import WeatherClient
from src.database import HOLIDAYS_INDEX, MARKET_PRICES_INDEX, WEATHER_INDEX, es_client
from src.loggers import PERIODIC_SCRAPER_LOGGER_NAME

# Default start date of prices to load
DEFAULT_START_DATE = datetime(2000, 1, 1)
# Default days interval of prices to load
DEFAULT_DAYS_INTERVAL = 1


class PeriodicPricesScraper:
    """ Prices existence validator """

    def __init__(self, vegetables: List[str], start_date: datetime = DEFAULT_START_DATE, days_interval: int = DEFAULT_DAYS_INTERVAL) -> None:
        self.vegetables = vegetables
        self.start_date = start_date
        self.interval = timedelta(days=days_interval)

        self.scheduler = scheduler(datetime.now, self.delay)
        logger = getLogger(PERIODIC_SCRAPER_LOGGER_NAME)
        self.logger = logger
        self.scraper = PlantsCouncilScraper(es_client, self.logger, MARKET_PRICES_INDEX)
        self.weather_client = WeatherClient(es_client, self.logger, WEATHER_INDEX)
        self.holidays_client = HolidaysClient(es_client, self.logger, HOLIDAYS_INDEX)

    @staticmethod
    def delay(time_delta: timedelta) -> None:
        """ Sleep the given timedelta """
        with suppress(AttributeError):
            sleep(time_delta.total_seconds())

    def safely(self, description: str, action: callable, *args) -> None:
        """ Run a load step, logging instead of raising so one failing source never stops the schedule """
        try:
            action(*args)
        except Exception as error:
            self.logger.error(f"Failed to {description}: {error}")

    def get_indexed_vegetables(self) -> List[str]:
        """ :return: every vegetable that already has prices in the index """
        aggs = {"vegetables": {"terms": {"field": "vegetable_name.keyword", "size": 500}}}
        try:
            response = es_client.search(index=MARKET_PRICES_INDEX, size=0, aggs=aggs)
        except Exception as error:
            self.logger.error(f"Failed to list indexed vegetables: {error}")
            return []
        return [bucket["key"] for bucket in response["aggregations"]["vegetables"]["buckets"]]

    def tracked_vegetables(self) -> List[str]:
        """ :return: the configured vegetables plus everything loaded since, e.g. through the web app """
        return sorted(set(self.vegetables) | set(self.get_indexed_vegetables()))

    def load_last_prices(self) -> None:
        """ Save vegetables prices from the last interval date until now, and refresh the enrichment data """
        today = datetime.now()
        start_date = today - self.interval

        tracked = self.tracked_vegetables()
        self.logger.info(f"Refreshing prices of {len(tracked)} vegetables")
        for vegetable in tracked:
            self.safely(f"load last prices of {vegetable}", self.scraper.scrap_historic_prices,
                        vegetable, start_date, today, True, False)
        self.safely("refresh weather", self.weather_client.load_recent)
        self.safely("refresh holidays calendar", self.holidays_client.load_years, today.year)

    def load_prices_periodically(self) -> None:
        """ Load the given vegetables every <self.interval> seconds """
        self.scheduler.enter(delay=self.interval, priority=1,action=self.load_prices_periodically)
        self.load_last_prices()

        self.logger.debug(f"next tasks: {self.get_scheduled_tasks()}")

    def get_next_execution_datetime(self) -> datetime:
        """ return: calculated next execution midday datetime """
        next_execution_date = datetime.now() + self.interval
        next_execution_midday = next_execution_date.replace(hour=12, minute=0, second=0, microsecond=0)
        return next_execution_midday

    def load_historic_prices(self) -> None:
        """ Load vegetables historic prices, weather history and the holidays calendar """
        for vegetable in self.vegetables:
            self.safely(f"load historic prices of {vegetable}", self.scraper.scrap_historic_prices,
                        vegetable, self.start_date, datetime.now(), True, False)
        self.safely("load weather history", self.weather_client.load_history)
        self.safely("load holidays calendar", self.holidays_client.load_years)

    def get_scheduled_tasks(self) -> Dict[datetime, callable]:
        """ :return: all scheduled tasks """
        return {event.time.strftime("%Y-%m-%d-%H-%M-%S"): event.action for event in self.scheduler.queue}

    def track_prices(self) -> None:
        """ Track the given vegetables prices since the given date forever """
        self.logger.info(f"Load prices of: {self.vegetables} since: {self.start_date}")
        self.load_historic_prices()

        self.logger.info(f"Start loading prices of: {self.vegetables} every {self.interval.days} days")
        self.scheduler.enterabs(time=self.get_next_execution_datetime(),priority=1,action=self.load_prices_periodically)
        self.logger.debug(f"next tasks: {self.get_scheduled_tasks()}")

        self.scheduler.run(blocking=True)
