import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const PerformanceChart = ({ predictions }) => {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-[300px]">
        <p className="text-gray-500">No prediction data available</p>
      </div>
    );
  }

  const getScore = (p) => {
    const nested = p?.prediction && typeof p.prediction === 'object' ? p.prediction : null;
    const s = nested?.combined_score ?? p?.combined_score ?? 0;
    return parseFloat(s) || 0;
  };

  // Top 5 strongest signals (positive and negative)
  const sortedPredictions = [...predictions]
    .sort((a, b) => Math.abs(getScore(b)) - Math.abs(getScore(a)))
    .slice(0, 5);

  const chartData = sortedPredictions.map((stock) => {
    const score = getScore(stock);
    return {
      ticker: stock.ticker,
      score: Number((score * 100).toFixed(1)),
      fill: score > 0 ? '#10b981' : '#ef4444'
    };
  });

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Signals</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="ticker" />
          <YAxis />
          <Tooltip formatter={(value) => [`${value}%`, 'Signal Strength']} />
          <Bar dataKey="score">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceChart;
