""" Implement client for CBS API """

from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from requests import Request, Session

from .cbs_consts import (API_ERR_MSG, CBS_DATA_PATH, CBS_WEBSITE_URL,
                         DEFAULT_PAGE_SIZE, ENGLISH_LANGUAGE_CODE,
                         GENERAL_DATE_FORMAT, JSON_FORMAT, REQUEST_DATE_FORMAT,
                         RESPONSE_DATE_FORMAT, SHOULD_DOWNLOAD, RequestParams,
                         ResponseFields)


class CbsApiClient:
    """ Client to CBS API """

    def __init__(
        self,
        es_client: Elasticsearch,
        logger: Logger,
        es_statistics_index_name: str,
    ) -> None:
        self.session = Session()
        self.logger = logger
        self.es_client = es_client
        self.es_statistics_index_name = es_statistics_index_name

    def build_request_params(
        self,
        series: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """ Given relevant parameters, return query params to the request """
        formatted_start_date = start_date.strftime(REQUEST_DATE_FORMAT)
        formatted_end_date = end_date.strftime(REQUEST_DATE_FORMAT)

        return {
            RequestParams.LANGUAGE.value: ENGLISH_LANGUAGE_CODE,
            RequestParams.DATA_FORMAT.value: JSON_FORMAT,
            RequestParams.DOWNLOAD.value: SHOULD_DOWNLOAD,
            RequestParams.PAGE_SIZE.value: DEFAULT_PAGE_SIZE,
            RequestParams.SERIES_ID.value: series,
            RequestParams.START_DATE.value: formatted_start_date,
            RequestParams.END_DATE.value: formatted_end_date,
        }

    def get_row_date(self, row: Dict) -> datetime:
        """ Given a response data row, return its date as datetime """
        row_date_as_str = row[ResponseFields.DATE.value]
        return datetime.strptime(row_date_as_str, RESPONSE_DATE_FORMAT)

    def get_row_value(self, row: Dict) -> Any:
        """ Given a response data row, return its value """
        return row[ResponseFields.VALUE.value]

    def extract_data(
        self,
        series_id: str,
        response_content: Dict
    ) -> List[Dict[datetime, Any]]:
        """ Given the response content, extract the data """
        data = response_content[ResponseFields.CONTENT.value][ResponseFields.SERIES_DATA.value]

        return [
            {
                "series_id": series_id,
                "date": self.get_row_date(row),
                "value": self.get_row_value(row)
            }
            for chunk in data
            for row in chunk[ResponseFields.CHUNK_DATA.value]
        ]

    def get_next_url(self, response_content: Dict) -> Optional[str]:
        """ Given the response content, return the next utl to fetch """
        paging_data = response_content[ResponseFields.CONTENT.value][ResponseFields.PAGING_DATA.value]
        return paging_data[ResponseFields.NEXT_URL.value]

    def index_data(self, data: List[Dict[str, Any]]) -> int:
        """ 
        Given the series and its data, index it to elasticsearch 
        :return: Number of upserted documents
        """
        upserted_docs_amount = 0

        for doc in data:
            doc_id = f"{doc['series_id']}_{doc['date'].strftime(RESPONSE_DATE_FORMAT)}"
            response = self.es_client.update(
                index=self.es_statistics_index_name,
                id=doc_id,
                body={"doc": doc,
                      "doc_as_upsert": True}
            )
            if response["result"] in ("created", "updated"):
                upserted_docs_amount += 1

        return upserted_docs_amount

    def collect_data(
        self,
        series_id: str,
        start_date: datetime,
        end_date: datetime,
        save: bool,
        get_results: bool,
    ) -> Dict:
        """ 
        Given a series, a start date and an end date, 
        return the series data from the server
        """
        req_url = CBS_WEBSITE_URL + CBS_DATA_PATH
        req_params = self.build_request_params(series_id, start_date, end_date)
        next_url = Request("GET", url=req_url, params=req_params).prepare().url

        data = []
        saved_dates_amount = 0
        collected_dates_amount = 0

        self.logger.info(f"Starting to collect {series_id} series data "
                         f"between {start_date.strftime(GENERAL_DATE_FORMAT)} "
                         f"and {end_date.strftime(GENERAL_DATE_FORMAT)}")

        while next_url:
            response = self.session.get(next_url)
            response_content = response.json()

            if response_content.get(ResponseFields.API_ERR_MSG.value) == API_ERR_MSG:
                return data

            response_data = self.extract_data(series_id, response_content)
            self.logger.debug(f"Got {len(response_data)} new dates values "
                              f"for {series_id}")

            if save:
                saved_dates_amount += self.index_data(response_data)
            if get_results:
                data += response_data

            collected_dates_amount += len(response_data)
            next_url = self.get_next_url(response_content)

        self.logger.info(f"collected {collected_dates_amount} dates data "
                         f"with total {saved_dates_amount} new dates data of "
                         f"series {series_id} "
                         f"between {start_date.strftime(GENERAL_DATE_FORMAT)} "
                         f"and {end_date.strftime(GENERAL_DATE_FORMAT)}")

        return data
