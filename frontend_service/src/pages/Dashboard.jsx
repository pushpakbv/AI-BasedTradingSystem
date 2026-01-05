import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { usePredictionsStore } from "../context/PredictionsContext";
import PredictionCard from '../components/PredictionCard';
import PerformanceChart from '../components/PerformanceChart';

const Dashboard = () => {
  const { predictions, loading, error, lastUpdate, refreshNow, connected } = usePredictionsStore();
  const refresh = refreshNow;

  const navigate = useNavigate();

  const predictionList = useMemo(
    () => (Array.isArray(predictions) ? predictions : []),
    [predictions]
  );

  const lastUpdateTime = lastUpdate ? new Date(lastUpdate) : null;

  useEffect(() => {
    console.log('📊 Dashboard re-rendered');
    console.log('   - Predictions count:', predictionList.length);
    console.log('   - Loading:', loading);
    console.log('   - Connected:', connected);
    console.log('   - Last update:', lastUpdateTime ? lastUpdateTime.toISOString() : null);
  }, [predictionList, loading, connected, lastUpdate]);


  if (loading && predictionList.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading predictions...</p>
        </div>
      </div>
    );
  }

  if (error && predictionList.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 inline-block">
            <p className="text-red-600 mb-4 text-lg">⚠️ {error}</p>
            <button
              onClick={refreshNow}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (predictionList.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg mb-4">No predictions available yet.</p>
          <button
            onClick={refreshNow}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  const getSignal = (p) => {
    const nested = p?.prediction && typeof p.prediction === 'object' ? p.prediction : null;
    return (nested?.final_signal ?? p?.final_signal ?? 'HOLD');
  };

  const buySignals = predictionList.filter(p => {
    const s = getSignal(p);
    return s === 'BUY' || s === 'STRONG_BUY';
  }).length;

  const sellSignals = predictionList.filter(p => {
    const s = getSignal(p);
    return s === 'SELL' || s === 'STRONG_SELL';
  }).length;

  const holdSignals = predictionList.filter(p => getSignal(p) === 'HOLD').length;

  const avgSentiment = predictionList.length > 0
    ? (predictionList.reduce((sum, p) => sum + (parseFloat(p.average_sentiment) || 0), 0) / predictionList.length)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Trading Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">Real-time market predictions and analysis</p>
            </div>

            <div className="flex items-center gap-6">
              {/* Status */}
              <div className="text-right">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm font-medium text-gray-700">
                    {connected ? 'Live' : 'Offline'}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  {lastUpdateTime ? `Updated ${lastUpdateTime.toLocaleTimeString()}` : 'Never updated'}
                </p>
              </div>

              {/* Refresh Button */}
              <button
                onClick={refreshNow}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner (if any) */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700 flex items-center gap-3">
            <Activity className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-gray-600 text-sm font-medium">Total Predictions</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{predictionList.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-green-200 p-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <p className="text-gray-600 text-sm font-medium">Buy Signals</p>
            </div>
            <p className="text-3xl font-bold text-green-600 mt-2">{buySignals}</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-red-600" />
              <p className="text-gray-600 text-sm font-medium">Sell Signals</p>
            </div>
            <p className="text-3xl font-bold text-red-600 mt-2">{sellSignals}</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-gray-600 text-sm font-medium">Hold Signals</p>
            <p className="text-3xl font-bold text-gray-600 mt-2">{holdSignals}</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-blue-200 p-6">
            <p className="text-gray-600 text-sm font-medium">Avg Sentiment</p>
            <p className={`text-3xl font-bold mt-2 ${
              avgSentiment > 0 ? 'text-green-600' : avgSentiment < 0 ? 'text-red-600' : 'text-gray-600'
            }`}>
              {(avgSentiment * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Performance Chart */}
        {predictionList.length > 0 && (
          <div className="mb-8">
            <PerformanceChart predictions={predictionList} />
          </div>
        )}

        {/* Predictions Grid */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Stock Predictions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {predictionList.map((stock) => (
              <div
                key={stock.ticker}
                className="cursor-pointer transform transition-transform hover:scale-105"
                onClick={() => navigate(`/stock/${stock.ticker}`)}
              >
                <PredictionCard prediction={stock} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
