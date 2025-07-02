"""
無料株価APIの統合サービス
複数の無料APIを活用してデータ取得の信頼性を向上
"""
import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

class FreeAPIsService:
    """無料の株価APIを統合管理するサービス"""
    
    def __init__(self):
        self.last_request_times = {}
        
    def _rate_limit(self, api_name: str, min_interval: float = 1.0):
        """APIごとのレート制限管理"""
        current_time = time.time()
        if api_name in self.last_request_times:
            elapsed = current_time - self.last_request_times[api_name]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self.last_request_times[api_name] = time.time()
    
    def get_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Finnhub API - リアルタイム株価
        無料枠: 1分60リクエスト
        """
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            return None
            
        try:
            self._rate_limit('finnhub', 1.0)  # 1秒に1リクエスト
            
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Finnhubのデータ形式を標準形式に変換
            if data and 'c' in data:  # current price
                return {
                    "symbol": symbol,
                    "name": symbol,  # Finnhubは名前を返さない
                    "current_price": data['c'],
                    "change": data['d'],
                    "change_percent": data['dp'],
                    "volume": data.get('v', 0),
                    "high": data['h'],
                    "low": data['l'],
                    "open": data['o'],
                    "previous_close": data['pc']
                }
        except Exception as e:
            print(f"Finnhub APIエラー: {str(e)}")
        
        return None
    
    def get_polygon_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Polygon.io API - 前日の株価
        無料枠: 1分5リクエスト
        """
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            return None
            
        try:
            self._rate_limit('polygon', 12.0)  # 12秒に1リクエスト
            
            # 前日の日付を取得
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f"https://api.polygon.io/v1/open-close/{symbol}/{yesterday}?apiKey={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'status' in data and data['status'] == 'OK':
                # 前日終値を現在価格として使用（遅延データ）
                return {
                    "symbol": symbol,
                    "name": symbol,
                    "current_price": data['close'],
                    "change": data['close'] - data['open'],
                    "change_percent": ((data['close'] - data['open']) / data['open']) * 100,
                    "volume": data.get('volume', 0),
                    "high": data['high'],
                    "low": data['low'],
                    "open": data['open'],
                    "previous_close": data['open'],  # 概算
                    "data_date": yesterday
                }
        except Exception as e:
            print(f"Polygon APIエラー: {str(e)}")
        
        return None
    
    def get_twelvedata_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Twelve Data API - リアルタイム株価
        無料枠: 1日800リクエスト、1分8リクエスト
        """
        api_key = os.getenv('TWELVEDATA_API_KEY')
        if not api_key:
            return None
            
        try:
            self._rate_limit('twelvedata', 7.5)  # 7.5秒に1リクエスト
            
            url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'price' in data:
                return {
                    "symbol": symbol,
                    "name": data.get('name', symbol),
                    "current_price": float(data['price']),
                    "change": float(data.get('change', 0)),
                    "change_percent": float(data.get('percent_change', 0)),
                    "volume": int(data.get('volume', 0)),
                    "high": float(data.get('high', 0)),
                    "low": float(data.get('low', 0)),
                    "open": float(data.get('open', 0)),
                    "previous_close": float(data.get('previous_close', 0))
                }
        except Exception as e:
            print(f"Twelve Data APIエラー: {str(e)}")
        
        return None
    
    def get_marketstack_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Marketstack API - EOD（終値）データ
        無料枠: 月1000リクエスト
        """
        api_key = os.getenv('MARKETSTACK_API_KEY')
        if not api_key:
            return None
            
        try:
            self._rate_limit('marketstack', 3.0)  # 3秒に1リクエスト
            
            url = f"http://api.marketstack.com/v1/eod/latest?access_key={api_key}&symbols={symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                quote = data['data'][0]
                return {
                    "symbol": symbol,
                    "name": symbol,
                    "current_price": quote['close'],
                    "change": quote['close'] - quote['open'],
                    "change_percent": ((quote['close'] - quote['open']) / quote['open']) * 100,
                    "volume": quote.get('volume', 0),
                    "high": quote['high'],
                    "low": quote['low'],
                    "open": quote['open'],
                    "previous_close": quote['open'],
                    "data_date": quote['date']
                }
        except Exception as e:
            print(f"Marketstack APIエラー: {str(e)}")
        
        return None
    
    def get_best_available_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        利用可能な全ての無料APIから最適なデータを取得
        優先順位: Finnhub > Twelve Data > Polygon > Marketstack
        """
        # 設定されているAPIを優先順位順に試行
        api_methods = [
            ('finnhub', self.get_finnhub_quote),
            ('twelvedata', self.get_twelvedata_quote),
            ('polygon', self.get_polygon_quote),
            ('marketstack', self.get_marketstack_quote)
        ]
        
        for api_name, method in api_methods:
            try:
                print(f"{api_name}で株価取得を試行: {symbol}")
                result = method(symbol)
                if result and result.get('current_price', 0) > 0:
                    result['data_source'] = api_name
                    return result
            except Exception as e:
                print(f"{api_name}エラー: {str(e)}")
                continue
        
        return None
    
    def search_symbols_finnhub(self, query: str) -> List[Dict[str, str]]:
        """
        Finnhub APIで銘柄検索
        """
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            return []
            
        try:
            self._rate_limit('finnhub', 1.0)
            
            url = f"https://finnhub.io/api/v1/search?q={query}&token={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            if 'result' in data:
                for item in data['result'][:10]:  # 最大10件
                    results.append({
                        'symbol': item['symbol'],
                        'name': item['description'],
                        'exchange': item.get('type', 'STOCK')
                    })
            
            return results
        except Exception as e:
            print(f"Finnhub検索エラー: {str(e)}")
            return []
    
    def get_price_history_polygon(self, symbol: str, from_date: str, to_date: str) -> Optional[Dict[str, Any]]:
        """
        Polygon.ioで価格履歴を取得
        """
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            return None
            
        try:
            self._rate_limit('polygon', 12.0)
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}?apiKey={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'results' in data:
                dates = []
                prices = []
                volumes = []
                
                for bar in data['results']:
                    dates.append(datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d'))
                    prices.append(bar['c'])  # 終値
                    volumes.append(bar['v'])
                
                return {
                    "symbol": symbol,
                    "dates": dates,
                    "prices": prices,
                    "volumes": volumes
                }
        except Exception as e:
            print(f"Polygon履歴取得エラー: {str(e)}")
        
        return None

# グローバルインスタンス
free_apis_service = FreeAPIsService()