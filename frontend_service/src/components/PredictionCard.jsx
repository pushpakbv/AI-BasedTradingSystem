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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`${config.text} p-4 bg-white rounded-lg shadow-sm`}>
            <Icon className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{config.label}</h2>
            <p className="text-gray-600 mt-1">AI Trading Signal</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className={`text-4xl font-bold ${config.text}`}>
            {pred.combined_score > 0 ? '+' : ''}
            {(pred.combined_score * 100).toFixed(1)}%
          </div>
          <p className="text-sm text-gray-600 mt-1">Signal Strength</p>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-300">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Direction</p>
            <p className={`text-lg font-bold ${config.text}`}>{pred.direction}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Confidence</p>
            <p className="text-lg font-bold text-gray-900">{pred.confidence_level}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Date</p>
            <p className="text-lg font-bold text-gray-900">{prediction.date}</p>
          </div>
        </div>
      </div>

      <div className="mt-4 p-4 bg-white rounded-lg">
        <p className="text-sm text-gray-700 leading-relaxed">
          <span className="font-semibold">Analysis: </span>
          {pred.reasoning}
        </p>
      </div>
    </div>
  );
};

export default PredictionCard;