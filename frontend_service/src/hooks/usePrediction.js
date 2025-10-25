import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const usePredictions = () => {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch daily predictions summary
      const response = await axios.get(`${API_BASE_URL}/predictions/daily`);
      setPredictions(response.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch predictions');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPredictions();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchPredictions, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [fetchPredictions]);

  return {
    predictions,
    loading,
    error,
    refresh: fetchPredictions
  };
};