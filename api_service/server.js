const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Path to predictions
const PREDICTIONS_DIR = path.join(__dirname, '..', 'data_processor_service', 'final_predictions');

// Get daily predictions summary
app.get('/api/predictions/daily', async (req, res) => {
  try {
    const summaryPath = path.join(PREDICTIONS_DIR, 'daily_predictions_summary.json');
    const data = await fs.readFile(summaryPath, 'utf8');
    const summary = JSON.parse(data);
    
    res.json({
      summary: {
        date: summary.date,
        total_companies: summary.total_companies,
        signal_distribution: summary.signal_distribution
      },
      predictions: summary.predictions
    });
  } catch (error) {
    console.error('Error reading predictions:', error);
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
    const sentimentPath = path.join(__dirname, '..', 'data_processor_service', 'sentiment_results', `${ticker}_sentiment.json`);
    const data = await fs.readFile(sentimentPath, 'utf8');
    const sentiment = JSON.parse(data);
    
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
    const financialPath = path.join(__dirname, '..', 'data_processor_service', 'financial_analysis_results', `${ticker}_financial_analysis.json`);
    const data = await fs.readFile(financialPath, 'utf8');
    const financial = JSON.parse(data);
    
    res.json(financial);
  } catch (error) {
    console.error(`Error reading financial for ${req.params.ticker}:`, error);
    res.status(404).json({ error: 'Financial data not found' });
  }
});

app.listen(PORT, () => {
  console.log(`API Server running on http://localhost:${PORT}`);
});