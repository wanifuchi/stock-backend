"""
株式データAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.services.stock_service import StockService

router = APIRouter()
stock_service = StockService()

# レスポンスモデル
class StockInfo(BaseModel):
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None

class StockPriceHistory(BaseModel):
    symbol: str
    dates: List[str]
    prices: List[float]
    volumes: List[int]

class TechnicalIndicators(BaseModel):
    symbol: str
    rsi: Optional[float] = None
    macd: Optional[dict] = None
    bollinger_bands: Optional[dict] = None
    moving_averages: Optional[dict] = None

@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="検索クエリ（銘柄コードまたは企業名）")
):
    """
    株式銘柄を検索
    """
    results = stock_service.search_stocks(query)
    return {
        "query": query,
        "results": results
    }

@router.get("/{symbol}", response_model=StockInfo)
async def get_stock_info(symbol: str):
    """
    指定銘柄の現在情報を取得
    """
    try:
        info = stock_service.get_stock_info(symbol)
        return StockInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"株式情報の取得に失敗しました: {str(e)}")

@router.get("/{symbol}/history", response_model=StockPriceHistory)
async def get_price_history(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """
    株価履歴データを取得
    """
    try:
        history = stock_service.get_price_history(symbol, period)
        return StockPriceHistory(**history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"価格履歴の取得に失敗しました: {str(e)}")

@router.get("/{symbol}/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(symbol: str):
    """
    テクニカル指標を計算・取得
    """
    try:
        indicators = stock_service.calculate_technical_indicators(symbol)
        return TechnicalIndicators(**indicators)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テクニカル指標の計算に失敗しました: {str(e)}")

@router.get("/{symbol}/analysis")
async def get_stock_analysis(symbol: str):
    """
    AIによる株式分析と売買アドバイス
    """
    try:
        analysis = stock_service.analyze_stock(symbol)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"株式分析に失敗しました: {str(e)}")

@router.get("/debug/test")
async def debug_test():
    """
    デバッグ用テストエンドポイント
    """
    import yfinance as yf
    try:
        # 簡単なテスト
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        return {
            "status": "success",
            "yfinance_version": yf.__version__,
            "info_keys": len(info),
            "sample_data": {
                "symbol": info.get("symbol"),
                "longName": info.get("longName"),
                "currentPrice": info.get("currentPrice")
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }