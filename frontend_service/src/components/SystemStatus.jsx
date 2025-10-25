import React, { useState, useEffect } from 'react';
import { Activity, Database, TrendingUp, Clock } from 'lucide-react';
import axios from 'axios';

const SystemStatus = () => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/health');
        setHealth(response.data);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

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
          <span className="text-gray-600">Last update: {new Date(health.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;