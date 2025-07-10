"""
Webダッシュボード用データ生成器
データベースからWebダッシュボード表示用のJSONデータを生成
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import shutil

class DashboardGenerator:
    """Webダッシュボード用データ生成クラス"""
    
    def __init__(self, db_path: str = "bidding_system.db", web_dir: str = "web"):
        self.db_path = db_path
        self.web_dir = web_dir
        self.data_file = os.path.join(web_dir, "dashboard_data.json")
        
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用データを生成"""
        
        if not os.path.exists(self.db_path):
            return self._generate_empty_data()
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 案件データ取得
            cursor.execute("""
                SELECT * FROM procurement_entries 
                ORDER BY created_at DESC 
                LIMIT 100
            """)
            entries = [dict(row) for row in cursor.fetchall()]
            
            # 統計データ生成
            stats = self._generate_statistics(cursor)
            
            # システム情報
            system_info = self._generate_system_info()
            
            conn.close()
            
            dashboard_data = {
                "last_updated": datetime.now().isoformat(),
                "stats": stats,
                "entries": entries,
                "system_info": system_info,
                "metadata": {
                    "total_entries": len(entries),
                    "data_source": "bidding_system.db",
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            print(f"ダッシュボードデータ生成エラー: {e}")
            return self._generate_error_data(str(e))
    
    def _generate_statistics(self, cursor) -> Dict[str, Any]:
        """統計データを生成"""
        
        # 総案件数
        cursor.execute("SELECT COUNT(*) FROM procurement_entries")
        total_entries = cursor.fetchone()[0]
        
        # 高優先度案件数
        cursor.execute("SELECT COUNT(*) FROM procurement_entries WHERE relevance_score >= 80")
        high_priority = cursor.fetchone()[0]
        
        # 本日追加案件数
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM procurement_entries WHERE date(created_at) = ?", (today,))
        today_entries = cursor.fetchone()[0]
        
        # 地域別統計
        cursor.execute("""
            SELECT region, COUNT(*) as count 
            FROM procurement_entries 
            GROUP BY region 
            ORDER BY count DESC 
            LIMIT 10
        """)
        region_stats = [{"region": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # 適合度分布
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN relevance_score >= 80 THEN 'high'
                    WHEN relevance_score >= 60 THEN 'medium'
                    ELSE 'low'
                END as priority,
                COUNT(*) as count
            FROM procurement_entries
            GROUP BY priority
        """)
        priority_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 最近7日間の追加案件数
        daily_stats = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM procurement_entries WHERE date(created_at) = ?", (date,))
            count = cursor.fetchone()[0]
            daily_stats.append({
                "date": date,
                "count": count
            })
        
        return {
            "total_entries": total_entries,
            "high_priority": high_priority,
            "today_entries": today_entries,
            "region_stats": region_stats,
            "priority_distribution": priority_distribution,
            "daily_stats": daily_stats
        }
    
    def _generate_system_info(self) -> Dict[str, Any]:
        """システム情報を生成"""
        
        # データベースファイルサイズ
        db_size = 0
        if os.path.exists(self.db_path):
            db_size = os.path.getsize(self.db_path)
        
        # ログファイル情報
        log_files = []
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            for filename in os.listdir(logs_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(logs_dir, filename)
                    log_files.append({
                        "name": filename,
                        "size": os.path.getsize(filepath),
                        "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })
        
        return {
            "database_size": db_size,
            "database_size_mb": round(db_size / 1024 / 1024, 2),
            "log_files": log_files,
            "python_version": "3.11+",
            "system_status": "active"
        }
    
    def _generate_empty_data(self) -> Dict[str, Any]:
        """空データを生成"""
        return {
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_entries": 0,
                "high_priority": 0,
                "today_entries": 0,
                "region_stats": [],
                "priority_distribution": {},
                "daily_stats": []
            },
            "entries": [],
            "system_info": {
                "database_size": 0,
                "database_size_mb": 0,
                "log_files": [],
                "python_version": "3.11+",
                "system_status": "no_data"
            },
            "metadata": {
                "total_entries": 0,
                "data_source": "none",
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def _generate_error_data(self, error_message: str) -> Dict[str, Any]:
        """エラーデータを生成"""
        return {
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_entries": 0,
                "high_priority": 0,
                "today_entries": 0,
                "region_stats": [],
                "priority_distribution": {},
                "daily_stats": []
            },
            "entries": [],
            "system_info": {
                "database_size": 0,
                "database_size_mb": 0,
                "log_files": [],
                "python_version": "3.11+",
                "system_status": "error",
                "error_message": error_message
            },
            "metadata": {
                "total_entries": 0,
                "data_source": "error",
                "generated_at": datetime.now().isoformat(),
                "error": error_message
            }
        }
    
    def save_dashboard_data(self) -> bool:
        """ダッシュボードデータをJSONファイルに保存"""
        try:
            # Webディレクトリ作成
            os.makedirs(self.web_dir, exist_ok=True)
            
            # データ生成
            data = self.generate_dashboard_data()
            
            # JSONファイルに保存
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"ダッシュボードデータ保存: {self.data_file}")
            return True
            
        except Exception as e:
            print(f"ダッシュボードデータ保存エラー: {e}")
            return False
    
    def update_dashboard_html(self) -> bool:
        """ダッシュボードHTMLファイルを最新データで更新"""
        try:
            # データ生成・保存
            self.save_dashboard_data()
            
            print("ダッシュボード更新完了")
            return True
            
        except Exception as e:
            print(f"ダッシュボード更新エラー: {e}")
            return False
    
    def create_static_site(self) -> bool:
        """GitHub Pages用の静的サイトを作成"""
        try:
            # GitHub Pages用ディレクトリ
            pages_dir = "docs"
            os.makedirs(pages_dir, exist_ok=True)
            
            # HTMLファイルをコピー
            html_source = os.path.join(self.web_dir, "dashboard.html")
            html_dest = os.path.join(pages_dir, "index.html")
            
            if os.path.exists(html_source):
                shutil.copy2(html_source, html_dest)
                print(f"HTMLファイルコピー: {html_dest}")
            
            # データファイルをコピー
            data_source = self.data_file
            data_dest = os.path.join(pages_dir, "dashboard_data.json")
            
            if os.path.exists(data_source):
                shutil.copy2(data_source, data_dest)
                print(f"データファイルコピー: {data_dest}")
            
            # README作成
            readme_content = """# 入札案件自動収集システム - ダッシュボード

このディレクトリには、入札案件自動収集システムのWebダッシュボードが含まれています。

## ファイル構成
- `index.html` - メインダッシュボードページ
- `dashboard_data.json` - 表示用データ（自動生成）

## GitHub Pages設定
1. リポジトリ設定 > Pages
2. Source: Deploy from a branch
3. Branch: main, Folder: /docs

データは毎日自動更新されます。
"""
            
            with open(os.path.join(pages_dir, "README.md"), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"GitHub Pages用サイト作成完了: {pages_dir}")
            return True
            
        except Exception as e:
            print(f"静的サイト作成エラー: {e}")
            return False


def main():
    """メイン実行"""
    print("=== Webダッシュボード生成 ===")
    
    generator = DashboardGenerator()
    
    # ダッシュボードデータ生成・保存
    success = generator.save_dashboard_data()
    
    if success:
        print("✓ ダッシュボードデータ生成完了")
        
        # 静的サイト作成
        if generator.create_static_site():
            print("✓ GitHub Pages用サイト作成完了")
    else:
        print("✗ ダッシュボードデータ生成失敗")
    
    print("\n=== 生成完了 ===")


if __name__ == "__main__":
    main()