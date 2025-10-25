import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const usePredictions = () => {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [connected, setConnected] = useState(false);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const fetchPredictions = useCallback(async () => {
    try {
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/predictions/daily`);
      setPredictions(response.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to fetch predictions');
      setLoading(false);
      console.error('Error fetching predictions:', err);
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
          console.log('📨 WebSocket message received:', message);
          
          if (message.type === 'predictions_updated') {
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
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    }
  }, [fetchPredictions]);

  useEffect(() => {
    fetchPredictions();
    connectWebSocket();
    
    const pollInterval = setInterval(fetchPredictions, 5 * 60 * 1000);
    
    return () => {
      clearInterval(pollInterval);
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