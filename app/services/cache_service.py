"""
キャッシュサービス
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

class CacheService:
    """SQLiteを使ったキャッシュサービス"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / "data" / "stocks.db"
        self.db_path.parent.mkdir(exist_ok=True)
    
    def _get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(str(self.db_path))
    
    def set(self, symbol: str, data_type: str, data: Any, ttl_minutes: int = 60):
        """
        キャッシュにデータを保存
        
        Args:
            symbol: 銘柄コード
            data_type: データタイプ（info, history, indicators, analysis等）
            data: 保存するデータ
            ttl_minutes: キャッシュの有効期限（分）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 有効期限を計算
            expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
            
            # JSONシリアライゼーション
            data_json = json.dumps(data, default=str)
            
            # データを挿入または更新
            cursor.execute("""
                INSERT OR REPLACE INTO stock_cache 
                (symbol, data_type, data, expires_at)
                VALUES (?, ?, ?, ?)
            """, (symbol.upper(), data_type, data_json, expires_at))
            
            conn.commit()
            print(f"キャッシュに保存: {symbol} - {data_type}")
            
        except Exception as e:
            print(f"キャッシュ保存エラー: {str(e)}")
        finally:
            conn.close()
    
    def get(self, symbol: str, data_type: str) -> Optional[Any]:
        """
        キャッシュからデータを取得
        
        Args:
            symbol: 銘柄コード
            data_type: データタイプ
            
        Returns:
            キャッシュされたデータ（有効期限内の場合）またはNone
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 現在時刻より後の有効期限のデータを検索
            cursor.execute("""
                SELECT data FROM stock_cache 
                WHERE symbol = ? AND data_type = ? AND expires_at > ?
            """, (symbol.upper(), data_type, datetime.now()))
            
            result = cursor.fetchone()
            
            if result:
                data_json = result[0]
                data = json.loads(data_json)
                print(f"キャッシュからデータを取得: {symbol} - {data_type}")
                return data
            
            return None
            
        except Exception as e:
            print(f"キャッシュ取得エラー: {str(e)}")
            return None
        finally:
            conn.close()
    
    def delete(self, symbol: str, data_type: Optional[str] = None):
        """
        キャッシュからデータを削除
        
        Args:
            symbol: 銘柄コード
            data_type: データタイプ（Noneの場合、その銘柄の全データを削除）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if data_type:
                cursor.execute("""
                    DELETE FROM stock_cache 
                    WHERE symbol = ? AND data_type = ?
                """, (symbol.upper(), data_type))
            else:
                cursor.execute("""
                    DELETE FROM stock_cache 
                    WHERE symbol = ?
                """, (symbol.upper(),))
            
            conn.commit()
            print(f"キャッシュから削除: {symbol} - {data_type or '全データ'}")
            
        except Exception as e:
            print(f"キャッシュ削除エラー: {str(e)}")
        finally:
            conn.close()
    
    def cleanup_expired(self):
        """
        期限切れのキャッシュデータを削除
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM stock_cache 
                WHERE expires_at <= ?
            """, (datetime.now(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"期限切れキャッシュを削除: {deleted_count}件")
            
        except Exception as e:
            print(f"キャッシュクリーンアップエラー: {str(e)}")
        finally:
            conn.close()
    
    def get_cache_stats(self) -> dict:
        """
        キャッシュの統計情報を取得
        
        Returns:
            キャッシュの統計情報
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 有効なキャッシュ数
            cursor.execute("""
                SELECT COUNT(*) FROM stock_cache 
                WHERE expires_at > ?
            """, (datetime.now(),))
            valid_count = cursor.fetchone()[0]
            
            # 期限切れキャッシュ数
            cursor.execute("""
                SELECT COUNT(*) FROM stock_cache 
                WHERE expires_at <= ?
            """, (datetime.now(),))
            expired_count = cursor.fetchone()[0]
            
            # データタイプ別の統計
            cursor.execute("""
                SELECT data_type, COUNT(*) FROM stock_cache 
                WHERE expires_at > ?
                GROUP BY data_type
            """, (datetime.now(),))
            type_stats = dict(cursor.fetchall())
            
            return {
                "valid_count": valid_count,
                "expired_count": expired_count,
                "type_stats": type_stats
            }
            
        except Exception as e:
            print(f"キャッシュ統計取得エラー: {str(e)}")
            return {
                "valid_count": 0,
                "expired_count": 0,
                "type_stats": {}
            }
        finally:
            conn.close()

# グローバルキャッシュインスタンス
cache_service = CacheService()