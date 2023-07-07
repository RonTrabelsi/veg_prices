""" Implements Vegetables Council Website Scraper """

from datetime import datetime
from logging import Logger
from re import compile, findall
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from requests import Session

from .plants_council_consts import (DEFAULT_EVENT_TARGET, DEFAULT_VIEW_STATE,
                                    GENERAL_DATE_FORMAT,
                                    PLANTS_COUNCIL_WEBSITE_URL,
                                    PRICES_TABLE_PATTERN, REQUEST_DATE_FORMAT,
                                    RESPONSE_DATE_FORMAT, ROW_DATE_PATTERN,
                                    ROW_REGULAR_PRICE_PATTERN,
                                    ROW_SPECIAL_PRICE_PATTERN, ROWS_DELIMITER,
                                    RequestFields)


class PlantsCouncilScraper:
    def __init__(
        self,
        es_client: Elasticsearch,
        logger: Logger,
        es_prices_index_name: str,
    ) -> None:
        """ Initialize regex patterns and website session """
        self.session = Session()
        self.logger = logger
        self.es_client = es_client
        self.es_prices_index_name = es_prices_index_name

        self.prices_table_pattern = compile(PRICES_TABLE_PATTERN)
        self.date_pattern = compile(ROW_DATE_PATTERN)
        self.regular_price_pattern = compile(ROW_REGULAR_PRICE_PATTERN)
        self.special_price_pattern = compile(ROW_SPECIAL_PRICE_PATTERN)

    def prep_request_date(self, date: datetime) -> str:
        """ :return: The date in the request needed format """
        return date.strftime(REQUEST_DATE_FORMAT)

    def build_request_body(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        page_number: int,
    ) -> Dict[str, str]:
        """ Given the relevant parameters of request, build the request body """
        return {
            RequestFields.EVENT_TARGET.value: DEFAULT_EVENT_TARGET,
            RequestFields.VIEW_STATE.value: DEFAULT_VIEW_STATE,
            RequestFields.VEGETABLE_NAME.value: vegetable_name,
            RequestFields.START_DATE.value: self.prep_request_date(start_date),
            RequestFields.END_DATE.value: self.prep_request_date(end_date),
            RequestFields.PAGE_NUMBER.value: page_number,
        }

    def scrap_prices_page(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        page_number: int,
    ) -> List[Dict[str, Any]]:
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
        splitted_prices_table = prices_table_data.split(ROWS_DELIMITER)[:-1]
        prices_to_dates = [
            {
                "vegetable_name": vegetable_name,
                "date": self.extract_date(row_data),
                "regular_price": self.extract_regular_price(row_data),
                "special_price": self.extract_special_price(row_data),
            }
            for row_data in splitted_prices_table
        ]
        return prices_to_dates

    def extract_date(self, row_data: str) -> datetime:
        """ :return: Date extracted from the row data """
        raw_date = findall(self.date_pattern, row_data)[0]
        date = datetime.strptime(raw_date, RESPONSE_DATE_FORMAT)
        return date

    def extract_regular_price(self, row_data: str) -> float:
        """ :return: Regular price extracted from the row data """
        regular_price = findall(self.regular_price_pattern, row_data)[0]
        return float(regular_price)

    def extract_special_price(self, row_data: str) -> Optional[float]:
        """ :return: Special price extracted from the row data """
        try:
            special_price = findall(self.special_price_pattern, row_data)[0]
            return float(special_price)
        except IndexError:
            return None

    def scrap_historic_prices(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        save: bool = True,
        get_results: bool = True,
    ) -> Dict[str, Any]:
        """ 
        Given a vegetable name, a start date an and end date, scrap all the
        vegetable prices data between the start and the end date

        :return: mapping between the dates and the prices
        """
        vegetable_historic_prices = []
        saved_dates_amount = 0
        scraped_dates_amount = 0

        cur_page = 1
        cur_prices = True

        self.logger.info(f"Starting to scrap {vegetable_name} historic prices "
                         f"between {start_date.strftime(GENERAL_DATE_FORMAT)} "
                         f"and {end_date.strftime(GENERAL_DATE_FORMAT)}")

        while cur_prices:
            cur_prices = self.scrap_prices_page(
                vegetable_name=vegetable_name,
                start_date=start_date,
                end_date=end_date,
                page_number=cur_page,
            )
            self.logger.debug(f"Got {len(cur_prices)} new dates prices data "
                              f"for {vegetable_name}")

            if save:
                saved_dates_amount += self.index_prices(cur_prices)
            if get_results:
                vegetable_historic_prices += cur_prices

            scraped_dates_amount += len(cur_prices)
            cur_page += 1

        self.logger.info(f"Scraped {scraped_dates_amount} dates prices data "
                         f"with total {saved_dates_amount} new dates data of "
                         f"{vegetable_name} "
                         f"between {start_date.strftime(GENERAL_DATE_FORMAT)} "
                         f"and {end_date.strftime(GENERAL_DATE_FORMAT)}")

        if get_results:
            return vegetable_historic_prices

    def index_prices(
        self,
        vegetable_prices_data: List[Dict[str, Any]]
    ) -> int:
        """ 
        Given a dict of vegetable historical prices, index it to elasticsearch
        :return: number of upserted documents
        """
        upserted_docs_amount = 0

        for doc in vegetable_prices_data:
            doc_id = f"{doc['vegetable_name']}_{doc['date'].strftime(GENERAL_DATE_FORMAT)}"
            response = self.es_client.update(
                index=self.es_prices_index_name,
                id=doc_id,
                body={
                    "doc": doc,
                    "doc_as_upsert": True
                }
            )
            if response["result"] in ("created", "updated"):
                upserted_docs_amount += 1

        return upserted_docs_amount
