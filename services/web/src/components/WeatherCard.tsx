import { WeatherSignal } from "../api";
import { date, pct, signed, trendClass, weekdayShort } from "../format";

// Region-specific context shown under the explanation
const REGION_NOTES: Record<string, string> = {
  arava: "הערבה היא אזור הגידול של עונת החורף, ולכן חום בסוף הקיץ משפיע בעיקר על המחירים של נובמבר–דצמבר.",
};

export default function WeatherCard({ weather }: { weather: WeatherSignal | null }) {
  if (!weather) {
    return (
      <section className="card weather">
        <header className="card-header">
          <h2>מזג האוויר באזורי הגידול</h2>
        </header>
        <p className="muted">נתוני מזג האוויר עוד לא נטענו.</p>
      </section>
    );
  }
  const meaningful = weather.correlation >= 0.2;
  return (
    <section className="card weather">
      <header className="card-header">
        <h2>מזג האוויר ב{weather.region_name}</h2>
        <span className="stamp">נמדד עד {date(weather.last_observed)}</span>
      </header>

      <div className="stats">
        <div className={`stat ${Math.abs(weather.tmax_anomaly_60d) >= 1 ? "warn" : "neutral"}`}>
          <span className="stat-value">{signed(weather.tmax_anomaly_60d, 1, "°")}</span>
          <span className="stat-label">טמפרטורת השיא ב־60 הימים האחרונים לעומת הרגיל</span>
        </div>
        <div className={`stat ${weather.heat_stress_days_30d_normal != null && weather.heat_stress_days_30d - weather.heat_stress_days_30d_normal >= 3 ? "warn" : "neutral"}`}>
          <span className="stat-value">{weather.heat_stress_days_30d}</span>
          <span className="stat-label">
            ימי חום מעל {weather.heat_stress_tmax}° בחודש האחרון
            {weather.heat_stress_days_30d_normal != null && <> (בדרך כלל {Math.round(weather.heat_stress_days_30d_normal)})</>}
          </span>
        </div>
        <div className={`stat ${trendClass(weather.implied_pressure_pct, 3)}`}>
          <span className="stat-value">{pct(weather.implied_pressure_pct)}</span>
          <span className="stat-label">השפעה משוערת על המחיר בעוד {weather.lag_months} חודשים</span>
        </div>
      </div>

      <div className="explain">
        <h3 className="sub">איך הטמפרטורה משפיעה על המחיר</h3>
        {meaningful ? (
          <>
            <p>
              חום מעל ~{weather.heat_stress_tmax}° פוגע בחנטה — פחות פרחים הופכים לפרי. את זה לא רואים בשוק כשחם, אלא כשהפרי החסר היה
              אמור להיקטף, <strong>כ{weather.lag_months === 2 ? "חודשיים" : `${weather.lag_months} חודשים`} אחר כך</strong>: פחות סחורה, מחיר
              גבוה יותר. ב־{weather.n_months} החודשים שנבדקו, כל מעלה מעל הרגיל הייתה שווה כ־
              <strong>{signed(weather.pct_per_degree, 0, "%")}</strong> במחיר {weather.lag_months === 2 ? "חודשיים" : `${weather.lag_months} חודשים`} אחר כך.
            </p>
            <p>
              <strong>כרגע:</strong> {weather.tmax_anomaly_60d >= 0 ? "חם" : "קריר"} ב־{Math.abs(weather.tmax_anomaly_60d).toFixed(1)}° מהרגיל
              {weather.heat_stress_days_30d_normal != null && (
                <>
                  , עם {weather.heat_stress_days_30d} ימי חום לעומת {Math.round(weather.heat_stress_days_30d_normal)} בדרך כלל
                </>
              )}{" "}
              — לחץ משוער של <strong>{pct(weather.implied_pressure_pct)}</strong> על המחיר. זה אות חלש־בינוני (מתאם {weather.correlation.toFixed(2)}):
              הטמפרטורה מסבירה רק כ־{Math.round(weather.correlation * weather.correlation * 100)}% מהתנודות; חגים, עונה ועובדים משפיעים הרבה יותר.
              לכן ההשפעה נכללת בתחזית רק מחודש ומעלה, ומוגבלת ל־±15%.
            </p>
          </>
        ) : (
          <p>בנתונים הקיימים לא נמצא קשר מובהק בין הטמפרטורה באזור למחיר, ולכן היא לא משפיעה על התחזית.</p>
        )}
        {REGION_NOTES[weather.region] && <p className="muted small">{REGION_NOTES[weather.region]}</p>}
      </div>

      {weather.forecast.length > 0 && (
        <>
          <h3 className="sub">השבוע הקרוב</h3>
          <div className="week">
            {weather.forecast.map((day) => (
              <div key={day.date} className={`day ${day.tmax >= weather.heat_stress_tmax ? "hot" : ""}`}>
                <div className="day-name">{weekdayShort(day.date)}</div>
                <div className="day-max">{Math.round(day.tmax)}°</div>
                <div className="day-min muted">{Math.round(day.tmin)}°</div>
                {day.rain_mm >= 1 && <div className="day-rain">☔ {Math.round(day.rain_mm)}</div>}
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
