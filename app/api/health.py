"""
ヘルスチェック用エンドポイント
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """
    APIサーバーのヘルスチェック
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Stock Advisor API"
    }

@router.get("/ready")
async def readiness_check():
    """
    サービスの準備状況チェック
    """
    checks = {}
    overall_status = "ready"
    
    # データベース接続確認
    try:
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), "../../data/stocks.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # 外部API接続確認（Yahoo Finance）
    try:
        import yfinance as yf
        # 簡単なテスト銘柄でデータ取得を試行
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info and "symbol" in info:
            checks["external_apis"] = "ok"
        else:
            checks["external_apis"] = "warning: limited data"
            overall_status = "degraded"
    except Exception as e:
        checks["external_apis"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # システムリソース確認
    try:
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        checks["system_resources"] = {
            "cpu_usage": f"{cpu_percent}%",
            "memory_usage": f"{memory_percent}%",
            "status": "ok" if cpu_percent < 90 and memory_percent < 90 else "warning"
        }
        if cpu_percent >= 90 or memory_percent >= 90:
            overall_status = "degraded"
    except Exception as e:
        checks["system_resources"] = f"error: {str(e)}"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }