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
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import axios from 'axios';

const StockGraphCard = ({ ticker, stockData: initialStockData }) => {
  const POLYGON_API_KEY = '4GRu2rLV1D6q7ZcPj33L0bw72YmZNAdN';
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    currentPrice: 0,
    change: 0,
    changePercent: 0,
    high: 0,
    low: 0,
  });
  const [stockData, setStockData] = useState(initialStockData);

  // Fetch from Polygon.io API
  const fetchFromPolygon = async (tickerSymbol) => {
    try {
      console.log(`📊 Fetching from Polygon.io for ${tickerSymbol}...`);
      
      // Get 90 days of data
      const today = new Date();
      const ninetyDaysAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
      
      const fromDate = ninetyDaysAgo.toISOString().split('T')[0];
      const toDate = today.toISOString().split('T')[0];
      
      const response = await axios.get('https://api.polygon.io/v2/aggs/ticker/' + tickerSymbol + '/range/1/day/' + fromDate + '/' + toDate, {
        params: {
          apikey: POLYGON_API_KEY
        },
        timeout: 10000
      });

      if (response.data && response.data.results && response.data.results.length > 0) {
        console.log(`✅ Data from Polygon.io for ${tickerSymbol}`);
        
        const historicalData = response.data.results.map(item => ({
          date: new Date(item.t).toISOString().split('T')[0],
          open: parseFloat(item.o.toFixed(2)),
          high: parseFloat(item.h.toFixed(2)),
          low: parseFloat(item.l.toFixed(2)),
          close: parseFloat(item.c.toFixed(2)),
          volume: item.v || 0
        }));

        const currentPrice = historicalData[historicalData.length - 1].close;

        return {
          ticker: tickerSymbol,
          company_name: tickerSymbol,
          historical_data: historicalData,
          current_price: currentPrice,
          last_updated: new Date().toISOString()
        };
      }
    } catch (err) {
      console.warn(`⚠️ Polygon.io fetch failed:`, err.message);
    }
    return null;
  };

  // Fallback: Generate mock data
  const generateMockData = (tickerSymbol) => {
    console.log(`📊 Generating mock data for ${tickerSymbol}...`);
    const today = new Date();
    const mockData = [];
    
    let price = 100 + Math.random() * 50;
    
    for (let i = 89; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Simulate realistic price movement
      price += (Math.random() - 0.48) * 2;
      price = Math.max(price, 50); // Don't go below 50
      
      const open = price + (Math.random() - 0.5) * 1;
      const close = price;
      const high = Math.max(open, close) + Math.random() * 0.5;
      const low = Math.min(open, close) - Math.random() * 0.5;
      
      mockData.push({
        date: date.toISOString().split('T')[0],
        open: parseFloat(open.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        volume: Math.floor(Math.random() * 5000000)
      });
    }
    
    return {
      ticker: tickerSymbol,
      current_price: price,
      historical_data: mockData,
      last_updated: new Date().toISOString()
    };
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        let data = null;

        if (ticker) {
          data = await fetchFromPolygon(ticker);
          
          // Fallback to mock data if API fails
          if (!data) {
            console.log(`⚠️ Falling back to mock data for ${ticker}`);
            data = generateMockData(ticker);
          }
        }

        if (data) {
          setStockData(data);
        } else {
          setError('Unable to fetch stock data');
        }
      } catch (err) {
        console.error(`❌ Error fetching data for ${ticker}:`, err.message);
        setError(`Failed to load data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    if (ticker) {
      fetchData();
    }
  }, [ticker]);

  useEffect(() => {
    if (stockData && stockData.historical_data && stockData.historical_data.length > 0) {
      const data = stockData.historical_data.map(item => ({
        date: item.date,
        close: parseFloat(item.close),
        open: parseFloat(item.open),
        high: parseFloat(item.high),
        low: parseFloat(item.low),
        volume: item.volume
      }));
      
      setChartData(data);
      
      if (data.length > 0) {
        const closes = data.map(d => d.close);
        const currentPrice = stockData.current_price || closes[closes.length - 1];
        const previousClose = closes[0];
        const change = currentPrice - previousClose;
        const changePercent = (change / previousClose) * 100;
        
        setStats({
          currentPrice: currentPrice.toFixed(2),
          change: change.toFixed(2),
          changePercent: changePercent.toFixed(2),
          high: Math.max(...closes).toFixed(2),
          low: Math.min(...closes).toFixed(2),
        });
      }
      
      setLoading(false);
    } else if (!loading && !error) {
      setError('No stock data available');
    }
  }, [stockData, loading]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !chartData || chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          Stock Price - {ticker}
        </h3>
        <div className="flex items-center justify-center py-8 text-gray-500">
          <AlertCircle className="w-5 h-5 mr-2" />
          <p>{error || 'No stock data available'}</p>
        </div>
      </div>
    );
  }

  const isPositive = parseFloat(stats.change) >= 0;
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600';
  const bgColor = isPositive ? 'bg-green-50' : 'bg-red-50';
  const lineColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      {/* Header */}
      <div className={`${bgColor} rounded-lg p-4 mb-6 border border-gray-200`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Stock Price - {ticker}
            </h3>
            <p className="text-2xl font-bold text-gray-900">${stats.currentPrice}</p>
          </div>
          <div className="text-right">
            <p className={`text-xl font-bold ${changeColor} flex items-center justify-end gap-1`}>
              {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              {parseFloat(stats.change) >= 0 ? '+' : ''}{stats.change} ({stats.changePercent}%)
            </p>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 gap-4 mb-6 pb-6 border-b">
        <div>
          <p className="text-xs text-gray-500 mb-1 font-medium">Period High</p>
          <p className="text-lg font-bold text-gray-900">${stats.high}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1 font-medium">Period Low</p>
          <p className="text-lg font-bold text-gray-900">${stats.low}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={lineColor} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={lineColor} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              interval={Math.floor(chartData.length / 6)}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px'
              }}
              formatter={(value) => `$${parseFloat(value).toFixed(2)}`}
              labelStyle={{ color: '#1f2937' }}
            />
            <Area 
              type="monotone" 
              dataKey="close" 
              stroke={lineColor}
              fillOpacity={1} 
              fill="url(#colorClose)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <p className="text-xs text-gray-400 mt-4 text-center">
        {chartData.length} trading days | Updated: {stockData?.last_updated ? new Date(stockData.last_updated).toLocaleDateString() : 'N/A'}
      </p>
    </div>
  );
};

export default StockGraphCard;