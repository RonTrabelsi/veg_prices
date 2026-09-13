import { WeatherSignal } from "../api";
import { date, pct, signed, trendClass, weekdayShort } from "../format";

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

      <p className="footnote">
        {meaningful
          ? `חודש חם מהרגיל נטה להעלות את המחיר כחודשיים אחר כך (${signed(weather.pct_per_degree, 1, "%")} לכל מעלה, מתאם ${weather.correlation.toFixed(2)} על ${weather.n_months} חודשים). זה אות חלש יחסית — הוא נכלל בתחזית לחודש ומעלה בלבד.`
          : "בנתונים הקיימים לא נמצא קשר מובהק בין מזג האוויר למחיר, ולכן הוא לא משפיע על התחזית."}
      </p>

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
