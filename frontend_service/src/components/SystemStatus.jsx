import React, { useState, useEffect } from 'react';
import { Activity, Database, Clock } from 'lucide-react';
import axios from 'axios';

const SystemStatus = () => {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  // Normalizes REACT_APP_API_URL to always point to ".../api"
  const rawBase = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  const API_BASE_URL = rawBase.replace(/\/$/, '').endsWith('/api')
    ? rawBase.replace(/\/$/, '')
    : `${rawBase.replace(/\/$/, '')}/api`;

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
        setHealth(response.data);
        setError(null);
      } catch (err) {
        console.error('Health check failed:', err);
        setError('Failed to fetch health status');
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);

    return () => clearInterval(interval);
  }, [API_BASE_URL]);

  if (!health) return <div className="text-xs text-gray-500">Loading...</div>;
  if (error) return <div className="text-xs text-red-500">{error}</div>;

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <Activity className="w-4 h-4" />
        System Status
      </h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-gray-600">API: Online</span>
        </div>
        <div className="flex items-center gap-2">
          <Database className="w-3 h-3 text-gray-400" />
          <span className="text-gray-600">{health.websocket_clients} clients</span>
        </div>
        <div className="flex items-center gap-2 col-span-2">
          <Clock className="w-3 h-3 text-gray-400" />
          <span className="text-gray-600">
            Last update: {new Date(health.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
