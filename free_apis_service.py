"""
無料株価APIサービス統合
複数の無料APIを使用してリアルタイム株価データを取得
"""
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import json
from functools import lru_cache

class FreeAPIsService:
    def __init__(self):
        # APIキーの読み込み（環境変数から）
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
        self.twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY", "")
        self.polygon_api_key = os.getenv("POLYGON_API_KEY", "")
        self.marketstack_api_key = os.getenv("MARKETSTACK_API_KEY", "")
        
        # API エンドポイント
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.twelve_data_base_url = "https://api.twelvedata.com"
        self.polygon_base_url = "https://api.polygon.io/v2"
        self.marketstack_base_url = "http://api.marketstack.com/v1"
        
        # レート制限管理
        self.last_request_time = {}
        self.request_count = {}
        
    def _rate_limit_wait(self, api_name: str, requests_per_minute: int):
        """レート制限に対応するための待機処理"""
        current_time = time.time()
        
        if api_name not in self.last_request_time:
            self.last_request_time[api_name] = 0
            self.request_count[api_name] = 0
            
        # 1分経過したらカウントリセット
        if current_time - self.last_request_time[api_name] > 60:
            self.request_count[api_name] = 0
            self.last_request_time[api_name] = current_time
            
        # レート制限に達している場合は待機
        if self.request_count[api_name] >= requests_per_minute:
            wait_time = 60 - (current_time - self.last_request_time[api_name])
            if wait_time > 0:
                time.sleep(wait_time + 1)
                self.request_count[api_name] = 0
                self.last_request_time[api_name] = time.time()
                
        self.request_count[api_name] += 1
        
    @lru_cache(maxsize=128)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """複数のAPIから株価を取得（優先順位付き）"""
        
        # 1. Finnhub（最優先 - リアルタイムデータ）
        if self.finnhub_api_key:
            try:
                self._rate_limit_wait("finnhub", 60)  # 60 requests/minute
                response = requests.get(
                    f"{self.finnhub_base_url}/quote",
                    params={"symbol": symbol, "token": self.finnhub_api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):  # current price
                        return {
                            "symbol": symbol,
                            "current_price": data["c"],
                            "change": data["d"],
                            "change_percent": data["dp"],
                            "high": data["h"],
                            "low": data["l"],
                            "open": data["o"],
                            "previous_close": data["pc"],
                            "timestamp": data["t"],
                            "source": "finnhub"
                        }
            except Exception as e:
                print(f"Finnhub error: {str(e)}")
                
        # 2. Twelve Data
        if self.twelve_data_api_key:
            try:
                self._rate_limit_wait("twelve_data", 8)  # 8 requests/minute (free tier)
                response = requests.get(
                    f"{self.twelve_data_base_url}/price",
                    params={"symbol": symbol, "apikey": self.twelve_data_api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if "price" in data:
                        # 追加で quote データも取得
                        quote_response = requests.get(
                            f"{self.twelve_data_base_url}/quote",
                            params={"symbol": symbol, "apikey": self.twelve_data_api_key}
                        )
                        quote_data = quote_response.json() if quote_response.status_code == 200 else {}
                        
                        return {
                            "symbol": symbol,
                            "current_price": float(data["price"]),
                            "change": float(quote_data.get("change", 0)),
                            "change_percent": float(quote_data.get("percent_change", 0)),
                            "high": float(quote_data.get("high", data["price"])),
                            "low": float(quote_data.get("low", data["price"])),
                            "open": float(quote_data.get("open", data["price"])),
                            "previous_close": float(quote_data.get("previous_close", data["price"])),
                            "volume": int(quote_data.get("volume", 0)),
                            "source": "twelve_data"
                        }
            except Exception as e:
                print(f"Twelve Data error: {str(e)}")
                
        # 3. Polygon.io
        if self.polygon_api_key:
            try:
                self._rate_limit_wait("polygon", 5)  # 5 requests/minute (free tier)
                # 前日の終値を取得
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                response = requests.get(
                    f"{self.polygon_base_url}/aggs/ticker/{symbol}/prev",
                    params={"apiKey": self.polygon_api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        return {
                            "symbol": symbol,
                            "current_price": result["c"],  # close price
                            "change": result["c"] - result["o"],
                            "change_percent": ((result["c"] - result["o"]) / result["o"]) * 100,
                            "high": result["h"],
                            "low": result["l"],
                            "open": result["o"],
                            "volume": result["v"],
                            "source": "polygon"
                        }
            except Exception as e:
                print(f"Polygon error: {str(e)}")
                
        # 4. yfinance（バックアップ - 無料、APIキー不要）
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if "currentPrice" in info or "regularMarketPrice" in info:
                current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                previous_close = info.get("previousClose", current_price)
                
                return {
                    "symbol": symbol,
                    "current_price": current_price,
                    "change": current_price - previous_close,
                    "change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close else 0,
                    "high": info.get("dayHigh", current_price),
                    "low": info.get("dayLow", current_price),
                    "open": info.get("open", current_price),
                    "previous_close": previous_close,
                    "volume": info.get("volume", 0),
                    "market_cap": info.get("marketCap", 0),
                    "source": "yfinance"
                }
        except Exception as e:
            print(f"yfinance error: {str(e)}")
            
        return None
        
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """銘柄検索（yfinanceを使用）"""
        try:
            # yfinanceには直接の検索機能がないため、一般的な銘柄リストから検索
            common_stocks = {
                "NVDA": "NVIDIA Corporation",
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com Inc.",
                "META": "Meta Platforms Inc.",
                "TSLA": "Tesla Inc.",
                "TSM": "Taiwan Semiconductor",
                "AVGO": "Broadcom Inc.",
                "ORCL": "Oracle Corporation",
                "ASML": "ASML Holding",
                "AMD": "Advanced Micro Devices",
                "INTC": "Intel Corporation",
                "CRM": "Salesforce Inc.",
                "QCOM": "Qualcomm Inc.",
                "IBM": "IBM Corporation",
                "SONY": "Sony Group Corporation",
                "NFLX": "Netflix Inc.",
                "DIS": "Walt Disney Company",
                "PYPL": "PayPal Holdings Inc."
            }
            
            query_upper = query.upper()
            results = []
            
            # シンボルまたは名前で検索
            for symbol, name in common_stocks.items():
                if query_upper in symbol or query_upper in name.upper():
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "exchange": "NASDAQ" if symbol in ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "INTC", "QCOM", "NFLX", "PYPL"] else "NYSE"
                    })
                    
            # Finnhubの検索APIも試す
            if self.finnhub_api_key and len(results) < 5:
                try:
                    self._rate_limit_wait("finnhub", 60)
                    response = requests.get(
                        f"{self.finnhub_base_url}/search",
                        params={"q": query, "token": self.finnhub_api_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("result", [])[:10]:
                            if item["symbol"] not in [r["symbol"] for r in results]:
                                results.append({
                                    "symbol": item["symbol"],
                                    "name": item["description"],
                                    "exchange": item.get("displaySymbol", "")
                                })
                except:
                    pass
                    
            return results[:10]  # 最大10件
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
            
    def get_price_history(self, symbol: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
        """価格履歴の取得（主にyfinanceを使用）"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 期間の変換
            period_map = {
                "1d": "1d",
                "5d": "5d",
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
                "2y": "2y",
                "5y": "5y"
            }
            
            yf_period = period_map.get(period, "1mo")
            history = ticker.history(period=yf_period)
            
            if not history.empty:
                dates = [date.strftime("%Y-%m-%d") for date in history.index]
                prices = history["Close"].tolist()
                volumes = history["Volume"].tolist()
                
                return {
                    "symbol": symbol,
                    "dates": dates,
                    "prices": prices,
                    "volumes": volumes,
                    "source": "yfinance"
                }
                
        except Exception as e:
            print(f"History error: {str(e)}")
            
        return None