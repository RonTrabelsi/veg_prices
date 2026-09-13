import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { History } from "../api";
import { dateShort, price } from "../format";

export default function HistoryChart({ history }: { history: History }) {
  const weekly = history.weekly.filter((point) => point.price != null);
  return (
    <section className="card history">
      <header className="card-header">
        <h2>השנה האחרונה</h2>
        <span className="stamp">מחיר שבועי (ירוק) לעומת המחיר האופייני לעונה (אפור מקווקו)</span>
      </header>

      <div className="chart" dir="ltr">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={weekly} margin={{ top: 24, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tickFormatter={dateShort} tick={{ fontSize: 12 }} minTickGap={28} />
            <YAxis tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
            <Tooltip
              formatter={(value: any, name: any) => [price(value), name === "price" ? "מחיר" : name === "norm" ? "אופייני לעונה" : "מבצע"]}
              labelFormatter={(label: any) => dateShort(String(label))}
              contentStyle={{ direction: "rtl", fontFamily: "inherit" }}
            />
            {history.markers.map((marker) => (
              <ReferenceLine
                key={`${marker.group}-${marker.date}`}
                x={marker.date}
                stroke="#b7791f"
                strokeDasharray="2 2"
                label={{ value: marker.name_he, position: "top", fontSize: 11, fill: "#b7791f" }}
              />
            ))}
            <Line type="monotone" dataKey="norm" stroke="#718096" strokeDasharray="6 4" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="price" stroke="#2f855a" dot={false} strokeWidth={2.5} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3 className="sub">ממוצע שנתי לאורך השנים</h3>
      <div className="chart" dir="ltr">
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={history.yearly} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(value: any) => [price(value), "ממוצע"]} contentStyle={{ direction: "rtl", fontFamily: "inherit" }} />
            <Bar dataKey="mean" fill="#68a882" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="footnote">קווים כתומים מסמנים חגים. במקור אין נתונים בין 2009 ל־2014.</p>
    </section>
  );
}
