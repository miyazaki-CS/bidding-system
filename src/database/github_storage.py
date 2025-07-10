"""
GitHub Actions用データベース永続化
GitHub Actionsの実行間でデータを保持するための仕組み
"""

import os
import json
import sqlite3
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class GitHubStorageManager:
    """GitHub Actions環境でのデータ永続化管理"""
    
    def __init__(self, db_path: str = "bidding_system.db"):
        self.db_path = db_path
        self.backup_dir = "database_backups"
        self.max_backups = 30  # 30日分のバックアップを保持
        
    def create_backup_directory(self):
        """バックアップディレクトリを作成"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def export_database_to_json(self) -> Dict[str, Any]:
        """データベースをJSONファイルにエクスポート"""
        if not os.path.exists(self.db_path):
            return {"tables": {}, "metadata": {"export_date": datetime.now().isoformat()}}
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # エクスポートデータ構造
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "tables": {}
            }
            
            # 全テーブルの取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table["name"]
                
                # テーブルデータの取得
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # 辞書形式に変換
                export_data["tables"][table_name] = [
                    dict(row) for row in rows
                ]
                
                print(f"エクスポート: {table_name} テーブル ({len(rows)}件)")
            
            conn.close()
            return export_data
            
        except Exception as e:
            print(f"データベースエクスポートエラー: {e}")
            return {"tables": {}, "metadata": {"export_date": datetime.now().isoformat(), "error": str(e)}}
    
    def import_database_from_json(self, import_data: Dict[str, Any]) -> bool:
        """JSONファイルからデータベースをインポート"""
        try:
            # データベース初期化
            from scripts.init_sqlite import create_database
            create_database(self.db_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # データの復元
            for table_name, rows in import_data.get("tables", {}).items():
                if not rows:
                    continue
                
                # 既存データの削除
                cursor.execute(f"DELETE FROM {table_name}")
                
                # データの挿入
                for row in rows:
                    columns = list(row.keys())
                    placeholders = ["?" for _ in columns]
                    values = [row[col] for col in columns]
                    
                    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    cursor.execute(sql, values)
                
                print(f"インポート: {table_name} テーブル ({len(rows)}件)")
            
            conn.commit()
            conn.close()
            
            metadata = import_data.get("metadata", {})
            print(f"データベース復元完了: {metadata.get('export_date', '不明')}")
            return True
            
        except Exception as e:
            print(f"データベースインポートエラー: {e}")
            return False
    
    def save_backup(self) -> bool:
        """現在のデータベースをバックアップとして保存"""
        try:
            self.create_backup_directory()
            
            # バックアップファイル名（日付付き）
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # データベースをJSONにエクスポート
            export_data = self.export_database_to_json()
            
            # JSONファイルとして保存
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"バックアップ保存: {backup_path}")
            
            # 古いバックアップの清理
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"バックアップ保存エラー: {e}")
            return False
    
    def restore_latest_backup(self) -> bool:
        """最新のバックアップからデータベースを復元"""
        try:
            if not os.path.exists(self.backup_dir):
                print("バックアップディレクトリが存在しません")
                return False
            
            # 最新のバックアップファイルを検索
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("backup_") and f.endswith(".json")]
            
            if not backup_files:
                print("バックアップファイルが見つかりません")
                return False
            
            # 最新ファイルを選択
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(self.backup_dir, latest_backup)
            
            # バックアップファイルの読み込み
            with open(backup_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # データベースの復元
            result = self.import_database_from_json(import_data)
            
            if result:
                print(f"データベース復元成功: {latest_backup}")
            else:
                print(f"データベース復元失敗: {latest_backup}")
            
            return result
            
        except Exception as e:
            print(f"バックアップ復元エラー: {e}")
            return False
    
    def cleanup_old_backups(self):
        """古いバックアップファイルを削除"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("backup_") and f.endswith(".json")]
            backup_files.sort()
            
            # 保持する件数を超えた場合、古いファイルを削除
            if len(backup_files) > self.max_backups:
                files_to_delete = backup_files[:-self.max_backups]
                
                for filename in files_to_delete:
                    file_path = os.path.join(self.backup_dir, filename)
                    os.remove(file_path)
                    print(f"古いバックアップを削除: {filename}")
            
        except Exception as e:
            print(f"バックアップ清理エラー: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """データベースの統計情報を取得"""
        try:
            if not os.path.exists(self.db_path):
                return {"total_records": 0, "tables": {}}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {"tables": {}, "total_records": 0}
            
            # 全テーブルの統計
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                stats["tables"][table_name] = count
                stats["total_records"] += count
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"統計情報取得エラー: {e}")
            return {"total_records": 0, "tables": {}, "error": str(e)}


def initialize_persistent_database():
    """GitHub Actions用の永続化データベースを初期化"""
    print("=== GitHub Actions 永続化データベース初期化 ===")
    
    storage_manager = GitHubStorageManager()
    
    # 既存のバックアップから復元を試行
    print("既存バックアップからの復元を試行中...")
    restored = storage_manager.restore_latest_backup()
    
    if not restored:
        print("バックアップが見つからないため、新規データベースを作成...")
        # 新規データベース作成
        from scripts.init_sqlite import create_database
        create_database("bidding_system.db")
    
    # 統計情報を表示
    stats = storage_manager.get_database_stats()
    print(f"データベース統計: 総レコード数 {stats['total_records']}")
    for table_name, count in stats.get("tables", {}).items():
        print(f"  - {table_name}: {count}件")
    
    return storage_manager


def finalize_persistent_database():
    """GitHub Actions実行終了時のデータベース永続化"""
    print("=== GitHub Actions データベース永続化処理 ===")
    
    storage_manager = GitHubStorageManager()
    
    # 現在の状態をバックアップ
    backup_success = storage_manager.save_backup()
    
    if backup_success:
        print("✓ データベースバックアップ完了")
    else:
        print("✗ データベースバックアップ失敗")
    
    # 統計情報を表示
    stats = storage_manager.get_database_stats()
    print(f"最終統計: 総レコード数 {stats['total_records']}")
    
    return backup_success


if __name__ == "__main__":
    # テスト実行
    print("=== GitHub Storage Manager テスト ===")
    
    manager = GitHubStorageManager()
    
    # 統計情報の表示
    stats = manager.get_database_stats()
    print(f"現在の統計: {stats}")
    
    # バックアップテスト
    print("\nバックアップテスト...")
    success = manager.save_backup()
    print(f"バックアップ結果: {'成功' if success else '失敗'}")
    
    print("\n=== テスト完了 ===")