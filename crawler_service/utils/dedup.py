"""
URL Deduplication Utility
Provides reusable functions for checking and marking URLs as seen.
"""
import os
import sqlite3
import datetime

# Default database path
DB_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", 
    "data", 
    "dedupe.db"
)
DB_PATH = os.path.abspath(DB_PATH)


def ensure_db():
    """Create deduplication database if it doesn't exist"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_urls (
            url TEXT PRIMARY KEY,
            seen_at TEXT,
            title TEXT,
            status INTEGER
        )
    """)
    conn.commit()
    conn.close()


def is_duplicate(url: str) -> bool:
    """
    Check if URL has been seen before.
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL has been seen, False otherwise
    """
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen_urls WHERE url = ?", (url,))
    found = cur.fetchone() is not None
    if not found:
        cur.execute(
            "INSERT OR IGNORE INTO seen_urls (url, seen_at) VALUES (?, ?)",
            (url, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
    conn.close()
    return found


def mark_as_seen(url: str, title: str = "", status: int = 200):
    """
    Explicitly mark a URL as seen.
    
    Args:
        url: The URL to mark
        title: Optional page title
        status: HTTP status code
    """
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO seen_urls (url, seen_at, title, status) VALUES (?, ?, ?, ?)",
        (url, datetime.datetime.utcnow().isoformat(), title, status)
    )
    conn.commit()
    conn.close()


def get_seen_count() -> int:
    """Return count of URLs in deduplication database"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM seen_urls")
    count = cur.fetchone()[0]
    conn.close()
    return count


def clear_dedupe_db():
    """Clear all entries from deduplication database (use with caution)"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM seen_urls")
    conn.commit()
    conn.close()