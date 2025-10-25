import React, { useState } from 'react';
import { 
  TrendingUp, TrendingDown, Minus, 
  ChevronDown, ChevronUp, ExternalLink,
  Info, DollarSign, Activity
} from 'lucide-react';

const StockCard = ({ stock }) => {
  const [expanded, setExpanded] = useState(false);
  const { ticker, prediction, data_sources } = stock;

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

  const config = signalConfig[prediction.final_signal] || signalConfig['HOLD'];
  const Icon = config.icon;

  const confidenceColor = {
    'HIGH': 'text-green-600 bg-green-100 border-green-200',
    'MEDIUM': 'text-yellow-600 bg-yellow-100 border-yellow-200',
    'LOW': 'text-red-600 bg-red-100 border-red-200'
  }[prediction.confidence_level] || 'text-gray-600 bg-gray-100';

  return (
    <div className={`bg-white rounded-lg shadow-sm border-2 ${config.border} overflow-hidden transition-all hover:shadow-lg`}>
      {/* Header */}
      <div className={`${config.bg} p-4 flex items-center justify-between border-b ${config.border}`}>
        <div className="flex items-center gap-3">
          <div className={`${config.text} p-2 bg-white rounded-lg shadow-sm`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{ticker}</h3>
            <span className={`text-sm font-semibold ${config.text}`}>
              {config.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${config.text}`}>
            {prediction.combined_score > 0 ? '+' : ''}
            {(prediction.combined_score * 100).toFixed(1)}
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
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${confidenceColor}`}>
              {prediction.confidence_level}
            </span>
          </div>
          <div className="flex-1">
            <div className="text-xs text-gray-500 mb-1 font-medium">Direction</div>
            <span className={`font-semibold text-sm ${config.text}`}>
              {prediction.direction}
            </span>
          </div>
        </div>

        {/* Reasoning */}
        <div className="mb-4">
          <div className="text-xs text-gray-500 mb-1 font-medium">Analysis</div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {prediction.reasoning}
          </p>
        </div>

        {/* Data Sources */}
        <div className="flex items-center gap-4 text-xs text-gray-500 pb-3 border-b">
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            <span>{data_sources.general_articles} general</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            <span>{data_sources.financial_articles} financial</span>
          </div>
        </div>

        {/* Expand/Collapse */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 flex items-center justify-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Hide Details
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Show Details
            </>
          )}
        </button>

        {/* Expanded Details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t space-y-3 animate-fadeIn">
            {/* Component Breakdown */}
            <div>
              <div className="text-xs font-semibold text-gray-700 mb-2">Signal Components</div>
              <div className="space-y-2">
                <ComponentBar
                  label="General Sentiment"
                  value={prediction.components.general_sentiment.score}
                  contribution={prediction.components.general_sentiment.contribution}
                  weight={prediction.components.general_sentiment.weight}
                />
                <ComponentBar
                  label="Financial Signal"
                  value={prediction.components.financial_signal.score}
                  contribution={prediction.components.financial_signal.contribution}
                  weight={prediction.components.financial_signal.weight}
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium flex items-center justify-center gap-2 transition-colors">
                <ExternalLink className="w-4 h-4" />
                View News
              </button>
              <button className="flex-1 px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium flex items-center justify-center gap-2 transition-colors">
                <Info className="w-4 h-4" />
                Full Report
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Component Bar
const ComponentBar = ({ label, value, contribution, weight }) => {
  const percentage = Math.abs(contribution) * 100;
  const isPositive = contribution > 0;
  
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label} ({(weight * 100).toFixed(0)}% weight)</span>
        <span className={`font-semibold ${isPositive ? 'text-green-600' : contribution < 0 ? 'text-red-600' : 'text-gray-600'}`}>
          {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all ${isPositive ? 'bg-green-500' : contribution < 0 ? 'bg-red-500' : 'bg-gray-400'}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};

export default StockCard;