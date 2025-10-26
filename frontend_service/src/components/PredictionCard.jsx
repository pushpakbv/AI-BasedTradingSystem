import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Activity } from 'lucide-react';

const PredictionCard = ({ prediction }) => {
  if (!prediction || !prediction.prediction) {
    return null;
  }

  const pred = prediction.prediction;

  const signalConfig = {
    'STRONG_BUY': {
      bg: 'bg-green-100',
      border: 'border-green-500',
      text: 'text-green-700',
      icon: TrendingUp,
      label: 'Strong Buy'
    },
    'BUY': {
      bg: 'bg-green-50',
      border: 'border-green-400',
      text: 'text-green-600',
      icon: TrendingUp,
      label: 'Buy'
    },
    'HOLD': {
      bg: 'bg-gray-50',
      border: 'border-gray-400',
      text: 'text-gray-600',
      icon: Minus,
      label: 'Hold'
    },
    'SELL': {
      bg: 'bg-red-50',
      border: 'border-red-400',
      text: 'text-red-600',
      icon: TrendingDown,
      label: 'Sell'
    },
    'STRONG_SELL': {
      bg: 'bg-red-100',
      border: 'border-red-500',
      text: 'text-red-700',
      icon: TrendingDown,
      label: 'Strong Sell'
    }
  };

  const config = signalConfig[pred.final_signal] || signalConfig['HOLD'];
  const Icon = config.icon;

  return (
    <div className={`${config.bg} border-2 ${config.border} rounded-lg p-6`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          {/* Show full company name and ticker */}
          <span className="text-lg font-bold text-gray-900">
            {prediction.company_name || prediction.ticker}
          </span>
          <span className="ml-2 text-xs text-gray-500">{prediction.ticker}</span>
        </div>
        <div className={`${config.text} p-2 bg-white rounded-lg shadow-sm`}>
          <Icon className="w-8 h-8" />
        </div>
      </div>
      <h2 className={`text-2xl font-bold mb-2 ${config.text}`}>{config.label}</h2>
      <div className="mb-2">
        <span className="text-xs text-gray-500 mr-2">Direction:</span>
        <span className={`font-semibold ${config.text}`}>{pred.direction}</span>
      </div>
      <div className="mb-2">
        <span className="text-xs text-gray-500 mr-2">Confidence:</span>
        <span className="font-semibold">{pred.confidence_level}</span>
      </div>
      <div className="mb-2">
        <span className="text-xs text-gray-500 mr-2">Score:</span>
        <span className="font-semibold">{(pred.combined_score * 100).toFixed(1)}</span>
      </div>
      <div className="mb-2">
        <span className="text-xs text-gray-500 mr-2">Reasoning:</span>
        <span className="text-sm text-gray-700">{pred.reasoning}</span>
      </div>
    </div>
  );
};

export default PredictionCard;