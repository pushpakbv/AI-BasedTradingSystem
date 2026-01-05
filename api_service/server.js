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
const ArticleReader = require('./articleReader');
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Paths - use environment variable or default
const PREDICTIONS_DIR = process.env.PREDICTIONS_DIR || path.join(__dirname, '..', 'data_processor_service', 'final_predictions');

console.log('🗂️ PREDICTIONS_DIR:', PREDICTIONS_DIR);

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
  console.log(`✅ WebSocket client connected. Total: ${wss.clients.size}`);
  clients.add(ws);

  ws.on('close', () => {
    clients.delete(ws);
    console.log(`❌ WebSocket client disconnected. Total: ${wss.clients.size}`);
  });

  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
    clients.delete(ws);
  });
});

// ============ Broadcast Function ============
function broadcastToClients(message) {
  if (clients.size === 0) {
    console.log('📢 No clients connected to broadcast to');
    return;
  }
  
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
    console.log('📥 GET /api/predictions/daily');
    
    let files = [];
    try {
      files = await fs.readdir(PREDICTIONS_DIR);
      console.log(`📂 Found ${files.length} files in ${PREDICTIONS_DIR}`);
    } catch (err) {
      console.error(`❌ Cannot read directory ${PREDICTIONS_DIR}:`, err.message);
      return res.json({ predictions: [], count: 0, timestamp: new Date().toISOString() });
    }

    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const filePath = path.join(PREDICTIONS_DIR, file);
          const data = await fs.readFile(filePath, 'utf8');
          const pred = JSON.parse(data);

          if (pred.ticker && typeof pred.prediction !== 'undefined') {
            predictions.push({
              ...pred,
              company_name: COMPANY_MAP[ticker] || ticker
            });
            console.log(`✅ Loaded: ${ticker}`);
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
    res.status(500).json({ error: 'Failed to load predictions', predictions: [], count: 0 });
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

app.get('/api/articles/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const { limit = 10 } = req.query;

    const articles = await ArticleReader.getArticlesForTicker(ticker, parseInt(limit));

    res.json({
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      articles,
      count: articles.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching articles:', error);
    res.status(500).json({ error: 'Failed to fetch articles' });
  }
});

app.get('/api/articles/:ticker/:type', async (req, res) => {
  try {
    const { ticker, type } = req.params;
    const { limit = 10 } = req.query;

    const articles = await ArticleReader.getArticlesByType(
      ticker,
      type,
      parseInt(limit)
    );

    res.json({
      ticker,
      type,
      company_name: COMPANY_MAP[ticker] || ticker,
      articles,
      count: articles.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching articles:', error);
    res.status(500).json({ error: 'Failed to fetch articles' });
  }
});

app.get('/api/news/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;

    const generalArticles = await ArticleReader.getArticlesByType(ticker, 'general', 5);
    const financialArticles = await ArticleReader.getArticlesByType(ticker, 'financial', 5);

    res.json({
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      general: generalArticles,
      financial: financialArticles,
      total: generalArticles.length + financialArticles.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching news:', error);
    res.status(500).json({ error: 'Failed to fetch news' });
  }
});

app.get('/api/company/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const filePath = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    const data = await fs.readFile(filePath, 'utf8');
    const pred = JSON.parse(data);
    
    res.json({
      ...pred,
      company_name: COMPANY_MAP[ticker] || ticker,
      general_articles: [],
      financial_articles: [],
      sentiment: null,
      financial: null
    });
  } catch (error) {
    res.status(404).json({ error: 'Company data not found' });
  }
});

app.get('/api/stock/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    
    const stockData = {
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      current_price: Math.random() * 300 + 50,
      previous_close: Math.random() * 300 + 50,
      day_high: Math.random() * 350 + 50,
      day_low: Math.random() * 250 + 50,
      fifty_two_week_high: Math.random() * 400 + 100,
      fifty_two_week_low: Math.random() * 200 + 20,
      volume: Math.floor(Math.random() * 50000000),
      avg_volume: Math.floor(Math.random() * 40000000),
      market_cap: 'N/A',
      pe_ratio: (Math.random() * 30 + 10).toFixed(2),
      dividend_yield: (Math.random() * 4).toFixed(2),
      historical_data: [],
      lastUpdated: new Date().toISOString()
    };
    
    res.json(stockData);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch stock data' });
  }
});

app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    websocket_clients: clients.size,
    predictions_dir: PREDICTIONS_DIR,
    timestamp: new Date().toISOString()
  });
});

// ============ File Watching ============
console.log(`👀 Watching directory: ${PREDICTIONS_DIR}`);

chokidar.watch(PREDICTIONS_DIR, {
  awaitWriteFinish: {
    stabilityThreshold: 2000,
    pollInterval: 100
  }
}).on('change', async (filePath) => {
  try {
    if (!filePath.endsWith('_prediction.json')) return;

    const ticker = path.basename(filePath).replace('_prediction.json', '');
    console.log(`📝 Prediction file changed: ${ticker}`);

    const data = await fs.readFile(filePath, 'utf8');
    const prediction = JSON.parse(data);

    broadcastToClients({
      type: 'prediction_updated',
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction,
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    console.error(`Error processing file change:`, err);
  }
}).on('error', (err) => {
  console.error('Watcher error:', err);
});

// Periodic broadcast every 2 minutes
setInterval(async () => {
  try {
    let files = [];
    try {
      files = await fs.readdir(PREDICTIONS_DIR);
    } catch (err) {
      return;
    }

    const predictions = [];

    for (const file of files) {
      if (file.endsWith('_prediction.json')) {
        try {
          const ticker = file.replace('_prediction.json', '');
          const data = await fs.readFile(path.join(PREDICTIONS_DIR, file), 'utf8');
          const pred = JSON.parse(data);

          if (pred.ticker && typeof pred.prediction !== 'undefined') {
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
      console.log(`📢 Periodic broadcast: ${predictions.length} predictions to ${clients.size} clients`);
      broadcastToClients({
        type: 'predictions_refresh',
        predictions,
        timestamp: new Date().toISOString()
      });
    }
  } catch (err) {
    console.error('Error in periodic broadcast:', err);
  }
}, 2 * 60 * 1000);

// ============ Start Server ============
server.listen(PORT, () => {
  console.log(`✅ API Server running on port ${PORT}`);
  console.log(`🌐 WebSocket: ws://localhost:${PORT}`);
  console.log(`📂 Watching: ${PREDICTIONS_DIR}`);
});