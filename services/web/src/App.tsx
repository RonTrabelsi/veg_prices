import { useEffect, useState } from "react";
import { Dashboard, Vegetable, fetchDashboard, fetchVegetables, friendlyError } from "./api";
import { dateWithYear } from "./format";
import CatalogPanel from "./components/CatalogPanel";
import Caveats from "./components/Caveats";
import ForecastCard from "./components/ForecastCard";
import HistoryChart from "./components/HistoryChart";
import HolidaysCard from "./components/HolidaysCard";
import PlantingPlanner from "./components/PlantingPlanner";
import SeasonalityChart from "./components/SeasonalityChart";
import TodayCard from "./components/TodayCard";
import WeatherCard from "./components/WeatherCard";

const STORAGE_KEY = "veg-prices.vegetable";
// Cherry tomatoes: ~75 days from transplant to first harvest
const DEFAULT_DAYS_TO_HARVEST = 75;
// Shown on first visit, before the user picks anything
const DEFAULT_VEGETABLE = "עגבניות שרי אשכולות אכות מעולה";

function readStoredVegetable(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export default function App() {
  const [vegetables, setVegetables] = useState<Vegetable[]>([]);
  const [vegetable, setVegetable] = useState<string>(readStoredVegetable);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catalogOpen, setCatalogOpen] = useState(false);

  useEffect(() => {
    fetchVegetables()
      .then((list) => {
        setVegetables(list);
        const stored = list.find((item) => item.name === vegetable && item.has_analytics);
        if (!stored) {
          const first =
            list.find((item) => item.name === DEFAULT_VEGETABLE && item.has_analytics) ??
            list.find((item) => item.has_analytics) ??
            list[0];
          if (first) setVegetable(first.name);
          else {
            setError("אין עדיין נתוני מחירים. יש להמתין לטעינה הראשונית.");
            setLoading(false);
          }
        }
      })
      .catch((err: Error) => {
        setError(`לא ניתן להתחבר לשרת: ${err.message}`);
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!vegetable) return;
    setLoading(true);
    setError(null);
    try {
      localStorage.setItem(STORAGE_KEY, vegetable);
    } catch {
      /* private mode */
    }
    fetchDashboard(vegetable, DEFAULT_DAYS_TO_HARVEST)
      .then(setDashboard)
      .catch((err: Error) => {
        setDashboard(null);
        setError(friendlyError(err.message));
      })
      .finally(() => setLoading(false));
  }, [vegetable]);

  const handleLoaded = (name: string) => {
    fetchVegetables()
      .then((list) => {
        setVegetables(list);
        setVegetable(name);
      })
      .catch(() => undefined);
  };

  return (
    <div className="app">
      {catalogOpen && <CatalogPanel current={vegetable} onClose={() => setCatalogOpen(false)} onLoaded={handleLoaded} />}
      <header className="header">
        <div className="brand">
          <h1>מחירי ירקות</h1>
          <p className="subtitle">כלי החלטה לחקלאי · מחירי מועצת הצמחים</p>
        </div>
        <div className="controls">
          <label className="select">
            <span>ירק</span>
            <select value={vegetable} onChange={(event) => setVegetable(event.target.value)}>
              {vegetables.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                  {item.has_analytics ? "" : " (אין די נתונים)"}
                </option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={() => setCatalogOpen(true)}>
            ＋ הוסף ירק
          </button>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {loading && <div className="banner loading">מחשב נתונים…</div>}

      {dashboard && !loading && (
        <>
          <main className="grid">
            <TodayCard overview={dashboard.overview} />
            <ForecastCard forecast={dashboard.forecast} overview={dashboard.overview} />
            <HolidaysCard holidays={dashboard.holidays} />
            <SeasonalityChart seasonality={dashboard.seasonality} currentMonth={dashboard.overview.month} />
            <HistoryChart history={dashboard.history} />
            <PlantingPlanner vegetable={dashboard.vegetable} initial={dashboard.planting} />
            <WeatherCard weather={dashboard.weather} />
            <Caveats meta={dashboard.meta} />
          </main>
          <footer className="footer">
            נתונים מ־{dateWithYear(dashboard.meta.data_from)} עד {dateWithYear(dashboard.meta.data_to)} · {dashboard.meta.n_days.toLocaleString("he-IL")} ימי
            מסחר · בסיס עונתי: {dashboard.meta.baseline_years} שנים מ־{dashboard.meta.baseline_since}
          </footer>
        </>
      )}
    </div>
  );
}
