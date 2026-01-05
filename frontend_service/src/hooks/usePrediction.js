import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const usePredictions = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [connected, setConnected] = useState(false);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const fetchPredictions = useCallback(async () => {
    try {
      setError(null);
      console.log(`📡 Fetching predictions from: ${API_BASE_URL}/predictions/daily`);
      
      const response = await axios.get(`${API_BASE_URL}/predictions/daily`);
      console.log('✅ API Response:', response.data);
      
      // Handle both response formats
      let predictionsData = [];
      
      if (response.data.predictions) {
        // Format: { predictions: [...] }
        predictionsData = response.data.predictions;
      } else if (Array.isArray(response.data)) {
        // Format: [...]
        predictionsData = response.data;
      } else if (response.data.companies) {
        // Format: { companies: [...] }
        predictionsData = response.data.companies;
      } else {
        console.warn('Unexpected response format:', response.data);
        predictionsData = [];
      }
      
      console.log(`📊 Parsed ${predictionsData.length} predictions`);
      
      // Filter and validate predictions
      const validPredictions = predictionsData
        .filter(p => {
          const isValid = p && p.ticker && (p.prediction || p.final_signal);
          if (!isValid) {
            console.warn('⚠️ Invalid prediction structure:', p);
          }
          return isValid;
        })
        .map(p => {
          // Normalize the structure
          if (!p.prediction && p.final_signal) {
            // Flatten nested prediction
            return {
              ...p,
              prediction: {
                final_signal: p.final_signal || 'HOLD',
                direction: p.direction || 'NEUTRAL',
                combined_score: p.combined_score || 0,
                confidence_level: p.confidence_level || 'LOW',
                reasoning: p.reasoning || 'No reasoning available'
              }
            };
          }
          return p;
        });
      
      console.log(`✅ Loaded ${validPredictions.length} valid predictions`);
      
      setPredictions(validPredictions);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching predictions:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load predictions');
      setPredictions([]);
      setLoading(false);
    }
  }, []);

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    console.log('🔌 Connecting to WebSocket...');
    
    try {
      const ws = new WebSocket(WS_BASE_URL);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', message.type);
          
          if (
            message.type === 'predictions_updated' || 
            message.type === 'prediction_updated' ||
            message.type === 'predictions_refresh'
          ) {
            console.log('🔄 Predictions updated, refreshing data...');
            fetchPredictions();
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnected(false);
      };
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected, attempting to reconnect in 5s...');
        setConnected(false);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };
      
      wsRef.current = ws;
      
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('WebSocket connection failed');
    }
  }, [fetchPredictions]);

  useEffect(() => {
    fetchPredictions();
    connectWebSocket();
    
    // Poll every 30 seconds for fresh data
    const pollInterval = setInterval(fetchPredictions, 30 * 1000);
    
    // Monitor WebSocket connection status
    const wsCheckInterval = setInterval(() => {
      if (connected) {
        console.log('✅ WebSocket connected, relying on push updates');
      } else {
        console.warn('⚠️ WebSocket disconnected, using polling fallback');
      }
    }, 60 * 1000);
    
    return () => {
      clearInterval(pollInterval);
      clearInterval(wsCheckInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchPredictions, connectWebSocket]);

  return {
    predictions,
    loading,
    error,
    lastUpdate,
    connected,
    refresh: fetchPredictions
  };
};