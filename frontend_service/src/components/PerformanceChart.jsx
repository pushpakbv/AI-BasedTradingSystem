import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PerformanceChart = ({ predictions }) => {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-[300px]">
        <p className="text-gray-500">No prediction data available</p>
      </div>
    );
  }

  // Top 5 strongest signals (positive and negative)
  const sortedPredictions = [...predictions]
    .sort((a, b) => Math.abs(b.prediction.combined_score) - Math.abs(a.prediction.combined_score))
    .slice(0, 5);

  const chartData = sortedPredictions.map(stock => ({
    ticker: stock.ticker,
    score: (stock.prediction.combined_score * 100).toFixed(1),
    fill: stock.prediction.combined_score > 0 ? '#10b981' : '#ef4444'
  }));

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Signals</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="ticker" />
          <YAxis />
          <Tooltip 
            formatter={(value) => [`${value}%`, 'Signal Strength']}
          />
          <Bar dataKey="score" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceChart;