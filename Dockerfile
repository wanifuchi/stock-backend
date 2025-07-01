# 標準Python環境でのシンプルなDockerfile
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新とgccインストール
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ポート公開
EXPOSE $PORT

# アプリケーション起動
CMD python -m uvicorn main:app --host 0.0.0.0 --port $PORT