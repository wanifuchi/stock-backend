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

# CORS設定（本番環境対応）
origins = [
    "http://localhost:3000",  # 開発環境
    "http://localhost:3001",  # 開発環境
    "https://stock-frontend-mu.vercel.app",  # Vercel本番環境
    "https://stock-frontend-kcn1oe96y-wanifucks.vercel.app",  # Vercelデプロイメント環境
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)