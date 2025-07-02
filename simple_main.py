"""
Railway用のシンプルなFastAPIアプリ - 実際のAPIサービスを使用
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 既存のサービスをインポート
try:
    from app.services.stock_service import StockService
    from app.services.alpha_vantage_service import alpha_vantage_service
    from app.services.enhanced_analysis_service import enhanced_analysis_service
    stock_service = StockService()
except ImportError as e:
    print(f"サービスのインポートエラー: {e}")
    stock_service = None

# FastAPIインスタンス
app = FastAPI(
    title="Stock API with Real Data",
    version="2.0.0",
    description="実際の株価データを提供するAPI"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """ルートエンドポイント"""
    return {
        "message": "Stock API with Real Data",
        "status": "running",
        "version": "2.0.0",
        "data_source": os.getenv('PRIMARY_API_PROVIDER', 'alpha_vantage')
    }

@app.get("/api/health")
def health():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "service": "stock api with real data",
        "alpha_vantage_key": "configured" if os.getenv('ALPHA_VANTAGE_API_KEY') else "not configured"
    }

@app.get("/api/stocks/search")
def search_stocks(query: str = ""):
    """銘柄検索エンドポイント - 実データを使用"""
    if not stock_service:
        # フォールバック：基本的なモックデータ
        return {"query": query, "results": [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"}
        ]}
    
    try:
        results = stock_service.search_stocks(query)
        return {"query": query, "results": results}
    except Exception as e:
        print(f"検索エラー: {str(e)}")
        # エラー時はフォールバック
        return {"query": query, "results": [], "error": str(e)}

@app.get("/api/stocks/{symbol}")
def get_stock_info(symbol: str):
    """株式情報取得エンドポイント - 実データを使用"""
    if not stock_service:
        # フォールバック：基本的なモックデータ
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol.upper()} Corporation",
            "current_price": 100.00,
            "change": 1.00,
            "change_percent": 1.0,
            "volume": 1000000,
            "error": "Service not available"
        }
    
    try:
        stock_info = stock_service.get_stock_info(symbol)
        return stock_info
    except Exception as e:
        print(f"株式情報取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{symbol}/history")
def get_price_history(symbol: str, period: str = "1mo"):
    """価格履歴取得エンドポイント - 実データを使用"""
    if not stock_service:
        # フォールバック：空のデータ
        return {
            "symbol": symbol.upper(),
            "dates": [],
            "prices": [],
            "volumes": [],
            "error": "Service not available"
        }
    
    try:
        history = stock_service.get_price_history(symbol, period)
        return history
    except Exception as e:
        print(f"価格履歴取得エラー: {str(e)}")
        return {
            "symbol": symbol.upper(),
            "dates": [],
            "prices": [],
            "volumes": [],
            "error": str(e)
        }

@app.get("/api/stocks/{symbol}/indicators")
def get_technical_indicators(symbol: str):
    """テクニカル指標取得エンドポイント - 実データを使用"""
    if not stock_service:
        # フォールバック：基本的なモックデータ
        return {
            "symbol": symbol.upper(),
            "rsi": 50.0,
            "macd": {"macd": 0, "signal": 0, "histogram": 0},
            "bollinger_bands": {"upper": 110, "middle": 100, "lower": 90},
            "moving_averages": {"sma_20": 100, "sma_50": 100, "sma_200": 100},
            "error": "Service not available"
        }
    
    try:
        indicators = stock_service.calculate_technical_indicators(symbol)
        return indicators
    except Exception as e:
        print(f"テクニカル指標取得エラー: {str(e)}")
        return {
            "symbol": symbol.upper(),
            "error": str(e)
        }

@app.get("/api/stocks/{symbol}/analysis")
def get_stock_analysis(symbol: str):
    """株式分析エンドポイント - AI分析を使用"""
    if not stock_service:
        # フォールバック：基本的なモック分析
        return {
            "symbol": symbol.upper(),
            "analysis": {
                "recommendation": "HOLD",
                "confidence": 0.5,
                "target_price": 100.0,
                "stop_loss": 95.0,
                "reasoning": ["サービスが利用できません"]
            },
            "timestamp": "2024-01-01T00:00:00Z",
            "error": "Service not available"
        }
    
    try:
        analysis = stock_service.analyze_stock(symbol)
        return analysis
    except Exception as e:
        print(f"株式分析エラー: {str(e)}")
        return {
            "symbol": symbol.upper(),
            "analysis": {
                "recommendation": "ERROR",
                "confidence": 0,
                "target_price": 0,
                "stop_loss": 0,
                "reasoning": [f"分析エラー: {str(e)}"]
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

# 以下は開発/デバッグ用のエンドポイント
@app.get("/api/debug/config")
def debug_config():
    """現在の設定を確認（開発用）"""
    return {
        "primary_api": os.getenv('PRIMARY_API_PROVIDER', 'not set'),
        "alpha_vantage_configured": bool(os.getenv('ALPHA_VANTAGE_API_KEY')),
        "environment": os.getenv('ENVIRONMENT', 'not set')
    }