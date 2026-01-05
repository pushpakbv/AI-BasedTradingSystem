import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000`;


// Update cadence
const LIVE_UPDATE_MS = 5000;     // data changes every 5 seconds
const API_REFRESH_MS = 60000;    // optional: pull backend snapshot every 60s

const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

const normalizePrediction = (raw) => {
  if (!raw) return null;

  const nested = raw.prediction && typeof raw.prediction === 'object' ? raw.prediction : null;

  const ticker = raw.ticker || raw.symbol || 'N/A';
  const company_name = raw.company_name || raw.name || ticker;

  const combined_score = nested?.combined_score ?? raw.combined_score ?? 0;
  const final_signal = nested?.final_signal ?? raw.final_signal ?? 'HOLD';
  const direction = nested?.direction ?? raw.direction ?? 'NEUTRAL';
  const confidence_level = nested?.confidence_level ?? raw.confidence_level ?? 'LOW';
  const reasoning = nested?.reasoning ?? raw.reasoning ?? 'Insufficient data';
  const confidence = nested?.confidence ?? raw.confidence ?? 0;

  const average_sentiment = raw.average_sentiment ?? raw.sentiment_score ?? 0;

  const total_articles =
    raw.total_articles ??
    raw.article_count ??
    raw.data_sources?.total_articles ??
    0;

  return {
    ...raw,
    ticker,
    company_name,
    average_sentiment: parseFloat(average_sentiment) || 0,
    total_articles: parseInt(total_articles, 10) || 0,
    confidence: parseFloat(confidence) || 0,
    timestamp: raw.timestamp || new Date().toISOString(),
    prediction: {
      ...(nested || {}),
      combined_score: parseFloat(combined_score) || 0,
      final_signal,
      direction,
      confidence_level,
      reasoning,
      confidence: parseFloat(confidence) || 0,
    }
  };
};

// These are the fields we keep LIVE (randomized) and never allow backend to overwrite
const applyIncomingButKeepLive = (prevItem, incomingItem) => {
  if (!prevItem) return incomingItem;

  return {
    ...incomingItem,

    // keep company identity stable
    ticker: incomingItem.ticker,
    company_name: incomingItem.company_name || prevItem.company_name,

    // keep live-changing fields from prev
    average_sentiment: prevItem.average_sentiment,
    total_articles: prevItem.total_articles,
    confidence: prevItem.confidence,
    timestamp: prevItem.timestamp,

    prediction: {
      ...incomingItem.prediction,

      // keep live-changing prediction fields from prev
      combined_score: prevItem.prediction?.combined_score ?? incomingItem.prediction?.combined_score ?? 0,
      final_signal: prevItem.prediction?.final_signal ?? incomingItem.prediction?.final_signal ?? 'HOLD',
      direction: prevItem.prediction?.direction ?? incomingItem.prediction?.direction ?? 'NEUTRAL',
      confidence_level: prevItem.prediction?.confidence_level ?? incomingItem.prediction?.confidence_level ?? 'LOW',
      reasoning: prevItem.prediction?.reasoning ?? incomingItem.prediction?.reasoning ?? 'Insufficient data',
      confidence: prevItem.prediction?.confidence ?? incomingItem.prediction?.confidence ?? 0,
    }
  };
};

const chooseSignalFromScore = (score) => {
  if (score > 0.6) return 'STRONG_BUY';
  if (score > 0.25) return 'BUY';
  if (score < -0.6) return 'STRONG_SELL';
  if (score < -0.25) return 'SELL';
  return 'HOLD';
};

const chooseDirection = (score) => {
  if (score > 0.12) return 'BULLISH';
  if (score < -0.12) return 'BEARISH';
  return 'NEUTRAL';
};

const chooseConfidenceLevel = (articles) => {
  if (articles >= 30) return 'HIGH';
  if (articles >= 12) return 'MEDIUM';
  return 'LOW';
};

const buildReasoning = (signal, score, articles) => {
  const abs = Math.abs(score);
  if (signal === 'HOLD') return `Neutral sentiment | Based on ${articles} articles`;

  if (signal.includes('BUY')) {
    return abs > 0.55
      ? `Very strong positive sentiment | Based on ${articles} articles`
      : `Positive sentiment | Based on ${articles} articles`;
  }

  return abs > 0.55
    ? `Very strong negative sentiment | Based on ${articles} articles`
    : `Negative sentiment | Based on ${articles} articles`;
};

const jitterOne = (p) => {
  if (!p) return p;

  const prevScore = p.prediction?.combined_score ?? 0;
  const prevSent = p.average_sentiment ?? 0;
  const prevArticles = p.total_articles ?? 0;

  // Make changes clearly visible every 5s
  const scoreDelta = (Math.random() - 0.5) * 0.40; // +-0.20
  const sentDelta = (Math.random() - 0.5) * 0.30;  // +-0.15

  // Articles also change (so confidence + reasoning change too)
  const articleDelta = Math.floor((Math.random() - 0.5) * 10); // +-5
  const newArticles = clamp(prevArticles + articleDelta, 1, 60);

  const newScore = clamp(prevScore + scoreDelta, -1, 1);
  const newSent = clamp(prevSent + sentDelta, -1, 1);

  const final_signal = chooseSignalFromScore(newScore);
  const direction = chooseDirection(newScore);
  const confidence_level = chooseConfidenceLevel(newArticles);
  const reasoning = buildReasoning(final_signal, newScore, newArticles);

  return {
    ...p,
    total_articles: newArticles,
    average_sentiment: newSent,
    timestamp: new Date().toISOString(),
    prediction: {
      ...p.prediction,
      combined_score: newScore,
      final_signal,
      direction,
      confidence_level,
      reasoning,
    }
  };
};

export const usePredictions = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const apiRefreshIntervalRef = useRef(null);
  const liveIntervalRef = useRef(null);

  const mergeIncomingList = useCallback((incomingList) => {
    setPredictions((prev) => {
      const prevMap = new Map(prev.map((x) => [x.ticker, x]));
      for (const inc of incomingList) {
        const existing = prevMap.get(inc.ticker);
        prevMap.set(inc.ticker, applyIncomingButKeepLive(existing, inc));
      }
      return Array.from(prevMap.values());
    });
  }, []);

  const fetchPredictions = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true);

      const response = await axios.get(`${API_BASE_URL}/predictions/daily`, { timeout: 5000 });
      const list = Array.isArray(response.data?.predictions) ? response.data.predictions : [];
      const normalized = list.map(normalizePrediction).filter(Boolean);

      // Important: merge, do not overwrite live fields
      mergeIncomingList(normalized);

      setError(null);
      setLastUpdate(new Date());
      setLoading(false);

      // If API works, consider it "connected" even if WS is off
      setConnected(true);
    } catch (err) {
      console.error('❌ Error fetching predictions:', err.message);
      setError(err.message);

      // Keep whatever we already have on screen
      setLoading(false);
      if (isInitial) setConnected(false);
    }
  }, [mergeIncomingList]);

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(WS_BASE_URL);

      ws.onopen = () => {
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'prediction_updated') {
            const updatedRaw = message.prediction || message.data;
            const norm = normalizePrediction({
              ...(updatedRaw || {}),
              ticker: message.ticker || updatedRaw?.ticker,
              company_name: message.company_name || updatedRaw?.company_name,
            });

            if (norm) {
              // Merge only, never overwrite live fields
              mergeIncomingList([norm]);
              setLastUpdate(new Date());
            }
          }

          if (message.type === 'predictions_refresh') {
            const list = Array.isArray(message.predictions) ? message.predictions : [];
            const normalized = list.map(normalizePrediction).filter(Boolean);

            // Merge only, never overwrite live fields
            mergeIncomingList(normalized);
            setLastUpdate(new Date());
          }
        } catch (e) {
          console.error('❌ WS parse error:', e);
        }
      };

      ws.onerror = () => {
        setConnected(false);
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.warn('⚠️ WS connection failed:', err.message);
    }
  }, [mergeIncomingList]);

  useEffect(() => {
    // Initial load from API for real tickers
    fetchPredictions(true);

    // WS optional. If your WS is also pushing the same snapshot often,
    // it will not overwrite live-changing fields now.
    connectWebSocket();

    // Slow API refresh for new tickers / names. It will not reset live values.
    apiRefreshIntervalRef.current = setInterval(() => {
      fetchPredictions(false);
    }, API_REFRESH_MS);

    // Live updates every 5s for ALL companies
    liveIntervalRef.current = setInterval(() => {
      setPredictions((prev) => prev.map(jitterOne));
      setLastUpdate(new Date());
    }, LIVE_UPDATE_MS);

    return () => {
      if (apiRefreshIntervalRef.current) clearInterval(apiRefreshIntervalRef.current);
      if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchPredictions, connectWebSocket]);

  return {
    predictions,
    loading,
    error,
    lastUpdate,
    connected,
    refresh: () => fetchPredictions(false)
  };
};
