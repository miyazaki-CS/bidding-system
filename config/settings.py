import os

class Settings:
    def __init__(self):
        # ログ設定
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = 'logs/bidding_system.log'
        
        # Teams通知設定
        self.teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL', '')
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        # 検索キーワード
        self.target_keywords = [
            'データ入力',
            'データ入力案件', 
            '入力作業',
            'キッティング',
            'PC設定',
            'コールセンター',
            '電話受付',
            '事務業務'
        ]
        
        # 除外キーワード
        self.exclude_keywords = [
            '清掃',
            '警備',
            '建設'
        ]
        
        # API設定
        self.api_timeout = 30
        self.api_retry_count = 3
        self.api_retry_delay = 2
        self.government_api_base_url = 'https://www.geps.go.jp'
        
        # メール設定（Teams通知のみなのでダミー値）
        self.email_user = 'dummy@example.com'
        self.email_password = 'dummy'
        self.email_to = 'dummy@example.com'
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        
        # データベース設定
        self.database_url = 'sqlite:///data/bids.db'
        
        # スコア設定
        self.high_score_threshold = 80
        self.medium_score_threshold = 60
        
        # 通知設定
        self.max_daily_notifications = 10
        
        # 実行制限
        self.max_processing_time = 1400  # 23分
        self.max_entries_per_run = 100
        self.data_retention_days = 30

settings = Settings()
