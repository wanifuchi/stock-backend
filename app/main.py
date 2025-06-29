"""
株式投資アドバイスアプリ - バックエンドAPIサーバー
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.api import stocks, health
from app.database.init_db import init_database

# アプリケーションのライフサイクル管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の処理
    print("アプリケーションを起動しています...")
    init_database()
    yield
    # 終了時の処理
    print("アプリケーションを終了しています...")

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Stock Advisor API",
    description="株式投資アドバイスアプリケーションのバックエンドAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定（開発環境用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.jsのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターの登録
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Stock Advisor API へようこそ！",
        "documentation": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)