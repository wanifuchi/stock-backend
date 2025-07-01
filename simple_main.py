"""
超シンプルなFastAPIアプリ - Railway起動テスト用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPIインスタンス
app = FastAPI(title="Simple Stock API", version="0.1.0")

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
    return {"message": "Hello World", "status": "running"}

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "simple stock api"}

@app.get("/api/stocks/search")
def search_stocks(query: str = ""):
    # 超シンプルなモックレスポンス
    return {
        "query": query,
        "results": [
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"}
        ]
    }