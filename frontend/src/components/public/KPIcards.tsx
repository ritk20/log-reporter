interface StatsCardProps {
  title: string;
  value: number;
  median: number;
  stdev: number;
}
export default function StatsCard({ title, value, median, stdev }: StatsCardProps) {

  return (
  <div className="kpi-card">
    <h3>{title}</h3>
    <div className="main-value">{value.toLocaleString()} ms</div>
    <div className="stats-context">
      <span className="stdev">  : &plusmn;{stdev.toFixed(1)}&nbsp;&sigma;</span>
      <span className="median">Median: {median}</span>
    </div>
    <div className="deviation-bar">
      <div 
        className="stdev-range" 
        style={{ width: `${(stdev/value)*100}%` }}
      ></div>
    </div>
  </div>
  );
}
