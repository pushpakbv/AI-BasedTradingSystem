const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const http = require('http');
const WebSocket = require('ws');
const chokidar = require('chokidar');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Paths
const PREDICTIONS_DIR = path.join(__dirname, '..', 'data_processor_service', 'final_predictions');
const SENTIMENT_DIR = path.join(__dirname, '..', 'data_processor_service', 'sentiment_results');
const FINANCIAL_DIR = path.join(__dirname, '..', 'data_processor_service', 'financial_analysis_results');

// Company mapping
const COMPANY_MAP = {
  MSFT: "Microsoft",
  AAPL: "Apple",
  GOOGL: "Alphabet",
  AMZN: "Amazon",
  TSLA: "Tesla",
  NVDA: "NVIDIA",
  META: "Meta",
  NFLX: "Netflix",
  BABA: "Alibaba",
  AMD: "AMD",
  INTC: "Intel",
  CRM: "Salesforce",
  UNP: "Union Pacific",
  FDX: "FedEx",
  UPS: "UPS",
  XPO: "XPO",
  CHRW: "C.H. Robinson",
  DPW_DE: "DHL",
  AMKBY: "Ambev",
  GXO: "GXO"
};

// Track connected clients
const clients = new Set();

// ============ WebSocket Handler ============
wss.on('connection', (ws) => {
  console.log(`🔌 Client connected. Total: ${wss.clients.size}`);
  clients.add(ws);

  ws.on('close', () => {
    clients.delete(ws);
    console.log(`🔌 Client disconnected. Total: ${wss.clients.size}`);
  });

  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
    clients.delete(ws);
  });
});

// ============ Broadcast Function ============
function broadcastToClients(message) {
  console.log(`📢 Broadcasting to ${clients.size} clients:`, message.type);
  
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      try {
        client.send(JSON.stringify(message));
      } catch (err) {
        console.error('Error sending to client:', err);
        clients.delete(client);
      }
    }
  });
}

// ============ REST Endpoints ============

// Get all predictions
app.get('/api/predictions/daily', async (req, res) => {
  try {
    const files = await fs.readdir(PREDICTIONS_DIR);
    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const data = await fs.readFile(path.join(PREDICTIONS_DIR, file), 'utf8');
          const pred = JSON.parse(data);

          // Validate and normalize
          if (pred.ticker && pred.prediction) {
            predictions.push({
              ...pred,
              company_name: COMPANY_MAP[ticker] || ticker
            });
          }
        } catch (e) {
          console.warn(`⚠️ Skipping ${file}:`, e.message);
        }
      }
    }

    console.log(`✅ Returning ${predictions.length} predictions`);
    res.json({
      predictions,
      count: predictions.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error reading predictions:', error);
    res.status(500).json({ error: 'Failed to load predictions' });
  }
});

// Get single prediction
app.get('/api/prediction/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const filePath = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    const data = await fs.readFile(filePath, 'utf8');
    const pred = JSON.parse(data);
    res.json({
      ...pred,
      company_name: COMPANY_MAP[ticker] || ticker
    });
  } catch (error) {
    res.status(404).json({ error: 'Prediction not found' });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    websocket_clients: clients.size,
    timestamp: new Date().toISOString()
  });
});

// ============ File Watching ============
console.log(`👀 Watching directory: ${PREDICTIONS_DIR}`);

// Watch predictions directory
chokidar.watch(PREDICTIONS_DIR, {
  awaitWriteFinish: {
    stabilityThreshold: 2000,
    pollInterval: 100
  }
}).on('change', async (filePath) => {
  try {
    if (!filePath.endsWith('_prediction.json')) return;

    const ticker = path.basename(filePath).replace('_prediction.json', '');
    console.log(`📝 Prediction changed: ${ticker}`);

    // Read the updated file
    const data = await fs.readFile(filePath, 'utf8');
    const prediction = JSON.parse(data);

    // Broadcast to all connected clients
    broadcastToClients({
      type: 'prediction_updated',
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction,
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    console.error(`Error processing file change for ${filePath}:`, err);
  }
}).on('error', (err) => {
  console.error('Watcher error:', err);
});

// Also broadcast all predictions every 2 minutes for fallback
setInterval(async () => {
  try {
    const files = await fs.readdir(PREDICTIONS_DIR);
    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const data = await fs.readFile(path.join(PREDICTIONS_DIR, file), 'utf8');
          const pred = JSON.parse(data);

          if (pred.ticker && pred.prediction) {
            predictions.push({
              ...pred,
              company_name: COMPANY_MAP[ticker] || ticker
            });
          }
        } catch (e) {
          // Skip invalid files
        }
      }
    }

    if (predictions.length > 0 && clients.size > 0) {
      console.log(`📢 Broadcast refresh: ${predictions.length} predictions to ${clients.size} clients`);
      broadcastToClients({
        type: 'predictions_refresh',
        predictions,
        timestamp: new Date().toISOString()
      });
    }
  } catch (err) {
    console.error('Error in periodic broadcast:', err);
  }
}, 2 * 60 * 1000); // Every 2 minutes

// ============ Start Server ============
server.listen(PORT, () => {
  console.log(`✅ API Server running on port ${PORT}`);
  console.log(`🌐 WebSocket: ws://localhost:${PORT}`);
});const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const http = require('http');
const WebSocket = require('ws');
const chokidar = require('chokidar');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Paths
const PREDICTIONS_DIR = path.join(__dirname, '..', 'data_processor_service', 'final_predictions');
const SENTIMENT_DIR = path.join(__dirname, '..', 'data_processor_service', 'sentiment_results');
const FINANCIAL_DIR = path.join(__dirname, '..', 'data_processor_service', 'financial_analysis_results');

// Company mapping
const COMPANY_MAP = {
  MSFT: "Microsoft",
  AAPL: "Apple",
  GOOGL: "Alphabet",
  AMZN: "Amazon",
  TSLA: "Tesla",
  NVDA: "NVIDIA",
  META: "Meta",
  NFLX: "Netflix",
  BABA: "Alibaba",
  AMD: "AMD",
  INTC: "Intel",
  CRM: "Salesforce",
  UNP: "Union Pacific",
  FDX: "FedEx",
  UPS: "UPS",
  XPO: "XPO",
  CHRW: "C.H. Robinson",
  DPW_DE: "DHL",
  AMKBY: "Ambev",
  GXO: "GXO"
};

// Track connected clients
const clients = new Set();

// ============ WebSocket Handler ============
wss.on('connection', (ws) => {
  console.log(`🔌 Client connected. Total: ${wss.clients.size}`);
  clients.add(ws);

  ws.on('close', () => {
    clients.delete(ws);
    console.log(`🔌 Client disconnected. Total: ${wss.clients.size}`);
  });

  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
    clients.delete(ws);
  });
});

// ============ Broadcast Function ============
function broadcastToClients(message) {
  console.log(`📢 Broadcasting to ${clients.size} clients:`, message.type);
  
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      try {
        client.send(JSON.stringify(message));
      } catch (err) {
        console.error('Error sending to client:', err);
        clients.delete(client);
      }
    }
  });
}

// ============ REST Endpoints ============

// Get all predictions
app.get('/api/predictions/daily', async (req, res) => {
  try {
    const files = await fs.readdir(PREDICTIONS_DIR);
    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const data = await fs.readFile(path.join(PREDICTIONS_DIR, file), 'utf8');
          const pred = JSON.parse(data);

          // Validate and normalize
          if (pred.ticker && pred.prediction) {
            predictions.push({
              ...pred,
              company_name: COMPANY_MAP[ticker] || ticker
            });
          }
        } catch (e) {
          console.warn(`⚠️ Skipping ${file}:`, e.message);
        }
      }
    }

    console.log(`✅ Returning ${predictions.length} predictions`);
    res.json({
      predictions,
      count: predictions.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error reading predictions:', error);
    res.status(500).json({ error: 'Failed to load predictions' });
  }
});

// Get single prediction
app.get('/api/prediction/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const filePath = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    const data = await fs.readFile(filePath, 'utf8');
    const pred = JSON.parse(data);
    res.json({
      ...pred,
      company_name: COMPANY_MAP[ticker] || ticker
    });
  } catch (error) {
    res.status(404).json({ error: 'Prediction not found' });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    websocket_clients: clients.size,
    timestamp: new Date().toISOString()
  });
});

// ============ File Watching ============
console.log(`👀 Watching directory: ${PREDICTIONS_DIR}`);

// Watch predictions directory
chokidar.watch(PREDICTIONS_DIR, {
  awaitWriteFinish: {
    stabilityThreshold: 2000,
    pollInterval: 100
  }
}).on('change', async (filePath) => {
  try {
    if (!filePath.endsWith('_prediction.json')) return;

    const ticker = path.basename(filePath).replace('_prediction.json', '');
    console.log(`📝 Prediction changed: ${ticker}`);

    // Read the updated file
    const data = await fs.readFile(filePath, 'utf8');
    const prediction = JSON.parse(data);

    // Broadcast to all connected clients
    broadcastToClients({
      type: 'prediction_updated',
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction,
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    console.error(`Error processing file change for ${filePath}:`, err);
  }
}).on('error', (err) => {
  console.error('Watcher error:', err);
});

// Also broadcast all predictions every 2 minutes for fallback
setInterval(async () => {
  try {
    const files = await fs.readdir(PREDICTIONS_DIR);
    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const data = await fs.readFile(path.join(PREDICTIONS_DIR, file), 'utf8');
          const pred = JSON.parse(data);

          if (pred.ticker && pred.prediction) {
            predictions.push({
              ...pred,
              company_name: COMPANY_MAP[ticker] || ticker
            });
          }
        } catch (e) {
          // Skip invalid files
        }
      }
    }

    if (predictions.length > 0 && clients.size > 0) {
      console.log(`📢 Broadcast refresh: ${predictions.length} predictions to ${clients.size} clients`);
      broadcastToClients({
        type: 'predictions_refresh',
        predictions,
        timestamp: new Date().toISOString()
      });
    }
  } catch (err) {
    console.error('Error in periodic broadcast:', err);
  }
}, 2 * 60 * 1000); // Every 2 minutes

// ============ Start Server ============
server.listen(PORT, () => {
  console.log(`✅ API Server running on port ${PORT}`);
  console.log(`🌐 WebSocket: ws://localhost:${PORT}`);
});