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
  const updateTimeoutRef = useRef(null);

  const fetchPredictions = useCallback(async () => {
    try {
      console.log('📡 Fetching predictions...');
      const response = await axios.get(`${API_BASE_URL}/predictions/daily`, {
        timeout: 5000
      });

      let predictionsData = response.data.predictions || [];
      console.log(`✅ Received ${predictionsData.length} predictions`);

      // Filter valid predictions
      const validPredictions = predictionsData
        .filter(p => p && p.ticker && p.prediction)
        .map(p => ({
          ...p,
          company_name: p.company_name || p.ticker
        }));

      console.log(`✅ Loaded ${validPredictions.length} valid predictions`);
      
      // Log a sample prediction to verify data structure
      if (validPredictions.length > 0) {
        console.log('📊 Sample prediction:', validPredictions[0]);
      }
      
      // Force a new reference to trigger re-render
      setPredictions([...validPredictions]);
      setLastUpdate(new Date());
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching predictions:', err.message);
      setError(err.message);
      setLoading(false);
    }
  }, []);

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected');
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

          // Handle different message types
          if (message.type === 'prediction_updated') {
            // Single prediction updated
            console.log(`🔄 Updated prediction for ${message.ticker}`);
            setPredictions(prev => {
              const updated = prev.map(p =>
                p.ticker === message.ticker
                  ? { ...message.prediction, company_name: message.company_name }
                  : p
              );
              // If ticker not found, add it
              if (!updated.find(p => p.ticker === message.ticker)) {
                updated.push(message.prediction);
              }
              console.log(`📊 Updated predictions array:`, updated);
              // Force new reference
              return [...updated];
            });
            setLastUpdate(new Date());
          } 
          else if (message.type === 'predictions_refresh') {
            // All predictions refreshed
            console.log(`🔄 Refreshed all predictions (${message.predictions.length})`);
            console.log('📊 First refreshed prediction:', message.predictions[0]);
            // Force new reference
            setPredictions([...message.predictions]);
            setLastUpdate(new Date());
          }
        } catch (err) {
          console.error('Error parsing message:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnected(false);
      };
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected, reconnecting in 5s...');
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
  }, []);

  // Setup polling and WebSocket
  useEffect(() => {
    // Initial fetch
    console.log('🔧 Setting up predictions hook...');
    fetchPredictions();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Poll every 30 seconds (for redundancy)
    const pollInterval = setInterval(() => {
      console.log('⏱️ Polling for updates...');
      fetchPredictions();
    }, 30 * 1000);

    return () => {
      console.log('🧹 Cleaning up predictions hook...');
      clearInterval(pollInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
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