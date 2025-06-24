import { useState } from 'react';
import ReactECharts from 'echarts-for-react';

interface DrillDownData {
  [key: string]: {
    [key: string]: number;
  };
}

interface DrillDownPieChartProps {
  data: DrillDownData;
  title: string;
  colorScheme?: 'blue' | 'green' | 'purple' | 'orange';
}

const colorSchemes = {
  blue: ['#3B82F6', '#1E40AF', '#172554'],
  green: ['#10B981', '#047857', '#064E3B'],
  purple: ['#8B5CF6', '#6D28D9', '#4C1D95'],
  orange: ['#F59E0B', '#B45309', '#78350F']
};

export default function DrillDownPieChart({ 
  data, 
  title, 
  colorScheme = 'blue' 
}: DrillDownPieChartProps) {
  const [currentLevel, setCurrentLevel] = useState<'parent' | 'child'>('parent');
  const [selectedParent, setSelectedParent] = useState<string>('');
  const [breadcrumb, setBreadcrumb] = useState<string[]>([title]);

  const colors = colorSchemes[colorScheme];

  // Prepare parent level data
  const getParentData = () => {
    return Object.entries(data).map(([name, operations], index) => {
      const totalValue = Object.values(operations).reduce((sum, val) => sum + val, 0);
      return { 
        name, 
        value: totalValue,
        groupId: name,
        itemStyle: {
          color: colors[index % colors.length],
          borderColor: '#ffffff',
          borderWidth: 2
        }
      };
    });
  };

  // Prepare child level data (operations within selected type)
  const getChildData = (parentKey: string) => {
    if (!data[parentKey]) return [];
    return Object.entries(data[parentKey]).map(([name, value], index) => ({
      name,
      value,
      // Set parent's group ID for transition matching
      groupId: parentKey,
      itemStyle: {
        color: colors[index % colors.length],
        borderColor: '#ffffff',
        borderWidth: 2
      }
    }));
  };

  // Handle drill-down click
  interface PieChartClickEvent {
    name: string;
    [key: string]: unknown;
  }

  const handleDrillDown = (params: PieChartClickEvent) => {
    if (currentLevel === 'parent') {
      const parentName = params.name;
      
      // Trigger animation sequence
      setTimeout(() => {
        setSelectedParent(parentName);
        setCurrentLevel('child');
        setBreadcrumb([title, parentName]);
      }, 100);
    }
  };

  // Handle drill-up (back to parent)
  const handleDrillUp = () => {
        setCurrentLevel('parent');
        setSelectedParent('');
        setBreadcrumb([title]);
  };

  // Get current chart data based on level
  const getCurrentData = () => {
    return currentLevel === 'parent' 
      ? getParentData() 
      : getChildData(selectedParent);
  };

  // ECharts option configuration
  const getChartOption = () => {
    const currentData = getCurrentData();
    
    return {
      tooltip: {
        trigger: 'item',
        formatter: function(params: { name: string; value: number; percent: number }) {
          const percentage = params.percent.toFixed(1);
          return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 4px;">${params.name}</div>
              <div>Count: <span style="font-weight: bold;">${params.value}</span></div>
              <div>Percentage: <span style="font-weight: bold;">${percentage}%</span></div>
              ${currentLevel === 'parent' ? '<div style="margin-top: 4px; color: #6B7280; font-size: 12px;">Click to drill down</div>' : ''}
            </div>
          `;
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#E5E7EB',
        borderWidth: 1,
        textStyle: {
          color: '#374151'
        }
      },
      legend: {
        orient: 'horizontal',
        top: 0,
        left: 'center',
        textStyle: {
          color: '#6B7280',
          fontSize: 12
        }
      },
      series: [{
        type: 'pie',
        id: 'drilldownPie',
        radius: '60%',
        center: ['50%', '55%'],
        // FIXED UNIVERSAL TRANSITION
        universalTransition: {
          enabled: true,
          divideShape: 'clone'  // Essential for pie transitions
        },
        // SET DATA GROUP ID FOR TRANSITION MATCHING
        dataGroupId: currentLevel === 'parent' 
          ? 'parent' 
          : `child_${selectedParent}`,
        data: currentData.map((item) => ({
          ...item,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              scale: currentLevel === 'parent' ? 1.05 : 1.02
            }
          }
        })),
        label: {
          show: true,
          formatter: '{b}: {d}%',
          fontSize: 11,
          color: '#374151'
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10
        }
      }]
    };
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
              <nav className="flex items-center space-x-1 text-sm text-gray-500 mt-1">
                {breadcrumb.map((item, index) => (
                  <span key={index} className="flex items-center">
                    {index > 0 && (
                      <svg className="w-4 h-4 mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                    <span className='text-lg font-semibold text-gray-900'>
                      {item}
                    </span>
                  </span>
                ))}
              </nav>
          </div>
          
          {/* Back Button */}
          {currentLevel === 'child' && (
            <button
              onClick={handleDrillUp}
              className={`inline-flex items-center gap-2 px-2 py-1 rounded-lg font-medium transition-all duration-300`}
            >
              <svg className={`w-4 h-4 transition-transform duration-300`} 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div className="p-6">
        <div className="h-96">
          <ReactECharts
            option={getChartOption()}
            style={{ height: '100%', width: '100%' }}
            onEvents={{
              click: handleDrillDown
            }}
          />
        </div>
      </div>
    </div>
  );
}
