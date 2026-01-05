import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

const PredictionsContext = createContext(null);

const STORAGE_KEY = "tradesystem_live_predictions_v1";

const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const rand = (min, max) => min + Math.random() * (max - min);

const normalizeBaseUrl = (raw) => {
  const base = (raw || "http://localhost:8000/api").replace(/\/$/, "");
  return base.endsWith("/api") ? base : `${base}/api`;
};

const toNum = (v) => {
  const n = typeof v === "string" ? parseFloat(v) : v;
  return Number.isFinite(n) ? n : 0;
};

// Converts values into a safe -1..+1 range.
// If backend sends 0..100 (or -100..100), it converts back by dividing by 100.
const normalizeScore01 = (v) => {
  const n = toNum(v);

  // If it looks like percentage scale, convert to -1..1
  if (Math.abs(n) > 1.5) return n / 100;

  // Otherwise assume already -1..1
  return n;
};

const normalizeOne = (item) => {
  // Your API uses: item.prediction = { combined_score, final_signal, ... }
  const predObj =
    item?.prediction && typeof item.prediction === "object" ? item.prediction : null;

  // Normalize scores so UI always treats them as -1..+1
  const combined = normalizeScore01(predObj?.combined_score);
  const avgSent = normalizeScore01(item?.average_sentiment);

  return {
    ticker: item?.ticker || "N/A",
    company_name: item?.company_name || item?.ticker || "N/A",
    timestamp: item?.timestamp || new Date().toISOString(),
    total_articles: item?.total_articles ?? item?.article_count ?? 0,

    // Always use real sentiment (normalized), never fallback to combined_score
    average_sentiment: avgSent,

    prediction: {
      final_signal: predObj?.final_signal || "HOLD",
      direction: predObj?.direction || "NEUTRAL",

      // Always store combined_score in -1..+1 format
      combined_score: combined,

      confidence_level: predObj?.confidence_level || "LOW",
      reasoning: predObj?.reasoning || "Insufficient data",
    },

    _simulated: true,
  };
};


const signalFromScore = (score) => {
  if (score >= 0.55) return "STRONG_BUY";
  if (score >= 0.12) return "BUY";
  if (score <= -0.55) return "STRONG_SELL";
  if (score <= -0.12) return "SELL";
  return "HOLD";
};

const directionFromSignal = (sig) => {
  if (sig === "BUY" || sig === "STRONG_BUY") return "BULLISH";
  if (sig === "SELL" || sig === "STRONG_SELL") return "BEARISH";
  return "NEUTRAL";
};

const confidenceFromAbs = (absScore) => {
  if (absScore >= 0.65) return "HIGH";
  if (absScore >= 0.25) return "MEDIUM";
  return "LOW";
};

const applyTick = (p) => {
  // jitter score and sentiment a little each tick
  const oldScore = p?.prediction?.combined_score ?? 0;
  const newScore = clamp(oldScore + rand(-0.12, 0.12), -0.99, 0.99);

  const oldSent = p?.average_sentiment ?? 0;
  const newSent = clamp(oldSent + rand(-0.08, 0.08), -0.99, 0.99);

  const sig = signalFromScore(newScore);
  const dir = directionFromSignal(sig);
  const conf = confidenceFromAbs(Math.abs(newScore));

  const baseArticles = p?.total_articles ?? 0;
  const newArticles = clamp(Math.round(baseArticles + rand(-3, 6)), 0, 200);

  const reasoning =
    sig === "HOLD"
      ? "Neutral bias | Monitoring"
      : sig.includes("BUY")
      ? `Positive sentiment | Based on ${newArticles} articles`
      : `Negative sentiment | Based on ${newArticles} articles`;

  return {
    ...p,
    timestamp: new Date().toISOString(),
    total_articles: newArticles,
    average_sentiment: newSent,
    prediction: {
      ...p.prediction,
      combined_score: newScore,
      final_signal: sig,
      direction: dir,
      confidence_level: conf,
      reasoning,
    },
    _simulated: true,
  };
};

const loadPersisted = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.predictions)) return null;
    return parsed.predictions;
  } catch {
    return null;
  }
};

const persist = (predictions) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ predictions, savedAt: new Date().toISOString() }));
  } catch {
    // ignore
  }
};

const stableMerge = (prevList, apiList) => {
  const prevMap = new Map((prevList || []).map((x) => [x.ticker, x]));

  // Keep order stable: use API order, but preserve simulated values from prev when present
  const merged = (apiList || []).map((apiItem) => {
    const normalizedApi = normalizeOne(apiItem);
    const prev = prevMap.get(normalizedApi.ticker);

    if (!prev) return normalizedApi;

    // Preserve the simulated fields from prev, only update stable identity fields from API
    return {
      ...prev,
      ticker: normalizedApi.ticker,
      company_name: normalizedApi.company_name || prev.company_name,
    };
  });

  // If prev had extra tickers not in API, keep them at the end (optional)
  const apiTickers = new Set(merged.map((x) => x.ticker));
  (prevList || []).forEach((p) => {
    if (!apiTickers.has(p.ticker)) merged.push(p);
  });

  return merged;
};

export const PredictionsProvider = ({ children }) => {
  const rawBase = process.env.REACT_APP_API_URL;
  const API_BASE_URL = useMemo(() => normalizeBaseUrl(rawBase), [rawBase]);

  const [predictions, setPredictions] = useState(() => {
    const saved = loadPersisted();
    return saved && saved.length ? saved : [];
  });

  const [loading, setLoading] = useState(predictions.length === 0);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const tickTimerRef = useRef(null);
  const apiTimerRef = useRef(null);

  const fetchFromApi = async () => {
    try {
      setError(null);
      const res = await axios.get(`${API_BASE_URL}/predictions/daily`, { timeout: 8000 });
      const apiList = Array.isArray(res?.data?.predictions) ? res.data.predictions : [];
      setPredictions((prev) => {
        const merged = stableMerge(prev, apiList);
        persist(merged);
        return merged;
      });
      setLastUpdate(new Date().toISOString());
      setLoading(false);
    } catch (e) {
      setError("Failed to fetch predictions");
      setLoading(false);
    }
  };

  // Initial load and periodic API refresh (keep this slower than your 5s tick)
  useEffect(() => {
    fetchFromApi();

    // refresh baseline list every 60s (not 5s) so it never fights your tick updates
    apiTimerRef.current = setInterval(fetchFromApi, 60000);

    return () => {
      if (apiTimerRef.current) clearInterval(apiTimerRef.current);
    };
  }, [API_BASE_URL]);

  // 5 second tick update + persist
  useEffect(() => {
    if (tickTimerRef.current) clearInterval(tickTimerRef.current);

    tickTimerRef.current = setInterval(() => {
      setPredictions((prev) => {
        if (!prev || prev.length === 0) return prev;
        const next = prev.map(applyTick);
        persist(next);
        setLastUpdate(new Date().toISOString());
        return next;
      });
    }, 5000);

    return () => {
      if (tickTimerRef.current) clearInterval(tickTimerRef.current);
    };
  }, []);

  const value = useMemo(
    () => ({
      predictions,
      loading,
      error,
      lastUpdate,
      refreshNow: fetchFromApi,
    }),
    [predictions, loading, error, lastUpdate]
  );

  return <PredictionsContext.Provider value={value}>{children}</PredictionsContext.Provider>;
};

export const usePredictionsStore = () => {
  const ctx = useContext(PredictionsContext);
  if (!ctx) throw new Error("usePredictionsStore must be used inside PredictionsProvider");
  return ctx;
};
