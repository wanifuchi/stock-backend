# Stock Backend API

## 概要
次世代の株式分析プラットフォームのバックエンドAPI。FastAPIベースで高速な分析結果を提供。

## 機能
- 株式銘柄検索
- リアルタイム株価情報
- テクニカル指標計算
- AI駆動の投資分析
- 強化分析エンジン（多様性のある現実的な分析結果）

## デプロイ
Railway.appでホスティング

## 環境変数
- `PORT`: サーバーポート（Railway自動設定）
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage APIキー（オプション）

## ローカル開発
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```