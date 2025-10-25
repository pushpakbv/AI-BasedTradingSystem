"""
ML Model Trainer
Trains supervised models for stock price prediction
"""
import os
import json
import pickle
import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockPredictor:
    """Train and evaluate stock price prediction models"""
    
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "trained_models")
        
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.model = None
        self.feature_names = []
        self.model_type = None
    
    def train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: list
    ) -> xgb.XGBRegressor:
        """Train XGBoost model"""
        logger.info("Training XGBoost model...")
        
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        return model
    
    def train_lightgbm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: list
    ) -> lgb.LGBMRegressor:
        """Train LightGBM model"""
        logger.info("Training LightGBM model...")
        
        model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
        )
        
        return model
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: list
    ) -> RandomForestRegressor:
        """Train Random Forest model"""
        logger.info("Training Random Forest model...")
        
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        return model
    
    def evaluate_model(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """Evaluate model performance"""
        # Predictions
        y_pred = model.predict(X_test)
        
        # Regression metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Direction accuracy (did we predict the right direction?)
        direction_actual = (y_test > 0).astype(int)
        direction_pred = (y_pred > 0).astype(int)
        direction_accuracy = (direction_actual == direction_pred).mean()
        
        metrics = {
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'direction_accuracy': float(direction_accuracy)
        }
        
        logger.info("=" * 70)
        logger.info("MODEL EVALUATION")
        logger.info("=" * 70)
        logger.info(f"RMSE: {rmse:.4f}%")
        logger.info(f"MAE: {mae:.4f}%")
        logger.info(f"R²: {r2:.4f}")
        logger.info(f"Direction Accuracy: {direction_accuracy:.2%}")
        logger.info("=" * 70)
        
        return metrics
    
    def get_feature_importance(self, model, feature_names: list, top_n: int = 20) -> pd.DataFrame:
        """Get feature importance"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        else:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\nTop {top_n} Most Important Features:")
        for idx, row in df.head(top_n).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        
        return df
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: list,
        model_type: str = 'xgboost'
    ):
        """
        Train model with given data
        
        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data
            feature_names: List of feature names
            model_type: 'xgboost', 'lightgbm', or 'random_forest'
        """
        self.feature_names = feature_names
        self.model_type = model_type
        
        logger.info(f"Training {model_type} model...")
        logger.info(f"Training samples: {len(X_train)}")
        logger.info(f"Validation samples: {len(X_val)}")
        logger.info(f"Features: {len(feature_names)}")
        
        if model_type == 'xgboost':
            self.model = self.train_xgboost(X_train, y_train, X_val, y_val, feature_names)
        elif model_type == 'lightgbm':
            self.model = self.train_lightgbm(X_train, y_train, X_val, y_val, feature_names)
        elif model_type == 'random_forest':
            self.model = self.train_random_forest(X_train, y_train, feature_names)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        logger.info("✅ Model training complete")
    
    def save_model(self, model_name: str = 'stock_predictor'):
        """Save trained model"""
        model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
        metadata_path = os.path.join(self.model_dir, f'{model_name}_metadata.json')
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'num_features': len(self.feature_names),
            'trained_at': pd.Timestamp.now().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Model saved to {model_path}")
    
    def load_model(self, model_name: str = 'stock_predictor'):
        """Load trained model"""
        model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
        metadata_path = os.path.join(self.model_dir, f'{model_name}_metadata.json')
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.feature_names = metadata['feature_names']
        self.model_type = metadata['model_type']
        
        logger.info(f"✅ Model loaded from {model_path}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        return self.model.predict(X)


def main():
    """Train and save model"""
    import sys
    sys.path.append('..')
    
    from ml_pipeline.feature_engineer import FeatureEngineer
    
    # Load engineered features
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_training_data')
    data_file = os.path.join(data_dir, 'training_dataset.csv')
    
    if not os.path.exists(data_file):
        print("Training dataset not found. Run historical_data_collector.py first.")
        return
    
    logger.info("Loading data...")
    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    
    # Engineer features
    engineer = FeatureEngineer()
    df = engineer.create_features(df)
    
    # Prepare data
    X, y = engineer.get_feature_importance_data(df)
    
    # Remove any rows with NaN
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    logger.info(f"Total samples: {len(X)}")
    
    # Time-series split (80% train, 10% val, 10% test)
    n = len(X)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    
    # Train model
    predictor = StockPredictor()
    predictor.train_model(
        X_train, y_train,
        X_val, y_val,
        feature_names=engineer.feature_names,
        model_type='xgboost'  # Can also try 'lightgbm' or 'random_forest'
    )
    
    # Evaluate
    metrics = predictor.evaluate_model(predictor.model, X_test, y_test)
    
    # Feature importance
    importance_df = predictor.get_feature_importance(predictor.model, engineer.feature_names, top_n=20)
    
    # Save model
    predictor.save_model('stock_predictor_xgb')
    
    print("\n✅ Model training complete!")
    print(f"Direction Accuracy: {metrics['direction_accuracy']:.2%}")


if __name__ == "__main__":
    main()