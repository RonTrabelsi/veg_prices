""" Load data to elastic """

from datetime import datetime
from json import dumps

from prices_scraper.veg_council_scraper import VegCouncilScraper

# Conf for the scrapper
VEGETABLES = [
    'עגבניות שרי אשכולות אכות מעולה',
    'פלפל אדום איכות מעולה',
    'בצל יבש',
]
START_DATE = datetime(2010,1,1)
END_DATE = datetime.now()

scraper = VegCouncilScraper()
for vegetable in VEGETABLES:
    prices_list = scraper.get_historic_prices(vegetable, START_DATE, END_DATE)
    prices_json = dumps(prices_list)
