"""
緊急復旧用シンプルエントリーポイント
"""
import os
import uvicorn
from simple_main_real import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Real Stock API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)