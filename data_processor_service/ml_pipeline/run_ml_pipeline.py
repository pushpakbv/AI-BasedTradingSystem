"""
Complete ML Pipeline Runner
1. Collect historical data
2. Engineer features
3. Train model
4. Save for production use
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline.historical_data_collector import HistoricalDataCollector
from ml_pipeline.feature_engineer import FeatureEngineer
from ml_pipeline.model_trainer import StockPredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_complete_ml_pipeline():
    """Execute complete ML training pipeline"""
    
    logger.info("=" * 80)
    logger.info("STARTING COMPLETE ML PIPELINE")
    logger.info("=" * 80)
    
    # Configuration
    tickers = [
        'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'NVDA',
        'META', 'BABA', 'FDX', 'UPS', 'CHRW', 'XPO', 'GXO'
    ]
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 years
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    news_dir = os.path.join(base_dir, "crawler_service", "data", "by_company")
    
    # STEP 1: Collect historical data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: COLLECTING HISTORICAL DATA")
    logger.info("=" * 80)
    
    collector = HistoricalDataCollector()
    df_raw = collector.create_training_dataset(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        news_dir=news_dir
    )
    
    # STEP 2: Feature engineering
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df_raw)
    
    # STEP 3: Prepare training data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: PREPARING TRAINING DATA")
    logger.info("=" * 80)
    
    X, y = engineer.get_feature_importance_data(df_features)
    
    # Remove NaN
    import numpy as np
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    logger.info(f"Total samples: {len(X)}")
    logger.info(f"Features: {len(engineer.feature_names)}")
    
    # Time-series split
    n = len(X)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # STEP 4: Train models
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: TRAINING MODELS")
    logger.info("=" * 80)
    
    # Train XGBoost
    predictor_xgb = StockPredictor()
    predictor_xgb.train_model(
        X_train, y_train,
        X_val, y_val,
        feature_names=engineer.feature_names,
        model_type='xgboost'
    )
    metrics_xgb = predictor_xgb.evaluate_model(predictor_xgb.model, X_test, y_test)
    predictor_xgb.save_model('stock_predictor_xgb')
    
    # Train LightGBM
    predictor_lgb = StockPredictor()
    predictor_lgb.train_model(
        X_train, y_train,
        X_val, y_val,
        feature_names=engineer.feature_names,
        model_type='lightgbm'
    )
    metrics_lgb = predictor_lgb.evaluate_model(predictor_lgb.model, X_test, y_test)
    predictor_lgb.save_model('stock_predictor_lgb')
    
    # STEP 5: Feature importance
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: FEATURE IMPORTANCE ANALYSIS")
    logger.info("=" * 80)
    
    importance_df = predictor_xgb.get_feature_importance(
        predictor_xgb.model,
        engineer.feature_names,
        top_n=30
    )
    
    # Save feature importance
    importance_file = os.path.join(collector.data_dir, 'feature_importance.csv')
    importance_df.to_csv(importance_file, index=False)
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("ML PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nXGBoost Performance:")
    logger.info(f"  Direction Accuracy: {metrics_xgb['direction_accuracy']:.2%}")
    logger.info(f"  RMSE: {metrics_xgb['rmse']:.4f}%")
    logger.info(f"  R²: {metrics_xgb['r2']:.4f}")
    
    logger.info(f"\nLightGBM Performance:")
    logger.info(f"  Direction Accuracy: {metrics_lgb['direction_accuracy']:.2%}")
    logger.info(f"  RMSE: {metrics_lgb['rmse']:.4f}%")
    logger.info(f"  R²: {metrics_lgb['r2']:.4f}")
    
    logger.info("\n✅ Models saved and ready for production!")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_complete_ml_pipeline()