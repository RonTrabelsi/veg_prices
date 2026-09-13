import { WeatherSignal } from "../api";
import { date, pct, signed, trendClass, weekdayShort } from "../format";

// Region-specific context shown under the explanation
const REGION_NOTES: Record<string, string> = {
  arava: "הערבה היא אזור הגידול של עונת החורף, ולכן חום בסוף הקיץ משפיע בעיקר על המחירים של נובמבר–דצמבר.",
};

const months = (n: number) => (n === 1 ? "חודש" : n === 2 ? "חודשיים" : `${n} חודשים`);

export default function WeatherCard({ weather, vegetable }: { weather: WeatherSignal | null; vegetable: string }) {
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
  const meaningful = weather.correlation >= weather.min_correlation;
  const bestLag = weather.lag_results.reduce((best, item) => (item.correlation > best.correlation ? item : best), weather.lag_results[0]);

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
        <div className={`stat ${meaningful ? trendClass(weather.implied_pressure_pct, 3) : "neutral"}`}>
          <span className="stat-value">{meaningful ? pct(weather.implied_pressure_pct) : "—"}</span>
          <span className="stat-label">{meaningful ? `השפעה משוערת על המחיר בעוד ${months(weather.lag_months)}` : "אין השפעה על התחזית של הירק הזה"}</span>
        </div>
      </div>

      <div className="explain">
        <h3 className="sub">איך מחושבת ההשפעה של הטמפרטורה</h3>
        <ol className="steps">
          <li>
            לכל חודש מ־2015 מחשבים בכמה טמפרטורת השיא הייתה שונה <em>מהרגיל לאותו חודש</em>, ובכמה המחיר היה שונה (באחוזים)
            <em> מהרגיל לאותו חודש</em>. כך העונה עצמה — קיץ חם, סתיו יקר — לא נספרת פעמיים.
          </li>
          <li>
            משווים את סטיית המחיר לסטיית הטמפרטורה חודש, חודשיים ושלושה חודשים קודם. הפער הזה הוא זמן התפתחות הפרי: חום קיצוני פוגע
            בחנטה, ואת הפרי החסר רואים בשוק רק כשהוא היה אמור להיקטף.
          </li>
          <li>
            הפער עם הקשר החזק ביותר נבחר. השיפוע שלו אומר כמה אחוזים למעלה, והמתאם אומר כמה הקשר אמין. מתאם מתחת ל־
            {weather.min_correlation.toFixed(1)} נחשב רעש ולא נכנס לתחזית.
          </li>
          <li>
            הלחץ הנוכחי = השיפוע × הסטייה הממוצעת של 60 הימים האחרונים, מוגבל ל־±{weather.max_pressure_pct.toFixed(0)}%, ונכלל בתחזיות מחודש
            ומעלה בלבד.
          </li>
        </ol>

        <h3 className="sub">מה נמצא ל{vegetable}</h3>
        <div className="scroll-x">
          <table className="table compact lags">
            <thead>
              <tr>
                <th>פער</th>
                <th>מתאם</th>
                <th>לכל מעלה</th>
              </tr>
            </thead>
            <tbody>
              {weather.lag_results.map((item) => (
                <tr key={item.lag_months} className={item.lag_months === bestLag.lag_months ? "best" : ""}>
                  <td>{months(item.lag_months)} קודם</td>
                  <td className={item.correlation >= weather.min_correlation ? "cell up" : "muted"}>{item.correlation.toFixed(2)}</td>
                  <td className={item.correlation >= weather.min_correlation ? "" : "muted"}>{signed(item.pct_per_degree, 1, "%")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {meaningful ? (
          <p>
            נבחר פער של <strong>{months(weather.lag_months)}</strong>: כל מעלה מעל הרגיל הייתה שווה כ־<strong>{signed(weather.pct_per_degree, 0, "%")}</strong> במחיר,
            על {weather.n_months} חודשים. זה אות חלש־בינוני — הטמפרטורה מסבירה כ־{Math.round(weather.correlation * weather.correlation * 100)}% מהתנודות;
            חגים, עונה ועובדים משפיעים הרבה יותר. <strong>כרגע:</strong> {weather.tmax_anomaly_60d >= 0 ? "חם" : "קריר"} ב־
            {Math.abs(weather.tmax_anomaly_60d).toFixed(1)}° מהרגיל
            {weather.heat_stress_days_30d_normal != null && <>, {weather.heat_stress_days_30d} ימי חום לעומת {Math.round(weather.heat_stress_days_30d_normal)} בדרך כלל</>} — לחץ
            משוער של <strong>{pct(weather.implied_pressure_pct)}</strong> על המחיר בעוד {months(weather.lag_months)}.
          </p>
        ) : (
          <p>
            ל{vegetable} <strong>לא נמצא קשר</strong> בין הטמפרטורה ב{weather.region_name} למחיר — המתאם הגבוה ביותר הוא {bestLag.correlation.toFixed(2)}, מתחת לסף.
            לכן מזג האוויר לא משפיע על התחזית של הירק הזה, גם כשחם מהרגיל (כרגע {signed(weather.tmax_anomaly_60d, 1, "°")}). סיבות אפשריות: גידול
            בעיקר בבתי צמיחה או באזור אחר, רגישות שונה לחום, או שוק שמושפע בעיקר מיצוא ולא מהיבול המקומי.
          </p>
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
