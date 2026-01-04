import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const PredictionCard = ({ prediction }) => {
  // Log the incoming prediction for debugging
  React.useEffect(() => {
    console.log('PredictionCard received:', prediction);
    if (prediction) {
      console.log('Prediction structure:', {
        has_prediction: !!prediction.prediction,
        has_final_signal: !!prediction.prediction?.final_signal,
        ticker: prediction.ticker,
        company_name: prediction.company_name,
        keys: Object.keys(prediction)
      });
    }
  }, [prediction]);

  // Handle case where prediction data is missing
  if (!prediction) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <p className="text-gray-500 text-center">No prediction data available</p>
      </div>
    );
  }

  // Extract nested prediction object - check both structures
  const pred = prediction.prediction || prediction;
  const ticker = prediction.ticker || 'N/A';
  const company_name = prediction.company_name || ticker;

  // Log extracted data
  console.log('Extracted pred:', {
    pred_keys: Object.keys(pred),
    final_signal: pred?.final_signal,
    direction: pred?.direction,
    confidence_level: pred?.confidence_level,
    combined_score: pred?.combined_score
  });

  // Validate we have the required signal data
  if (!pred || typeof pred !== 'object' || !pred.final_signal) {
    console.warn('❌ Invalid prediction structure:', {
      pred_exists: !!pred,
      is_object: typeof pred === 'object',
      has_final_signal: !!pred?.final_signal,
      full_prediction: prediction
    });
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <p className="text-gray-500 text-center">Invalid prediction data</p>
        <p className="text-xs text-gray-400 mt-2">Check console for details</p>
      </div>
    );
  }

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

  const confidenceColor = {
    'HIGH': 'text-green-600 bg-green-100 border-green-200',
    'MEDIUM': 'text-yellow-600 bg-yellow-100 border-yellow-200',
    'LOW': 'text-red-600 bg-red-100 border-red-200'
  }[pred.confidence_level] || 'text-gray-600 bg-gray-100';

  return (
    <div className={`${config.bg} border-2 ${config.border} rounded-lg p-6`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-lg font-bold text-gray-900">
            {company_name}
          </span>
          <span className="ml-2 text-xs text-gray-500">{ticker}</span>
        </div>
        <div className={`${config.text} p-2 bg-white rounded-lg shadow-sm`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      
      <h2 className={`text-2xl font-bold mb-4 ${config.text}`}>{config.label}</h2>
      
      <div className="space-y-3 bg-white bg-opacity-50 rounded p-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-700">Direction:</span>
          <span className={`font-semibold ${config.text}`}>{pred.direction || 'N/A'}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-700">Confidence:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${confidenceColor}`}>
            {pred.confidence_level || 'N/A'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-700">Score:</span>
          <span className="font-semibold text-lg">{(pred.combined_score * 100).toFixed(1)}</span>
        </div>
        
        {pred.reasoning && (
          <div className="pt-3 border-t border-gray-300">
            <span className="text-xs font-semibold text-gray-600 block mb-2">Reasoning:</span>
            <span className="text-sm text-gray-700">{pred.reasoning}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionCard;