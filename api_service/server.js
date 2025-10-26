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
const STOCK_DATA_DIR = path.join(__dirname, '..', 'market_data_service', 'stock_data');
const CRAWLER_DATA_DIR = path.join(__dirname, '..', 'crawler_service', 'data', 'by_company');

// --- Company name mapping ---
const COMPANY_MAP = {
  MSFT: "Microsoft Corporation",
  AAPL: "Apple Inc.",
  GOOGL: "Alphabet Inc.",
  AMZN: "Amazon.com, Inc.",
  TSLA: "Tesla, Inc.",
  META: "Meta Platforms, Inc.",
  NVDA: "NVIDIA Corporation",
  NFLX: "Netflix, Inc.",
  BABA: "Alibaba Group",
  AMD: "Advanced Micro Devices, Inc.",
  INTC: "Intel Corporation",
  CRM: "Salesforce, Inc.",
  UNP: "Union Pacific Corporation"
};
// --- End company name mapping ---

// WebSocket clients
const clients = new Set();

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('✅ Client connected to WebSocket');
  clients.add(ws);
  
  // Send initial connection message
  ws.send(JSON.stringify({ 
    type: 'connected', 
    message: 'WebSocket connection established',
    timestamp: new Date().toISOString() 
  }));
  
  ws.on('close', () => {
    console.log('❌ Client disconnected from WebSocket');
    clients.delete(ws);
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
    clients.delete(ws);
  });
});

// Broadcast updates to all connected clients
function broadcastUpdate(type, data) {
  const message = JSON.stringify({ 
    type, 
    data, 
    timestamp: new Date().toISOString() 
  });
  
  let sent = 0;
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
      sent++;
    }
  });
  
  console.log(`📡 Broadcasted ${type} to ${sent} clients`);
}

// Watch for file changes
const watchDirectories = [PREDICTIONS_DIR, SENTIMENT_DIR, FINANCIAL_DIR, STOCK_DATA_DIR];

watchDirectories.forEach(dir => {
  if (fs.access(dir).catch(() => false)) {
    const watcher = chokidar.watch(dir, {
      ignored: /(^|[\/\\])\../,
      persistent: true,
      ignoreInitial: true
    });
    
    watcher
      .on('add', path => {
        console.log(`📄 File added: ${path}`);
        broadcastUpdate('file_added', { path });
      })
      .on('change', path => {
        console.log(`📝 File changed: ${path}`);
        
        // Determine what changed
        if (path.includes('_prediction.json')) {
          const ticker = path.match(/([A-Z]+)_prediction\.json/)?.[1];
          broadcastUpdate('prediction_updated', { ticker });
        } else if (path.includes('_sentiment.json')) {
          const ticker = path.match(/([A-Z]+)_sentiment\.json/)?.[1];
          broadcastUpdate('sentiment_updated', { ticker });
        } else if (path.includes('_stock_data.json')) {
          const ticker = path.match(/([A-Z]+)_stock_data\.json/)?.[1];
          broadcastUpdate('stock_data_updated', { ticker });
        }
      });
    
    console.log(`👀 Watching directory: ${dir}`);
  }
});

// ============ API ROUTES ============

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    websocket_clients: clients.size
  });
});

// Get daily predictions summary
app.get('/api/predictions/daily', async (req, res) => {
  try {
    const summaryPath = path.join(PREDICTIONS_DIR, 'daily_predictions_summary.json');
    const data = await fs.readFile(summaryPath, 'utf8');
    const summary = JSON.parse(data);
    
    res.json(summary);
  } catch (error) {
    console.error('Error reading daily summary:', error);
    res.status(500).json({ error: 'Failed to load predictions' });
  }
});

// Get individual stock prediction
app.get('/api/predictions/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const filePath = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    const data = await fs.readFile(filePath, 'utf8');
    const prediction = JSON.parse(data);
    
    // Add company name
    prediction.company_name = COMPANY_MAP[ticker] || ticker;

    res.json(prediction);
  } catch (error) {
    console.error(`Error reading ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Stock not found' });
  }
});

// Get sentiment results
app.get('/api/sentiment/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const sentimentPath = path.join(SENTIMENT_DIR, `${ticker}_sentiment.json`);
    const data = await fs.readFile(sentimentPath, 'utf8');
    const sentiment = JSON.parse(data);
    
    // Add company name
    sentiment.company_name = COMPANY_MAP[ticker] || ticker;

    res.json(sentiment);
  } catch (error) {
    console.error(`Error reading sentiment for ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Sentiment data not found' });
  }
});

// Get financial analysis
app.get('/api/financial/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const financialPath = path.join(FINANCIAL_DIR, `${ticker}_financial_analysis.json`);
    const data = await fs.readFile(financialPath, 'utf8');
    const financial = JSON.parse(data);
    
    // Add company name
    financial.company_name = COMPANY_MAP[ticker] || ticker;

    res.json(financial);
  } catch (error) {
    console.error(`Error reading financial for ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Financial data not found' });
  }
});

// Get stock price data
app.get('/api/stock/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const stockPath = path.join(STOCK_DATA_DIR, `${ticker}_stock_data.json`);
    const data = await fs.readFile(stockPath, 'utf8');
    const stockData = JSON.parse(data);
    
    // Add company name
    stockData.company_name = COMPANY_MAP[ticker] || ticker;

    res.json(stockData);
  } catch (error) {
    console.error(`Error reading stock data for ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Stock data not found' });
  }
});

// Get complete company data (all in one)
app.get('/api/company/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    
    // Fetch all data for this company
    const [prediction, sentiment, financial, stockData] = await Promise.allSettled([
      fs.readFile(path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`), 'utf8'),
      fs.readFile(path.join(SENTIMENT_DIR, `${ticker}_sentiment.json`), 'utf8'),
      fs.readFile(path.join(FINANCIAL_DIR, `${ticker}_financial_analysis.json`), 'utf8'),
      fs.readFile(path.join(STOCK_DATA_DIR, `${ticker}_stock_data.json`), 'utf8')
    ]);
    
    const result = {
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction: prediction.status === 'fulfilled' ? { ...JSON.parse(prediction.value), company_name: COMPANY_MAP[ticker] || ticker } : null,
      sentiment: sentiment.status === 'fulfilled' ? { ...JSON.parse(sentiment.value), company_name: COMPANY_MAP[ticker] || ticker } : null,
      financial: financial.status === 'fulfilled' ? { ...JSON.parse(financial.value), company_name: COMPANY_MAP[ticker] || ticker } : null,
      stockData: stockData.status === 'fulfilled' ? { ...JSON.parse(stockData.value), company_name: COMPANY_MAP[ticker] || ticker } : null,
    };
    
    res.json(result);
  } catch (error) {
    console.error(`Error reading company data for ${req.params.ticker}:`, error);
    res.status(500).json({ error: 'Failed to load company data' });
  }
});

// Get list of available companies
app.get('/api/companies', async (req, res) => {
  try {
    const files = await fs.readdir(PREDICTIONS_DIR);
    const companies = files
      .filter(f => f.endsWith('_prediction.json'))
      .map(f => {
        const ticker = f.replace('_prediction.json', '');
        return { ticker, company_name: COMPANY_MAP[ticker] || ticker };
      });
    res.json({ companies });
  } catch (error) {
    console.error('Error reading companies:', error);
    res.status(500).json({ error: 'Failed to load companies' });
  }
});

// Get news articles for a company
app.get('/api/news/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const companyDir = path.join(CRAWLER_DATA_DIR, ticker);
    
    // Get latest date folder
    const dates = await fs.readdir(companyDir);
    dates.sort().reverse();
    
    if (dates.length === 0) {
      return res.json({ articles: [] });
    }
    
    const latestDate = dates[0];
    const articlesDir = path.join(companyDir, latestDate);
    const articleFiles = await fs.readdir(articlesDir);
    
    const articles = await Promise.all(
      articleFiles
        .filter(f => f.endsWith('.json'))
        .map(async (file) => {
          const data = await fs.readFile(path.join(articlesDir, file), 'utf8');
          return JSON.parse(data);
        })
    );
    
    res.json({ ticker, articles });
  } catch (error) {
    console.error(`Error reading news for ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'News not found' });
  }
});

server.listen(PORT, () => {
  console.log(`🚀 API Server running on http://localhost:${PORT}`);
  console.log(`🔌 WebSocket Server running on ws://localhost:${PORT}`);
  console.log(`👀 Watching for file changes...`);
});