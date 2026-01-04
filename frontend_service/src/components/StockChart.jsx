import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { TrendingUp, TrendingDown, Loader, AlertCircle, Calendar } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const StockChart = ({ ticker, stockData }) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    current: 0,
    previous_close: 0,
    high: 0,
    low: 0,
    change: 0,
    changePercent: 0,
    volume: 0,
    avgVolume: 0
  });
  const [chartType, setChartType] = useState('area'); // 'area', 'line', 'composed'

  useEffect(() => {
    const loadStockData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let data = stockData;
        
        // Fetch from API if not provided
        if (!data && ticker) {
          console.log(`📡 Fetching stock data for ${ticker}`);
          try {
            const response = await axios.get(`${API_BASE_URL}/stock/${ticker}`);
            data = response.data;
            console.log('✅ Stock data received:', data);
          } catch (apiErr) {
            console.warn(`⚠️ API fetch failed, will use generated data: ${apiErr.message}`);
            data = null;
          }
        }
        
        // If no data from API or props, generate realistic sample data
        if (!data || !data.historical_data || data.historical_data.length === 0) {
          console.log('📊 Generating sample stock data...');
          data = generateSampleStockData(ticker);
        }
        
        if (data && data.historical_data && data.historical_data.length > 0) {
          processStockData(data);
        } else {
          setError('Unable to load stock data');
          setLoading(false);
        }
      } catch (err) {
        console.error('Error loading stock data:', err);
        setError(err.message || 'Failed to load stock data');
        setLoading(false);
      }
    };

    if (ticker || stockData) {
      loadStockData();
    } else {
      setError('No ticker provided');
      setLoading(false);
    }
  }, [ticker, stockData]);

  // Generate realistic sample stock data
  const generateSampleStockData = (tickerSymbol) => {
    const now = new Date();
    const historicalData = [];
    let basePrice = Math.random() * 200 + 50; // Random base price between 50-250

    // Generate 180 days of data
    for (let i = 180; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Add realistic price movements
      const volatility = (Math.random() - 0.5) * 10;
      const trend = (Math.random() - 0.5) * 2;
      basePrice = Math.max(basePrice + trend, basePrice * 0.95);
      
      const open = basePrice + (Math.random() - 0.5) * 5;
      const close = basePrice + volatility;
      const high = Math.max(open, close) + Math.random() * 3;
      const low = Math.min(open, close) - Math.random() * 3;
      const volume = Math.floor(Math.random() * 50000000 + 10000000);

      historicalData.push({
        date: date.toISOString().split('T')[0],
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: volume,
        adjClose: parseFloat(close.toFixed(2))
      });

      basePrice = close;
    }

    return {
      ticker: tickerSymbol || 'SAMPLE',
      company_name: `${tickerSymbol} Inc.`,
      current_price: parseFloat(basePrice.toFixed(2)),
      previous_close: parseFloat((basePrice * 0.98).toFixed(2)),
      day_high: parseFloat((basePrice * 1.02).toFixed(2)),
      day_low: parseFloat((basePrice * 0.98).toFixed(2)),
      fifty_two_week_high: parseFloat((basePrice * 1.15).toFixed(2)),
      fifty_two_week_low: parseFloat((basePrice * 0.70).toFixed(2)),
      volume: Math.floor(Math.random() * 50000000 + 10000000),
      avg_volume: Math.floor(Math.random() * 40000000 + 15000000),
      market_cap: 'Sample Data',
      pe_ratio: (Math.random() * 30 + 10).toFixed(2),
      dividend_yield: (Math.random() * 4).toFixed(2),
      historical_data: historicalData,
      lastUpdated: new Date().toISOString()
    };
  };

  const processStockData = (data) => {
    try {
      if (!data.historical_data || data.historical_data.length === 0) {
        setError('No historical data available');
        setLoading(false);
        return;
      }

      const historical = data.historical_data;
      
      // Transform data for chart - last 90 days
      const transformedData = historical
        .slice(-90)
        .map((item) => ({
          date: new Date(item.date).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: '2-digit'
          }),
          fullDate: item.date,
          price: parseFloat(item.close),
          open: parseFloat(item.open),
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          volume: item.volume,
          sma20: calculateSMA(historical, 20, historical.indexOf(item)), // 20-day moving average
          sma50: calculateSMA(historical, 50, historical.indexOf(item))  // 50-day moving average
        }));

      setChartData(transformedData);

      // Calculate statistics
      const latest = historical[historical.length - 1];
      const previous = historical[Math.max(0, historical.length - 2)];
      const change = parseFloat(latest.close) - parseFloat(previous.close);
      const changePercent = (change / parseFloat(previous.close)) * 100;
      const volumes = historical.map(h => h.volume);

      setStats({
        current: parseFloat(latest.close),
        previous_close: parseFloat(previous.close),
        high: Math.max(...historical.map(h => parseFloat(h.high))).toFixed(2),
        low: Math.min(...historical.map(h => parseFloat(h.low))).toFixed(2),
        change: change.toFixed(2),
        changePercent: changePercent.toFixed(2),
        volume: latest.volume,
        avgVolume: Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length)
      });

      setLoading(false);
    } catch (err) {
      console.error('Error processing stock data:', err);
      setError('Failed to process stock data');
      setLoading(false);
    }
  };

  // Calculate Simple Moving Average
  const calculateSMA = (data, period, currentIndex) => {
    if (currentIndex < period - 1) return null;
    
    const subset = data.slice(currentIndex - period + 1, currentIndex + 1);
    const sum = subset.reduce((acc, item) => acc + parseFloat(item.close), 0);
    return parseFloat((sum / period).toFixed(2));
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-2">
          <Loader className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-gray-600">Loading chart data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <AlertCircle className="w-8 h-8 text-yellow-500" />
          <p className="text-gray-600">{error}</p>
          <p className="text-sm text-gray-500">Using sample data for demonstration</p>
        </div>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex items-center justify-center h-96">
        <p className="text-gray-500">No stock data available</p>
      </div>
    );
  }

  const isPositive = parseFloat(stats.change) >= 0;
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600';
  const bgColor = isPositive ? 'bg-green-50' : 'bg-red-50';
  const lineColor = isPositive ? '#10b981' : '#ef4444';

  const formatVolume = (volume) => {
    if (volume >= 1000000000) return (volume / 1000000000).toFixed(2) + 'B';
    if (volume >= 1000000) return (volume / 1000000).toFixed(2) + 'M';
    if (volume >= 1000) return (volume / 1000).toFixed(2) + 'K';
    return volume.toString();
  };

  const formatPrice = (value) => {
    return `$${parseFloat(value).toFixed(2)}`;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-700 text-white text-sm shadow-lg">
          <p className="font-semibold text-blue-400 mb-2">{payload[0].payload.date}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? formatPrice(entry.value) : entry.value}
            </p>
          ))}
          <p className="text-gray-400 text-xs mt-2">
            H: {formatPrice(payload[0].payload.high)} | L: {formatPrice(payload[0].payload.low)}
          </p>
          <p className="text-gray-400 text-xs">
            Vol: {formatVolume(payload[0].payload.volume)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header Section */}
      <div className={`${bgColor} p-6 border-b border-gray-200`}>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-baseline gap-3 mb-2">
              <h3 className="text-4xl font-bold text-gray-900">
                {formatPrice(stats.current)}
              </h3>
              <span className={`flex items-center gap-1 text-lg font-semibold ${changeColor}`}>
                {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {isPositive ? '+' : ''}{stats.change} ({stats.changePercent}%)
              </span>
            </div>
            <p className="text-sm text-gray-600">
              Previous close: {formatPrice(stats.previous_close)}
            </p>
          </div>
          
          {/* Chart Type Selector */}
          <div className="flex gap-2">
            {['area', 'line', 'composed'].map((type) => (
              <button
                key={type}
                onClick={() => setChartType(type)}
                className={`px-3 py-2 rounded-md text-sm font-medium capitalize transition-colors ${
                  chartType === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-600 font-medium">52W High</p>
            <p className="text-lg font-semibold text-gray-900">{formatPrice(stats.high)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">52W Low</p>
            <p className="text-lg font-semibold text-gray-900">{formatPrice(stats.low)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">Volume</p>
            <p className="text-lg font-semibold text-gray-900">{formatVolume(stats.volume)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 font-medium">Avg Volume</p>
            <p className="text-lg font-semibold text-gray-900">{formatVolume(stats.avgVolume)}</p>
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="p-6">
        <ResponsiveContainer width="100%" height={450}>
          {chartType === 'area' && (
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={lineColor} stopOpacity={0.8}/>
                  <stop offset="95%" stopColor={lineColor} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} domain={['dataMin - 5', 'dataMax + 5']} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="price" stroke={lineColor} strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" name="Price" />
            </AreaChart>
          )}

          {chartType === 'line' && (
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} domain={['dataMin - 5', 'dataMax + 5']} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line type="monotone" dataKey="price" stroke={lineColor} strokeWidth={2} name="Close Price" dot={false} />
              <Line type="monotone" dataKey="sma20" stroke="#f59e0b" strokeWidth={1} strokeDasharray="5 5" name="20-Day SMA" dot={false} />
              <Line type="monotone" dataKey="sma50" stroke="#8b5cf6" strokeWidth={1} strokeDasharray="5 5" name="50-Day SMA" dot={false} />
            </LineChart>
          )}

          {chartType === 'composed' && (
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis yAxisId="left" stroke="#9ca3af" style={{ fontSize: '12px' }} domain={['dataMin - 5', 'dataMax + 5']} />
              <YAxis yAxisId="right" orientation="right" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar yAxisId="right" dataKey="volume" fill="#e5e7eb" opacity={0.5} name="Volume" />
              <Line yAxisId="left" type="monotone" dataKey="price" stroke={lineColor} strokeWidth={2} name="Price" dot={false} />
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <span>Last {chartData.length} trading days</span>
        </div>
        <div className="text-right">
          <p>This is sample/demo data for visualization purposes</p>
        </div>
      </div>
    </div>
  );
};

export default StockChart;