"""
シンプルなデータベースアクセスクラス
SQLiteを直接使用してSQLAlchemyに依存しない実装
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any

class SimpleDatabaseManager:
    """シンプルなデータベース管理クラス"""
    
    def __init__(self, db_path: str = "bidding_system.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """データベースファイルとテーブルが存在しない場合は作成"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # 必要なテーブルを作成
            self.create_tables(cursor)
            self.insert_default_data(cursor)
            
            conn.commit()
        finally:
            conn.close()
    
    def create_tables(self, cursor):
        """必要なテーブルを作成"""
        
        # procurement_entries テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS procurement_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            organization TEXT,
            region TEXT,
            budget_amount INTEGER,
            published_date DATE,
            deadline_date DATE,
            source_url TEXT,
            source_type TEXT,
            relevance_score INTEGER DEFAULT 0,
            keywords_matched TEXT DEFAULT '[]',
            processed BOOLEAN DEFAULT FALSE,
            notified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # filter_keywords テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS filter_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            category TEXT DEFAULT 'include',
            weight INTEGER DEFAULT 1,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # notification_history テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            notification_type TEXT,
            recipient TEXT,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_id) REFERENCES procurement_entries (id)
        )
        """)
        
        # system_logs テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            module TEXT,
            additional_data TEXT,
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    
    def insert_default_data(self, cursor):
        """デフォルトデータを挿入"""
        
        # デフォルトキーワードを挿入
        default_keywords = [
            ('データ入力', 'include', 10),
            ('データ入力案件', 'include', 10),
            ('入力作業', 'include', 8),
            ('キッティング', 'include', 9),
            ('PC設定', 'include', 7),
            ('コールセンター', 'include', 8),
            ('電話受付', 'include', 6),
            ('事務業務', 'include', 5),
            ('清掃', 'exclude', -10),
            ('警備', 'exclude', -8),
            ('建設', 'exclude', -8),
            ('工事', 'exclude', -8),
            ('修繕', 'exclude', -5),
            ('保守', 'exclude', -3)
        ]
        
        # 既存のキーワードをチェックして重複を避ける
        for keyword, category, weight in default_keywords:
            cursor.execute(
                "SELECT COUNT(*) FROM filter_keywords WHERE keyword = ? AND category = ?",
                (keyword, category)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO filter_keywords (keyword, category, weight) VALUES (?, ?, ?)",
                    (keyword, category, weight)
                )
    
    def get_connection(self):
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """クエリを実行して結果を返す"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # SELECT文の場合は結果を返す
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def insert_procurement_entry(self, entry_data: Dict) -> int:
        """入札案件を挿入"""
        query = """
        INSERT INTO procurement_entries (
            title, description, organization, region, budget_amount,
            published_date, deadline_date, source_url, source_type,
            relevance_score, keywords_matched, processed, notified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            entry_data.get('title', ''),
            entry_data.get('description', ''),
            entry_data.get('organization', ''),
            entry_data.get('region', ''),
            entry_data.get('budget_amount'),
            entry_data.get('published_date'),
            entry_data.get('deadline_date'),
            entry_data.get('source_url', ''),
            entry_data.get('source_type', ''),
            entry_data.get('relevance_score', 0),
            entry_data.get('keywords_matched', '[]'),
            entry_data.get('processed', False),
            entry_data.get('notified', False)
        )
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_procurement_entries(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """入札案件を取得"""
        query = """
        SELECT * FROM procurement_entries 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """
        return self.execute_query(query, (limit, offset))
    
    def get_entries_by_score(self, min_score: int) -> List[Dict]:
        """適合度スコアでフィルタリング"""
        query = """
        SELECT * FROM procurement_entries 
        WHERE relevance_score >= ? 
        ORDER BY relevance_score DESC, created_at DESC
        """
        return self.execute_query(query, (min_score,))
    
    def check_duplicate_entry(self, title: str, organization: str) -> bool:
        """重複チェック"""
        query = """
        SELECT COUNT(*) as count FROM procurement_entries 
        WHERE title = ? AND organization = ?
        """
        result = self.execute_query(query, (title, organization))
        return result[0]['count'] > 0
    
    def insert_notification_history(self, entry_id: int, notification_type: str, recipient: str, success: bool = True, error_message: str = None):
        """通知履歴を挿入"""
        query = """
        INSERT INTO notification_history (entry_id, notification_type, recipient, success, error_message)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (entry_id, notification_type, recipient, success, error_message)
        self.execute_query(query, params)
    
    def insert_system_log(self, level: str, message: str, module: str, additional_data: Dict = None):
        """システムログを挿入"""
        query = """
        INSERT INTO system_logs (level, message, module, additional_data)
        VALUES (?, ?, ?, ?)
        """
        additional_data_json = json.dumps(additional_data) if additional_data else None
        params = (level, message, module, additional_data_json)
        self.execute_query(query, params)
    
    def get_database_stats(self) -> Dict:
        """データベース統計情報を取得"""
        stats = {}
        
        # 各テーブルの行数
        tables = ['procurement_entries', 'filter_keywords', 'notification_history', 'system_logs']
        for table in tables:
            result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = result[0]['count']
        
        # 適合度別統計
        high_priority = self.execute_query("SELECT COUNT(*) as count FROM procurement_entries WHERE relevance_score >= 80")
        medium_priority = self.execute_query("SELECT COUNT(*) as count FROM procurement_entries WHERE relevance_score >= 60 AND relevance_score < 80")
        
        stats['high_priority_count'] = high_priority[0]['count']
        stats['medium_priority_count'] = medium_priority[0]['count']
        stats['total_entries'] = stats['procurement_entries']
        
        return stats
    
    def cleanup_old_data(self, days: int = 30):
        """古いデータを削除"""
        # 古い案件を削除
        query = """
        DELETE FROM procurement_entries 
        WHERE created_at < datetime('now', '-{} days')
        """.format(days)
        self.execute_query(query)
        
        # 古いログを削除
        query = """
        DELETE FROM system_logs 
        WHERE execution_time < datetime('now', '-7 days')
        """
        self.execute_query(query)
    
    def get_filter_keywords(self, category: str = None) -> List[Dict]:
        """フィルタキーワードを取得"""
        if category:
            query = "SELECT * FROM filter_keywords WHERE category = ? AND active = 1"
            return self.execute_query(query, (category,))
        else:
            query = "SELECT * FROM filter_keywords WHERE active = 1"
            return self.execute_query(query)

# 使用例とテスト
def test_simple_database():
    """シンプルデータベースのテスト"""
    print("=== シンプルデータベーステスト ===")
    
    try:
        db = SimpleDatabaseManager()
        
        # テストデータ挿入
        test_entry = {
            'title': 'シンプルDBテスト案件',
            'description': 'テスト用の説明',
            'organization': 'テスト機関',
            'region': '東京都',
            'budget_amount': 1000000,
            'published_date': datetime.now().date().isoformat(),
            'deadline_date': datetime.now().date().isoformat(),
            'source_url': 'https://example.com/test',
            'source_type': 'test',
            'relevance_score': 85,
            'keywords_matched': '["テスト"]',
            'processed': True,
            'notified': False
        }
        
        # 重複チェック
        if not db.check_duplicate_entry(test_entry['title'], test_entry['organization']):
            entry_id = db.insert_procurement_entry(test_entry)
            print(f"✓ テストデータ挿入成功: ID={entry_id}")
        else:
            print("✓ テストデータは既に存在します")
        
        # データ取得
        entries = db.get_procurement_entries(limit=5)
        print(f"✓ 案件取得成功: {len(entries)}件")
        
        # 高優先度案件
        high_priority = db.get_entries_by_score(80)
        print(f"✓ 高優先度案件: {len(high_priority)}件")
        
        # 統計情報
        stats = db.get_database_stats()
        print(f"✓ 統計情報: {stats}")
        
        # フィルタキーワード取得
        keywords = db.get_filter_keywords('include')
        print(f"✓ 対象キーワード: {len(keywords)}件")
        
        return True
        
    except Exception as e:
        print(f"✗ シンプルデータベーステストエラー: {e}")
        return False

if __name__ == "__main__":
    test_simple_database()
