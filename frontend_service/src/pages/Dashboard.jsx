import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePredictions } from '../hooks/usePrediction';
import PredictionCard from '../components/PredictionCard';
import PerformanceChart from '../components/PerformanceChart';
import CompanySelector from '../components/CompanySelector';

const Dashboard = () => {
  const { predictions, loading, error, lastUpdate, refresh } = usePredictions();
  const navigate = useNavigate();

  // Always use the predictions array from the API response
  const predictionList = Array.isArray(predictions) ? predictions : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading predictions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={refresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!predictionList || predictionList.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-600">No predictions available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">AI Trading Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdate?.toLocaleString()}
            </span>
            <button
              onClick={refresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <PerformanceChart predictions={predictionList} />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-8">
          {predictionList.map((stock) => (
            <div
              key={stock.ticker}
              className="cursor-pointer"
              onClick={() => navigate(`/stock/${stock.ticker}`)}
            >
              <PredictionCard prediction={stock} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;