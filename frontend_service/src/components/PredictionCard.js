import React, { useEffect, useState, useRef } from 'react';

function PredictionCard({ ticker }) {
  const [prediction, setPrediction] = useState(null);
  const wsRef = useRef(null);

  // Fetch prediction from API
  const fetchPrediction = async () => {
    try {
      const res = await fetch(`/api/predictions/${ticker}`);
      if (res.ok) {
        const data = await res.json();
        setPrediction(data);
      }
    } catch (err) {
      setPrediction(null);
    }
  };

  useEffect(() => {
    fetchPrediction();

    // Setup WebSocket connection
    wsRef.current = new window.WebSocket('ws://localhost:8000');
    wsRef.current.onopen = () => {
      // Optionally log or send a handshake
    };
    wsRef.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        // Listen for prediction updates for this ticker
        if (msg.type === 'prediction_updated' && msg.data.ticker === ticker) {
          fetchPrediction();
        }
      } catch (e) {
        // Ignore malformed messages
      }
    };
    wsRef.current.onerror = () => {};
    wsRef.current.onclose = () => {};

    // Cleanup on unmount
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
    // eslint-disable-next-line
  }, [ticker]);

  if (!prediction) return <div>Loading...</div>;

  return (
    <div className="prediction-card">
      <h2>{prediction.company_name || ticker}</h2>
      <p><b>Signal:</b> {prediction.prediction?.final_signal}</p>
      <p><b>Direction:</b> {prediction.prediction?.direction}</p>
      <p><b>Confidence:</b> {prediction.prediction?.confidence_level}</p>
      <p><b>Probability:</b> {prediction.prediction?.probability ? (prediction.prediction.probability * 100).toFixed(1) + '%' : 'N/A'}</p>
      {/* Add more fields as needed */}
    </div>
  );
}

export default PredictionCard;