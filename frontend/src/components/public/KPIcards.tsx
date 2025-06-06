interface KPICardProps {
  title: string;
  mean: number;
  stdev: number;
  min: number;
  max: number;
  percentile25: number;
  percentile50: number;
  percentile75: number;
}

const tooltipTexts: Record<string, string> = {
  mean:
    "Mean (average): The sum of all values divided by the number of values, giving the central value of the data set.",
  stdev:
    "Standard Deviation: A measure of how spread out the numbers are around the mean. A low stdev means data points are close to the mean.",
  min: "Minimum: The smallest value in the data set.",
  max: "Maximum: The largest value in the data set.",
  percentile25:
    "25th Percentile (Q1): The value below which 25% of the data falls. Also known as the first quartile.",
  percentile50:
    "50th Percentile (Median): The middle value of the data set when sorted. Half the data is below, half above.",
  percentile75:
    "75th Percentile (Q3): The value below which 75% of the data falls. Also known as the third quartile.",
};

export default function KPICard({
  title,
  mean,
  stdev,
  min,
  max,
  percentile25,
  percentile50,
  percentile75,
}: KPICardProps) {
  const metrics = [
    { key: "mean", label: "Mean", value: mean },
    { key: "stdev", label: "Stdev", value: stdev },
    { key: "min", label: "Min", value: min },
    { key: "max", label: "Max", value: max },
    { key: "percentile25", label: "25%", value: percentile25 },
    { key: "percentile50", label: "50%", value: percentile50 },
    { key: "percentile75", label: "75%", value: percentile75 },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 w-80">
      <h2 className="text-lg font-semibold mb-3 text-gray-800 flex justify-center">{title}</h2>
      <div className="grid grid-cols-2 gap-4 mx-5">
        {metrics.map((metric) => (
          <div key={metric.key} className="relative group">
            <div className="flex items-center space-x-1">
              <span className="font-medium text-gray-700 cursor-pointer">{metric.label}:</span>
              <span className="text-gray-900 cursor-pointer">{metric.value}</span>
            </div>
            <div className="absolute bottom-0 left-0 transform translate-y-full mt-1 w-56 bg-gray-800 text-white text-xs rounded-md p-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-200 z-10">
              {tooltipTexts[metric.key]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
