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

# 起動 - main.pyでPORT環境変数を確実に処理
CMD ["python", "main.py"]