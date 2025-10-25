import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const SignalDistribution = ({ data }) => {
  if (!data) return null;

  const chartData = [
    { name: 'Strong Buy', value: data.STRONG_BUY || 0, color: '#10b981' },
    { name: 'Buy', value: data.BUY || 0, color: '#34d399' },
    { name: 'Hold', value: data.HOLD || 0, color: '#9ca3af' },
    { name: 'Sell', value: data.SELL || 0, color: '#f87171' },
    { name: 'Strong Sell', value: data.STRONG_SELL || 0, color: '#ef4444' }
  ].filter(item => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-[300px]">
        <p className="text-gray-500">No signal data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Signal Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SignalDistribution;