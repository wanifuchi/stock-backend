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
    # クエリに基づいたフィルタリング
    all_stocks = [
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"}
    ]
    
    if not query:
        return {"query": query, "results": all_stocks}
    
    # クエリに一致する株式をフィルタリング
    filtered = [
        stock for stock in all_stocks 
        if query.upper() in stock["symbol"] or query.upper() in stock["name"].upper()
    ]
    
    return {"query": query, "results": filtered}

@app.get("/api/stocks/{symbol}")
def get_stock_info(symbol: str):
    # 個別株式情報のモックデータ
    mock_data = {
        "NVDA": {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation", 
            "current_price": 875.50,
            "change": 12.45,
            "change_percent": 1.44,
            "volume": 45678900,
            "market_cap": 2150000000000
        },
        "AAPL": {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": 189.75,
            "change": -2.15,
            "change_percent": -1.12,
            "volume": 52345600,
            "market_cap": 2950000000000
        }
    }
    
    return mock_data.get(symbol.upper(), {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Company",
        "current_price": 100.00,
        "change": 0.00,
        "change_percent": 0.00,
        "volume": 1000000,
        "market_cap": 10000000000
    })

@app.get("/api/stocks/{symbol}/history")
def get_price_history(symbol: str, period: str = "1mo"):
    # 価格履歴のモックデータ
    import random
    dates = [f"2024-06-{i:02d}" for i in range(1, 31)]
    base_price = 150.0
    prices = []
    volumes = []
    
    for i in range(30):
        price = base_price + random.uniform(-10, 10)
        volume = random.randint(1000000, 10000000)
        prices.append(round(price, 2))
        volumes.append(volume)
        base_price = price
    
    return {
        "symbol": symbol.upper(),
        "dates": dates,
        "prices": prices,
        "volumes": volumes
    }

@app.get("/api/stocks/{symbol}/indicators")
def get_technical_indicators(symbol: str):
    # テクニカル指標のモックデータ
    import random
    return {
        "symbol": symbol.upper(),
        "rsi": round(random.uniform(30, 70), 2),
        "macd": {
            "macd": round(random.uniform(-2, 2), 2),
            "signal": round(random.uniform(-2, 2), 2),
            "histogram": round(random.uniform(-1, 1), 2)
        },
        "bollinger_bands": {
            "upper": round(random.uniform(160, 180), 2),
            "middle": round(random.uniform(140, 160), 2),
            "lower": round(random.uniform(120, 140), 2)
        },
        "moving_averages": {
            "sma_20": round(random.uniform(140, 160), 2),
            "sma_50": round(random.uniform(130, 150), 2),
            "sma_200": round(random.uniform(120, 140), 2)
        }
    }

@app.get("/api/stocks/{symbol}/analysis")
def get_stock_analysis(symbol: str):
    # 株式分析のモックデータ
    import random
    recommendations = ["BUY", "SELL", "HOLD"]
    
    return {
        "symbol": symbol.upper(),
        "analysis": {
            "recommendation": random.choice(recommendations),
            "confidence": round(random.uniform(0.6, 0.9), 2),
            "target_price": round(random.uniform(160, 200), 2),
            "stop_loss": round(random.uniform(120, 140), 2),
            "reasoning": [
                f"{symbol.upper()}の技術的指標は強気を示している",
                "市場環境は良好",
                "業績予想は堅調"
            ]
        },
        "timestamp": "2024-06-30T12:00:00Z"
    }