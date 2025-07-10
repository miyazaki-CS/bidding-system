import os

class Settings:
    def __init__(self):
        # Teams通知設定
        self.teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL', '')
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'

        # データベース設定
        self.database_path = 'data/bids.db'

        # 検索キーワード
        self.search_keywords = [
            'データ入力',
            'データ入力案件',
            '入力作業',
            'キッティング',
            'PC設定',
            'コールセンター',
            '電話受付',
            '事務業務'
        ]

        # 通知設定
        self.notification_enabled = bool(self.teams_webhook_url)

settings = Settings()
