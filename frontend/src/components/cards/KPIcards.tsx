interface KPICardProps {
  title: string;
  mean: number;
  min: number;
  max: number;
  unit?: string;
  colorScheme?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}

const tooltipTexts: Record<string, string> = {
  mean: "Mean (average): The sum of all values divided by the number of values, giving the central value of the data set.",
  min: "Minimum: The smallest value in the data set.",
  max: "Maximum: The largest value in the data set.",
};

const colorSchemes = {
  blue: {
    primary: 'text-blue-600',
    secondary: 'text-blue-500',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: 'bg-blue-100',
  },
  green: {
    primary: 'text-green-600',
    secondary: 'text-green-500',
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: 'bg-green-100',
  },
  purple: {
    primary: 'text-purple-600',
    secondary: 'text-purple-500',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    icon: 'bg-purple-100',
  },
  orange: {
    primary: 'text-orange-600',
    secondary: 'text-orange-500',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    icon: 'bg-orange-100',
  },
  red: {
    primary: 'text-red-600',
    secondary: 'text-red-500',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'bg-red-100',
  }
};

export default function KPICard({
  title,
  mean,
  min,
  max,
  unit = '',
  colorScheme = 'blue'
}: KPICardProps) {

  const colors = colorSchemes[colorScheme];

  const formatValue = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toFixed(2);
  };

  const primaryMetrics = [
    { key: "mean", label: "Mean", value: mean, isPrimary: true }
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 ${colors.icon} rounded-lg flex items-center justify-center`}>
              <svg className={`w-6 h-6 ${colors.primary}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500">Statistical Overview</p>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Metrics */}
      <div className="p-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          {primaryMetrics.map((metric) => (
            <div key={metric.key} className="text-center">
              <div className="relative group">
                <p className={`text-2xl font-bold ${colors.primary}`}>
                  {formatValue(metric.value)}{unit}
                </p>
                <p className="text-sm font-medium text-gray-600 mb-1">{metric.label}</p>
                
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 w-64 pointer-events-none">
                  {tooltipTexts[metric.key]}
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Stats Bar */}
        <div className={`${colors.bg} rounded-lg p-3 border ${colors.border}`}>
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Range:</span>
            <span className={`font-medium ${colors.primary}`}>
              {formatValue(min)}{unit} - {formatValue(max)}{unit}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
