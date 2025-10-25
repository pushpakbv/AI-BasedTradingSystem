import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceDot, ReferenceLine
} from 'recharts';
import { format, parseISO, addDays } from 'date-fns';

const StockChart = ({ stockData, prediction }) => {
  if (!stockData || !stockData.historical_data) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 h-96 flex items-center justify-center">
        <p className="text-gray-500">No stock data available</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = stockData.historical_data.map(item => ({
    date: item.date,
    price: item.close,
    volume: item.volume
  }));

  // Add prediction point
  if (prediction && prediction.prediction) {
    const lastDate = stockData.historical_data[stockData.historical_data.length - 1].date;
    const lastPrice = stockData.historical_data[stockData.historical_data.length - 1].close;
    const nextDate = format(addDays(parseISO(lastDate), 1), 'yyyy-MM-dd');
    
    // Calculate predicted price based on signal
    const predictionMultiplier = prediction.prediction.combined_score;
    const predictedPrice = lastPrice * (1 + predictionMultiplier * 0.05); // 5% max change
    
    chartData.push({
      date: nextDate,
      price: null,
      predictedPrice: predictedPrice,
      isPrediction: true
    });
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="text-sm font-semibold text-gray-900">
            {format(parseISO(data.date), 'MMM dd, yyyy')}
          </p>
          {data.price && (
            <p className="text-sm text-gray-700">
              Price: <span className="font-semibold">${data.price.toFixed(2)}</span>
            </p>
          )}
          {data.predictedPrice && (
            <p className="text-sm text-blue-600 font-semibold">
              Predicted: ${data.predictedPrice.toFixed(2)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Price Chart (7 Days + Prediction)</h3>
        {prediction && (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
            <span className="text-sm text-gray-600">Actual</span>
            <div className="w-3 h-3 bg-purple-600 rounded-full ml-3"></div>
            <span className="text-sm text-gray-600">Predicted</span>
          </div>
        )}
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => format(parseISO(date), 'MMM dd')}
            style={{ fontSize: '12px' }}
          />
          <YAxis
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Actual price line */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ fill: '#2563eb', r: 4 }}
            name="Actual Price"
            connectNulls={false}
          />
          
          {/* Predicted price point */}
          <Line
            type="monotone"
            dataKey="predictedPrice"
            stroke="#9333ea"
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ fill: '#9333ea', r: 6 }}
            name="AI Prediction"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;