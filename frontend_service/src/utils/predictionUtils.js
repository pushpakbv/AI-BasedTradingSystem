// src/utils/predictionUtils.js

export const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

export const signalFromScore = (score) => {
  // score in [-1, 1]
  if (score >= 0.55) return 'STRONG_BUY';
  if (score >= 0.15) return 'BUY';
  if (score <= -0.55) return 'STRONG_SELL';
  if (score <= -0.15) return 'SELL';
  return 'HOLD';
};

export const directionFromScore = (score) => {
  if (score > 0.1) return 'BULLISH';
  if (score < -0.1) return 'BEARISH';
  return 'NEUTRAL';
};

export const confidenceLevelFromArticles = (totalArticles) => {
  const n = Number(totalArticles) || 0;
  if (n >= 30) return 'HIGH';
  if (n >= 15) return 'MEDIUM';
  return 'LOW';
};

/**
 * Normalizes ANY backend shape into ONE canonical structure:
 * {
 *   ticker,
 *   company_name,
 *   timestamp,
 *   total_articles,
 *   average_sentiment,
 *   prediction: {
 *     final_signal, direction, combined_score, confidence_level, reasoning, confidence
 *   }
 * }
 */
export const normalizePrediction = (raw) => {
  if (!raw) return null;

  const ticker = raw.ticker || raw.symbol || 'N/A';
  const company_name = raw.company_name || raw.company || ticker;

  const total_articles =
    raw.total_articles ??
    raw.article_count ??
    raw.data_sources?.total_articles ??
    raw.data_sources?.general_articles ??
    0;

  const avgSent =
    raw.average_sentiment ??
    raw.sentiment_score ??
    raw.prediction_snapshot?.average_sentiment ??
    0;

  // Case A: /predictions/daily gives prediction as an object
  const predObj = (raw.prediction && typeof raw.prediction === 'object') ? raw.prediction : null;

  // Case B: /prediction/{ticker} sometimes gives flat fields + prediction_snapshot
  const snapshotObj = (raw.prediction_snapshot && typeof raw.prediction_snapshot === 'object')
    ? raw.prediction_snapshot
    : null;

  // Case C: sometimes prediction is a NUMBER like -4.5 (percent-ish)
  const predNumber = (typeof raw.prediction === 'number') ? raw.prediction : null;

  // Pick best source for fields
  const source = predObj || snapshotObj || raw;

  // combined_score can be missing in some shapes, so derive it
  let combined_score = 0;

  if (typeof source.combined_score === 'number') {
    combined_score = source.combined_score; // already in [-1,1] in your /predictions/daily
  } else if (typeof raw.combined_score === 'number') {
    combined_score = raw.combined_score; // sometimes flat
  } else if (typeof raw.signal_strength === 'number') {
    // signal_strength looks like 4.5 means 4.5%
    combined_score = clamp(raw.signal_strength / 100, -1, 1);
  } else if (typeof predNumber === 'number') {
    // predNumber often looks like -4.5, treat as percent
    combined_score = clamp(predNumber / 100, -1, 1);
  } else if (typeof avgSent === 'number') {
    combined_score = clamp(avgSent, -1, 1);
  }

  const final_signal = source.final_signal || raw.final_signal || signalFromScore(combined_score);
  const direction = source.direction || raw.direction || directionFromScore(combined_score);

  const confidence_level =
    source.confidence_level ||
    raw.confidence_level ||
    confidenceLevelFromArticles(total_articles);

  const reasoning =
    source.reasoning ||
    raw.reasoning ||
    'Analysis based on sentiment and market signals';

  const confidence =
    (typeof source.confidence === 'number' ? source.confidence : null) ??
    (typeof raw.confidence === 'number' ? raw.confidence : null) ??
    0;

  const timestamp =
    raw.timestamp ||
    raw.last_updated ||
    new Date().toISOString();

  return {
    ticker,
    company_name,
    timestamp,
    total_articles: Number(total_articles) || 0,
    average_sentiment: Number(avgSent) || 0,
    prediction: {
      final_signal,
      direction,
      combined_score: clamp(Number(combined_score) || 0, -1, 1),
      confidence_level,
      reasoning,
      confidence
    }
  };
};

/**
 * Apply a "live tick" every 5s so ALL companies change,
 * but do NOT revert back to base after a fetch.
 */
export const tickPredictions = (currentList) => {
  const now = new Date().toISOString();

  return (Array.isArray(currentList) ? currentList : []).map((item) => {
    const base = normalizePrediction(item);
    if (!base) return item;

    const currScore = Number(base.prediction?.combined_score) || 0;

    // Smooth-ish random movement
    const delta = (Math.random() - 0.5) * 0.30; // +-0.15
    const nextScore = clamp(currScore + delta, -1, 1);

    const nextSignal = signalFromScore(nextScore);
    const nextDirection = directionFromScore(nextScore);

    // Also move avg sentiment and article count so the cards "feel alive"
    const sentimentDelta = (Math.random() - 0.5) * 0.20; // +-0.10
    const nextSent = clamp((Number(base.average_sentiment) || 0) + sentimentDelta, -1, 1);

    const articleDelta = Math.floor((Math.random() - 0.5) * 6); // +-3
    const nextArticles = clamp((Number(base.total_articles) || 0) + articleDelta, 1, 60);

    const nextConfLevel = confidenceLevelFromArticles(nextArticles);

    const reasoning =
      nextSignal === 'STRONG_BUY' ? `Very strong positive sentiment | Based on ${nextArticles} articles` :
      nextSignal === 'BUY' ? `Positive sentiment | Based on ${nextArticles} articles` :
      nextSignal === 'STRONG_SELL' ? `Very strong negative sentiment | Based on ${nextArticles} articles` :
      nextSignal === 'SELL' ? `Negative sentiment | Based on ${nextArticles} articles` :
      `Neutral sentiment | Based on ${nextArticles} articles`;

    return {
      ...base,
      timestamp: now,
      total_articles: nextArticles,
      average_sentiment: Number(nextSent.toFixed(3)),
      prediction: {
        ...base.prediction,
        combined_score: Number(nextScore.toFixed(3)),
        final_signal: nextSignal,
        direction: nextDirection,
        confidence_level: nextConfLevel,
        reasoning
      }
    };
  });
};
