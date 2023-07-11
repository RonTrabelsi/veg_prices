# Start the tracking
from json import loads
from typing import List

from src.periodic_prices_scraper import PeriodicPricesScraper

VEGETABLES_LIST_FILE_NAME = "src/vegetables_list.json"


def get_vegetables_list() -> List[str]:
    """ :return: Vegetables list from the file """
    with open(VEGETABLES_LIST_FILE_NAME, mode="r") as fd:
        file_content = fd.read()
    return loads(file_content)


def main():
    vegetables_to_track = get_vegetables_list()
    PeriodicPricesScraper(vegetables=vegetables_to_track).track_prices()


if __name__ == "__main__":
    main()
