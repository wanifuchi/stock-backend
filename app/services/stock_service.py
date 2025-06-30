"""
株式データサービス
"""
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands
from .cache_service import cache_service
from .alpha_vantage_service import alpha_vantage_service

class StockService:
    """株式データの取得と分析を行うサービス"""
    
    def __init__(self):
        self.cache = {}  # シンプルなメモリキャッシュ
        self.primary_api = os.getenv('PRIMARY_API_PROVIDER', 'alpha_vantage')
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        株式銘柄を検索（Alpha Vantage優先、ハードコードフォールバック）
        """
        results = []
        
        # Alpha Vantageのシンボル検索を優先
        if self.primary_api == 'alpha_vantage':
            try:
                print(f"Alpha Vantageで銘柄検索中: {query}")
                av_results = alpha_vantage_service.search_symbol(query)
                
                for match in av_results:
                    # USの株式とETFのみをフィルタ
                    if (match.get('region') == 'United States' and
                            match.get('type') in ['Equity', 'ETF']):
                        results.append({
                            "symbol": match['symbol'],
                            "name": match['name'],
                            "exchange": self._determine_exchange(match['symbol'])
                        })
                
                if results:
                    print(f"Alpha Vantageで{len(results)}件の結果を取得")
                    return results[:10]
                else:
                    print("Alpha Vantageで適切な結果が見つからず、フォールバックに移行")
            except Exception as e:
                print(f"Alpha Vantage検索エラー: {str(e)}")
        
        # フォールバック：ハードコードされた銘柄リスト + 直接検証
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
        
        query_upper = query.upper()
        
        # ハードコードリストから検索
        for symbol, name in common_stocks.items():
            if query_upper in symbol or query.lower() in name.lower():
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": self._determine_exchange(symbol)
                })
        
        # 直接的な銘柄コード検証（例：EC, PBR, TRMD, NVTS）
        if query_upper not in [r['symbol'] for r in results]:
            if self._is_valid_ticker(query_upper):
                results.insert(0, {
                    "symbol": query_upper,
                    "name": f"{query_upper} Corporation",
                    "exchange": self._determine_exchange(query_upper)
                })
        
        return results[:10]  # 最大10件まで返す
    
    def _determine_exchange(self, symbol: str) -> str:
        """銘柄コードから取引所を推定"""
        # NASDAQ銘柄の一般的なパターン
        nasdaq_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM"]
        if symbol in nasdaq_symbols:
            return "NASDAQ"
        # その他はNYSEと仮定
        return "NYSE"
    
    def _is_valid_ticker(self, symbol: str) -> bool:
        """yfinanceを使用して銘柄コードが有効かどうかを簡易チェック"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            # 基本情報を取得を試行
            info = ticker.info
            # 有効な銘柄であれば何らかの情報が返される
            return (len(info) > 1 and 
                    ('symbol' in info or 'shortName' in info or 'longName' in info))
        except Exception:
            return False
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        指定銘柄の現在情報を取得（Alpha Vantage優先、yfinanceフォールバック）
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "stock_info")
        if cached_data:
            return cached_data
        
        # Alpha Vantageを優先的に使用
        if self.primary_api == 'alpha_vantage':
            print(f"Alpha Vantageで株式情報を取得中: {symbol}")
            av_data = alpha_vantage_service.get_stock_quote(symbol)
            if av_data and av_data.get('current_price', 0) > 0:
                result = {
                    "symbol": symbol.upper(),
                    "name": av_data.get('name', symbol),
                    "current_price": av_data['current_price'],
                    "change": av_data['change'],
                    "change_percent": float(av_data['change_percent']) if av_data['change_percent'] else 0,
                    "volume": av_data['volume'],
                    "market_cap": None  # Alpha Vantageからは取得できない
                }
                
                # キャッシュに保存（5分間）
                cache_service.set(symbol, "stock_info", result, ttl_minutes=5)
                return result
            else:
                print(f"Alpha Vantage失敗、yfinanceにフォールバック: {symbol}")
        
        # yfinanceフォールバック
        try:
            print(f"yfinanceで株式情報を取得中: {symbol}")
            # レート制限対策: sessionを使用してリクエスト間隔を調整
            import requests
            import time
            
            # セッションを作成してUser-Agentを設定
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            ticker = yf.Ticker(symbol, session=session)
            
            # 少し待機してからデータ取得
            time.sleep(1)
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
            
            # API制限エラーの場合はモックデータを返す
            if "429" in str(e) or "Too Many Requests" in str(e):
                return self._get_mock_data(symbol)
            
            return {
                "symbol": symbol.upper(),
                "name": f"Error: {str(e)}",
                "current_price": 0,
                "change": 0,
                "change_percent": 0,
                "volume": 0,
                "market_cap": None
            }
    
    def _get_mock_data(self, symbol: str) -> Dict[str, Any]:
        """
        API制限時のモックデータを生成
        """
        import random
        
        # 銘柄別のモックデータ
        mock_data = {
            "AAPL": {"name": "Apple Inc.", "base_price": 195.0, "volume": 50000000},
            "GOOGL": {"name": "Alphabet Inc.", "base_price": 140.0, "volume": 25000000},
            "MSFT": {"name": "Microsoft Corporation", "base_price": 425.0, "volume": 30000000},
            "AMZN": {"name": "Amazon.com Inc.", "base_price": 155.0, "volume": 35000000},
            "TSLA": {"name": "Tesla Inc.", "base_price": 250.0, "volume": 40000000},
            "NVDA": {"name": "NVIDIA Corporation", "base_price": 480.0, "volume": 45000000},
            "META": {"name": "Meta Platforms Inc.", "base_price": 330.0, "volume": 20000000},
        }
        
        symbol_upper = symbol.upper()
        if symbol_upper in mock_data:
            data = mock_data[symbol_upper]
            # ランダムな変動を追加
            price_change = random.uniform(-5.0, 5.0)
            current_price = data["base_price"] + price_change
            change_percent = (price_change / data["base_price"]) * 100
            
            return {
                "symbol": symbol_upper,
                "name": data["name"] + " (モックデータ)",
                "current_price": round(current_price, 2),
                "change": round(price_change, 2),
                "change_percent": round(change_percent, 2),
                "volume": data["volume"] + random.randint(-1000000, 1000000),
                "market_cap": int(current_price * 16_000_000_000)  # 概算
            }
        else:
            # 未知の銘柄の場合
            return {
                "symbol": symbol_upper,
                "name": f"{symbol_upper} Corporation (モックデータ)",
                "current_price": round(random.uniform(50, 500), 2),
                "change": round(random.uniform(-10, 10), 2),
                "change_percent": round(random.uniform(-5, 5), 2),
                "volume": random.randint(1000000, 50000000),
                "market_cap": random.randint(10_000_000_000, 2_000_000_000_000)
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
        テクニカル指標を計算（Alpha Vantage優先、taライブラリフォールバック）
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "technical_indicators")
        if cached_data:
            return cached_data
        
        # Alpha Vantageを優先的に使用
        if self.primary_api == 'alpha_vantage':
            print(f"Alpha Vantageで技術指標を取得中: {symbol}")
            try:
                rsi_data = alpha_vantage_service.get_rsi(symbol)
                macd_data = alpha_vantage_service.get_macd(symbol)
                bbands_data = alpha_vantage_service.get_bollinger_bands(symbol)
                
                if rsi_data or macd_data or bbands_data:
                    result = {
                        "symbol": symbol,
                        "rsi": rsi_data.get('rsi') if rsi_data else None,
                        "macd": {
                            "macd": macd_data.get('macd'),
                            "signal": macd_data.get('signal'),
                            "histogram": macd_data.get('histogram')
                        } if macd_data else None,
                        "bollinger_bands": {
                            "upper": bbands_data.get('upper_band'),
                            "middle": bbands_data.get('middle_band'),
                            "lower": bbands_data.get('lower_band')
                        } if bbands_data else None,
                        "moving_averages": {
                            "sma_20": bbands_data.get('middle_band'),  # 中央線は20期間SMA
                            "sma_50": None,  # Alpha Vantageでは別途取得が必要
                            "sma_200": None
                        }
                    }
                    
                    # キャッシュに保存（15分間）
                    cache_service.set(symbol, "technical_indicators", result, ttl_minutes=15)
                    return result
            except Exception as e:
                print(f"Alpha Vantage技術指標取得エラー: {str(e)}")
        
        # taライブラリをフォールバック
        
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
        AIによる株式分析（Alpha Vantage優先、従来ロジックフォールバック）
        """
        # キャッシュから取得を試行
        cached_data = cache_service.get(symbol, "stock_analysis")
        if cached_data:
            return cached_data
        
        # Alpha Vantageの包括的分析を優先使用
        if self.primary_api == 'alpha_vantage':
            print(f"Alpha Vantageで包括的分析を実行中: {symbol}")
            av_analysis = alpha_vantage_service.get_comprehensive_analysis(symbol)
            if av_analysis and av_analysis.get('overall_signal') != 'ERROR':
                # Alpha Vantageの結果を標準形式に変換
                result = {
                    "symbol": symbol.upper(),
                    "analysis": {
                        "recommendation": av_analysis['overall_signal'],
                        "confidence": av_analysis['confidence'] / 100.0,  # 0-1の範囲に正規化
                        "target_price": 
                            self._calculate_target_price(av_analysis),
                        "stop_loss": self._calculate_stop_loss(av_analysis),
                        "reasoning": self._extract_reasoning(av_analysis)
                    },
                    "timestamp": av_analysis['timestamp'],
                    "data_source": "Alpha Vantage"
                }
                
                # キャッシュに保存（10分間）
                cache_service.set(symbol, "stock_analysis", result, ttl_minutes=10)
                return result
            else:
                print(f"Alpha Vantage分析失敗、従来ロジックにフォールバック: {symbol}")
        
        # 従来のロジックをフォールバック
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
    
    def _calculate_target_price(self, av_analysis: Dict) -> float:
        """Alpha Vantage分析結果から目標価格を計算"""
        try:
            quote = av_analysis.get('quote', {})
            current_price = quote.get('current_price', 0)
            confidence = av_analysis.get('confidence', 50)
            signal = av_analysis.get('overall_signal', 'HOLD')
            
            if signal == 'BUY':
                # 信頼度に基づいて5-15%の上昇目標
                multiplier = 1 + (0.05 + (confidence - 50) * 0.002)
                return round(current_price * multiplier, 2)
            elif signal == 'SELL':
                # 売りシグナルの場合は現在価格より低く設定
                multiplier = 1 - (0.05 + (confidence - 50) * 0.001)
                return round(current_price * multiplier, 2)
            else:
                return current_price
        except:
            return 0
    
    def _calculate_stop_loss(self, av_analysis: Dict) -> float:
        """Alpha Vantage分析結果からストップロスを計算"""
        try:
            quote = av_analysis.get('quote', {})
            current_price = quote.get('current_price', 0)
            signal = av_analysis.get('overall_signal', 'HOLD')
            
            if signal == 'BUY':
                # 買いポジションの場合は5-8%下で損切り
                return round(current_price * 0.95, 2)
            elif signal == 'SELL':
                # 売りポジションの場合は3-5%上で損切り
                return round(current_price * 1.03, 2)
            else:
                return current_price
        except:
            return 0
    
    def _extract_reasoning(self, av_analysis: Dict) -> List[str]:
        """Alpha Vantage分析結果から推論理由を抽出"""
        try:
            reasoning = []
            
            # 各指標の解釈を追加
            if 'rsi' in av_analysis and av_analysis['rsi']:
                rsi_data = av_analysis['rsi']
                reasoning.append(f"RSI: {rsi_data.get('rsi', 'N/A')} - {rsi_data.get('signal', '')}")
            
            if 'macd' in av_analysis and av_analysis['macd']:
                macd_data = av_analysis['macd']
                reasoning.append(f"MACD: {macd_data.get('signal_interpretation', '')}")
            
            if 'bollinger_bands' in av_analysis and av_analysis['bollinger_bands']:
                bb_data = av_analysis['bollinger_bands']
                reasoning.append(f"ボリンジャーバンド: {bb_data.get('signal', '')}")
            
            # 総合分析サマリーを追加
            if 'analysis_summary' in av_analysis:
                reasoning.append(f"総合判定: {av_analysis['analysis_summary']}")
            
            return reasoning if reasoning else ["Alpha Vantage技術分析に基づく判定"]
        except:
            return ["分析データの解釈中にエラーが発生"]