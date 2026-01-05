import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Activity, RefreshCw, AlertCircle, BarChart3,
  FileText, Newspaper, TrendingUpIcon
} from 'lucide-react';
import axios from 'axios';
import PredictionCard from '../components/PredictionCard';
import StockGraphCard from '../components/StockGraphCard';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const StockDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [newsData, setNewsData] = useState({ general: [], financial: [] });

  const fetchCompanyData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`📡 Fetching company data for ${ticker}...`);
      const response = await axios.get(`${API_BASE_URL}/prediction/${ticker}`, {
        timeout: 5000
      });
      
      console.log('✅ Company data received:', response.data);
      
      setCompanyData(response.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching company data:', err);
      const errorMsg = err.response?.data?.message || err.message || 'Failed to fetch company data. Please try again.';
      setError(errorMsg);
      setLoading(false);
    }
  };

  // Fetch news articles from backend
// Replace the fetchNewsArticles function with:

  const fetchNewsArticles = async () => {
    try {
      console.log(`📰 Fetching real news articles for ${ticker}...`);
      
      try {
        const response = await axios.get(`${API_BASE_URL}/news/${ticker}`, {
          timeout: 5000
        });

        console.log('✅ News articles received:', response.data);

        setNewsData({
          general: response.data.general || [],
          financial: response.data.financial || []
        });
      } catch (apiErr) {
        console.warn('⚠️ News endpoint error, trying articles endpoint...');
        
        try {
          const response = await axios.get(`${API_BASE_URL}/articles/${ticker}`, {
            timeout: 5000
          });
          
          setNewsData({
            general: response.data.articles || [],
            financial: response.data.articles || []
          });
        } catch (e) {
          console.warn('⚠️ No articles available');
          setNewsData({
            general: [],
            financial: []
          });
        }
      }
    } catch (err) {
      console.error('Error fetching news articles:', err);
      setNewsData({
        general: [],
        financial: []
      });
    }
  };
  // Generate mock news for demonstration
  const generateMockNews = (type, count) => {
    const mockTitles = {
      general: [
        `${ticker} announces new product line`,
        `${ticker} expands into new market`,
        `${ticker} reports strong quarterly earnings`,
        `${ticker} partners with major technology firm`,
        `${ticker} wins industry award for innovation`
      ],
      financial: [
        `${ticker} stock price surges on strong guidance`,
        `${ticker} beats analyst expectations`,
        `${ticker} announces share buyback program`,
        `${ticker} raises dividend by 15%`,
        `${ticker} credit rating upgraded by S&P`
      ]
    };

    const titles = mockTitles[type] || mockTitles.general;
    
    return Array.from({ length: count }, (_, i) => ({
      id: `mock-${type}-${i}`,
      title: titles[i % titles.length],
      content: `Important news about ${ticker}. This is a placeholder article showing what real news would look like in this section.`,
      published_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
      source: 'News Source',
      article_type: type
    }));
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected');
      return;
    }

    console.log(`🔌 Connecting WebSocket for ${ticker}...`);
    
    try {
      const ws = new WebSocket(WS_BASE_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`✅ WebSocket connected for ${ticker}`);
        setWsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 WebSocket message:', message.type, message);
          
          if (message.type === 'prediction_updated' && message.ticker === ticker) {
            console.log(`🔄 Prediction updated for ${ticker}:`, message.prediction);
            setCompanyData(prev => {
              if (!prev) return prev;
              
              // Deep merge to ensure all fields are updated
              const updatedData = {
                ...prev,
                prediction: {
                  ...prev.prediction,
                  ...message.prediction
                },
                timestamp: message.timestamp
              };
              
              console.log('✅ Updated company data:', updatedData);
              return updatedData;
            });
            setLastUpdate(new Date());
          } 
          else if (message.type === 'predictions_refresh') {
            const updatedPred = message.predictions.find(p => p.ticker === ticker);
            if (updatedPred) {
              console.log(`🔄 ${ticker} found in batch refresh:`, updatedPred);
              setCompanyData(updatedPred);
              setLastUpdate(new Date());
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setWsConnected(false);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect WebSocket...');
          connectWebSocket();
        }, 5000);
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setWsConnected(false);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    }
  };

  useEffect(() => {
    if (ticker) {
      console.log(`🔄 Component mounted/updated for ticker: ${ticker}`);
      fetchCompanyData();
      fetchNewsArticles();
      connectWebSocket();
    }

    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [ticker]);

  if (loading && !companyData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading company data...</p>
        </div>
      </div>
    );
  }

  if (error && !companyData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium transition-colors"
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
              <button
                onClick={fetchCompanyData}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!companyData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </button>
          </div>
        </header>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No data available for this stock.</p>
        </div>
      </div>
    );
  }

  const { prediction, company_name, average_sentiment, total_articles } = companyData || {};

  console.log('🎯 Current prediction state:', prediction);

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
                <h1 className="text-2xl font-bold text-gray-900">{company_name || ticker}</h1>
                <p className="text-sm text-gray-500">{ticker}</p>
                <div className="flex items-center gap-3 mt-2">
                  <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <p className="text-xs text-gray-400">
                    {wsConnected ? '🟢 Live Updates' : '🔴 Offline'} • {lastUpdate?.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchCompanyData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Prediction Card */}
        {prediction && (
          <div className="mb-8">
            <PredictionCard prediction={companyData} />
          </div>
        )}

        {/* Stock Chart */}
        <div className="mb-8">
          <StockGraphCard ticker={ticker} stockData={companyData} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - News Articles */}
          <div className="lg:col-span-2 space-y-6">
            {/* General News Block */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200 px-6 py-4">
                <h3 className="text-lg font-semibold text-blue-900 flex items-center gap-2">
                  <Newspaper className="w-5 h-5 text-blue-600" />
                  General News
                </h3>
                <p className="text-sm text-blue-700 mt-1">
                  {newsData.general.length} articles collected
                </p>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {newsData.general.length > 0 ? (
                  newsData.general.map((article, idx) => (
                    <div key={idx} className="p-4 hover:bg-blue-50 transition-colors cursor-pointer">
                      <div className="flex gap-3">
                        <Newspaper className="w-4 h-4 text-blue-600 flex-shrink-0 mt-1" />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 text-sm line-clamp-2">
                            {article.title || 'Untitled'}
                          </h4>
                          <p className="text-xs text-gray-500 mt-1">
                            {article.published_at 
                              ? new Date(article.published_at).toLocaleDateString()
                              : new Date().toLocaleDateString()
                            }
                          </p>
                          <p className="text-xs text-gray-600 line-clamp-2 mt-2">
                            {article.content?.substring(0, 120) || 'No preview available'}...
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-gray-500">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No general news articles</p>
                  </div>
                )}
              </div>
            </div>

            {/* Financial News Block */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-green-50 to-green-100 border-b border-green-200 px-6 py-4">
                <h3 className="text-lg font-semibold text-green-900 flex items-center gap-2">
                  <TrendingUpIcon className="w-5 h-5 text-green-600" />
                  Financial News
                </h3>
                <p className="text-sm text-green-700 mt-1">
                  {newsData.financial.length} articles collected
                </p>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {newsData.financial.length > 0 ? (
                  newsData.financial.map((article, idx) => (
                    <div key={idx} className="p-4 hover:bg-green-50 transition-colors cursor-pointer">
                      <div className="flex gap-3">
                        <TrendingUpIcon className="w-4 h-4 text-green-600 flex-shrink-0 mt-1" />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 text-sm line-clamp-2">
                            {article.title || 'Untitled'}
                          </h4>
                          <p className="text-xs text-gray-500 mt-1">
                            {article.published_at 
                              ? new Date(article.published_at).toLocaleDateString()
                              : new Date().toLocaleDateString()
                            }
                          </p>
                          <p className="text-xs text-gray-600 line-clamp-2 mt-2">
                            {article.content?.substring(0, 120) || 'No preview available'}...
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-gray-500">
                    <TrendingUpIcon className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No financial news articles</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Signals & Analysis */}
          <div className="space-y-6">
            {/* Trading Signal */}
            {prediction && (
              <div className={`rounded-lg shadow-sm p-6 border-2 transition-all ${
                prediction.final_signal && String(prediction.final_signal).toUpperCase().includes('BUY')
                  ? 'bg-green-50 border-green-300'
                  : prediction.final_signal && String(prediction.final_signal).toUpperCase().includes('SELL')
                  ? 'bg-red-50 border-red-300'
                  : 'bg-gray-50 border-gray-300'
              }`}>
                <p className="text-xs font-semibold mb-2 text-gray-600">TRADING SIGNAL</p>
                <p className={`text-4xl font-bold mb-3 ${
                  prediction.final_signal && String(prediction.final_signal).toUpperCase().includes('BUY')
                    ? 'text-green-700'
                    : prediction.final_signal && String(prediction.final_signal).toUpperCase().includes('SELL')
                    ? 'text-red-700'
                    : 'text-gray-700'
                }`}>
                  {prediction.final_signal || 'HOLD'}
                </p>
                <p className="text-sm font-semibold mb-4">
                  {prediction.direction === 'BULLISH' ? '📈 Bullish' : prediction.direction === 'BEARISH' ? '📉 Bearish' : '➡️ Neutral'}
                </p>
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-opacity-20 border-gray-400">
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">CONFIDENCE</p>
                    <p className="text-lg font-bold text-gray-900 mt-1">{prediction.confidence_level || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">SENTIMENT</p>
                    <p className={`text-lg font-bold mt-1 ${
                      (average_sentiment || 0) > 0 ? 'text-green-600' :
                      (average_sentiment || 0) < 0 ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {((average_sentiment || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Analysis */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                Analysis
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-600 font-semibold mb-1">REASONING</p>
                  <p className="text-sm text-gray-700">
                    {prediction?.reasoning || 'Analysis based on sentiment and market signals'}
                  </p>
                </div>
                <div className="border-t border-gray-200 pt-3">
                  <p className="text-xs text-gray-600 font-semibold mb-2">KEY METRICS</p>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Combined Score</span>
                      <span className="font-semibold text-gray-900">
                        {prediction?.combined_score ? (prediction.combined_score * 100).toFixed(1) : 'N/A'}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Confidence</span>
                      <span className="font-semibold text-gray-900">
                        {prediction?.confidence ? (prediction.confidence * 100).toFixed(1) : 'N/A'}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Articles</span>
                      <span className="font-semibold text-gray-900">{total_articles || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Connection Status */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-xs text-blue-600 font-semibold">CONNECTION STATUS</p>
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-700">WebSocket</span>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    wsConnected
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {wsConnected ? '🟢 Live' : '🔴 Offline'}
                  </span>
                </div>
                <p className="text-xs text-blue-600">
                  Updated: {lastUpdate?.toLocaleTimeString() || 'Never'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetail;