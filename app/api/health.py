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
    # TODO: データベース接続やAPIキーの確認などを実装
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": "ok",
            "external_apis": "ok"
        }
    }