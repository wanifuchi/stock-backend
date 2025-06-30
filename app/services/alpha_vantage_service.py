"""
Alpha Vantage API統合サービス
売買判断に必要な技術指標を提供
"""
import os
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .cache_service import cache_service

class AlphaVantageService:
    """Alpha Vantage APIを使った技術指標・株価データサービス"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'
        self.rate_limit_delay = 12  # 500呼び出し/日 ≈ 12秒間隔で安全
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """レート制限対応の待機"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            print(f"レート制限対応: {wait_time:.1f}秒待機")
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """API リクエストの実行"""
        try:
            self._wait_for_rate_limit()
            
            params['apikey'] = self.api_key
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # エラーレスポンスの確認
            if 'Error Message' in data:
                print(f"Alpha Vantage APIエラー: {data['Error Message']}")
                return None
            if 'Note' in data:
                print(f"Alpha Vantage制限メッセージ: {data['Note']}")
                return None
                
            return data
            
        except Exception as e:
            print(f"Alpha Vantage APIリクエストエラー: {str(e)}")
            return None
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        リアルタイム株価取得
        """
        cache_key = f"av_quote_{symbol}"
        cached_data = cache_service.get(symbol, "av_quote")
        if cached_data:
            return cached_data
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        
        try:
            result = {
                "symbol": quote.get('01. symbol', symbol),
                "name": symbol,  # Alpha Vantageからは名前が取得できないため
                "current_price": float(quote.get('05. price', 0)),
                "change": float(quote.get('09. change', 0)),
                "change_percent": quote.get('10. change percent', '0%').replace('%', ''),
                "volume": int(float(quote.get('06. volume', 0))),
                "open": float(quote.get('02. open', 0)),
                "high": float(quote.get('03. high', 0)),
                "low": float(quote.get('04. low', 0)),
                "previous_close": float(quote.get('08. previous close', 0))
            }
            
            # キャッシュに保存（1分間）
            cache_service.set(symbol, "av_quote", result, ttl_minutes=1)
            return result
            
        except (ValueError, KeyError) as e:
            print(f"株価データ解析エラー: {str(e)}")
            return None
    
    def get_rsi(self, symbol: str, time_period: int = 14, interval: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        RSI (Relative Strength Index) 取得
        """
        cache_key = f"av_rsi_{symbol}_{time_period}_{interval}"
        cached_data = cache_service.get(symbol, f"av_rsi_{time_period}_{interval}")
        if cached_data:
            return cached_data
        
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': 'close'
        }
        
        data = self._make_request(params)
        if not data or 'Technical Analysis: RSI' not in data:
            return None
        
        rsi_data = data['Technical Analysis: RSI']
        
        if not rsi_data:
            return None
        
        # 最新のRSI値を取得
        latest_date = max(rsi_data.keys())
        latest_rsi = float(rsi_data[latest_date]['RSI'])
        
        result = {
            "symbol": symbol,
            "rsi": round(latest_rsi, 2),
            "date": latest_date,
            "signal": self._interpret_rsi(latest_rsi)
        }
        
        # キャッシュに保存（15分間）
        cache_service.set(symbol, f"av_rsi_{time_period}_{interval}", result, ttl_minutes=15)
        return result
    
    def get_macd(self, symbol: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, interval: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        MACD (Moving Average Convergence Divergence) 取得
        """
        cache_key = f"av_macd_{symbol}_{fast_period}_{slow_period}_{signal_period}_{interval}"
        cached_data = cache_service.get(symbol, f"av_macd_{fast_period}_{slow_period}_{signal_period}_{interval}")
        if cached_data:
            return cached_data
        
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'fastperiod': str(fast_period),
            'slowperiod': str(slow_period),
            'signalperiod': str(signal_period),
            'series_type': 'close'
        }
        
        data = self._make_request(params)
        if not data or 'Technical Analysis: MACD' not in data:
            return None
        
        macd_data = data['Technical Analysis: MACD']
        
        if not macd_data:
            return None
        
        # 最新のMACD値を取得
        latest_date = max(macd_data.keys())
        latest_macd = macd_data[latest_date]
        
        macd_line = float(latest_macd['MACD'])
        signal_line = float(latest_macd['MACD_Signal'])
        histogram = float(latest_macd['MACD_Hist'])
        
        result = {
            "symbol": symbol,
            "macd": round(macd_line, 4),
            "signal": round(signal_line, 4),
            "histogram": round(histogram, 4),
            "date": latest_date,
            "signal_interpretation": self._interpret_macd(macd_line, signal_line, histogram)
        }
        
        # キャッシュに保存（15分間）
        cache_service.set(symbol, f"av_macd_{fast_period}_{slow_period}_{signal_period}_{interval}", result, ttl_minutes=15)
        return result
    
    def get_bollinger_bands(self, symbol: str, time_period: int = 20, nbdevup: int = 2, nbdevdn: int = 2, interval: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        ボリンジャーバンド取得
        """
        cache_key = f"av_bbands_{symbol}_{time_period}_{nbdevup}_{nbdevdn}_{interval}"
        cached_data = cache_service.get(symbol, f"av_bbands_{time_period}_{nbdevup}_{nbdevdn}_{interval}")
        if cached_data:
            return cached_data
        
        params = {
            'function': 'BBANDS',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': 'close',
            'nbdevup': str(nbdevup),
            'nbdevdn': str(nbdevdn)
        }
        
        data = self._make_request(params)
        if not data or 'Technical Analysis: BBANDS' not in data:
            return None
        
        bbands_data = data['Technical Analysis: BBANDS']
        
        if not bbands_data:
            return None
        
        # 最新のボリンジャーバンド値を取得
        latest_date = max(bbands_data.keys())
        latest_bbands = bbands_data[latest_date]
        
        upper_band = float(latest_bbands['Real Upper Band'])
        middle_band = float(latest_bbands['Real Middle Band'])
        lower_band = float(latest_bbands['Real Lower Band'])
        
        # 現在価格も取得
        current_quote = self.get_stock_quote(symbol)
        current_price = current_quote['current_price'] if current_quote else middle_band
        
        result = {
            "symbol": symbol,
            "upper_band": round(upper_band, 2),
            "middle_band": round(middle_band, 2),
            "lower_band": round(lower_band, 2),
            "current_price": round(current_price, 2),
            "date": latest_date,
            "signal": self._interpret_bollinger_bands(current_price, upper_band, middle_band, lower_band)
        }
        
        # キャッシュに保存（15分間）
        cache_service.set(symbol, f"av_bbands_{time_period}_{nbdevup}_{nbdevdn}_{interval}", result, ttl_minutes=15)
        return result
    
    def _interpret_rsi(self, rsi: float) -> str:
        """RSI解釈"""
        if rsi >= 70:
            return "売りシグナル（買われすぎ）"
        elif rsi <= 30:
            return "買いシグナル（売られすぎ）"
        elif rsi >= 50:
            return "中立（強気傾向）"
        else:
            return "中立（弱気傾向）"
    
    def _interpret_macd(self, macd: float, signal: float, histogram: float) -> str:
        """MACD解釈"""
        if macd > signal and histogram > 0:
            return "買いシグナル（上昇トレンド）"
        elif macd < signal and histogram < 0:
            return "売りシグナル（下降トレンド）"
        elif macd > signal:
            return "中立（上昇傾向）"
        else:
            return "中立（下降傾向）"
    
    def _interpret_bollinger_bands(self, price: float, upper: float, middle: float, lower: float) -> str:
        """ボリンジャーバンド解釈"""
        if price >= upper:
            return "売りシグナル（上限到達）"
        elif price <= lower:
            return "買いシグナル（下限到達）"
        elif price > middle:
            return "中立（上限寄り）"
        else:
            return "中立（下限寄り）"
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        包括的な技術分析（RSI + MACD + ボリンジャーバンド）
        """
        try:
            # 各指標を並行取得
            rsi_data = self.get_rsi(symbol)
            macd_data = self.get_macd(symbol)
            bbands_data = self.get_bollinger_bands(symbol)
            quote_data = self.get_stock_quote(symbol)
            
            # 総合判定
            signals = []
            if rsi_data:
                signals.append(rsi_data['signal'])
            if macd_data:
                signals.append(macd_data['signal_interpretation'])
            if bbands_data:
                signals.append(bbands_data['signal'])
            
            # 買い/売りシグナルのカウント
            buy_signals = sum(1 for s in signals if '買い' in s)
            sell_signals = sum(1 for s in signals if '売り' in s)
            
            # 総合判定ロジック
            if buy_signals >= 2:
                overall_signal = "BUY"
                confidence = min(90, 60 + buy_signals * 10)
            elif sell_signals >= 2:
                overall_signal = "SELL"
                confidence = min(90, 60 + sell_signals * 10)
            else:
                overall_signal = "HOLD"
                confidence = 50
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "quote": quote_data,
                "rsi": rsi_data,
                "macd": macd_data,
                "bollinger_bands": bbands_data,
                "overall_signal": overall_signal,
                "confidence": confidence,
                "analysis_summary": f"{buy_signals}個の買いシグナル, {sell_signals}個の売りシグナル"
            }
            
        except Exception as e:
            print(f"包括的分析エラー: {str(e)}")
            return {
                "symbol": symbol,
                "error": str(e),
                "overall_signal": "ERROR",
                "confidence": 0
            }

# グローバルインスタンス
alpha_vantage_service = AlphaVantageService()