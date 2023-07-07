""" Implement a periodic prices scraper """

from datetime import datetime, timedelta
from logging import getLogger
from sched import scheduler
from typing import List

from src.core.plants_council_scraper import PlantsCouncilScraper
from src.database import elastic_client
from src.loggers import Loggers

# Default start date of prices to load
DEFAULT_START_DATE = datetime(2000, 1, 1)


class PeriodicPricesScraper:
    """ Prices existence validator """

    def __init__(
        self,
        vegetables: List[str],
        start_date: datetime = DEFAULT_START_DATE,
        days_interval: int = 1,
    ) -> None:
        self.vegetables = vegetables
        self.start_date = start_date
        self.interval = days_interval
        self.scheduler = scheduler()
        self.logger = getLogger(Loggers.DATA_COLLECTOR_LOGGER.value)
        self.plants_council_scraper = PlantsCouncilScraper(elastic_client)

    def load_last_prices(self) -> None:
        """ Save vegetables prices from the last interval date until now """
        today = datetime.now()
        start_date = today - timedelta(days=self.interval)

        for vegetable in self.vegetables:
            self.plants_council_scraper.scrap_historic_prices(
                vegetable_name=vegetable,
                start_date=start_date,
                end_date=today,
                save=True,
                get_results=False,
            )

    def load_prices_periodically(self) -> None:
        """ Load the given vegetables every <self.interval> seconds """
        delay = timedelta(days=self.interval).total_seconds()
        self.scheduler.enter(delay=delay,
                             priority=1,
                             action=self.load_prices_periodically)
        self.load_last_prices()

    def get_next_execution_ts(self) -> int:
        """ Return next execution midday in epoch """
        next_execution_date = datetime.now() + timedelta(days=self.interval)
        next_execution_midday = next_execution_date.replace(hour=12,
                                                            minute=0,
                                                            second=0,
                                                            microsecond=0)
        return next_execution_midday.timestamp()

    def load_historic_prices(self) -> None:
        """ Load vegetables historic prices """
        for vegetable in self.vegetables:
            self.plants_council_scraper.scrap_historic_prices(
                vegetable_name=vegetable,
                start_date=self.start_date,
                end_date=datetime.now(),
                save=True,
                get_results=False,
            )

    def track_prices(self) -> None:
        """ Track the given vegetables prices since the given date forever """
        self.logger.info(f"Load prices of: {self.vegetables} "
                         f"since: {self.start_date}")
        self.load_historic_prices()

        self.logger.info(f"Start loading prices of: {self.vegetables} "
                         f"every {self.interval} days")
        self.scheduler.enterabs(
            time=self.get_next_execution_ts(),
            priority=1,
            action=self.load_prices_periodically
        )

        self.scheduler.run()


# Start the tracking
vegetables_to_track = [
    'עגבניות שרי אשכולות אכות מעולה',
    'פלפל אדום איכות מעולה',
    'בצל יבש',
]
PeriodicPricesScraper(vegetables=vegetables_to_track).track_prices()
