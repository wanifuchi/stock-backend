"""
株式データサービス
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
from .cache_service import cache_service

class StockService:
    """株式データの取得と分析を行うサービス"""
    
    def __init__(self):
        self.cache = {}  # シンプルなメモリキャッシュ
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        株式銘柄を検索
        """
        # yfinanceでは直接検索APIはないため、一般的な銘柄のリストから検索
        # 実際の実装では、別途銘柄リストDBを用意するのが良い
        common_stocks = {
            "AAPL": "Apple Inc.",
            "GOOGL": "Alphabet Inc.",
            "MSFT": "Microsoft Corporation",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "JPM": "JPMorgan Chase & Co.",
            "V": "Visa Inc.",
            "JNJ": "Johnson & Johnson",
            "WMT": "Walmart Inc.",
            "PG": "Procter & Gamble Co.",
            "DIS": "The Walt Disney Company",
            "MA": "Mastercard Inc.",
            "HD": "The Home Depot Inc.",
            "BAC": "Bank of America Corp.",
            "NFLX": "Netflix Inc.",
            "ADBE": "Adobe Inc.",
            "CRM": "Salesforce Inc.",
            "PFE": "Pfizer Inc."
        }
        
        results = []
        query_upper = query.upper()
        
        for symbol, name in common_stocks.items():
            if query_upper in symbol or query.lower() in name.lower():
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": "NASDAQ" if symbol in ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM"] else "NYSE"
                })
        
        return results[:10]  # 最大10件まで返す
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        指定銘柄の現在情報を取得
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "stock_info")
        if cached_data:
            return cached_data
        
        try:
            print(f"株式情報を取得中: {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            print(f"info取得完了: {len(info)} 項目")
            
            # 最新の価格データを取得
            hist = ticker.history(period="1d", interval="1m")
            print(f"履歴データ取得(1d): {len(hist)} 行")
            if hist.empty:
                hist = ticker.history(period="5d")
                print(f"履歴データ取得(5d): {len(hist)} 行")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = info.get('previousClose', current_price)
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                volume = int(hist['Volume'].iloc[-1])
            else:
                current_price = info.get('currentPrice', 0)
                prev_close = info.get('previousClose', current_price)
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                volume = info.get('volume', 0)
            
            result = {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol),
                "current_price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": volume,
                "market_cap": info.get('marketCap')
            }
            
            # キャッシュに保存（5分間）
            cache_service.set(symbol, "stock_info", result, ttl_minutes=5)
            return result
        except Exception as e:
            error_message = f"株式情報取得エラー: {str(e)}"
            print(error_message)
            import traceback
            print(f"詳細なエラー: {traceback.format_exc()}")
            return {
                "symbol": symbol.upper(),
                "name": f"Error: {str(e)}",
                "current_price": 0,
                "change": 0,
                "change_percent": 0,
                "volume": 0,
                "market_cap": None
            }
    
    def get_price_history(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """
        株価履歴データを取得
        """
        # キャッシュから取得を試行
        cache_key = f"price_history_{period}"
        cached_data = cache_service.get(symbol, cache_key)
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {
                    "symbol": symbol.upper(),
                    "dates": [],
                    "prices": [],
                    "volumes": []
                }
            
            # 日付を文字列に変換
            dates = [date.strftime("%Y-%m-%d") for date in hist.index]
            prices = [round(price, 2) for price in hist['Close'].tolist()]
            volumes = [int(vol) for vol in hist['Volume'].tolist()]
            
            result = {
                "symbol": symbol.upper(),
                "dates": dates,
                "prices": prices,
                "volumes": volumes
            }
            
            # キャッシュに保存（60分間）
            cache_service.set(symbol, cache_key, result, ttl_minutes=60)
            return result
        except Exception as e:
            print(f"価格履歴取得エラー: {str(e)}")
            return {
                "symbol": symbol.upper(),
                "dates": [],
                "prices": [],
                "volumes": []
            }
    
    def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        テクニカル指標を計算
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "technical_indicators")
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            # 3ヶ月分のデータを取得（テクニカル指標計算に十分なデータ量）
            hist = ticker.history(period="3mo")
            
            if len(hist) < 20:  # 最低限のデータがない場合
                return {
                    "symbol": symbol.upper(),
                    "rsi": None,
                    "macd": None,
                    "bollinger_bands": None,
                    "moving_averages": None
                }
            
            # RSI計算（14日）
            rsi = RSIIndicator(close=hist['Close'], window=14)
            current_rsi = rsi.rsi().iloc[-1]
            
            # MACD計算
            macd = MACD(close=hist['Close'])
            macd_line = macd.macd().iloc[-1]
            signal_line = macd.macd_signal().iloc[-1]
            macd_histogram = macd.macd_diff().iloc[-1]
            
            # ボリンジャーバンド計算（20日）
            bb = BollingerBands(close=hist['Close'], window=20, window_dev=2)
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_middle = bb.bollinger_mavg().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            
            # 移動平均線計算
            sma_20 = SMAIndicator(close=hist['Close'], window=20).sma_indicator().iloc[-1]
            sma_50 = SMAIndicator(close=hist['Close'], window=50).sma_indicator().iloc[-1] if len(hist) >= 50 else None
            sma_200 = SMAIndicator(close=hist['Close'], window=200).sma_indicator().iloc[-1] if len(hist) >= 200 else None
            
            result = {
                "symbol": symbol.upper(),
                "rsi": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
                "macd": {
                    "macd": round(macd_line, 2) if not pd.isna(macd_line) else None,
                    "signal": round(signal_line, 2) if not pd.isna(signal_line) else None,
                    "histogram": round(macd_histogram, 2) if not pd.isna(macd_histogram) else None
                },
                "bollinger_bands": {
                    "upper": round(bb_upper, 2) if not pd.isna(bb_upper) else None,
                    "middle": round(bb_middle, 2) if not pd.isna(bb_middle) else None,
                    "lower": round(bb_lower, 2) if not pd.isna(bb_lower) else None
                },
                "moving_averages": {
                    "sma_20": round(sma_20, 2) if not pd.isna(sma_20) else None,
                    "sma_50": round(sma_50, 2) if sma_50 and not pd.isna(sma_50) else None,
                    "sma_200": round(sma_200, 2) if sma_200 and not pd.isna(sma_200) else None
                }
            }
            
            # キャッシュに保存（30分間）
            cache_service.set(symbol, "technical_indicators", result, ttl_minutes=30)
            return result
        except Exception as e:
            print(f"テクニカル指標計算エラー: {str(e)}")
            return {
                "symbol": symbol.upper(),
                "rsi": None,
                "macd": None,
                "bollinger_bands": None,
                "moving_averages": None
            }
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        AIによる株式分析（簡易版）
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "stock_analysis")
        if cached_data:
            return cached_data
        
        try:
            # テクニカル指標を取得
            indicators = self.calculate_technical_indicators(symbol)
            current_info = self.get_stock_info(symbol)
            
            # 簡易的な分析ロジック
            recommendation = "HOLD"
            confidence = 0.5
            reasoning = []
            
            # RSI分析
            if indicators["rsi"]:
                if indicators["rsi"] < 30:
                    recommendation = "BUY"
                    confidence += 0.2
                    reasoning.append("RSIが30以下で売られすぎの状態")
                elif indicators["rsi"] > 70:
                    recommendation = "SELL"
                    confidence += 0.2
                    reasoning.append("RSIが70以上で買われすぎの状態")
                else:
                    reasoning.append("RSIは中立領域")
            
            # MACD分析
            if indicators["macd"] and indicators["macd"]["macd"] and indicators["macd"]["signal"]:
                if indicators["macd"]["macd"] > indicators["macd"]["signal"]:
                    if recommendation != "SELL":
                        recommendation = "BUY"
                        confidence += 0.15
                    reasoning.append("MACDがシグナルラインを上回り、上昇トレンド")
                else:
                    if recommendation != "BUY":
                        recommendation = "SELL"
                        confidence += 0.15
                    reasoning.append("MACDがシグナルラインを下回り、下降トレンド")
            
            # 移動平均線分析
            if indicators["moving_averages"]["sma_20"] and indicators["moving_averages"]["sma_50"]:
                if indicators["moving_averages"]["sma_20"] > indicators["moving_averages"]["sma_50"]:
                    if recommendation != "SELL":
                        confidence += 0.1
                    reasoning.append("短期移動平均線が中期移動平均線を上回る（ゴールデンクロス傾向）")
                else:
                    if recommendation != "BUY":
                        confidence += 0.1
                    reasoning.append("短期移動平均線が中期移動平均線を下回る（デッドクロス傾向）")
            
            # 価格目標の簡易計算
            current_price = current_info["current_price"]
            if recommendation == "BUY":
                target_price = current_price * 1.1  # 10%上昇目標
                stop_loss = current_price * 0.95   # 5%損切り
            elif recommendation == "SELL":
                target_price = current_price * 0.9  # 10%下落目標
                stop_loss = current_price * 1.05   # 5%損切り
            else:
                target_price = current_price * 1.05  # 5%上昇目標
                stop_loss = current_price * 0.97    # 3%損切り
            
            confidence = min(confidence, 0.9)  # 最大90%の信頼度
            
            result = {
                "symbol": symbol.upper(),
                "analysis": {
                    "recommendation": recommendation,
                    "confidence": round(confidence, 2),
                    "target_price": round(target_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "reasoning": reasoning
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # キャッシュに保存（15分間）
            cache_service.set(symbol, "stock_analysis", result, ttl_minutes=15)
            return result
        except Exception as e:
            print(f"株式分析エラー: {str(e)}")
            return {
                "symbol": symbol.upper(),
                "analysis": {
                    "recommendation": "ERROR",
                    "confidence": 0,
                    "target_price": 0,
                    "stop_loss": 0,
                    "reasoning": ["分析中にエラーが発生しました"]
                },
                "timestamp": datetime.now().isoformat()
            }