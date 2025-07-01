# 軽量で確実なPython環境
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# 必要最小限のシステムパッケージ
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# Railway用PORT設定
ENV PORT=8000

# アプリケーション起動
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"]