const fs = require('fs').promises;
const path = require('path');

const CRAWLER_DATA_DIR = path.join(__dirname, '..', 'crawler_service', 'data', 'by_company');

class ArticleReader {
  /**
   * Get articles for a specific ticker
   */
  static async getArticlesForTicker(ticker, limit = 10) {
    try {
      const tickerDir = path.join(CRAWLER_DATA_DIR, ticker);
      
      // Check if directory exists
      try {
        await fs.access(tickerDir);
      } catch (e) {
        console.warn(`⚠️ No data directory for ${ticker}`);
        return [];
      }

      const articles = [];

      // Read all date directories
      const dateDirs = await fs.readdir(tickerDir);

      for (const dateDir of dateDirs) {
        const datePath = path.join(tickerDir, dateDir);
        
        try {
          const stat = await fs.stat(datePath);
          if (!stat.isDirectory()) continue;
        } catch (e) {
          continue;
        }

        // Read all article files in this date directory
        let files = [];
        try {
          files = await fs.readdir(datePath);
        } catch (e) {
          console.warn(`⚠️ Failed to read directory ${datePath}`);
          continue;
        }

        for (const file of files) {
          if (!file.endsWith('.json')) continue;

          try {
            const filePath = path.join(datePath, file);
            const data = await fs.readFile(filePath, 'utf8');
            const article = JSON.parse(data);

            articles.push({
              id: file.replace('.json', ''),
              ticker,
              title: article.title || 'No Title',
              summary: article.meta_description || article.content?.substring(0, 150) || 'No summary available',
              content: article.content || '',
              url: article.url || '',
              source: article.source_domain || article.source || 'Unknown Source',
              published_date: article.published_date || dateDir,
              published_at: article.published_datetime || new Date().toISOString(),
              word_count: article.word_count || 0,
              sentiment: article.sentiment || null
            });
          } catch (e) {
            console.warn(`⚠️ Failed to read article ${file}:`, e.message);
          }
        }
      }

      // Sort by date (newest first) and limit
      const sorted = articles
        .sort((a, b) => new Date(b.published_at) - new Date(a.published_at))
        .slice(0, limit);

      console.log(`✅ Retrieved ${sorted.length} articles for ${ticker}`);
      return sorted;
    } catch (error) {
      console.error(`❌ Error reading articles for ${ticker}:`, error.message);
      return [];
    }
  }

  /**
   * Get articles by type (financial vs general)
   */
  static async getArticlesByType(ticker, type = 'all', limit = 10) {
    try {
      const articles = await this.getArticlesForTicker(ticker, limit * 3);

      if (!articles || articles.length === 0) {
        console.warn(`⚠️ No articles found for ${ticker}`);
        return [];
      }

      // Filter by type if specified
      if (type === 'financial') {
        const financialKeywords = [
          'earnings', 'revenue', 'profit', 'guidance', 'beat', 'miss', 
          'forecast', 'results', 'dividend', 'split', 'fiscal', 'quarter',
          'quarterly', 'annual', 'ipo', 'stock', 'share', 'price',
          'analyst', 'upgrade', 'downgrade', 'rating', 'target',
          'debt', 'cash', 'margin', 'ebitda', 'roe', 'eps'
        ];

        const filtered = articles.filter(a => {
          const text = `${a.title} ${a.summary}`.toLowerCase();
          return financialKeywords.some(kw => text.includes(kw));
        }).slice(0, limit);

        console.log(`✅ Retrieved ${filtered.length} financial articles for ${ticker}`);
        return filtered;
      } 
      else if (type === 'general') {
        const filtered = articles.slice(0, limit);
        console.log(`✅ Retrieved ${filtered.length} general articles for ${ticker}`);
        return filtered;
      }

      return articles.slice(0, limit);
    } catch (error) {
      console.error(`❌ Error filtering articles for ${ticker}:`, error.message);
      return [];
    }
  }

  /**
   * Get all articles across all tickers
   */
  static async getAllArticles(limit = 50) {
    try {
      const articles = [];
      
      // Read all ticker directories
      const tickers = await fs.readdir(CRAWLER_DATA_DIR);

      for (const ticker of tickers) {
        const tickerPath = path.join(CRAWLER_DATA_DIR, ticker);
        const stat = await fs.stat(tickerPath);

        if (!stat.isDirectory()) continue;

        const tickerArticles = await this.getArticlesForTicker(ticker, 10);
        articles.push(...tickerArticles);
      }

      // Sort by date (newest first) and limit
      return articles
        .sort((a, b) => new Date(b.published_at) - new Date(a.published_at))
        .slice(0, limit);
    } catch (error) {
      console.error('❌ Error reading all articles:', error.message);
      return [];
    }
  }

  /**
   * Search articles by keyword
   */
  static async searchArticles(ticker, keyword, limit = 10) {
    try {
      const articles = await this.getArticlesForTicker(ticker, limit * 5);
      const keywordLower = keyword.toLowerCase();

      const filtered = articles.filter(a => {
        const text = `${a.title} ${a.summary} ${a.content}`.toLowerCase();
        return text.includes(keywordLower);
      }).slice(0, limit);

      console.log(`✅ Found ${filtered.length} articles matching "${keyword}" for ${ticker}`);
      return filtered;
    } catch (error) {
      console.error(`❌ Error searching articles for ${ticker}:`, error.message);
      return [];
    }
  }

  /**
   * Get article statistics for a ticker
   */
  static async getArticleStats(ticker) {
    try {
      const articles = await this.getArticlesForTicker(ticker, 1000);

      const stats = {
        ticker,
        total_articles: articles.length,
        date_range: {
          oldest: articles.length > 0 ? articles[articles.length - 1].published_date : null,
          newest: articles.length > 0 ? articles[0].published_date : null
        },
        average_word_count: articles.length > 0 
          ? Math.round(articles.reduce((sum, a) => sum + a.word_count, 0) / articles.length)
          : 0,
        sources: [...new Set(articles.map(a => a.source))],
        source_count: new Set(articles.map(a => a.source)).size
      };

      return stats;
    } catch (error) {
      console.error(`❌ Error getting stats for ${ticker}:`, error.message);
      return null;
    }
  }
}

module.exports = ArticleReader;