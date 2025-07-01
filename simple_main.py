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
    # 現実的な価格データベース
    realistic_data = {
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
        },
        "MSFT": {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "current_price": 425.30,
            "change": 5.67,
            "change_percent": 1.35,
            "volume": 28456700,
            "market_cap": 3150000000000
        }
    }
    
    # デフォルトデータ（現実的な価格レンジ）
    import random
    if symbol.upper() not in realistic_data:
        base_price = random.uniform(50, 300)
        change = random.uniform(-10, 10)
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol.upper()} Company",
            "current_price": round(base_price, 2),
            "change": round(change, 2),
            "change_percent": round((change / base_price) * 100, 2),
            "volume": random.randint(1000000, 50000000),
            "market_cap": random.randint(10000000000, 500000000000)
        }
    
    return realistic_data[symbol.upper()]

@app.get("/api/stocks/{symbol}/history")
def get_price_history(symbol: str, period: str = "1mo"):
    # 現在価格と整合性のある価格履歴
    import random
    
    # 現在価格を取得
    current_data = get_stock_info(symbol)
    current_price = current_data["current_price"]
    
    dates = [f"2024-06-{i:02d}" for i in range(1, 31)]
    prices = []
    volumes = []
    
    # 30日前の価格を現在価格の90-95%に設定
    start_price = current_price * random.uniform(0.90, 0.95)
    
    # 現在価格に向けてリアルな価格推移を生成
    for i in range(30):
        # 線形補間 + ランダムな変動
        progress = i / 29  # 0から1へ
        base_price = start_price + (current_price - start_price) * progress
        
        # 日々の変動は±3%以内
        daily_variation = base_price * random.uniform(-0.03, 0.03)
        price = base_price + daily_variation
        
        # 最終日は現在価格に設定
        if i == 29:
            price = current_price
            
        volume = random.randint(
            int(current_data["volume"] * 0.5), 
            int(current_data["volume"] * 1.5)
        )
        
        prices.append(round(price, 2))
        volumes.append(volume)
    
    return {
        "symbol": symbol.upper(),
        "dates": dates,
        "prices": prices,
        "volumes": volumes
    }

@app.get("/api/stocks/{symbol}/indicators")
def get_technical_indicators(symbol: str):
    # 現在価格と整合性のあるテクニカル指標
    import random
    
    # 現在価格を取得
    current_data = get_stock_info(symbol)
    current_price = current_data["current_price"]
    
    # ボリンジャーバンド（現在価格を中央に±5-10%）
    volatility = random.uniform(0.05, 0.10)
    bb_middle = current_price * random.uniform(0.98, 1.02)  # 中央線
    bb_upper = bb_middle * (1 + volatility)
    bb_lower = bb_middle * (1 - volatility)
    
    # 移動平均線（現在価格周辺に配置）
    sma_20 = current_price * random.uniform(0.95, 1.05)
    sma_50 = current_price * random.uniform(0.90, 1.10) 
    sma_200 = current_price * random.uniform(0.85, 1.15)
    
    return {
        "symbol": symbol.upper(),
        "rsi": round(random.uniform(30, 70), 2),
        "macd": {
            "macd": round(random.uniform(-2, 2), 2),
            "signal": round(random.uniform(-2, 2), 2),
            "histogram": round(random.uniform(-1, 1), 2)
        },
        "bollinger_bands": {
            "upper": round(bb_upper, 2),
            "middle": round(bb_middle, 2),
            "lower": round(bb_lower, 2)
        },
        "moving_averages": {
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2)
        }
    }

@app.get("/api/stocks/{symbol}/analysis")
def get_stock_analysis(symbol: str):
    # 現在価格と整合性のある株式分析
    import random
    
    # 現在価格を取得
    current_data = get_stock_info(symbol)
    current_price = current_data["current_price"]
    
    recommendations = ["BUY", "SELL", "HOLD"]
    recommendation = random.choice(recommendations)
    
    # 推奨に基づいた論理的な目標価格・損切り設定
    if recommendation == "BUY":
        target_price = current_price * random.uniform(1.05, 1.20)  # 5-20%上昇目標
        stop_loss = current_price * random.uniform(0.85, 0.95)     # 5-15%下落で損切り
        reasoning = [
            f"{symbol.upper()}の技術的指標は強気を示している",
            "市場センチメントがポジティブ",
            "ファンダメンタルズが改善傾向"
        ]
    elif recommendation == "SELL":
        target_price = current_price * random.uniform(0.80, 0.95)  # 5-20%下落予想
        stop_loss = current_price * random.uniform(1.05, 1.15)     # 5-15%上昇で損切り
        reasoning = [
            f"{symbol.upper()}は過大評価の可能性",
            "市場環境の悪化懸念",
            "業績下方修正リスク"
        ]
    else:  # HOLD
        target_price = current_price * random.uniform(0.98, 1.08)  # ±2-8%レンジ
        stop_loss = current_price * random.uniform(0.90, 0.95)     # 5-10%下落で損切り
        reasoning = [
            f"{symbol.upper()}は適正価格で推移",
            "様子見の局面",
            "明確な方向性待ち"
        ]
    
    return {
        "symbol": symbol.upper(),
        "analysis": {
            "recommendation": recommendation,
            "confidence": round(random.uniform(0.6, 0.9), 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "reasoning": reasoning
        },
        "timestamp": "2024-06-30T12:00:00Z"
    }