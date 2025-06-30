"""
高度な売買タイミング判断サービス
Geminiと設計した複合的な売買戦略を実装
"""
import random
import math
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np


class AdvancedTradingService:
    """高度な売買タイミング判断を提供するサービス"""
    
    def __init__(self):
        # 市場特性データベース（銘柄ごとの特徴）
        self.stock_profiles = {
            'AAPL': {'liquidity': 'high', 'volatility': 'medium', 'sector': 'tech'},
            'GOOGL': {'liquidity': 'high', 'volatility': 'medium', 'sector': 'tech'},
            'TSLA': {'liquidity': 'high', 'volatility': 'high', 'sector': 'auto'},
            'NVDA': {'liquidity': 'high', 'volatility': 'high', 'sector': 'tech'},
            'JPM': {'liquidity': 'high', 'volatility': 'low', 'sector': 'finance'},
            'JNJ': {'liquidity': 'medium', 'volatility': 'low', 'sector': 'pharma'},
        }
    
    def calculate_market_environment(self, symbol: str, price_history: List[float]) -> Dict[str, Any]:
        """
        ステップ1: 市場環境分析（トレンド/レンジ判定）
        ADXと移動平均線の傾きで市場の状態を判別
        """
        if len(price_history) < 20:
            return {'type': 'unknown', 'strength': 0, 'direction': 'neutral'}
        
        # ADX計算（簡易版）
        # 実際のADXは複雑なので、ここではボラティリティベースで簡易計算
        volatility = np.std(price_history[-20:]) / np.mean(price_history[-20:])
        adx = min(100, volatility * 500)  # 0-100の範囲に正規化
        
        # 長期移動平均の傾き
        if len(price_history) >= 50:
            ma_50 = np.mean(price_history[-50:])
            ma_50_prev = np.mean(price_history[-51:-1])
            ma_slope = (ma_50 - ma_50_prev) / ma_50_prev * 100
        else:
            ma_slope = 0
        
        # 市場環境の判定
        if adx > 25:
            market_type = 'trending'
            direction = 'bullish' if ma_slope > 0.1 else 'bearish' if ma_slope < -0.1 else 'neutral'
        else:
            market_type = 'ranging'
            direction = 'neutral'
        
        return {
            'type': market_type,
            'adx': round(adx, 2),
            'strength': round(adx / 100, 2),
            'direction': direction,
            'ma_slope': round(ma_slope, 2)
        }
    
    def calculate_advanced_indicators(self, symbol: str, current_price: float, 
                                    price_history: List[float], volume_history: List[int]) -> Dict[str, Any]:
        """
        ステップ2: 高度なテクニカル指標の計算
        """
        indicators = {}
        
        # ストキャスティクス
        if len(price_history) >= 14:
            high_14 = max(price_history[-14:])
            low_14 = min(price_history[-14:])
            if high_14 != low_14:
                k_percent = ((current_price - low_14) / (high_14 - low_14)) * 100
            else:
                k_percent = 50
            indicators['stochastic'] = {
                'k': round(k_percent, 2),
                'd': round(k_percent * 0.9, 2),  # 簡易的なD値
                'signal': 'oversold' if k_percent < 20 else 'overbought' if k_percent > 80 else 'neutral'
            }
        
        # OBV (On-Balance Volume)
        if len(price_history) >= 2 and len(volume_history) >= len(price_history):
            obv = 0
            obv_trend = []
            for i in range(1, min(len(price_history), 20)):
                if price_history[-i] > price_history[-i-1]:
                    obv += volume_history[-i]
                elif price_history[-i] < price_history[-i-1]:
                    obv -= volume_history[-i]
                obv_trend.append(obv)
            
            # OBVトレンド判定
            if len(obv_trend) >= 5:
                obv_slope = (obv_trend[-1] - obv_trend[-5]) / abs(obv_trend[-5] + 1)
                indicators['obv'] = {
                    'value': obv,
                    'trend': 'bullish' if obv_slope > 0.1 else 'bearish' if obv_slope < -0.1 else 'neutral',
                    'divergence': self._check_divergence(price_history[-5:], obv_trend[-5:])
                }
        
        # VWAP (Volume Weighted Average Price) - 簡易版
        if len(price_history) >= 20 and len(volume_history) >= 20:
            vwap = sum(p * v for p, v in zip(price_history[-20:], volume_history[-20:])) / sum(volume_history[-20:])
            indicators['vwap'] = {
                'value': round(vwap, 2),
                'position': 'above' if current_price > vwap else 'below',
                'distance': round((current_price - vwap) / vwap * 100, 2)
            }
        
        # ATR (Average True Range)
        if len(price_history) >= 14:
            tr_values = []
            for i in range(1, 15):
                high = max(price_history[-i], price_history[-i-1])
                low = min(price_history[-i], price_history[-i-1])
                tr = high - low
                tr_values.append(tr)
            atr = np.mean(tr_values)
            indicators['atr'] = {
                'value': round(atr, 2),
                'percentage': round(atr / current_price * 100, 2)
            }
        
        return indicators
    
    def detect_support_resistance(self, price_history: List[float], current_price: float) -> Dict[str, Any]:
        """
        ステップ3: 支持線・抵抗線の自動検出
        ピボットポイントとスイングハイ/ローを検出
        """
        levels = {
            'support': [],
            'resistance': [],
            'pivot_points': {}
        }
        
        if len(price_history) < 20:
            return levels
        
        # スイングハイ/ローの検出
        for i in range(2, len(price_history) - 2):
            # スイングハイ（前後2本より高い）
            if (price_history[i] > price_history[i-1] and 
                price_history[i] > price_history[i-2] and
                price_history[i] > price_history[i+1] and 
                price_history[i] > price_history[i+2]):
                levels['resistance'].append(round(price_history[i], 2))
            
            # スイングロー（前後2本より低い）
            if (price_history[i] < price_history[i-1] and 
                price_history[i] < price_history[i-2] and
                price_history[i] < price_history[i+1] and 
                price_history[i] < price_history[i+2]):
                levels['support'].append(round(price_history[i], 2))
        
        # 重要度でソート（出現頻度が高い価格帯を重視）
        levels['support'] = sorted(set(levels['support']), reverse=True)[-3:]  # 最も近い3つ
        levels['resistance'] = sorted(set(levels['resistance']))[:3]  # 最も近い3つ
        
        # ピボットポイント計算（日足想定）
        if len(price_history) >= 1:
            high = max(price_history[-20:])
            low = min(price_history[-20:])
            close = price_history[-1]
            
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            
            levels['pivot_points'] = {
                'pivot': round(pivot, 2),
                'r1': round(r1, 2),
                'r2': round(r2, 2),
                's1': round(s1, 2),
                's2': round(s2, 2)
            }
        
        # 現在価格から最も近い支持線・抵抗線
        if levels['support']:
            levels['nearest_support'] = max([s for s in levels['support'] if s < current_price], default=None)
        if levels['resistance']:
            levels['nearest_resistance'] = min([r for r in levels['resistance'] if r > current_price], default=None)
        
        return levels
    
    def generate_trading_signals(self, symbol: str, stock_data: Dict, 
                               indicators: Dict, advanced_indicators: Dict,
                               market_env: Dict, support_resistance: Dict) -> Dict[str, Any]:
        """
        ステップ4: 複合的な売買シグナルの生成
        市場環境に応じて異なる戦略を適用
        """
        signals = {
            'primary_signal': 'HOLD',
            'strength': 0,
            'entry_signals': [],
            'exit_signals': [],
            'confidence': 0,
            'strategy_type': market_env['type']
        }
        
        current_price = stock_data['current_price']
        
        # トレンド相場の戦略
        if market_env['type'] == 'trending':
            # 順張り戦略
            if market_env['direction'] == 'bullish':
                # 押し目買いシグナル
                if indicators.get('rsi', 50) < 40:  # RSIが一時的に下落
                    signals['entry_signals'].append({
                        'type': 'pullback_buy',
                        'reason': 'トレンド中の一時的な押し目',
                        'strength': 0.7
                    })
                
                # VWAPサポート
                if advanced_indicators.get('vwap', {}).get('position') == 'above':
                    signals['entry_signals'].append({
                        'type': 'vwap_support',
                        'reason': 'VWAP上での買い優勢',
                        'strength': 0.6
                    })
            
            elif market_env['direction'] == 'bearish':
                # 戻り売りシグナル
                if indicators.get('rsi', 50) > 60:
                    signals['exit_signals'].append({
                        'type': 'rally_sell',
                        'reason': 'トレンド中の一時的な戻り',
                        'strength': 0.7
                    })
        
        # レンジ相場の戦略
        else:
            # 逆張り戦略
            stoch = advanced_indicators.get('stochastic', {})
            
            # オーバーソールドからの買い
            if stoch.get('signal') == 'oversold' and support_resistance.get('nearest_support'):
                if abs(current_price - support_resistance['nearest_support']) / current_price < 0.02:
                    signals['entry_signals'].append({
                        'type': 'oversold_bounce',
                        'reason': '売られすぎ + 支持線接近',
                        'strength': 0.8
                    })
            
            # オーバーボートからの売り
            if stoch.get('signal') == 'overbought' and support_resistance.get('nearest_resistance'):
                if abs(current_price - support_resistance['nearest_resistance']) / current_price < 0.02:
                    signals['exit_signals'].append({
                        'type': 'overbought_reversal',
                        'reason': '買われすぎ + 抵抗線接近',
                        'strength': 0.8
                    })
        
        # ボリューム確認
        obv = advanced_indicators.get('obv', {})
        if obv.get('divergence'):
            # ダイバージェンスは強力なシグナル
            if obv['trend'] == 'bullish' and any(s['type'] == 'pullback_buy' for s in signals['entry_signals']):
                signals['entry_signals'].append({
                    'type': 'bullish_divergence',
                    'reason': '価格とOBVの強気ダイバージェンス',
                    'strength': 0.9
                })
        
        # 総合判定
        total_buy_strength = sum(s['strength'] for s in signals['entry_signals'])
        total_sell_strength = sum(s['strength'] for s in signals['exit_signals'])
        
        if total_buy_strength > total_sell_strength and total_buy_strength >= 1.0:
            signals['primary_signal'] = 'BUY'
            signals['strength'] = min(1.0, total_buy_strength / 2)
            signals['confidence'] = min(0.9, 0.5 + total_buy_strength * 0.2)
        elif total_sell_strength > total_buy_strength and total_sell_strength >= 1.0:
            signals['primary_signal'] = 'SELL'
            signals['strength'] = min(1.0, total_sell_strength / 2)
            signals['confidence'] = min(0.9, 0.5 + total_sell_strength * 0.2)
        else:
            signals['confidence'] = 0.3 + (max(total_buy_strength, total_sell_strength) * 0.1)
        
        return signals
    
    def calculate_risk_reward_targets(self, symbol: str, current_price: float,
                                    signal: str, support_resistance: Dict,
                                    advanced_indicators: Dict) -> Dict[str, Any]:
        """
        ステップ5: リスク・リワード比の計算と価格目標の設定
        """
        targets = {
            'entry_price': current_price,
            'stop_loss': 0,
            'take_profit_1': 0,
            'take_profit_2': 0,
            'take_profit_3': 0,
            'risk_reward_ratio': 0,
            'position_size_suggestion': 1.0,
            'trailing_stop': {}
        }
        
        atr = advanced_indicators.get('atr', {}).get('value', current_price * 0.02)
        
        if signal == 'BUY':
            # 損切りライン：サポートラインの少し下 or ATRベース
            if support_resistance.get('nearest_support'):
                targets['stop_loss'] = support_resistance['nearest_support'] * 0.98
            else:
                targets['stop_loss'] = current_price - (2 * atr)
            
            # 利益確定目標
            if support_resistance.get('nearest_resistance'):
                targets['take_profit_1'] = support_resistance['nearest_resistance']
            else:
                targets['take_profit_1'] = current_price + (2 * atr)
            
            targets['take_profit_2'] = current_price + (3 * atr)
            targets['take_profit_3'] = current_price + (5 * atr)
            
            # トレーリングストップ
            targets['trailing_stop'] = {
                'initial': targets['stop_loss'],
                'step': atr * 0.5,
                'method': '20日移動平均線 or 2ATR下'
            }
        
        elif signal == 'SELL':
            # 損切りライン：レジスタンスラインの少し上 or ATRベース
            if support_resistance.get('nearest_resistance'):
                targets['stop_loss'] = support_resistance['nearest_resistance'] * 1.02
            else:
                targets['stop_loss'] = current_price + (2 * atr)
            
            # 利益確定目標（ショート）
            if support_resistance.get('nearest_support'):
                targets['take_profit_1'] = support_resistance['nearest_support']
            else:
                targets['take_profit_1'] = current_price - (2 * atr)
            
            targets['take_profit_2'] = current_price - (3 * atr)
            targets['take_profit_3'] = current_price - (5 * atr)
        
        # リスク・リワード比の計算
        if targets['stop_loss'] != 0:
            risk = abs(current_price - targets['stop_loss'])
            reward = abs(targets['take_profit_1'] - current_price)
            if risk > 0:
                targets['risk_reward_ratio'] = round(reward / risk, 2)
                
                # ポジションサイズの提案（リスクが高いほど小さく）
                if targets['risk_reward_ratio'] >= 2.0:
                    targets['position_size_suggestion'] = 1.0
                elif targets['risk_reward_ratio'] >= 1.5:
                    targets['position_size_suggestion'] = 0.75
                else:
                    targets['position_size_suggestion'] = 0.5
        
        # 価格を丸める
        for key in ['stop_loss', 'take_profit_1', 'take_profit_2', 'take_profit_3']:
            targets[key] = round(targets[key], 2)
        
        return targets
    
    def generate_comprehensive_analysis(self, symbol: str, stock_info: Dict,
                                      indicators: Dict, price_history: List[float],
                                      volume_history: List[int]) -> Dict[str, Any]:
        """
        総合的な売買タイミング分析
        """
        # 1. 市場環境分析
        market_env = self.calculate_market_environment(symbol, price_history)
        
        # 2. 高度な指標計算
        current_price = stock_info['current_price']
        advanced_indicators = self.calculate_advanced_indicators(
            symbol, current_price, price_history, volume_history
        )
        
        # 3. 支持線・抵抗線検出
        support_resistance = self.detect_support_resistance(price_history, current_price)
        
        # 4. 売買シグナル生成
        signals = self.generate_trading_signals(
            symbol, stock_info, indicators, advanced_indicators,
            market_env, support_resistance
        )
        
        # 5. リスク・リワード計算
        risk_reward = self.calculate_risk_reward_targets(
            symbol, current_price, signals['primary_signal'],
            support_resistance, advanced_indicators
        )
        
        # 6. 実行可能なアクションプラン
        action_plan = self._create_action_plan(signals, risk_reward, market_env)
        
        return {
            'symbol': symbol,
            'market_environment': market_env,
            'advanced_indicators': advanced_indicators,
            'support_resistance': support_resistance,
            'trading_signals': signals,
            'risk_reward_targets': risk_reward,
            'action_plan': action_plan,
            'timestamp': datetime.now().isoformat()
        }
    
    def _check_divergence(self, prices: List[float], indicator_values: List[float]) -> bool:
        """価格と指標のダイバージェンスをチェック"""
        if len(prices) < 2 or len(indicator_values) < 2:
            return False
        
        price_trend = prices[-1] > prices[0]
        indicator_trend = indicator_values[-1] > indicator_values[0]
        
        return price_trend != indicator_trend
    
    def _create_action_plan(self, signals: Dict, risk_reward: Dict, market_env: Dict) -> List[str]:
        """実行可能なアクションプランを作成"""
        plan = []
        
        if signals['primary_signal'] == 'BUY':
            plan.append(f"📈 買いエントリー推奨")
            plan.append(f"エントリー価格: ${risk_reward['entry_price']}")
            plan.append(f"損切り: ${risk_reward['stop_loss']} (-{round((risk_reward['entry_price'] - risk_reward['stop_loss']) / risk_reward['entry_price'] * 100, 1)}%)")
            plan.append(f"第1目標: ${risk_reward['take_profit_1']} (+{round((risk_reward['take_profit_1'] - risk_reward['entry_price']) / risk_reward['entry_price'] * 100, 1)}%)")
            plan.append(f"推奨ポジションサイズ: {int(risk_reward['position_size_suggestion'] * 100)}%")
            
            if market_env['type'] == 'trending':
                plan.append("💡 トレンド相場：利益を伸ばすため、段階的利確を推奨")
            else:
                plan.append("💡 レンジ相場：目標価格で確実に利確を推奨")
        
        elif signals['primary_signal'] == 'SELL':
            plan.append(f"📉 売りエントリー推奨")
            plan.append(f"エントリー価格: ${risk_reward['entry_price']}")
            plan.append(f"損切り: ${risk_reward['stop_loss']} (+{round((risk_reward['stop_loss'] - risk_reward['entry_price']) / risk_reward['entry_price'] * 100, 1)}%)")
            plan.append(f"第1目標: ${risk_reward['take_profit_1']} (-{round((risk_reward['entry_price'] - risk_reward['take_profit_1']) / risk_reward['entry_price'] * 100, 1)}%)")
        
        else:
            plan.append("⏸️ 様子見推奨")
            plan.append("明確なシグナルが出るまで待機してください")
            if signals['confidence'] < 0.5:
                plan.append("⚠️ 現在の市場は方向感が不明瞭です")
        
        # リスク警告
        if risk_reward['risk_reward_ratio'] < 1.5:
            plan.append("⚠️ リスク・リワード比が低いため、慎重な判断を")
        
        return plan


# グローバルインスタンス
advanced_trading_service = AdvancedTradingService()