"""
強化された株式分析サービス
現実的で多様性のある分析結果を生成
"""
import random
import hashlib
from typing import Dict, List, Any
from datetime import datetime, timedelta
import math


class EnhancedAnalysisService:
    """現実的な株式分析を提供する強化サービス"""
    
    def __init__(self):
        # 銘柄別の特性データベース
        self.stock_characteristics = {
            'AAPL': {'volatility': 0.3, 'trend': 'bullish', 'sector': 'tech'},
            'GOOGL': {'volatility': 0.35, 'trend': 'bullish', 'sector': 'tech'},
            'MSFT': {'volatility': 0.25, 'trend': 'bullish', 'sector': 'tech'},
            'AMZN': {'volatility': 0.4, 'trend': 'neutral', 'sector': 'consumer'},
            'TSLA': {'volatility': 0.6, 'trend': 'volatile', 'sector': 'auto'},
            'NVDA': {'volatility': 0.5, 'trend': 'bullish', 'sector': 'tech'},
            'META': {'volatility': 0.45, 'trend': 'recovery', 'sector': 'social'},
            'JPM': {'volatility': 0.2, 'trend': 'stable', 'sector': 'finance'},
            'V': {'volatility': 0.15, 'trend': 'stable', 'sector': 'finance'},
            'JNJ': {'volatility': 0.1, 'trend': 'stable', 'sector': 'pharma'},
        }
    
    def _get_symbol_seed(self, symbol: str) -> int:
        """銘柄コードから決定論的シードを生成（結果の一貫性確保）"""
        return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    
    def _get_time_seed(self, symbol: str) -> int:
        """時間ベースのシード（日単位で変動）"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        combined = f"{symbol}_{date_str}"
        return int(hashlib.md5(combined.encode()).hexdigest()[:8], 16)
    
    def generate_realistic_stock_info(self, symbol: str, base_price: float = None) -> Dict[str, Any]:
        """現実的な株価情報を生成"""
        random.seed(self._get_time_seed(symbol))
        
        characteristics = self.stock_characteristics.get(symbol, {
            'volatility': 0.3, 'trend': 'neutral', 'sector': 'unknown'
        })
        
        # ベース価格の設定
        if not base_price:
            symbol_seed = self._get_symbol_seed(symbol)
            base_price = 50 + (symbol_seed % 200)  # $50-$250の範囲
        
        # トレンドに基づく価格変動
        trend_multiplier = {
            'bullish': random.uniform(0.005, 0.03),
            'bearish': random.uniform(-0.03, -0.005),
            'neutral': random.uniform(-0.01, 0.01),
            'volatile': random.uniform(-0.05, 0.05),
            'stable': random.uniform(-0.005, 0.005),
            'recovery': random.uniform(-0.02, 0.025)
        }.get(characteristics['trend'], 0)
        
        # ボラティリティ調整
        volatility = characteristics['volatility']
        daily_change = trend_multiplier + random.gauss(0, volatility * 0.02)
        
        current_price = base_price * (1 + daily_change)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        # ボリュームの計算（価格変動と逆相関）
        volume_base = 1000000 + (abs(symbol_seed) % 50000000)
        volume_multiplier = 1 + abs(change_percent) * 0.5  # 変動が大きいほど出来高増加
        volume = int(volume_base * volume_multiplier)
        
        # 時価総額の推定
        shares_outstanding = 1000000000 + (symbol_seed % 5000000000)  # 10億-60億株
        market_cap = int(current_price * shares_outstanding)
        
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol} Corporation",
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": volume,
            "market_cap": market_cap
        }
    
    def generate_realistic_technical_indicators(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """現実的なテクニカル指標を生成"""
        random.seed(self._get_time_seed(symbol))
        
        characteristics = self.stock_characteristics.get(symbol, {
            'volatility': 0.3, 'trend': 'neutral'
        })
        
        # RSI生成（トレンドに基づく）
        trend = characteristics['trend']
        if trend == 'bullish':
            rsi = random.uniform(55, 75)
        elif trend == 'bearish':
            rsi = random.uniform(25, 45)
        elif trend == 'volatile':
            rsi = random.choice([random.uniform(20, 35), random.uniform(65, 80)])
        else:
            rsi = random.uniform(40, 60)
        
        # MACD生成（RSIと相関）
        macd_base = (rsi - 50) * 0.1
        macd = macd_base + random.gauss(0, 0.05)
        signal = macd - random.uniform(-0.02, 0.02)
        histogram = macd - signal
        
        # ボリンジャーバンド生成
        volatility = characteristics['volatility']
        band_width = current_price * volatility * 0.4
        middle_band = current_price * random.uniform(0.98, 1.02)
        upper_band = middle_band + band_width
        lower_band = middle_band - band_width
        
        # 移動平均線生成
        sma_20 = current_price * random.uniform(0.95, 1.05)
        sma_50 = current_price * random.uniform(0.90, 1.10)
        sma_200 = current_price * random.uniform(0.80, 1.20)
        
        return {
            "symbol": symbol.upper(),
            "rsi": round(rsi, 2),
            "macd": {
                "macd": round(macd, 3),
                "signal": round(signal, 3),
                "histogram": round(histogram, 3)
            },
            "bollinger_bands": {
                "upper": round(upper_band, 2),
                "middle": round(middle_band, 2),
                "lower": round(lower_band, 2)
            },
            "moving_averages": {
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "sma_200": round(sma_200, 2)
            }
        }
    
    def generate_advanced_analysis(self, symbol: str, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
        """高度な分析結果を生成"""
        random.seed(self._get_time_seed(symbol))
        
        current_price = stock_info['current_price']
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', {})
        bollinger = indicators.get('bollinger_bands', {})
        
        # 複数シグナルの分析
        buy_signals = 0
        sell_signals = 0
        reasoning = []
        
        # RSI分析
        if rsi < 30:
            buy_signals += 1
            reasoning.append("RSI売られすぎシグナル（強い買い推奨）")
        elif rsi > 70:
            sell_signals += 1
            reasoning.append("RSI買われすぎシグナル（利確推奨）")
        elif rsi > 55:
            reasoning.append("RSI強気傾向（上昇モメンタム継続）")
        else:
            reasoning.append("RSI中立圏（方向性待ち）")
        
        # MACD分析
        if macd.get('macd', 0) > macd.get('signal', 0):
            if macd.get('histogram', 0) > 0:
                buy_signals += 1
                reasoning.append("MACDゴールデンクロス（強気シグナル）")
            else:
                reasoning.append("MACD上昇トレンド（弱気転換注意）")
        else:
            if macd.get('histogram', 0) < 0:
                sell_signals += 1
                reasoning.append("MACDデッドクロス（弱気シグナル）")
            else:
                reasoning.append("MACD下降トレンド（反転の兆候）")
        
        # ボリンジャーバンド分析
        if bollinger:
            upper = bollinger.get('upper', current_price)
            lower = bollinger.get('lower', current_price)
            
            if current_price > upper * 0.98:
                sell_signals += 1
                reasoning.append("ボリンジャーバンド上限接触（過熱感）")
            elif current_price < lower * 1.02:
                buy_signals += 1
                reasoning.append("ボリンジャーバンド下限接触（割安感）")
            else:
                reasoning.append("ボリンジャーバンド中央推移（トレンド継続）")
        
        # 総合判定
        net_signals = buy_signals - sell_signals
        if net_signals >= 2:
            recommendation = "BUY"
            confidence = min(0.85, 0.6 + net_signals * 0.1)
        elif net_signals <= -2:
            recommendation = "SELL"
            confidence = min(0.85, 0.6 + abs(net_signals) * 0.1)
        elif net_signals == 1:
            recommendation = "BUY"
            confidence = 0.65
        elif net_signals == -1:
            recommendation = "SELL"
            confidence = 0.65
        else:
            recommendation = "HOLD"
            confidence = random.uniform(0.45, 0.55)
        
        # 価格目標の計算
        characteristics = self.stock_characteristics.get(symbol, {'volatility': 0.3})
        volatility = characteristics['volatility']
        
        if recommendation == "BUY":
            upside_potential = random.uniform(0.05, 0.15) * (confidence / 0.7)
            target_price = current_price * (1 + upside_potential)
            stop_loss = current_price * (1 - volatility * 0.3)
        elif recommendation == "SELL":
            downside_potential = random.uniform(0.05, 0.12) * (confidence / 0.7)
            target_price = current_price * (1 - downside_potential)
            stop_loss = current_price * (1 + volatility * 0.2)
        else:
            target_price = current_price * random.uniform(1.02, 1.08)
            stop_loss = current_price * random.uniform(0.92, 0.98)
        
        # 分析サマリーの追加
        reasoning.append(f"総合判定: {buy_signals}個の買いシグナル, {sell_signals}個の売りシグナル")
        
        if confidence > 0.75:
            reasoning.append("高信頼度の分析結果（複数指標が一致）")
        elif confidence < 0.5:
            reasoning.append("不確定要素が多い相場環境（慎重なアプローチ推奨）")
        
        return {
            "symbol": symbol.upper(),
            "analysis": {
                "recommendation": recommendation,
                "confidence": round(confidence, 2),
                "target_price": round(target_price, 2),
                "stop_loss": round(stop_loss, 2),
                "reasoning": reasoning
            },
            "timestamp": datetime.now().isoformat(),
            "data_source": "Enhanced Analysis Engine"
        }
    
    def generate_price_history(self, symbol: str, period: str = "3mo") -> Dict[str, Any]:
        """現実的な価格履歴を生成"""
        random.seed(self._get_symbol_seed(symbol))
        
        # 期間の設定
        days = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365}.get(period, 90)
        
        # 銘柄特性
        characteristics = self.stock_characteristics.get(symbol, {
            'volatility': 0.3, 'trend': 'neutral'
        })
        
        # ベース価格とトレンド
        base_price = 50 + (self._get_symbol_seed(symbol) % 200)
        trend = characteristics['trend']
        volatility = characteristics['volatility']
        
        # 価格生成
        prices = []
        dates = []
        volumes = []
        
        current_price = base_price
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            
            # トレンド成分
            trend_component = {
                'bullish': 0.002,
                'bearish': -0.002,
                'neutral': 0,
                'volatile': random.uniform(-0.005, 0.005),
                'stable': 0.0005,
                'recovery': 0.001 if i > days/2 else -0.001
            }.get(trend, 0)
            
            # ランダム成分
            random_component = random.gauss(0, volatility * 0.02)
            
            # 価格更新
            daily_change = trend_component + random_component
            current_price *= (1 + daily_change)
            
            # ボリューム（変動と逆相関）
            volume_base = 1000000 + random.randint(0, 5000000)
            volume_multiplier = 1 + abs(daily_change) * 10
            volume = int(volume_base * volume_multiplier)
            
            prices.append(round(current_price, 2))
            dates.append(date)
            volumes.append(volume)
        
        return {
            "symbol": symbol.upper(),
            "dates": dates,
            "prices": prices,
            "volumes": volumes
        }


# グローバルインスタンス
enhanced_analysis_service = EnhancedAnalysisService()