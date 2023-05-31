""" Implements Vegetables Council Website Scraper """

from copy import deepcopy
from datetime import datetime
from re import compile, findall
from typing import Any, Dict, Optional

from requests import Session

from consts import (PRICES_TABLE_PATTERN, REQUEST_DATA,
                    REQUEST_END_DATE_FORMAT,
                    REQUEST_START_DATE_FORMAT, REQUEST_URL,
                    RESPONSE_DATE_FORMAT, ROW_DATE_PATTERN,
                    ROW_REGULAR_PRICE_PATTERN,
                    ROW_SPECIAL_PRICE_PATTERN, ROWS_DELIMITER,
                    RequestFields)


class VegCouncilScraper:
    def __init__(self) -> None:
        """ Initialize regex patterns and website session """
        self.prices_table_pattern = compile(PRICES_TABLE_PATTERN)
        self.row_date_pattern = compile(ROW_DATE_PATTERN)
        self.row_regular_price_pattern = compile(ROW_REGULAR_PRICE_PATTERN)
        self.row_special_price_pattern = compile(ROW_SPECIAL_PRICE_PATTERN)
        self.session = Session()

    def format_start_date(self, start_date: datetime) -> str:
        """ :return: The start date to the request in the needed format """
        return start_date.strftime(REQUEST_START_DATE_FORMAT)

    def format_end_date(self, end_date: datetime) -> str:
        """ :return: The end date to the request in the needed format """
        return end_date.strftime(REQUEST_END_DATE_FORMAT)

    def build_request_data(
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

    def request_prices(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
        page_number: int,
    ) -> Dict[datetime, float]:
        """ Get the prices of the vegetable from the website """
        request_data = self.build_request_data(vegetable_name=vegetable_name,
                                               start_date=start_date,
                                               end_date=end_date,
                                               page_number=page_number)
        response = self.session.post(REQUEST_URL, data=request_data)

        raw_table = findall(self.prices_table_pattern, str(response.content))
        raw_table_data = raw_table[0] if raw_table else ""
        return self.extract_prices(vegetable_name, raw_table_data)

    def get_historic_prices(
        self,
        vegetable_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[datetime, float]:
        """ 
        Given a vegetable name, start_date and end_date, return all its 
        prices data in this period 
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
            vegetable_prices += cur_prices
            cur_page += 1

        return vegetable_prices

    def extract_prices(
        self,
        vegetable_name: str,
        prices_table_data: str
    ) -> Dict[str, Any]:
        """ 
        Given a vegetable name and its prices table, return the its price per
        date in the relevant format for indexing  
        """
        splitted_price_table = prices_table_data.split(ROWS_DELIMITER)[:-1]
        prices_to_dates = [
            {
                "vegetable": vegetable_name,
                "date": self.extract_date(row_data),
                "regular_price": self.extract_regular_price(row_data),
                "special_price": self.extract_special_price(row_data),
            }
            for row_data in splitted_price_table
        ]
        return prices_to_dates

    def extract_date(self, row_data: str) -> datetime:
        """ :return: Date extracted from the row data """
        date = findall(self.row_date_pattern, row_data)[0]
        return datetime.strptime(date, RESPONSE_DATE_FORMAT)

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


a = VegCouncilScraper()
print(a.get_historic_prices(
    vegetable_name='בצל אדום',
    start_date=datetime(2001, 1, 1),
    end_date=datetime.now(),
))
