"""
株式投資アドバイスアプリ - Railway用エントリーポイント v2.0.0
高度な売買タイミング判断システム搭載
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)