import React from 'react';
import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { format, parseISO } from 'date-fns';

const NewsTimeline = ({ articles, type }) => {
  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No {type} articles available</p>
      </div>
    );
  }

  const getSentimentIcon = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'negative':
        return 'bg-red-50 border-red-200 text-red-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
      {articles.slice(0, 10).map((article, index) => (
        <div
          key={index}
          className="border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-50 transition-colors"
        >
          {/* Article Header */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <h4 className="font-semibold text-sm text-gray-900 line-clamp-2">
              {article.title}
            </h4>
            {article.sentiment && (
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getSentimentColor(article.sentiment)}`}>
                {getSentimentIcon(article.sentiment)}
                <span>{article.sentiment}</span>
              </div>
            )}
          </div>

          {/* Article Summary */}
          {article.summary && (
            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
              {article.summary}
            </p>
          )}

          {/* Article Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-3">
              {article.published_date && (
                <span>
                  {format(parseISO(article.published_date), 'MMM dd, yyyy')}
                </span>
              )}
              {article.source && (
                <>
                  <span>•</span>
                  <span>{article.source}</span>
                </>
              )}
            </div>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
              >
                Read
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default NewsTimeline;