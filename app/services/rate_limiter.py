"""
レート制限・リトライ管理サービス
Geminiの提案による指数バックオフの実装
"""
import time
import asyncio
import random
from typing import Callable, Any, Optional
from functools import wraps


class RateLimiter:
    """レート制限とリトライ機能を提供するクラス"""
    
    def __init__(self, requests_per_minute: int = 5, max_retries: int = 3):
        self.requests_per_minute = requests_per_minute
        self.max_retries = max_retries
        self.request_times = []
        self.min_interval = 60.0 / requests_per_minute  # 最小間隔（秒）
    
    def _wait_for_rate_limit(self):
        """レート制限に従って待機"""
        current_time = time.time()
        
        # 1分以内のリクエストをフィルタ
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            # レート制限に達している場合、最古のリクエストから1分経過まで待機
            oldest_request = self.request_times[0]
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                print(f"レート制限: {wait_time:.1f}秒待機")
                time.sleep(wait_time)
        
        # 最小間隔の確保
        if self.request_times and current_time - self.request_times[-1] < self.min_interval:
            wait_time = self.min_interval - (current_time - self.request_times[-1])
            print(f"最小間隔確保: {wait_time:.1f}秒待機")
            time.sleep(wait_time)
        
        # リクエスト時刻を記録
        self.request_times.append(time.time())
    
    def exponential_backoff_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        指数バックオフによるリトライ機能
        
        Args:
            func: 実行する関数
            *args, **kwargs: 関数の引数
            
        Returns:
            関数の実行結果
            
        Raises:
            最後の試行で発生した例外
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self._wait_for_rate_limit()
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # 最後の試行の場合は例外を再発生
                if attempt == self.max_retries:
                    break
                
                # 指数バックオフ計算（ジッターあり）
                base_delay = 2 ** attempt  # 1, 2, 4秒...
                jitter = random.uniform(0.1, 0.5)  # ランダムな遅延を追加
                delay = base_delay + jitter
                
                # 特定のエラーの場合のみリトライ
                if self._should_retry(e):
                    print(f"リトライ {attempt + 1}/{self.max_retries}: {delay:.1f}秒後に再試行 (エラー: {str(e)})")
                    time.sleep(delay)
                else:
                    # リトライしないエラーの場合は即座に例外を再発生
                    break
        
        raise last_exception
    
    def _should_retry(self, exception: Exception) -> bool:
        """
        リトライすべき例外かどうかを判定
        
        Args:
            exception: 発生した例外
            
        Returns:
            リトライする場合はTrue
        """
        error_str = str(exception).lower()
        
        # リトライすべきエラーパターン
        retryable_errors = [
            '429',  # Too Many Requests
            'timeout',
            'connection',
            'network',
            'temporary failure',
            'rate limit',
            'quota exceeded'
        ]
        
        return any(pattern in error_str for pattern in retryable_errors)


class AsyncRateLimiter:
    """非同期版レート制限クラス"""
    
    def __init__(self, requests_per_minute: int = 5, max_retries: int = 3):
        self.requests_per_minute = requests_per_minute
        self.max_retries = max_retries
        self.request_times = []
        self.min_interval = 60.0 / requests_per_minute
    
    async def _wait_for_rate_limit(self):
        """非同期レート制限待機"""
        current_time = time.time()
        
        # 1分以内のリクエストをフィルタ
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                print(f"非同期レート制限: {wait_time:.1f}秒待機")
                await asyncio.sleep(wait_time)
        
        # 最小間隔の確保
        if self.request_times and current_time - self.request_times[-1] < self.min_interval:
            wait_time = self.min_interval - (current_time - self.request_times[-1])
            print(f"非同期最小間隔確保: {wait_time:.1f}秒待機")
            await asyncio.sleep(wait_time)
        
        self.request_times.append(time.time())
    
    async def exponential_backoff_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        非同期指数バックオフリトライ
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                await self._wait_for_rate_limit()
                
                # 非同期関数の場合はawait
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # 指数バックオフ
                base_delay = 2 ** attempt
                jitter = random.uniform(0.1, 0.5)
                delay = base_delay + jitter
                
                if self._should_retry(e):
                    print(f"非同期リトライ {attempt + 1}/{self.max_retries}: {delay:.1f}秒後に再試行")
                    await asyncio.sleep(delay)
                else:
                    break
        
        raise last_exception
    
    def _should_retry(self, exception: Exception) -> bool:
        """リトライ判定（同期版と同じ）"""
        error_str = str(exception).lower()
        retryable_errors = [
            '429', 'timeout', 'connection', 'network',
            'temporary failure', 'rate limit', 'quota exceeded'
        ]
        return any(pattern in error_str for pattern in retryable_errors)


# グローバルレート制限インスタンス
yfinance_limiter = RateLimiter(requests_per_minute=10, max_retries=3)
alpha_vantage_limiter = RateLimiter(requests_per_minute=5, max_retries=3)
async_yfinance_limiter = AsyncRateLimiter(requests_per_minute=10, max_retries=3)
async_alpha_vantage_limiter = AsyncRateLimiter(requests_per_minute=5, max_retries=3)