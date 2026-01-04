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
const GENERAL_ARTICLES_DIR = path.join(__dirname, '..', 'data_processor_service', 'classified_articles', 'general');
const FINANCIAL_ARTICLES_DIR = path.join(__dirname, '..', 'data_processor_service', 'classified_articles', 'financial');




// --- Company name mapping ---
const COMPANY_MAP = {
  MSFT: "Microsoft Corporation",
  AAPL: "Apple Inc.",
  GOOGL: "Alphabet Inc. (Google)",
  AMZN: "Amazon.com, Inc.",
  TSLA: "Tesla, Inc.",
  NVDA: "NVIDIA Corporation",
  BABA: "Alibaba Group Holding Limited",
  JD: "JD.com, Inc.",
  META: "Meta Platforms, Inc.",
  NFLX: "Netflix, Inc.",
  AMD: "Advanced Micro Devices, Inc.",
  INTC: "Intel Corporation",
  CRM: "Salesforce, Inc.",
  UNP: "Union Pacific Corporation",
  FDX: "FedEx Corporation",
  UPS: "United Parcel Service",
  DPW_DE: "DHL Group",
  XPO: "XPO Inc.",
  GXO: "GXO Logistics",
  CHRW: "C.H. Robinson Worldwide",
  AMKBY: "A.P. Moller – Maersk"
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
const watchDirectories = [
  PREDICTIONS_DIR,
  SENTIMENT_DIR,
  FINANCIAL_DIR,
  STOCK_DATA_DIR,
  GENERAL_ARTICLES_DIR,
  FINANCIAL_ARTICLES_DIR
];


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


app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    websocket_clients: clients.size
  });
});

// Get daily predictions summary
// Get daily predictions summary
app.get('/api/predictions/daily', async (req, res) => {
  try {
    console.log('📍 Fetching predictions from:', PREDICTIONS_DIR);
    
    // Ensure directory exists
    try {
      await fs.mkdir(PREDICTIONS_DIR, { recursive: true });
    } catch (err) {
      console.error('❌ Failed to access predictions directory');
    }
    
    const files = await fs.readdir(PREDICTIONS_DIR);
    console.log(`📂 Files in directory (${files.length}):`, files);
    
    const predictionFiles = files.filter(f => f.endsWith('_prediction.json'));
    console.log(`🔍 Prediction files found (${predictionFiles.length}):`, predictionFiles);
    
    if (predictionFiles.length === 0) {
      console.warn('⚠️ No prediction files found');
      return res.json({ 
        predictions: [],
        timestamp: new Date().toISOString()
      });
    }
    
    const predictions = [];
    
    for (const file of predictionFiles) {
      try {
        const ticker = file.replace('_prediction.json', '');
        const filePath = path.join(PREDICTIONS_DIR, file);
        console.log(`📄 Reading: ${filePath}`);
        
        const data = await fs.readFile(filePath, 'utf8');
        const predictionObj = JSON.parse(data);
        
        // Validate structure
        if (!predictionObj.prediction || !predictionObj.prediction.final_signal) {
          console.warn(`⚠️ Invalid prediction structure for ${ticker}:`, predictionObj);
          continue;
        }
        
        // Ensure proper structure
        const validPrediction = {
          ticker: predictionObj.ticker || ticker,
          company_name: COMPANY_MAP[ticker] || ticker,
          prediction: {
            final_signal: predictionObj.prediction.final_signal,
            direction: predictionObj.prediction.direction || 'NEUTRAL',
            combined_score: predictionObj.prediction.combined_score || 0,
            confidence: predictionObj.prediction.confidence || 0.5,
            confidence_level: predictionObj.prediction.confidence_level || 'LOW',
            reasoning: predictionObj.prediction.reasoning || 'No reasoning available',
            components: predictionObj.prediction.components || {}
          },
          data_sources: predictionObj.data_sources || {  // ✅ Add this
            general_articles: 0,
            financial_articles: 0,
            total_articles: 0
          },
          generated_at: predictionObj.generated_at || new Date().toISOString()
        };
        
        predictions.push(validPrediction);
        console.log(`✅ Loaded ${ticker}: ${validPrediction.prediction.final_signal}`);
      } catch (e) {
        console.error(`❌ Error loading ${file}:`, e.message);
      }
    }
    
    console.log(`✅ Returning ${predictions.length} valid predictions`);
    res.json({ 
      predictions,
      timestamp: new Date().toISOString(),
      count: predictions.length
    });
  } catch (error) {
    console.error('❌ Error in /api/predictions/daily:', error);
    res.status(500).json({ 
      error: 'Failed to load predictions',
      details: error.message
    });
  }
});

// Get individual stock prediction
app.get('/api/predictions/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    const filePath = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    const data = await fs.readFile(filePath, 'utf8');
    const prediction = JSON.parse(data);

    res.json({
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction
    });
  } catch (error) {
    console.error(`Error reading ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Stock not found' });
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
    
    console.log(`📍 Fetching stock data from: ${stockPath}`);
    
    // Check if file exists before reading
    if (!fs.existsSync(stockPath)) {
      console.warn(`⚠️ Stock file not found: ${stockPath}`);
      return res.status(404).json({ 
        error: 'Stock data not found',
        path: stockPath,
        ticker: ticker
      });
    }
    
    const data = await fs.readFile(stockPath, 'utf8');
    const stockData = JSON.parse(data);
    
    // Add company name
    stockData.company_name = COMPANY_MAP[ticker] || ticker;

    res.json(stockData);
  } catch (error) {
    console.error(`Error reading stock data for ${req.params.ticker}:`, error);
    res.status(500).json({ 
      error: 'Failed to load stock data',
      details: error.message,
      ticker: req.params.ticker
    });
  }
});

// Get complete company data (all in one)
// ...existing code...

app.get('/api/company/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;
    console.log(`📍 Fetching company data for ${ticker}`);
    
    // Read prediction file
    const predictionFile = path.join(PREDICTIONS_DIR, `${ticker}_prediction.json`);
    let prediction = null;
    try {
      const data = await fs.readFile(predictionFile, 'utf8');
      prediction = JSON.parse(data);
    } catch (e) {
      console.warn(`⚠️ No prediction found for ${ticker}`);
    }
    
    // Read stock data file
    let stockData = null;
    const stockFile = path.join(STOCK_DATA_DIR, `${ticker}_stock_data.json`);
    try {
      const data = await fs.readFile(stockFile, 'utf8');
      stockData = JSON.parse(data);
      console.log(`✅ Loaded stock data for ${ticker}: ${stockData.historical_data?.length || 0} data points`);
    } catch (e) {
      console.warn(`⚠️ No stock data found for ${ticker}`);
    }
    
    // Read sentiment file
    let sentiment = null;
    const sentimentFile = path.join(SENTIMENT_DIR, `${ticker}_sentiment.json`);
    try {
      const data = await fs.readFile(sentimentFile, 'utf8');
      sentiment = JSON.parse(data);
    } catch (e) {
      console.warn(`⚠️ No sentiment data found for ${ticker}`);
    }
    
    // Return aggregated data
    res.json({
      ticker,
      company_name: COMPANY_MAP[ticker] || ticker,
      prediction: prediction?.prediction || null,
      sentiment: sentiment || null,
      stockData: stockData || null,  // ✅ Include stock data
      general_articles: [],
      financial_articles: [],
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error(`❌ Error fetching company data for ${ticker}:`, error);
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