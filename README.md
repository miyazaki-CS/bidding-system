# 入札案件自動収集システム 📋

[![GitHub Actions](https://github.com/miyazaki-CS/bidding-system/workflows/入札案件自動収集/badge.svg)](https://github.com/miyazaki-CS/bidding-system/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

コールセンターやキッティング業務の入札案件を日本全国の自治体から自動収集し、適合案件を通知するシステムです。

## 🎯 主要機能

- **🤖 自動収集**: 政府調達API・自治体RSSから24時間365日自動収集
- **🔍 高精度フィルタリング**: キーワード適合度スコアリング
- **📧 リアルタイム通知**: Microsoft Teams・メール通知
- **📊 Webダッシュボード**: 統計・検索・エクスポート機能
- **💰 完全無料運用**: GitHub Actions無料枠で月額0円

## 🚀 システム概要

```
GitHub Actions (毎日朝8時・夕方6時自動実行)
├── データ収集
│   ├── 政府調達情報API（官公需情報ポータルサイト）
│   └── 自治体RSS（東京都、大阪府、神奈川県等）
├── データ処理・フィルタリング
├── 通知送信（Teams・メール）
├── Webダッシュボード更新
└── データベース永続化
```

## 📈 Webダッシュボード

**ライブダッシュボード**: https://miyazaki-cs.github.io/bidding-system/

- リアルタイム統計表示
- 案件検索・フィルタリング
- CSVエクスポート機能
- レスポンシブデザイン

## 特徴
- **完全無料運用**: GitHub Actions無料枠で運用可能
- **高精度フィルタリング**: キーワードベースの適合度スコアリング
- **リアルタイム通知**: 高優先度案件の即座アラート
- **日次レポート**: 収集結果の定期レポート

## システム構成
```
src/
├── collectors/          # データ収集（政府API、RSS）
├── processors/          # データ処理・フィルタリング
├── notifications/       # メール・Slack通知
├── database/           # データベース管理
└── utils/              # ユーティリティ

config/                 # 設定ファイル
.github/workflows/      # GitHub Actions設定
```

## セットアップ

### 1. 環境変数設定
GitHub Secretsに以下を設定：

```bash
DATABASE_URL=postgresql://user:password@hostname/database
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 2. 無料データベース設定
ElephantSQL（無料10,000行）を使用：

1. https://www.elephantsql.com/ でアカウント作成
2. 無料プラン「Tiny Turtle」を選択
3. データベースURLを `DATABASE_URL` に設定

### 3. Gmail設定
1. Googleアカウントで2段階認証を有効化
2. アプリパスワードを生成
3. `EMAIL_USER` と `EMAIL_PASSWORD` に設定

### 4. Slack設定（オプション）
1. Slack Workspaceで Incoming Webhooks を作成
2. Webhook URLを `SLACK_WEBHOOK_URL` に設定

## 実行スケジュール
- **定期実行**: 毎日8:00/18:00 UTC（17:00/03:00 JST）
- **手動実行**: GitHub Actionsページから実行可能
- **処理時間**: 最大25分（GitHub Actions制限）

## 検索対象キーワード
- データ入力
- データ入力案件
- 入力作業
- キッティング
- PC設定
- システム構築
- コールセンター
- 電話受付
- 事務業務

## 通知設定
- **高優先度案件（80点以上）**: 即座にメール・Slack通知
- **中優先度案件（60点以上）**: 日次レポートに含める
- **日次レポート**: 毎日の収集結果をまとめて送信

## 開発・テスト

### ローカル実行
```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env ファイルを編集

# 実行
python src/main.py
```

### テスト実行
```bash
# データ処理テスト
python src/processors/data_processor.py

# 通知テスト
python src/notifications/notifier.py
```

## 運用コスト
- **フェーズ1（1-3ヶ月）**: 0円
  - GitHub Actions無料枠
  - ElephantSQL無料プラン
  - Gmail SMTP無料
  
- **フェーズ2（拡張時）**: 月額600円
  - Railway（PostgreSQL付き）
  
- **フェーズ3（大規模時）**: 月額500-1,000円
  - 自宅サーバー運用

## 成果指標
- **データ収集成功率**: 95%以上
- **月次案件発見数**: 50件以上
- **適合案件率**: 20%以上
- **時間削減効果**: 80%以上

## トラブルシューティング

### GitHub Actions実行エラー
1. Secretsの設定確認
2. データベース接続確認
3. 処理時間制限（25分）確認

### 通知が届かない
1. メール設定の確認
2. Slack Webhook URLの確認
3. 通知制限（日10件）の確認

### データベース容量超過
1. 古いデータの削除
2. データ保持期間の短縮
3. 有料プランへの移行

## ライセンス
MIT License

## 更新履歴
- v1.0.0: 初回リリース（GitHub Actions対応）
- v1.1.0: 適合度スコアリング機能追加
- v1.2.0: Slack通知機能追加