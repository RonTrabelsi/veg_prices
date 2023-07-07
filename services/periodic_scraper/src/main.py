# Start the tracking
from src.periodic_prices_scraper import PeriodicPricesScraper


def main():
    vegetables_to_track = [
        'עגבניות שרי אשכולות אכות מעולה',
        'פלפל אדום איכות מעולה',
        'בצל יבש',
    ]
    PeriodicPricesScraper(vegetables=vegetables_to_track).track_prices()


if __name__ == "main":
    main()
