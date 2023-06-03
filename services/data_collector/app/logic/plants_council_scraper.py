""" Implements Vegetables Council Website Scraper """

from copy import deepcopy
from datetime import datetime
from logging import getLogger
from re import compile, findall
from typing import Any, Dict, Optional

from app.database import market_prices_collection
from app.loggers import Loggers
from app.logic.plants_council_consts import (LOG_DATE_FORMAT,
                                             PLANTS_COUNCIL_WEBSITE_URL,
                                             PRICES_TABLE_PATTERN,
                                             REQUEST_DATA,
                                             REQUEST_END_DATE_FORMAT,
                                             REQUEST_START_DATE_FORMAT,
                                             RESPONSE_DATE_FORMAT,
                                             ROW_DATE_PATTERN,
                                             ROW_REGULAR_PRICE_PATTERN,
                                             ROW_SPECIAL_PRICE_PATTERN,
                                             ROWS_DELIMITER, RequestFields)
from pymongo import UpdateOne
from requests import Session


class PlantsCouncilScraper:
    def __init__(self) -> None:
        """ Initialize regex patterns and website session """
        self.prices_table_pattern = compile(PRICES_TABLE_PATTERN)
        self.row_date_pattern = compile(ROW_DATE_PATTERN)
        self.row_regular_price_pattern = compile(ROW_REGULAR_PRICE_PATTERN)
        self.row_special_price_pattern = compile(ROW_SPECIAL_PRICE_PATTERN)
        self.session = Session()
        self.logger = getLogger(Loggers.DATA_COLLECTOR_LOGGER.value)

    def format_start_date(self, start_date: datetime) -> str:
        """ :return: The start date to the request in the needed format """
        return start_date.strftime(REQUEST_START_DATE_FORMAT)

    def format_end_date(self, end_date: datetime) -> str:
        """ :return: The end date to the request in the needed format """
        return end_date.strftime(REQUEST_END_DATE_FORMAT)

    def build_request_body(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        page_number: int,
    ) -> Dict[str, str]:
        """ Given the relevant parameters of request, build the request body """
        request_data = deepcopy(REQUEST_DATA)

        request_data[RequestFields.VEGETABLE_NAME.value] = vegetable_name
        request_data[RequestFields.START_DATE.value] = self.format_start_date(
            start_date)
        request_data[RequestFields.END_DATE.value] = self.format_end_date(
            end_date)
        request_data[RequestFields.PAGE_NUMBER.value] = page_number

        return request_data

    def scrap_prices_page(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        page_number: int,
    ) -> Dict[str, Any]:
        """ 
        Scrap a page of the prices of the vegetable from the plants council 
        website 
        """
        request_data = self.build_request_body(vegetable_name=vegetable_name,
                                               start_date=start_date,
                                               end_date=end_date,
                                               page_number=page_number)
        response = self.session.post(PLANTS_COUNCIL_WEBSITE_URL,
                                     data=request_data)

        raw_table = findall(self.prices_table_pattern, str(response.content))
        raw_table_data = raw_table[0] if raw_table else ""
        return self.extract_prices(vegetable_name, raw_table_data)

    def extract_prices(
        self,
        vegetable_name: str,
        prices_table_data: str
    ) -> Dict[str, Any]:
        """ 
        Given a vegetable name and its prices table, return the its price per
        date in the relevant format for indexing 

        :return: list of all the prices in the given table
        """
        splitted_price_table = prices_table_data.split(ROWS_DELIMITER)[:-1]
        prices_to_dates = [
            {
                "vegetable_name": vegetable_name,
                "date": self.extract_date(row_data),
                "regular_price": self.extract_regular_price(row_data),
                "special_price": self.extract_special_price(row_data),
            }
            for row_data in splitted_price_table
        ]
        return prices_to_dates

    def extract_date(self, row_data: str) -> datetime:
        """ :return: Date extracted from the row data """
        raw_date = findall(self.row_date_pattern, row_data)[0]
        date = datetime.strptime(raw_date, RESPONSE_DATE_FORMAT)
        return date

    def extract_regular_price(self, row_data: str) -> float:
        """ :return: Regular price extracted from the row data """
        regular_price = findall(self.row_regular_price_pattern, row_data)[0]
        return float(regular_price)

    def extract_special_price(self, row_data: str) -> Optional[float]:
        """ :return: Special price extracted from the row data """
        try:
            special_price = findall(
                self.row_special_price_pattern, row_data)[0]
            return float(special_price)
        except IndexError:
            return None

    def scrap_historic_prices(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """ 
        Given a vegetable name, a start date an and end date, scrap all the
        vegetable prices data between the start and the end date

        :return: mapping between the dates and the prices
        """
        vegetable_prices = []
        cur_page = 1
        cur_prices = True

        while cur_prices:
            cur_prices = self.request_prices(
                vegetable_name=vegetable_name,
                start_date=start_date,
                end_date=end_date,
                page_number=cur_page,
            )
            self.logger.debug(f"Got {len(cur_prices)} new dates prices data"
                              f"for {vegetable_name}")
            vegetable_prices += cur_prices
            cur_page += 1

        self.logger.info(f"Scraped {len(vegetable_prices)} dates prices data "
                         f"of {vegetable_name} "
                         f"between {start_date.strftime(LOG_DATE_FORMAT)} "
                         f"and {end_date.strftime(LOG_DATE_FORMAT)}")

        return vegetable_prices

    def save_prices_in_db(self, prices_to_dates: Dict[str, Any]) -> int:
        """ 
        Given a dict of historical prices, save prices only if they aren't
        exists in the DB

        :return: number of records saved in the DB
        """
        update_or_save_operations = [
            UpdateOne(
                {"vegetable_name": doc["vegetable_name"], "date": doc["date"]},
                {"$set": doc},
                upsert=True
            )
            for doc in prices_to_dates
        ]

        if update_or_save_operations:
            results = market_prices_collection.bulk_write(
                update_or_save_operations)
            return results.upserted_count

        return 0

    def save_historic_prices(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """ 
        Save the given vegetable prices in the given period in the DB  

        :return: amount of dates saved
        """
        saved_dates_amount = 0
        cur_prices = True
        cur_page = 1

        while cur_prices:
            cur_prices = self.scrap_prices_page(
                vegetable_name=vegetable_name,
                start_date=start_date,
                end_date=end_date,
                page_number=cur_page,
            )
            saved_dates_amount += self.save_prices_in_db(cur_prices)
            cur_page += 1

        self.logger.info(f"Saved {saved_dates_amount} dates prices data of "
                         f"{vegetable_name} "
                         f"between {start_date.strftime(LOG_DATE_FORMAT)} "
                         f"and {end_date.strftime(LOG_DATE_FORMAT)}")
        return saved_dates_amount


# Initialize global scrapper
plants_council_scraper = PlantsCouncilScraper()
