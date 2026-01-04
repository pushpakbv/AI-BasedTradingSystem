import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Loader } from 'lucide-react';

const StockChart = ({ ticker, stockData }) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    current: 0,
    previous_close: 0,
    high: 0,
    low: 0,
    change: 0,
    changePercent: 0,
    volume: 0
  });

  useEffect(() => {
    if (stockData && stockData.historical_data && Array.isArray(stockData.historical_data)) {
      processStockData(stockData);
    } else {
      setLoading(false);
    }
  }, [stockData, ticker]);

  const processStockData = (data) => {
    try {
      // Get historical data
      const historicalData = data.historical_data || [];
      
      // Transform the data for the chart - limit to last 60 data points for better performance
      const transformedData = historicalData
        .slice(-60)
        .map(point => ({
          date: point.date || '',
          price: parseFloat(point.close || 0),
          open: parseFloat(point.open || 0),
          high: parseFloat(point.high || 0),
          low: parseFloat(point.low || 0),
          volume: parseInt(point.volume || 0)
        }))
        .sort((a, b) => new Date(a.date) - new Date(b.date));

      if (transformedData.length > 0) {
        const latest = transformedData[transformedData.length - 1];
        const oldest = transformedData[0];
        const change = latest.price - (data.previous_close || oldest.price);
        const prevClose = data.previous_close || oldest.price;
        const changePercent = (change / prevClose) * 100;

        setChartData(transformedData);
        setStats({
          current: data.current_price || latest.price,
          previous_close: prevClose,
          high: Math.max(...transformedData.map(d => d.high)).toFixed(2),
          low: Math.min(...transformedData.map(d => d.low)).toFixed(2),
          change: change.toFixed(2),
          changePercent: changePercent.toFixed(2),
          volume: data.volume || 0
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error processing stock data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-2">
          <Loader className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-gray-600">Loading chart...</p>
        </div>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-96">
        <p className="text-gray-500">No stock data available</p>
      </div>
    );
  }

  const isPositive = parseFloat(stats.change) >= 0;
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600';
  const bgColor = isPositive ? 'bg-green-50' : 'bg-red-50';

  // Format volume
  const formatVolume = (volume) => {
    if (volume >= 1000000) return (volume / 1000000).toFixed(2) + 'M';
    if (volume >= 1000) return (volume / 1000).toFixed(2) + 'K';
    return volume.toString();
  };

  // Format date for display
  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700 text-white text-sm">
          <p className="font-semibold">{formatDate(data.date)}</p>
          <p className="text-blue-400">Close: ${data.price.toFixed(2)}</p>
          <p className="text-gray-300 text-xs">
            High: ${data.high.toFixed(2)} | Low: ${data.low.toFixed(2)}
          </p>
          <p className="text-gray-300 text-xs">Vol: {formatVolume(data.volume)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header Section */}
      <div className={`${bgColor} p-6 border-b border-gray-200`}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-baseline gap-3">
              <h3 className="text-3xl font-bold text-gray-900">
                ${parseFloat(stats.current).toFixed(2)}
              </h3>
              <span className={`flex items-center gap-1 text-lg font-semibold ${changeColor}`}>
                {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {isPositive ? '+' : ''}{stats.change} ({stats.changePercent}%)
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Previous close: ${parseFloat(stats.previous_close).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-600 font-medium">Today's High</p>
            <p className="text-lg font-semibold text-gray-900">${stats.high}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">Today's Low</p>
            <p className="text-lg font-semibold text-gray-900">${stats.low}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">Volume</p>
            <p className="text-lg font-semibold text-gray-900">{formatVolume(stats.volume)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">Data Points</p>
            <p className="text-lg font-semibold text-gray-900">{chartData.length}</p>
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="p-6">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop 
                  offset="5%" 
                  stopColor={isPositive ? '#10b981' : '#ef4444'} 
                  stopOpacity={0.3}
                />
                <stop 
                  offset="95%" 
                  stopColor={isPositive ? '#10b981' : '#ef4444'} 
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#e5e7eb"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#9ca3af' }}
              tickFormatter={formatDate}
              interval={Math.floor(chartData.length / 6)}
            />
            <YAxis
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#9ca3af' }}
              domain={['dataMin - 5', 'dataMax + 5']}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? '#10b981' : '#ef4444'}
              strokeWidth={2.5}
              fill="url(#colorPrice)"
              dot={false}
              activeDot={{ r: 6, fill: isPositive ? '#10b981' : '#ef4444' }}
              name="Price"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
        <p>
          {chartData[0]?.date && chartData[chartData.length - 1]?.date ? (
            <>Data from {formatDate(chartData[0].date)} to {formatDate(chartData[chartData.length - 1].date)}</>
          ) : (
            <>Displaying last {chartData.length} data points</>
          )}
        </p>
      </div>
    </div>
  );
};

export default StockChart;