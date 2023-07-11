""" Implement a periodic prices scraper """

from contextlib import suppress
from datetime import datetime, timedelta
from logging import getLogger
from sched import scheduler
from time import sleep
from typing import Dict, List

from common.plants_council_scraper import PlantsCouncilScraper
from src.database import MARKET_PRICES_INDEX, es_client
from src.loggers import PERIODIC_SCRAPER_LOGGER_NAME

# Default start date of prices to load
DEFAULT_START_DATE = datetime(2000, 1, 1)
# Default days interval of prices to load
DEFAULT_DAYS_INTERVAL = 1


class PeriodicPricesScraper:
    """ Prices existence validator """

    def __init__(
        self,
        vegetables: List[str],
        start_date: datetime = DEFAULT_START_DATE,
        days_interval: int = DEFAULT_DAYS_INTERVAL,
    ) -> None:
        self.vegetables = vegetables
        self.start_date = start_date
        self.interval = timedelta(days=days_interval)

        self.scheduler = scheduler(datetime.now, self.delay)
        logger = getLogger(PERIODIC_SCRAPER_LOGGER_NAME)
        self.logger = logger
        self.scraper = PlantsCouncilScraper(
            es_client=es_client,
            logger=self.logger,
            es_prices_index_name=MARKET_PRICES_INDEX
        )

    @staticmethod
    def delay(time_delta: timedelta) -> None:
        """ Sleep the given timedelta """
        with suppress(AttributeError):
            sleep(time_delta.total_seconds())

    def load_last_prices(self) -> None:
        """ Save vegetables prices from the last interval date until now """
        today = datetime.now()
        start_date = today - self.interval

        for vegetable in self.vegetables:
            self.scraper.scrap_historic_prices(
                vegetable_name=vegetable,
                start_date=start_date,
                end_date=today,
                save=True,
                get_results=False,
            )

    def load_prices_periodically(self) -> None:
        """ Load the given vegetables every <self.interval> seconds """
        self.scheduler.enter(delay=self.interval,
                             priority=1,
                             action=self.load_prices_periodically)
        self.load_last_prices()

        self.logger.debug(f"next tasks: {self.get_scheduled_tasks()}")

    def get_next_execution_datetime(self) -> datetime:
        """ return: calculated next execution midday datetime """
        next_execution_date = datetime.now() + self.interval
        next_execution_midday = next_execution_date.replace(hour=20,
                                                            minute=20,
                                                            second=0,
                                                            microsecond=0)
        return next_execution_midday

    def load_historic_prices(self) -> None:
        """ Load vegetables historic prices """
        for vegetable in self.vegetables:
            self.scraper.scrap_historic_prices(
                vegetable_name=vegetable,
                start_date=self.start_date,
                end_date=datetime.now(),
                save=True,
                get_results=False,
            )

    def get_scheduled_tasks(self) -> Dict[datetime, callable]:
        """ :return: all scheduled tasks """
        return {event.time.strftime("%Y-%m-%d-%H-%M-%S"): event.action
                for event in self.scheduler.queue}

    def track_prices(self) -> None:
        """ Track the given vegetables prices since the given date forever """
        self.logger.info(f"Load prices of: {self.vegetables} "
                         f"since: {self.start_date}")
        self.load_historic_prices()

        self.logger.info(f"Start loading prices of: {self.vegetables} "
                         f"every {self.interval.days} days")
        self.scheduler.enterabs(
            time=self.get_next_execution_datetime(),
            priority=1,
            action=self.load_prices_periodically
        )
        self.logger.debug(f"next tasks: {self.get_scheduled_tasks()}")

        self.scheduler.run(blocking=True)
