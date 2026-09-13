# veg_prices

The idea of this project is to give farmers the ability to decide how to manage their harvesting.
Vegetable prices are scraped daily from the Plants Council website, enriched with weather and the holidays
calendar, indexed to Elasticsearch and served to a Hebrew web app that turns them into decisions:
is now a good time to sell, what is the price likely to do, and when to plant so the harvest lands in the
expensive part of the season.

## The components
- **Web app** (`services/web`) - React + Vite, Hebrew / RTL, mobile first. Served by nginx which proxies `/api` to the REST service. Port `3000`.
- **REST Scraper** (`services/rest_scraper`) - FastAPI. Scrapes on demand, loads weather and holidays, and exposes the `/analytics` endpoints the web app renders. Port `80`, docs at `http://localhost/docs`.
- **Periodic Scraper** (`services/periodic_scraper`) - loads the full history on start, then refreshes prices, weather and holidays every day at noon.
- **Elasticsearch** - the store (`market_prices_index`, `weather_index`, `holidays_index`). Port `9200`.
- **Kibana** - ad-hoc exploration. Port `5601`, dashboard in [assets/market_prices_dashboard.ndjson](assets/market_prices_dashboard.ndjson).

## Data sources
| Source | What | Fetcher |
|---|---|---|
| [Plants Council](https://plants.moonsite.co.il) | Daily regular / special price per product | `common/plants_council_scraper.py` |
| [Open-Meteo](https://open-meteo.com) | Daily max/min temperature and rain per growing region (Arava, Beit She'an, Besor), history + 7 day forecast | `common/weather_client.py` |
| [Hebcal](https://www.hebcal.com) | Israeli holidays calendar 2005 → +2 years | `common/holidays_client.py` |
| [CBS](https://apis.cbs.gov.il) | Statistical series (optional) | `common/cbs_api_client.py` |

The Plants Council search matches by **substring**, and an empty search returns the whole catalog (~40 products).
The scraper takes the product name from each row, so mixed pages are indexed correctly.

**Adding a vegetable** is done from the web app: the ＋ button lists every product on the site with its index
coverage; picking one loads its full history (`POST /market_prices/load_prices`, up to a minute). The periodic
scraper refreshes everything that has ever been indexed, so app-loaded products keep updating daily without
touching [vegetables_list.json](services/periodic_scraper/src/vegetables_list.json) (which only seeds the first load).
`GET /market_prices/catalog` returns the same list for scripts.

**Holidays** are derived from the calendar, not hardcoded: each Hebcal item title is reduced to its holiday name
(`Pesach II (CH''M)` → `Pesach`, `חנוכה: ג׳ נרות` → `חנוכה`), consecutive dates are clustered into yearly
occurrences, and Hebcal's own `major` sub-category selects the festivals and fasts that are analyzed. State
commemorations (`modern`) and minor days are stored but not analyzed; change `TRACKED_SUBCATS` in
[holidays_consts.py](services/common/holidays_consts.py) to include them. Adding another calendar (e.g. Ramadan / Eid
for the Arab market) means another client writing the same document shape to `holidays_index`.

## How to run
1. Start everything: `./raise_app.sh` (or `docker compose up --build -d`).
2. Wait a few minutes for the periodic scraper to load the history (prices, weather, holidays).
3. Open the app at **http://localhost:3000**.
4. Optional: load the [Kibana dashboard](assets/market_prices_dashboard.ndjson) at http://localhost:5601.

Manual loads through the REST API:
```bash
curl -X POST localhost/market_prices/load_prices -H 'Content-Type: application/json' -d '{"vegetable_name": "עגבניות שרי אשכולות אכות מעולה"}'
curl -X POST localhost/weather/load  -H 'Content-Type: application/json' -d '{}'
curl -X POST localhost/holidays/load -H 'Content-Type: application/json' -d '{}'
```

## Deploying for free
See [deploy/ORACLE_CLOUD.md](deploy/ORACLE_CLOUD.md): an Oracle Cloud *Always Free* ARM VM running
`docker-compose.yml` + [`docker-compose.prod.yml`](docker-compose.prod.yml) (only the web app is published), reachable
privately through Tailscale. `deploy/setup-oracle-vm.sh` does the VM side in one run.

## What the analytics do
Everything is computed from the indexed data (`rest_scraper/src/analytics.py`), one call: `GET /analytics/dashboard?vegetable=...`.
- **Seasonal norm** - median across baseline years (2015+) of a ±7 day rolling mean, per day of year, scaled to the last year's price level.
- **Forecast** - blends today's deviation from the norm (weighted by how long deviations persist, measured by autocorrelation) with the norm at the target date, plus a small weather adjustment. The ±band is the 80th percentile absolute error from a backtest on the last 3 years with out-of-year baselines.
- **Holidays** - price around each holiday's first day relative to that year's mean, averaged over years, with consistency.
- **Planting** - for each planting week, the expected norm over the harvest window given days-to-harvest.
- **Weather signal** - temperature anomaly of the last 60 days in the Arava vs. the price anomaly two months later.

## Example
![Alt text](assets/prices_example.png)
