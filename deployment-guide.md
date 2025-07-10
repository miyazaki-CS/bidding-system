# 🚀 入札案件自動収集システム - 運用準備ガイド

## 📋 運用準備ステップ概要

システム開発が完了しました。24時間365日稼働する自動システムの運用開始まで、以下のステップを進めます。

### Phase 1: GitHubリポジトリ準備 (15分)
1. GitHubアカウント確認
2. 新規リポジトリ作成
3. プロジェクトファイルアップロード

### Phase 2: 認証・通知設定 (20分) 
4. Gmail App Password生成
5. Microsoft Teams Webhook作成
6. GitHub Secrets設定

### Phase 3: 自動実行・公開設定 (10分)
7. GitHub Actions有効化確認
8. GitHub Pages設定
9. 初回テスト実行

### Phase 4: 運用開始・監視 (5分)
10. システム稼働確認
11. 通知テスト
12. 監視・保守計画確認

**合計所要時間**: 約50分

---

## Phase 1: GitHubリポジトリ準備 🐙

### ステップ1: GitHubアカウント確認
- GitHubアカウントが必要（未作成の場合: https://github.com）
- 2段階認証の有効化を推奨

### ステップ2: 新規リポジトリ作成
1. GitHub > **Repositories** > **New**
2. Repository name: `bidding-system` (任意)
3. **Public** を選択（GitHub Pages使用のため）
4. **Create repository**

### ステップ3: プロジェクトファイルアップロード

**方法A: GitHub Web UI使用（推奨）**
```bash
# ローカルでファイル準備
cd C:\ClaudeCode\project2

# 不要ファイル除外（.gitignoreも作成済み）
# 以下のフォルダ/ファイルをZIP化またはGitHub Web UIでアップロード:
# - .github/
# - src/
# - docs/
# - config/
# - requirements.txt
# - CLAUDE.md
# - その他必要ファイル
```

**方法B: Git コマンド使用**
```bash
cd C:\ClaudeCode\project2
git init
git add .
git commit -m "Initial commit: 入札案件自動収集システム"
git branch -M main
git remote add origin https://github.com/[username]/bidding-system.git
git push -u origin main
```

---

## Phase 2: 認証・通知設定 🔐

### ステップ4: Gmail App Password生成

1. **Googleアカウント設定**
   - https://myaccount.google.com にアクセス
   - **セキュリティ** > **Googleへのログイン**

2. **2段階認証有効化**（未設定の場合）
   - **2段階認証プロセス** > **使ってみる**
   - 電話番号またはSMSで設定

3. **アプリパスワード生成**
   - **アプリパスワード** > **アプリを選択**
   - **その他（カスタム名）** > `入札案件システム`
   - **生成** をクリック
   - 表示された16文字のパスワードをコピー保存
   - 例: `abcd efgh ijkl mnop`

### ステップ5: Microsoft Teams Webhook作成

1. **Teamsチャンネル選択**
   - 通知を受けたいチャンネルを開く
   - 例: `#入札案件` または既存チャンネル

2. **Incoming Webhook追加**
   - チャンネル名横の **...** > **コネクタ**
   - **Incoming Webhook** を検索 > **構成**

3. **Webhook設定**
   - 名前: `入札案件システム`
   - アイコン: 任意（オプション）
   - **作成** をクリック

4. **Webhook URL取得**
   - 生成されたURLをコピー保存
   - 例: `https://outlook.office.com/webhook/...`

### ステップ6: GitHub Secrets設定

1. **リポジトリ設定**
   - GitHubリポジトリ > **Settings**
   - **Secrets and variables** > **Actions**

2. **Secrets追加**
   **New repository secret** で以下を設定:

   | Secret名 | 値 | 説明 |
   |----------|----|----|
   | `EMAIL_SENDER` | `your-email@gmail.com` | 送信用Gmailアドレス |
   | `EMAIL_PASSWORD` | `abcd efgh ijkl mnop` | 生成したアプリパスワード |
   | `EMAIL_RECIPIENT` | `notifications@yourcompany.com` | 通知受信先メール |
   | `TEAMS_WEBHOOK_URL` | `https://outlook.office.com/webhook/...` | Teams Webhook URL |

---

## Phase 3: 自動実行・公開設定 ⚙️

### ステップ7: GitHub Actions有効化確認

1. **Actions確認**
   - リポジトリ > **Actions** タブ
   - 「**入札案件自動収集**」ワークフローが表示される

2. **権限設定**
   - **Settings** > **Actions** > **General**
   - **Allow all actions and reusable workflows** を選択

### ステップ8: GitHub Pages設定

1. **Pages設定**
   - **Settings** > **Pages**
   - **Source**: Deploy from a branch
   - **Branch**: main
   - **Folder**: /docs
   - **Save** をクリック

2. **URL確認**
   - 数分後にWebダッシュボードのURLが表示
   - 例: `https://[username].github.io/bidding-system/`

### ステップ9: 初回テスト実行

1. **手動実行**
   - **Actions** > **入札案件自動収集**
   - **Run workflow** > **テストモード: true** > **Run workflow**

2. **実行確認**
   - 実行ログでエラーがないか確認
   - 約2-5分で完了

---

## Phase 4: 運用開始・監視 📊

### ステップ10: システム稼働確認

1. **ダッシュボード確認**
   - GitHub PagesのURLにアクセス
   - データが表示されることを確認

2. **自動実行スケジュール確認**
   - 毎日朝8時JST（23:00 UTC）
   - 毎日夕方6時JST（09:00 UTC）

### ステップ11: 通知テスト

1. **テスト通知確認**
   - Teamsチャンネルに通知が届くか確認
   - メールに通知が届くか確認

2. **通知内容確認**
   - 高優先度アラート形式
   - 日次レポート形式

### ステップ12: 監視・保守計画

**月次監視項目:**
- GitHub Actions使用時間確認
- 発見案件数の分析
- システムエラーの確認

**データダウンロード:**
- **Actions** > **Artifacts** から実行結果をダウンロード可能
- データベースファイル、ログファイルを取得

---

## 🎉 運用開始完了チェックリスト

- [ ] GitHubリポジトリ作成・ファイルアップロード
- [ ] Gmail App Password生成・設定
- [ ] Teams Webhook作成・設定  
- [ ] GitHub Secrets設定完了
- [ ] GitHub Actions初回テスト実行成功
- [ ] GitHub Pages Webダッシュボード表示確認
- [ ] Teams・メール通知テスト成功
- [ ] 自動実行スケジュール確認

**全て完了すると、24時間365日稼働する入札案件自動収集システムが運用開始されます！**

---

## 📞 トラブルシューティング・サポート

### よくある問題
- **Actions実行失敗**: Secrets設定を再確認
- **通知が届かない**: Webhook URL・メール設定を確認
- **ダッシュボード表示されない**: GitHub Pages設定を確認

### 追加カスタマイズ
- 検索キーワード追加: `config/settings.py`
- 通知頻度調整: `config/settings.py`
- ダッシュボードデザイン変更: `docs/index.html`

システム運用開始の準備が整いました！Phase 1から順番に進めていきましょう。