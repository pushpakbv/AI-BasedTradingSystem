// ...existing imports...
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, TrendingUp, TrendingDown, Calendar,
  DollarSign, Activity, RefreshCw, ExternalLink
} from 'lucide-react';
import axios from 'axios';
import StockChart from '../components/StockChart';
import NewsTimeline from '../components/NewsTimeline';
import PredictionCard from '../components/PredictionCard';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const StockDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchCompanyData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/company/${ticker}`);
      setCompanyData(response.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to fetch company data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanyData();
    // eslint-disable-next-line
  }, [ticker]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading company data...</p>
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
            onClick={fetchCompanyData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { prediction, sentiment, financial, stockData, company_name } = companyData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                {/* Show full company name and ticker */}
                <h1 className="text-2xl font-bold text-gray-900">{company_name || ticker}</h1>
                <p className="text-sm text-gray-500">{ticker}</p>
                <p className="text-xs text-gray-400">
                  Last updated: {lastUpdate?.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {stockData && (
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">
                    ${stockData.current_price.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500">Current Price</div>
                </div>
              )}
              <button
                onClick={fetchCompanyData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Prediction Summary */}
        {prediction && (
          <div className="mb-8">
            <PredictionCard prediction={prediction} />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Chart */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stock Price Chart */}
            {stockData && (
              <StockChart 
                stockData={stockData} 
                prediction={prediction}
              />
            )}

            {/* Financial News Timeline */}
            {financial && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-blue-600" />
                  Financial News
                </h3>
                <NewsTimeline articles={financial.articles} type="financial" />
              </div>
            )}
          </div>

          {/* Right Column - Sentiment & General News */}
          <div className="space-y-6">
            {/* Sentiment Summary */}
            {sentiment && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  General Sentiment
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Overall Sentiment</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      sentiment.company_sentiment.label === 'positive'
                        ? 'bg-green-100 text-green-700'
                        : sentiment.company_sentiment.label === 'negative'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {sentiment.company_sentiment.label.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Score</span>
                    <span className="text-lg font-bold">
                      {sentiment.company_sentiment.average_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Articles Analyzed</span>
                    <span className="font-semibold">
                      {sentiment.company_sentiment.article_count}
                    </span>
                  </div>
                  
                  {/* Distribution */}
                  <div className="pt-4 border-t">
                    <div className="text-sm font-medium text-gray-700 mb-2">Distribution</div>
                    <div className="space-y-2">
                      {Object.entries(sentiment.sentiment_distribution).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 capitalize">{key}</span>
                          <span className="font-semibold">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* General News Timeline */}
            {sentiment && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-purple-600" />
                  General News
                </h3>
                <NewsTimeline articles={sentiment.articles} type="general" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetail;