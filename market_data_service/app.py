"""
Market Data Service
Provides real-time and historical stock data via REST API
"""
import yfinance as yf
import json
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Companies to track - Extended list with all provided tickers
COMPANIES = [
    'AAPL', 'AMKBY', 'AMZN', 'BABA', 'CHRW', 'DPW_DE', 'FDX', 'GOOGL', 'MSFT', 'NVDA',
    'TSLA', 'UNP', 'UPS', 'XPO',
    # Additional common stocks
    'META', 'NFLX', 'AMD', 'INTC', 'PYPL', 'UBER', 'SPOT', 'ZOOM', 'ROKU', 'RIOT', 'COIN', 'F'
]

def fetch_realtime_stock_data(ticker, period='6mo'):
    """Fetch real-time and historical stock data"""
    try:
        logger.info(f"📊 Fetching realtime data for {ticker}...")
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval='1d')
        
        if hist.empty:
            logger.warning(f"⚠️ No data found for {ticker}")
            return None
        
        # Get current info
        info = stock.info
        
        # Format historical data
        historical_data = []
        for date, row in hist.iterrows():
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
                'adjClose': round(float(row['Adj Close']), 2)
            })
        
        # Calculate change
        current_price = float(hist['Close'].iloc[-1])
        previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close != 0 else 0
        
        stock_data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': round(current_price, 2),
            'previous_close': round(previous_close, 2),
            'day_high': round(float(hist['High'].iloc[-1]), 2),
            'day_low': round(float(hist['Low'].iloc[-1]), 2),
            'fifty_two_week_high': round(info.get('fiftyTwoWeekHigh', 0), 2),
            'fifty_two_week_low': round(info.get('fiftyTwoWeekLow', 0), 2),
            'volume': int(hist['Volume'].iloc[-1]),
            'avg_volume': int(info.get('averageVolume', 0)),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 0,
            'dividend_yield': round(info.get('dividendYield', 0), 4) if info.get('dividendYield') else 0,
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'historical_data': historical_data,
            'lastUpdated': datetime.now().isoformat()
        }
        
        logger.info(f"✅ {ticker}: ${current_price} | {len(historical_data)} data points")
        return stock_data
        
    except Exception as e:
        logger.error(f"❌ Error fetching {ticker}: {str(e)[:100]}")
        return None


@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    """Get real-time stock data for a ticker"""
    ticker = ticker.upper()
    
    # Allow any ticker, not just predefined ones
    data = fetch_realtime_stock_data(ticker)
    
    if not data:
        return jsonify({
            'error': f'Failed to fetch data for {ticker}',
            'ticker': ticker,
            'historical_data': []
        }), 200  # Return 200 even if no data, let frontend handle it
    
    return jsonify(data)


@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    """Get data for all tracked companies"""
    results = {}
    
    for ticker in COMPANIES:
        data = fetch_realtime_stock_data(ticker)
        if data:
            results[ticker] = data
    
    return jsonify(results)


@app.route('/api/stocks/batch', methods=['POST'])
def get_batch_stocks():
    """Get data for a batch of tickers (POST request)"""
    from flask import request
    
    tickers = request.json.get('tickers', [])
    results = {}
    
    for ticker in tickers:
        ticker = ticker.upper()
        data = fetch_realtime_stock_data(ticker)
        if data:
            results[ticker] = data
    
    return jsonify(results)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'market_data_service',
        'supported_tickers': len(COMPANIES),
        'tickers': sorted(COMPANIES)
    })


@app.route('/api/supported-tickers', methods=['GET'])
def get_supported_tickers():
    """Get list of supported tickers"""
    return jsonify({
        'tickers': sorted(COMPANIES),
        'count': len(COMPANIES)
    })


if __name__ == '__main__':
    logger.info("\n" + "="*70)
    logger.info("🚀 MARKET DATA SERVICE STARTING")
    logger.info("="*70)
    logger.info(f"Total Tickers: {len(COMPANIES)}")
    logger.info(f"Tracking: {', '.join(sorted(COMPANIES))}")
    logger.info("="*70 + "\n")
    
    port = int(os.getenv('PORT', 8001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)