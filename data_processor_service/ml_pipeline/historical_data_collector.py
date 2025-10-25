"""
Historical Data Collector
Collects historical stock prices and matches them with news articles
"""
import os
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalDataCollector:
    """Collects and aligns historical news with stock price movements"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "ml_training_data")
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def get_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Download historical stock data
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Downloading {ticker} data from {start_date} to {end_date}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return pd.DataFrame()
            
            # Calculate technical indicators
            df = self._add_technical_indicators(df)
            
            # Calculate next-day returns (target variable)
            df['next_day_return'] = df['Close'].pct_change().shift(-1) * 100
            df['next_day_direction'] = (df['next_day_return'] > 0).astype(int)
            
            logger.info(f"✅ Downloaded {len(df)} days of {ticker} data")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators as features"""
        # Returns
        df['return_1d'] = df['Close'].pct_change() * 100
        df['return_5d'] = df['Close'].pct_change(5) * 100
        df['return_20d'] = df['Close'].pct_change(20) * 100
        
        # Volatility
        df['volatility_5d'] = df['return_1d'].rolling(5).std()
        df['volatility_20d'] = df['return_1d'].rolling(20).std()
        
        # Moving averages
        df['sma_5'] = df['Close'].rolling(5).mean()
        df['sma_20'] = df['Close'].rolling(20).mean()
        df['sma_50'] = df['Close'].rolling(50).mean()
        
        # Price relative to moving averages
        df['price_vs_sma5'] = (df['Close'] / df['sma_5'] - 1) * 100
        df['price_vs_sma20'] = (df['Close'] / df['sma_20'] - 1) * 100
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume indicators
        df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        return df
    
    def match_news_to_prices(
        self,
        ticker: str,
        news_dir: str,
        stock_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Match news articles to stock prices
        
        Args:
            ticker: Stock ticker
            news_dir: Directory with historical news (by_company/TICKER/)
            stock_df: DataFrame with stock prices
            
        Returns:
            DataFrame with news features added
        """
        # Initialize news feature columns
        stock_df['has_news'] = 0
        stock_df['general_sentiment'] = 0.0
        stock_df['financial_signal'] = 0.0
        stock_df['num_articles'] = 0
        stock_df['positive_articles'] = 0
        stock_df['negative_articles'] = 0
        
        ticker_news_dir = os.path.join(news_dir, ticker)
        
        if not os.path.exists(ticker_news_dir):
            logger.warning(f"No news data found for {ticker}")
            return stock_df
        
        # Process each date folder
        for date_folder in os.listdir(ticker_news_dir):
            date_path = os.path.join(ticker_news_dir, date_folder)
            
            if not os.path.isdir(date_path):
                continue
            
            try:
                article_date = pd.to_datetime(date_folder)
                
                # Skip if date not in stock data
                if article_date not in stock_df.index:
                    continue
                
                # Load all articles for this date
                articles = []
                for article_file in os.listdir(date_path):
                    if article_file.endswith('.json'):
                        with open(os.path.join(date_path, article_file), 'r', encoding='utf-8') as f:
                            articles.append(json.load(f))
                
                if not articles:
                    continue
                
                # Extract features from articles
                sentiment_scores = []
                financial_scores = []
                positive_count = 0
                negative_count = 0
                
                for article in articles:
                    # Get sentiment (if available)
                    if 'sentiment_analysis' in article:
                        sent = article['sentiment_analysis']['overall']
                        sentiment_scores.append(sent['score'])
                        
                        if sent['label'] == 'positive':
                            positive_count += 1
                        elif sent['label'] == 'negative':
                            negative_count += 1
                    
                    # Get financial signal (if available)
                    if 'financial_analysis' in article:
                        fin = article['financial_analysis']
                        signal = fin.get('market_signal', 'NEUTRAL')
                        
                        if signal == 'POSITIVE':
                            financial_scores.append(0.5)
                        elif signal == 'NEGATIVE':
                            financial_scores.append(-0.5)
                        else:
                            financial_scores.append(0.0)
                
                # Update stock_df with news features
                stock_df.loc[article_date, 'has_news'] = 1
                stock_df.loc[article_date, 'num_articles'] = len(articles)
                stock_df.loc[article_date, 'positive_articles'] = positive_count
                stock_df.loc[article_date, 'negative_articles'] = negative_count
                
                if sentiment_scores:
                    stock_df.loc[article_date, 'general_sentiment'] = sum(sentiment_scores) / len(sentiment_scores)
                
                if financial_scores:
                    stock_df.loc[article_date, 'financial_signal'] = sum(financial_scores) / len(financial_scores)
                
            except Exception as e:
                logger.error(f"Error processing {date_folder}: {e}")
        
        logger.info(f"📰 Matched news to {stock_df['has_news'].sum()} days")
        return stock_df
    
    def create_training_dataset(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        news_dir: str
    ) -> pd.DataFrame:
        """
        Create complete training dataset for multiple tickers
        
        Args:
            tickers: List of stock tickers
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            news_dir: Directory with historical news
            
        Returns:
            Combined DataFrame with all features
        """
        all_data = []
        
        for ticker in tickers:
            logger.info(f"Processing {ticker}...")
            
            # Get stock data
            stock_df = self.get_stock_data(ticker, start_date, end_date)
            
            if stock_df.empty:
                continue
            
            # Match news
            stock_df = self.match_news_to_prices(ticker, news_dir, stock_df)
            
            # Add ticker column
            stock_df['ticker'] = ticker
            
            all_data.append(stock_df)
        
        # Combine all tickers
        combined_df = pd.concat(all_data, ignore_index=False)
        
        # Drop rows with NaN in target variable
        combined_df = combined_df.dropna(subset=['next_day_return'])
        
        # Save to CSV
        output_file = os.path.join(self.data_dir, 'training_dataset.csv')
        combined_df.to_csv(output_file)
        
        logger.info("=" * 70)
        logger.info("TRAINING DATASET CREATED")
        logger.info(f"Total samples: {len(combined_df)}")
        logger.info(f"Samples with news: {combined_df['has_news'].sum()}")
        logger.info(f"Date range: {combined_df.index.min()} to {combined_df.index.max()}")
        logger.info(f"Saved to: {output_file}")
        logger.info("=" * 70)
        
        return combined_df


def main():
    """Create historical training dataset"""
    collector = HistoricalDataCollector()
    
    # Define tickers to collect
    tickers = [
        'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'NVDA',
        'META', 'BABA', 'FDX', 'UPS', 'CHRW', 'XPO'
    ]
    
    # Date range (last 2 years)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    # Path to historical news
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    news_dir = os.path.join(base_dir, "crawler_service", "data", "by_company")
    
    # Create dataset
    df = collector.create_training_dataset(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        news_dir=news_dir
    )
    
    print(f"\n✅ Training dataset ready!")
    print(f"Shape: {df.shape}")
    print(f"\nFeature columns:")
    print(df.columns.tolist())


if __name__ == "__main__":
    main()