"""
非同期キャッシュサービス
Geminiの提案による非同期DB操作の実装
"""
import aiosqlite
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


class AsyncCacheService:
    """aiosqliteを使った非同期キャッシュサービス"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / "data" / "async_stocks.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialized = False
    
    async def _initialize_db(self):
        """データベースの初期化"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(str(self.db_path)) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, data_type)
                )
            """)
            
            # インデックス作成
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_type 
                ON stock_cache(symbol, data_type)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON stock_cache(expires_at)
            """)
            
            await conn.commit()
        
        self._initialized = True
        print("非同期キャッシュデータベースを初期化しました")
    
    async def set(self, symbol: str, data_type: str, data: Any, ttl_minutes: int = 60):
        """
        キャッシュにデータを非同期保存
        
        Args:
            symbol: 銘柄コード
            data_type: データタイプ（info, history, indicators, analysis等）
            data: 保存するデータ
            ttl_minutes: キャッシュの有効期限（分）
        """
        await self._initialize_db()
        
        try:
            # 有効期限を計算
            expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
            
            # JSONシリアライゼーション
            data_json = json.dumps(data, default=str)
            
            async with aiosqlite.connect(str(self.db_path)) as conn:
                # データを挿入または更新
                await conn.execute("""
                    INSERT OR REPLACE INTO stock_cache 
                    (symbol, data_type, data, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (symbol.upper(), data_type, data_json, expires_at))
                
                await conn.commit()
                print(f"非同期キャッシュに保存: {symbol} - {data_type}")
        
        except Exception as e:
            print(f"非同期キャッシュ保存エラー: {str(e)}")
    
    async def get(self, symbol: str, data_type: str) -> Optional[Any]:
        """
        キャッシュからデータを非同期取得
        
        Args:
            symbol: 銘柄コード
            data_type: データタイプ
            
        Returns:
            キャッシュされたデータまたはNone
        """
        await self._initialize_db()
        
        try:
            async with aiosqlite.connect(str(self.db_path)) as conn:
                async with conn.execute("""
                    SELECT data, expires_at FROM stock_cache 
                    WHERE symbol = ? AND data_type = ? AND expires_at > ?
                """, (symbol.upper(), data_type, datetime.now())) as cursor:
                    
                    row = await cursor.fetchone()
                    if row:
                        data_json, expires_at = row
                        print(f"非同期キャッシュヒット: {symbol} - {data_type}")
                        return json.loads(data_json)
                    else:
                        print(f"非同期キャッシュミス: {symbol} - {data_type}")
                        return None
        
        except Exception as e:
            print(f"非同期キャッシュ取得エラー: {str(e)}")
            return None
    
    async def cleanup_expired(self):
        """
        期限切れキャッシュを非同期削除
        """
        await self._initialize_db()
        
        try:
            async with aiosqlite.connect(str(self.db_path)) as conn:
                cursor = await conn.execute("""
                    DELETE FROM stock_cache WHERE expires_at <= ?
                """, (datetime.now(),))
                
                deleted_count = cursor.rowcount
                await conn.commit()
                
                if deleted_count > 0:
                    print(f"期限切れキャッシュを{deleted_count}件削除しました")
        
        except Exception as e:
            print(f"期限切れキャッシュ削除エラー: {str(e)}")
    
    async def get_cache_stats(self) -> dict:
        """
        キャッシュ統計情報を取得
        """
        await self._initialize_db()
        
        try:
            async with aiosqlite.connect(str(self.db_path)) as conn:
                # 総キャッシュ数
                async with conn.execute("SELECT COUNT(*) FROM stock_cache") as cursor:
                    total_cache = (await cursor.fetchone())[0]
                
                # 有効キャッシュ数
                async with conn.execute("""
                    SELECT COUNT(*) FROM stock_cache WHERE expires_at > ?
                """, (datetime.now(),)) as cursor:
                    valid_cache = (await cursor.fetchone())[0]
                
                # データタイプ別統計
                async with conn.execute("""
                    SELECT data_type, COUNT(*) FROM stock_cache 
                    WHERE expires_at > ? GROUP BY data_type
                """, (datetime.now(),)) as cursor:
                    type_stats = await cursor.fetchall()
                
                return {
                    "total_cache": total_cache,
                    "valid_cache": valid_cache,
                    "expired_cache": total_cache - valid_cache,
                    "type_breakdown": dict(type_stats)
                }
        
        except Exception as e:
            print(f"キャッシュ統計取得エラー: {str(e)}")
            return {}


# グローバル非同期キャッシュインスタンス
async_cache_service = AsyncCacheService()