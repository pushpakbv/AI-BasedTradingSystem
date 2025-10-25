import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Minus, 
  DollarSign, Activity, Calendar,
  ArrowUpCircle, ArrowDownCircle, AlertCircle
} from 'lucide-react';
import { usePredictions } from '../hooks/usePredictions';
import StockCard from '../components/StockCard';
import SignalDistribution from '../components/SignalDistribution';
import NewsTimeline from '../components/NewsTimeline';
import PerformanceChart from '../components/PerformanceChart';

const Dashboard = () => {
  const { predictions, loading, error, refresh } = usePredictions();
  const [filter, setFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('score');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600 text-center">
          <AlertCircle className="w-16 h-16 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Data</h2>
          <p>{error}</p>
          <button 
            onClick={refresh}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = predictions?.summary || {};
  const stocks = predictions?.predictions || [];

  // Filter stocks
  const filteredStocks = stocks.filter(stock => {
    if (filter === 'ALL') return true;
    return stock.prediction.final_signal === filter;
  });

  // Sort stocks
  const sortedStocks = [...filteredStocks].sort((a, b) => {
    if (sortBy === 'score') {
      return Math.abs(b.prediction.combined_score) - Math.abs(a.prediction.combined_score);
    } else if (sortBy === 'ticker') {
      return a.ticker.localeCompare(b.ticker);
    }
    return 0;
  });

  const signalColors = {
    'STRONG_BUY': 'text-green-600 bg-green-50 border-green-200',
    'BUY': 'text-green-500 bg-green-50 border-green-200',
    'HOLD': 'text-gray-600 bg-gray-50 border-gray-200',
    'SELL': 'text-red-500 bg-red-50 border-red-200',
    'STRONG_SELL': 'text-red-600 bg-red-50 border-red-200'
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">TradeSystem Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-Powered Stock Trading Signals • Updated: {new Date(summary.date).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={refresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
            >
              <Activity className="w-4 h-4" />
              Refresh Data
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="Total Companies"
            value={summary.total_companies || 0}
            icon={DollarSign}
            color="blue"
          />
          <StatCard
            title="Strong Buy"
            value={summary.signal_distribution?.STRONG_BUY || 0}
            icon={ArrowUpCircle}
            color="green"
          />
          <StatCard
            title="Buy"
            value={summary.signal_distribution?.BUY || 0}
            icon={TrendingUp}
            color="green"
          />
          <StatCard
            title="Sell"
            value={(summary.signal_distribution?.SELL || 0) + (summary.signal_distribution?.STRONG_SELL || 0)}
            icon={ArrowDownCircle}
            color="red"
          />
          <StatCard
            title="Hold"
            value={summary.signal_distribution?.HOLD || 0}
            icon={Minus}
            color="gray"
          />
        </div>

        {/* Signal Distribution Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <SignalDistribution data={summary.signal_distribution} />
          </div>
          <div className="lg:col-span-1">
            <PerformanceChart predictions={stocks} />
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div>
              <label className="text-sm font-medium text-gray-700 mr-2">Filter:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ALL">All Signals</option>
                <option value="STRONG_BUY">Strong Buy</option>
                <option value="BUY">Buy</option>
                <option value="HOLD">Hold</option>
                <option value="SELL">Sell</option>
                <option value="STRONG_SELL">Strong Sell</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mr-2">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="score">Signal Strength</option>
                <option value="ticker">Ticker (A-Z)</option>
              </select>
            </div>
            <div className="ml-auto text-sm text-gray-500">
              Showing {sortedStocks.length} of {stocks.length} stocks
            </div>
          </div>
        </div>

        {/* Stock Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedStocks.map((stock) => (
            <StockCard key={stock.ticker} stock={stock} />
          ))}
        </div>

        {sortedStocks.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No stocks match your filter criteria</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    gray: 'bg-gray-50 text-gray-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;