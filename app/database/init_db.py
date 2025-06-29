"""
データベース初期化
"""
import sqlite3
import os
from pathlib import Path

def init_database():
    """
    SQLiteデータベースの初期化
    """
    # データベースディレクトリの作成
    db_dir = Path(__file__).parent.parent.parent / "data"
    db_dir.mkdir(exist_ok=True)
    
    db_path = db_dir / "stocks.db"
    
    # データベース接続
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            data_type TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            UNIQUE(symbol, data_type)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            confidence REAL NOT NULL,
            reasoning TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # インデックスの作成
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_symbol ON stock_cache(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON stock_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_user ON user_watchlist(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_history(symbol)')
    
    conn.commit()
    conn.close()
    
    print(f"データベースを初期化しました: {db_path}")