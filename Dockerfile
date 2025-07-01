# 最小限Python環境
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションコピー
COPY . .

# ポート設定
ENV PORT=8000
EXPOSE 8000

# 起動 - Railway PORT環境変数を使用
CMD uvicorn simple_main:app --host 0.0.0.0 --port $PORT