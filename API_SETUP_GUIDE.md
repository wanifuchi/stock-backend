# 株価API セットアップガイド

## 概要
このプロジェクトでは、実際の株価データを取得するために複数のAPIプロバイダーをサポートしています。

## 推奨APIプロバイダー

### 1. Alpha Vantage（推奨）
- **無料枠**: 1日500リクエスト、1分5リクエスト
- **取得方法**: https://www.alphavantage.co/support/#api-key
- **特徴**: 
  - リアルタイム株価
  - テクニカル指標（RSI、MACD、ボリンジャーバンド）
  - 銘柄検索機能

### 2. yfinance（フォールバック）
- **無料**: 制限なし（ただし非公式）
- **特徴**:
  - Yahoo Financeからデータを取得
  - リアルタイム株価と履歴データ
  - 自動的にフォールバックとして使用

## セットアップ手順

### 1. 環境変数ファイルの作成
```bash
cp .env.example .env
```

### 2. Alpha Vantage APIキーの取得
1. https://www.alphavantage.co/support/#api-key にアクセス
2. メールアドレスを入力してAPIキーを取得
3. `.env`ファイルに設定：
```
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
PRIMARY_API_PROVIDER=alpha_vantage
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. アプリケーションの起動
```bash
# 開発環境
python main.py

# または
uvicorn simple_main:app --reload --host 0.0.0.0 --port 8000
```

## APIエンドポイント

### 実データを返すエンドポイント

1. **銘柄検索**
```
GET /api/stocks/search?query=AAPL
```

2. **現在価格**
```
GET /api/stocks/AAPL
```

3. **価格履歴**
```
GET /api/stocks/AAPL/history?period=1mo
```

4. **テクニカル指標**
```
GET /api/stocks/AAPL/indicators
```

5. **AI分析**
```
GET /api/stocks/AAPL/analysis
```

## トラブルシューティング

### Alpha Vantageのレート制限エラー
- 1分間に5リクエストまでの制限があります
- キャッシュが自動的に動作し、同じデータの再取得を防ぎます

### yfinanceエラー
- 自動的にAlpha Vantageまたはモックデータにフォールバックします
- VPNを使用している場合は無効にしてください

### データが取得できない場合
1. `.env`ファイルが正しく設定されているか確認
2. APIキーが有効か確認
3. `/api/debug/config`エンドポイントで設定を確認

## 本番環境へのデプロイ

Railway等のPaaSにデプロイする場合：

1. 環境変数を設定：
   - `ALPHA_VANTAGE_API_KEY`
   - `PRIMARY_API_PROVIDER=alpha_vantage`

2. ポート設定を確認（環境変数`PORT`が自動的に使用されます）

3. requirements.txtの全ての依存関係がインストールされることを確認

## 注意事項

- Alpha Vantageの無料枠は1日500リクエストまでです
- 本番環境では適切なキャッシュ戦略を実装することを推奨します
- 機密情報（APIキー）は絶対にコードにハードコーディングしないでください