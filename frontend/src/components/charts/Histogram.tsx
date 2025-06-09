import { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";

interface HistogramDataPoint {
  interval: string;
  total: number;
  load: number;
  transfer: number;
  redeem: number;
  split: number;
  merge: number;
  issue: number;
}

interface HistogramProps {
  title: string;
  data: HistogramDataPoint[];
  stacked?: boolean;
}

type ViewMode = "type" | "operation" | "total";

export default function Histogram({
  title,
  data,
  stacked = true,
}: HistogramProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("type");

  // Determine which series names and corresponding fields to show
  const { legendData, seriesData } = useMemo(() => {
    if (viewMode === "type") {
      return {
        legendData: ["LOAD", "TRANSFER", "REDEEM"],
        seriesData: [
          {
            name: "LOAD",
            data: data.map((d) => d.load),
          },
          {
            name: "TRANSFER",
            data: data.map((d) => d.transfer),
          },
          {
            name: "REDEEM",
            data: data.map((d) => d.redeem),
          },
        ],
      };
    } else if (viewMode === "operation") {
      return {
        legendData: ["SPLIT", "MERGE", "ISSUE"],
        seriesData: [
          {
            name: "SPLIT",
            data: data.map((d) => d.split),
          },
          {
            name: "MERGE",
            data: data.map((d) => d.merge),
          },
          {
            name: "ISSUE",
            data: data.map((d) => d.issue),
          },
        ],
      };
    } else {
      // viewMode === "total"
      return {
        legendData: ["TOTAL"],
        seriesData: [
          {
            name: "TOTAL",
            data: data.map((d) => d.total),
          },
        ],
      };
    }
  }, [viewMode, data]);

  const option = {
    title: { text: title, left: "center" },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" as const },
    },
    legend: {
      data: legendData,
      top: 30,
    },
    xAxis: {
      type: "category" as const,
      data: data.map((d) => d.interval),
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: "value" as const,
      name: "Amount",
    },
    series: seriesData.map((s) => ({
      name: s.name,
      type: "bar" as const,
      stack: viewMode === "total" ? undefined : stacked ? "total" : undefined,
      data: s.data,
    })),
  };

  return (
    <div>
      {/* View mode selector */}
      <div className="mb-3 flex space-x-2">
        <button
          onClick={() => setViewMode("type")}
          className={`px-3 py-1 rounded ${
            viewMode === "type"
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          } text-sm`}
        >
          By Type
        </button>
        <button
          onClick={() => setViewMode("operation")}
          className={`px-3 py-1 rounded ${
            viewMode === "operation"
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          } text-sm`}
        >
          By Operation
        </button>
        <button
          onClick={() => setViewMode("total")}
          className={`px-3 py-1 rounded ${
            viewMode === "total"
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          } text-sm`}
        >
          Total Only
        </button>
      </div>

      {/* ECharts Bar Chart */}
      <ReactECharts
        option={option}
        style={{ height: 400 }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}
