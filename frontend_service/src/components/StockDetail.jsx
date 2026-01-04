import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  AlertCircle,
  DollarSign,
  Newspaper,
  BarChart3,
  Clock,
} from 'lucide-react';
import PredictionCard from '../components/PredictionCard';
import StockGraphCard from '../components/StockGraphCard';
import StockChart from '../components/StockChart';
import NewsTimeline from '../components/NewsTimeline';
import SentimentAnalysis from '../components/SentimentAnalysis';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const StockDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchCompanyData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch company data from API
      const response = await axios.get(`${API_BASE_URL}/company/${ticker}`);
      setCompanyData(response.data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error fetching company data:', err);
      setError(err.response?.data?.message || 'Failed to load company data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (ticker) {
      fetchCompanyData();

      // Setup WebSocket connection for real-time updates
      try {
        wsRef.current = new WebSocket(`${WS_BASE_URL}/ws`);
        
        wsRef.current.onopen = () => {
          console.log(`📡 WebSocket connected for ${ticker}`);
          // Subscribe to ticker updates
          wsRef.current.send(JSON.stringify({ action: 'subscribe', ticker }));
        };

        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.ticker === ticker && data.prediction) {
            setCompanyData(prev => ({
              ...prev,
              prediction: data.prediction
            }));
            setLastUpdate(new Date().toLocaleTimeString());
          }
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
        };
      } catch (err) {
        console.warn('WebSocket connection failed:', err);
      }
    }

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [ticker]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading company data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </button>
          </div>
        </header>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900">Error Loading Company Data</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { prediction, sentiment, financial, stockData, company_name, general_articles = [], financial_articles = [] } = companyData || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Dashboard
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{company_name || ticker}</h1>
                <p className="text-sm text-gray-500">{ticker}</p>
              </div>
            </div>
            <div className="text-right">
              {lastUpdate && (
                <p className="text-xs text-gray-500 flex items-center gap-1 justify-end">
                  <Clock className="w-3 h-3" />
                  Last updated: {lastUpdate}
                </p>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Prediction Card */}
        {prediction && (
          <div className="mb-8">
            <PredictionCard prediction={prediction} />
          </div>
        )}

        {/* Stock Graph Card - NEW */}
        {stockData && stockData.historical_data && stockData.historical_data.length > 0 && (
          <div className="mb-8">
            <StockGraphCard ticker={ticker} stockData={stockData} />
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Stock Chart and Financial News */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stock Chart */}
            {stockData && (
              <div>
                <StockChart ticker={ticker} stockData={stockData} />
              </div>
            )}

            {/* Financial News */}
            {financial && financial.articles && financial.articles.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-blue-600" />
                  Financial News
                </h3>
                <NewsTimeline articles={financial.articles} type="financial" />
              </div>
            )}

            {/* General News */}
            {general_articles && general_articles.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Newspaper className="w-5 h-5 text-blue-600" />
                  General News
                </h3>
                <NewsTimeline articles={general_articles} type="general" />
              </div>
            )}
          </div>

          {/* Right Column - Sentiment and Key Metrics */}
          <div className="space-y-6">
            {/* Sentiment Analysis */}
            {sentiment && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  Sentiment Analysis
                </h3>
                <SentimentAnalysis sentiment={sentiment} />
              </div>
            )}

            {/* Stock Info */}
            {stockData && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Stock Info</h3>
                <div className="space-y-3">
                  {stockData.current_price && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Current Price</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ${parseFloat(stockData.current_price).toFixed(2)}
                      </span>
                    </div>
                  )}
                  {stockData.day_high && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Day High</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ${parseFloat(stockData.day_high).toFixed(2)}
                      </span>
                    </div>
                  )}
                  {stockData.day_low && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Day Low</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ${parseFloat(stockData.day_low).toFixed(2)}
                      </span>
                    </div>
                  )}
                  {stockData.volume && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Volume</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {(stockData.volume / 1000000).toFixed(2)}M
                      </span>
                    </div>
                  )}
                  {stockData.avg_volume && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Avg Volume</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {(stockData.avg_volume / 1000000).toFixed(2)}M
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetail;