import { HolidayEffect, UpcomingHoliday } from "../api";
import { date, daysUntil, pct, trendClass } from "../format";

const WINDOW_LABELS: Record<string, string> = {
  "-28..-15": "2–4 שבועות לפני",
  "-14..-8": "שבועיים לפני",
  "-7..-1": "שבוע לפני",
  "0..6": "בחג",
  "7..20": "אחרי החג",
};

export default function HolidaysCard({ holidays }: { holidays: { upcoming: UpcomingHoliday[]; effects: HolidayEffect[] } }) {
  const upcoming = holidays.upcoming.slice(0, 4);
  return (
    <section className="card holidays">
      <header className="card-header">
        <h2>חגים קרובים</h2>
        <span className="stamp">איך המחיר התנהג סביב החג בשנים האחרונות</span>
      </header>

      {upcoming.length === 0 && <p className="muted">לוח החגים עוד לא נטען.</p>}

      <ul className="holiday-list">
        {upcoming.map((holiday) => (
          <li key={`${holiday.group}-${holiday.date}`} className="holiday">
            <div className="holiday-when">
              <div className="strong">{holiday.name_he}</div>
              <div className="muted small">
                {date(holiday.date)} · {daysUntil(holiday.days_until)}
              </div>
            </div>
            {holiday.pre_holiday_effect_pct != null ? (
              <div className={`chip large ${trendClass(holiday.pre_holiday_effect_pct, 5)}`}>
                {pct(holiday.pre_holiday_effect_pct)} <span className="chip-note">בשבוע שלפני · ב־{Math.round(holiday.consistency_pct ?? 0)}% מהשנים</span>
              </div>
            ) : (
              <div className="chip neutral">אין די נתונים</div>
            )}
          </li>
        ))}
      </ul>

      {holidays.effects.length > 0 && (
        <details className="details">
          <summary>הפרופיל המלא של כל החגים</summary>
          <div className="scroll-x">
            <table className="table compact">
              <thead>
                <tr>
                  <th>חג</th>
                  {holidays.effects[0].windows.map((window) => (
                    <th key={window.window}>{WINDOW_LABELS[window.window] ?? window.window}</th>
                  ))}
                  <th>שנים</th>
                </tr>
              </thead>
              <tbody>
                {holidays.effects.map((effect) => (
                  <tr key={effect.group}>
                    <td className="strong">{effect.name_he}</td>
                    {effect.windows.map((window) => (
                      <td key={window.window} className={`cell ${trendClass(window.effect_pct, 5)}`}>
                        {pct(window.effect_pct)}
                      </td>
                    ))}
                    <td className="muted">{effect.n_years}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="footnote">האחוזים הם ביחס למחיר הממוצע של אותה שנה.</p>
        </details>
      )}
    </section>
  );
}
