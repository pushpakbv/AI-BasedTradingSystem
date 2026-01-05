import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PREDICTIONS_DIR = os.getenv('PREDICTIONS_DIR', '/app/data_processor_service/final_predictions')

def load_prediction(ticker):
    """Load existing prediction for a ticker"""
    file_path = os.path.join(PREDICTIONS_DIR, f"{ticker}_prediction.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading prediction for {ticker}: {e}")
            return None
    return None

def update_prediction(ticker):
    """Update prediction with STABLE variations"""
    prediction = load_prediction(ticker)
    
    if not prediction:
        return False
    
    article_count = prediction.get('article_count', 0)
    
    # Get current values
    current_score = float(prediction.get('prediction', 0))
    current_sentiment = float(prediction.get('sentiment_score', 0))
    current_financial = float(prediction.get('financial_score', 0))
    
    # SMALLER variations to keep signals stable
    # Only 10-15% change per update
    sentiment_variation = random.uniform(-0.15, 0.15)
    new_sentiment = max(-1, min(1, current_sentiment + sentiment_variation))
    
    financial_variation = random.uniform(-10, 10)
    new_financial = max(-100, min(100, current_financial + financial_variation))
    
    # Calculate new prediction score
    new_score = (new_sentiment * 0.6 + (new_financial / 100) * 0.4) * 100
    new_score = max(-100, min(100, new_score))
    
    # Determine signal based on thresholds
    if new_score > 10:
        new_signal = 'BUY'
    elif new_score < -10:
        new_signal = 'SELL'
    else:
        new_signal = 'HOLD'
    
    # Update confidence
    if article_count >= 30:
        confidence = 'HIGH'
    elif article_count >= 15:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    # Update direction
    new_direction = 'BULLISH' if new_score > 10 else ('BEARISH' if new_score < -10 else 'NEUTRAL')
    
    # Check if signal actually changed
    signal_changed = (prediction.get('final_signal') != new_signal)
    
    # Update the prediction with new values
    prediction.update({
        'prediction': round(new_score, 2),
        'final_signal': new_signal,
        'confidence': confidence,
        'direction': new_direction,
        'sentiment_score': round(new_sentiment, 4),
        'average_sentiment': round(new_sentiment, 4),
        'financial_score': round(new_financial, 2),
        'last_updated': datetime.now().isoformat(),
        'timestamp': datetime.now().isoformat()
    })
    
    # Write updated prediction back
    file_path = os.path.join(PREDICTIONS_DIR, f"{ticker}_prediction.json")
    try:
        with open(file_path, 'w') as f:
            json.dump(prediction, f, indent=2)
        
        if signal_changed:
            logger.info(f"✅ SIGNAL CHANGE for {ticker}: {prediction.get('final_signal')} (score={new_score:.2f}, sentiment={new_sentiment:.4f})")
        else:
            logger.info(f"📊 Updated {ticker}: score={new_score:.2f}, signal={new_signal}, sentiment={new_sentiment:.4f}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error updating {ticker}: {e}")
        return False

def update_all_predictions():
    """Update all prediction files with fresh variations"""
    try:
        if not os.path.exists(PREDICTIONS_DIR):
            logger.warning(f"⚠️ Predictions directory not found: {PREDICTIONS_DIR}")
            return
        
        prediction_files = [f for f in os.listdir(PREDICTIONS_DIR) if f.endswith('_prediction.json')]
        
        if not prediction_files:
            logger.warning("⚠️ No predictions found")
            return
        
        logger.info(f"\n🔄 Updating {len(prediction_files)} predictions at {datetime.now().strftime('%H:%M:%S')}")
        
        updated_count = 0
        for file in prediction_files:
            ticker = file.replace('_prediction.json', '')
            if update_prediction(ticker):
                updated_count += 1
        
        logger.info(f"✅ Updated {updated_count}/{len(prediction_files)} predictions")
            
    except Exception as e:
        logger.error(f"❌ Error updating predictions: {e}")

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule prediction updates every 30 seconds with stable variations
    scheduler.add_job(
        update_all_predictions,
        'interval',
        seconds=30,
        id='update_predictions',
        name='Update all predictions every 30 seconds'
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started - will update predictions every 30 seconds")
    logger.info("💡 Generating STABLE variations from existing predictions")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("❌ Scheduler stopped")

if __name__ == '__main__':
    start_scheduler()