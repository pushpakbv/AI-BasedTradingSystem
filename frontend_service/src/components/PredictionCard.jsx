import React, { useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const PredictionCard = ({ prediction }) => {
  useEffect(() => {
    console.log('PredictionCard received:', prediction);
  }, [prediction]);

  if (!prediction) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <p className="text-gray-500 text-center">No prediction data available</p>
      </div>
    );
  }

  // Extract prediction - handle both nested and flat structures
  const pred = prediction.prediction || prediction;
  const ticker = prediction.ticker || 'N/A';
  const company_name = prediction.company_name || ticker;
  
  // Ensure we have all required fields
  const final_signal = pred?.final_signal || 'HOLD';
  const direction = pred?.direction || 'NEUTRAL';
  const combined_score = pred?.combined_score || 0;
  const confidence_level = pred?.confidence_level || 'LOW';
  const reasoning = pred?.reasoning || 'Insufficient data';
  const average_sentiment = prediction.average_sentiment || 0;
  const total_articles = prediction.total_articles || 0;

  // Signal configuration
  const signalConfig = {
    'STRONG_BUY': { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700', icon: TrendingUp },
    'BUY': { bg: 'bg-green-50', border: 'border-green-400', text: 'text-green-600', icon: TrendingUp },
    'HOLD': { bg: 'bg-gray-50', border: 'border-gray-400', text: 'text-gray-600', icon: Minus },
    'SELL': { bg: 'bg-red-50', border: 'border-red-400', text: 'text-red-600', icon: TrendingDown },
    'STRONG_SELL': { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700', icon: TrendingDown },
  };

  const config = signalConfig[final_signal] || signalConfig['HOLD'];
  const Icon = config.icon;

  const confidenceColors = {
    'HIGH': 'bg-green-100 text-green-700',
    'MEDIUM': 'bg-yellow-100 text-yellow-700',
    'LOW': 'bg-gray-100 text-gray-700'
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-2 ${config.border} overflow-hidden transition-all hover:shadow-lg`}>
      {/* Header */}
      <div className={`${config.bg} p-4 flex items-center justify-between border-b ${config.border}`}>
        <div className="flex items-center gap-3">
          <div className={`${config.text} p-2 bg-white rounded-lg shadow-sm`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">{company_name}</h3>
            <span className="text-xs text-gray-500">{ticker}</span>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${config.text}`}>
            {(combined_score * 100).toFixed(0)}%
          </div>
          <span className="text-xs text-gray-600">Signal Strength</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Confidence & Direction */}
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1">
            <div className="text-xs text-gray-500 mb-1 font-medium">Confidence</div>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${confidenceColors[confidence_level] || confidenceColors['LOW']}`}>
              {confidence_level}
            </span>
          </div>
          <div className="flex-1">
            <div className="text-xs text-gray-500 mb-1 font-medium">Direction</div>
            <span className={`font-semibold text-sm ${config.text}`}>
              {direction}
            </span>
          </div>
        </div>

        {/* Reasoning */}
        <div className="mb-4">
          <div className="text-xs text-gray-500 mb-1 font-medium">Analysis</div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {reasoning}
          </p>
        </div>

        {/* Data Sources */}
        <div className="flex items-center gap-4 text-xs text-gray-500 pb-3 border-b">
          <div className="flex items-center gap-1">
            <span>📊 {total_articles} articles</span>
          </div>
          <div className="flex items-center gap-1">
            <span>😊 {(average_sentiment * 100).toFixed(1)}% sentiment</span>
          </div>
        </div>

        {/* Signal Badge */}
        <div className="mt-4 text-center">
          <span className={`inline-block px-4 py-2 rounded-full font-bold text-sm ${config.bg} ${config.text}`}>
            {final_signal}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;