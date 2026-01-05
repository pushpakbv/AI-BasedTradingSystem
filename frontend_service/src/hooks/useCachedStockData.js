import { useEffect, useState } from 'react';
import axios from 'axios';

const MARKET_DATA_API = process.env.REACT_APP_MARKET_DATA_API || 'http://localhost:8001/api';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours
const CACHE_KEY_PREFIX = 'stock_data_';
const REQUEST_QUEUE = [];
const REQUEST_INTERVAL = 3000; // 3 seconds between requests

let isProcessing = false;

const processQueue = async () => {
  if (isProcessing || REQUEST_QUEUE.length === 0) return;
  
  isProcessing = true;
  const { ticker, callback } = REQUEST_QUEUE.shift();
  
  try {
    const response = await axios.get(`${MARKET_DATA_API}/stock/${ticker}`);
    callback(response.data);
  } catch (err) {
    callback(null, err);
  }
  
  isProcessing = false;
  setTimeout(processQueue, REQUEST_INTERVAL);
};

export const useCachedStockData = (ticker) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cacheKey = `${CACHE_KEY_PREFIX}${ticker}`;
    const cached = localStorage.getItem(cacheKey);

    if (cached) {
      const { data: cachedData, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp < CACHE_DURATION) {
        setData(cachedData);
        setLoading(false);
        return;
      }
    }

    REQUEST_QUEUE.push({
      ticker,
      callback: (result, err) => {
        if (err) {
          setError(err.message);
        } else {
          localStorage.setItem(cacheKey, JSON.stringify({ data: result, timestamp: Date.now() }));
          setData(result);
        }
        setLoading(false);
      }
    });

    processQueue();
  }, [ticker]);

  return { data, loading, error };
};