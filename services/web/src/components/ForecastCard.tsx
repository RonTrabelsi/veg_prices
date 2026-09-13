import { Forecast, ForecastPoint, Overview, VerdictLabel } from "../api";
import { date, horizonLabel, pct, price, trendClass } from "../format";

const VERDICTS: Record<VerdictLabel, { title: string; hint: string; icon: string }> = {
  wait: { title: "כדאי לחכות", hint: "המחיר צפוי לעלות בחודש הקרוב", icon: "⏳" },
  sell: { title: "כדאי למכור עכשיו", hint: "המחיר צפוי לרדת בחודש הקרוב", icon: "✅" },
  hold: { title: "המחיר צפוי להישאר יציב", hint: "אין יתרון ברור לחכות או להזדרז", icon: "➡️" },
};

/** One line saying what the point forecast was built from */
function basis(point: ForecastPoint): string {
  const parts: string[] = [];
  const todayShare = Math.round(point.persistence_weight * 100);
  if (todayShare > 0) parts.push(`המחיר של היום ${todayShare}%`);
  if (todayShare < 100) {
    const season = point.norm_kind === "holiday" && point.nearest_holiday ? `פרופיל ${point.nearest_holiday.name_he}` : "העונה";
    parts.push(`${season} ${100 - todayShare}%`);
  }
  if (point.weather_scale > 0 && point.weather_pressure_pct !== 0) parts.push(`מזג אוויר ${pct(point.weather_scale * point.weather_pressure_pct)}`);
  return parts.join(" · ");
}

export default function ForecastCard({ forecast, overview }: { forecast: Forecast; overview: Overview }) {
  const verdict = VERDICTS[forecast.verdict.label];
  const priceOnly = forecast.horizons.filter((point) => point.persistence_weight === 1 && point.weather_scale === 0);
  const withSignals = forecast.horizons.filter((point) => point.persistence_weight < 1 || point.weather_scale > 0);
  return (
    <section className="card forecast">
      <header className="card-header">
        <h2>מה צפוי?</h2>
      </header>

      <div className={`verdict ${forecast.verdict.label} ${forecast.verdict.confidence}`}>
        <span className="verdict-icon" aria-hidden>
          {verdict.icon}
        </span>
        <div>
          <div className="verdict-title">{verdict.title}</div>
          <div className="verdict-hint">
            {verdict.hint} · {pct(forecast.verdict.change_pct)} · ביטחון {forecast.verdict.confidence === "high" ? "גבוה" : "נמוך"}
          </div>
        </div>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>מתי</th>
            <th>מחיר צפוי</th>
            <th>טווח סביר</th>
            <th>שינוי</th>
          </tr>
        </thead>
        <tbody>
          {forecast.horizons.map((point) => (
            <tr key={point.horizon_days}>
              <td>
                <div>{horizonLabel(point.horizon_days)}</div>
                <div className="muted small">{date(point.target_date)}</div>
                <div className="basis">{basis(point)}</div>
              </td>
              <td className="strong">{price(point.point)}</td>
              <td className="muted">
                {price(point.low)} – {price(point.high)}
              </td>
              <td>
                <span className={`chip ${trendClass(point.change_vs_now_pct)}`}>{pct(point.change_vs_now_pct)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <details className="details">
        <summary>איך נבנתה התחזית, ולמה החגים ומזג האוויר לא תמיד משפיעים</summary>
        <div className="explain">
          <p>
            לכל טווח נבדקו על {forecast.horizons[0]?.n ?? 0} מקרים מהשנים האחרונות כל השילובים של: המחיר של היום, המחיר האופייני לעונה,
            <strong> פרופיל המחיר סביב החג הקרוב</strong> (כי חגים נודדים בין השנים), ו<strong>לחץ הטמפרטורה</strong> של החודשיים האחרונים. השילוב עם
            השגיאה הקטנה ביותר הוא שמוצג, והוא כתוב מתחת לכל שורה.
          </p>
          {priceOnly.length > 0 && (
            <p>
              ל{priceOnly.map((point) => horizonLabel(point.horizon_days).replace("בעוד ", "")).join(", ")} נבחר{" "}
              <strong>המחיר של היום בלבד</strong>: בטווח הזה השוק כבר מגלם את החג הקרוב ואת החום שהיה — הפרי שלא חנט כבר חסר, והעלייה
              לפני החג כבר התחילה. הוספת החגים ומזג האוויר בכוח הייתה <em>מגדילה</em> את השגיאה
              {priceOnly[0]?.mae != null && priceOnly[0]?.signals_forced_mae != null && (
                <>
                  {" "}
                  (ל{horizonLabel(priceOnly[0].horizon_days).replace("בעוד ", "")}: מ־{price(priceOnly[0].mae)} ל־{price(priceOnly[0].signals_forced_mae)})
                </>
              )}
              .
            </p>
          )}
          {withSignals.length > 0 && withSignals[0].mae != null && withSignals[0].naive_mae != null && (
            <p>
              מ{horizonLabel(withSignals[0].horizon_days).replace("בעוד ", "")} ומעלה החגים ומזג האוויר כן משפרים: שגיאה של {price(withSignals[0].mae)} לעומת{" "}
              {price(withSignals[0].naive_mae)} אם מניחים שהמחיר לא ישתנה
              {withSignals[0].season_mae != null && <> ו־{price(withSignals[0].season_mae)} לפי העונה בלבד</>}.
            </p>
          )}
          <p className="muted small">
            הטווח הסביר מכסה 80% ממקרי העבר. המחיר הנוכחי: {price(overview.last_price)}.
          </p>
        </div>
      </details>
    </section>
  );
}
