import os

class Settings:
    def __init__(self):
        # ログ設定
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = 'logs/bidding_system.log'

        # Teams通知設定
        self.teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL', '')
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'

        # メール設定（空の値でエラー回避）
        self.email_enabled = False
        self.email_sender = ''
        self.email_password = ''
        self.email_recipient = ''

        # データベース設定
        self.database_path = 'data/bids.db'
        self.database_url = f'sqlite:///{self.database_path}'

        # API設定（重要：不足していた項目）
        self.government_api_url = 'https://www.geps.go.jp'
        self.api_timeout = 30
        self.api_retry_count = 3  # ← これが不足していた
        self.api_retry_delay = 2
        self.request_delay = 2
        self.max_concurrent_requests = 5

        # 検索設定
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
        self.notification_threshold = 60
        self.max_notifications_per_run = 10

        # RSS設定
        self.rss_urls = [
            'https://www.city.shibuya.tokyo.jp/rss/tender.xml',
            'https://www.pref.osaka.lg.jp/rss/tender.xml'
        ]
        self.rss_timeout = 15

        # システム設定
        self.max_execution_time = 1400  # 23分（GitHub Actions制限内）
        self.cleanup_old_data_days = 30
        self.enable_debug_mode = self.test_mode

settings = Settings()
