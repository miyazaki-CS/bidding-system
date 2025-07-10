#!/usr/bin/env python3
"""
入札案件自動収集システム メイン実行スクリプト
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.utils.logger import setup_logger
from src.database.simple_db import SimpleDatabaseManager
from src.collectors.government_api import GovernmentProcurementAPI, MockGovernmentAPI
from src.collectors.rss_collector import RSSCollector
from src.processors.data_processor import BidDataProcessor
from src.notifications.notifier import NotificationService

# ログ設定
logger = setup_logger("bid_collector", settings.log_level)

class BidCollectionSystem:
    """入札案件収集システム"""
    
    def __init__(self):
        self.db_manager = SimpleDatabaseManager("bidding_system.db")
        self.api_client = GovernmentProcurementAPI()  # 実機APIを使用
        self.rss_collector = RSSCollector()  # RSS収集器を追加
        self.processor = BidDataProcessor()
        self.notifier = NotificationService()
        self.start_time = time.time()
        
    def run(self):
        """メイン実行"""
        logger.info("=== 入札案件収集システム開始 ===")
        
        try:
            # データベース初期化
            self._initialize_database()
            
            # データ収集
            raw_entries = self._collect_data()
            
            # データ処理
            processed_entries = self._process_data(raw_entries)
            
            # データベース保存
            saved_entries = self._save_to_database(processed_entries)
            
            # 通知送信
            self._send_notifications(saved_entries)
            
            # 統計情報作成
            statistics = self._create_statistics(raw_entries, processed_entries, saved_entries)
            
            # 日次レポート送信
            self._send_daily_report(saved_entries, statistics)
            
            logger.info("=== 入札案件収集システム完了 ===")
            
        except Exception as e:
            logger.error(f"システム実行中にエラーが発生: {e}")
            raise
        
        finally:
            self._cleanup()
    
    def _initialize_database(self):
        """データベース初期化"""
        logger.info("データベース初期化開始")
        
        try:
            # シンプルDBは自動的に初期化される
            stats = self.db_manager.get_database_stats()
            logger.info(f"データベース統計: {stats}")
            
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
            raise
    
    def _collect_data(self) -> List[Dict]:
        """データ収集"""
        logger.info("データ収集開始")
        
        all_entries = []
        
        try:
            # 政府APIからデータ収集
            logger.info("政府APIからデータ収集中...")
            api_entries = self.api_client.search_bids(
                keywords=settings.target_keywords,
                date_from=None,  # 今日から
                date_to=None
            )
            all_entries.extend(api_entries)
            logger.info(f"政府APIから {len(api_entries)} 件収集")
            
            # 処理時間制限チェック
            if time.time() - self.start_time > settings.max_processing_time:
                logger.warning("処理時間制限に達しました")
                return all_entries
            
            # RSS収集（追加データソース）
            logger.info("自治体RSSからデータ収集中...")
            try:
                rss_entries = self.rss_collector.collect_all_rss_sources()
                all_entries.extend(rss_entries)
                logger.info(f"RSSから {len(rss_entries)} 件収集")
            except Exception as e:
                logger.error(f"RSS収集エラー: {e}")
                # RSS収集エラーは致命的ではないので続行
            
        except Exception as e:
            logger.error(f"データ収集エラー: {e}")
            # エラーが発生しても既に収集したデータは処理を続行
        
        logger.info(f"データ収集完了: 合計 {len(all_entries)} 件")
        return all_entries
    
    def _process_data(self, raw_entries: List[Dict]) -> List[Dict]:
        """データ処理"""
        logger.info("データ処理開始")
        
        try:
            # 処理件数制限
            if len(raw_entries) > settings.max_entries_per_run:
                logger.warning(f"処理件数制限により {settings.max_entries_per_run} 件のみ処理")
                raw_entries = raw_entries[:settings.max_entries_per_run]
            
            # データ処理実行
            processed_entries = self.processor.process_entries(raw_entries)
            
            # 古いデータの除去
            processed_entries = self.processor.clean_old_data(processed_entries)
            
            logger.info(f"データ処理完了: {len(processed_entries)} 件")
            return processed_entries
            
        except Exception as e:
            logger.error(f"データ処理エラー: {e}")
            return []
    
    def _save_to_database(self, processed_entries: List[Dict]) -> List[Dict]:
        """データベース保存"""
        logger.info("データベース保存開始")
        
        saved_entries = []
        
        try:
            for entry_data in processed_entries:
                try:
                    # データ検証
                    if not self.processor.validate_entry(entry_data):
                        continue
                    
                    # データ正規化
                    normalized_data = self.processor.normalize_entry_data(entry_data)
                    
                    # 重複チェック
                    if self.db_manager.check_duplicate_entry(
                        normalized_data['title'],
                        normalized_data['organization']
                    ):
                        logger.debug(f"重複データをスキップ: {normalized_data['title']}")
                        continue
                    
                    # エントリー保存
                    entry_id = self.db_manager.insert_procurement_entry(normalized_data)
                    if entry_id:
                        saved_entries.append(entry_data)
                        logger.debug(f"エントリー保存成功: {entry_id}")
                    
                except Exception as e:
                    logger.warning(f"エントリー保存エラー: {e}")
                    continue
            
            logger.info(f"データベース保存完了: {len(saved_entries)} 件")
            
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
        
        return saved_entries
    
    def _send_notifications(self, entries: List[Dict]):
        """通知送信"""
        logger.info("通知送信開始")
        
        try:
            # 高優先度案件の抽出
            high_priority = self.processor.get_high_priority_entries(entries)
            
            # 高優先度案件の即座通知
            if high_priority:
                success = self.notifier.send_high_priority_alert(high_priority)
                if success:
                    logger.info(f"高優先度案件アラート送信完了: {len(high_priority)} 件")
                else:
                    logger.warning("高優先度案件アラート送信失敗")
            
        except Exception as e:
            logger.error(f"通知送信エラー: {e}")
    
    def _send_daily_report(self, entries: List[Dict], statistics: Dict):
        """日次レポート送信"""
        logger.info("日次レポート送信開始")
        
        try:
            # 優先度別分類
            high_priority = self.processor.get_high_priority_entries(entries)
            medium_priority = self.processor.get_medium_priority_entries(entries)
            
            # レポート送信
            success = self.notifier.send_daily_report(
                entries, high_priority, medium_priority, statistics
            )
            
            if success:
                logger.info("日次レポート送信完了")
            else:
                logger.warning("日次レポート送信失敗")
                
        except Exception as e:
            logger.error(f"日次レポート送信エラー: {e}")
    
    def _create_statistics(self, raw_entries: List[Dict], processed_entries: List[Dict], saved_entries: List[Dict]) -> Dict:
        """統計情報作成"""
        processing_time = time.time() - self.start_time
        
        statistics = {
            "execution_time": datetime.now().isoformat(),
            "total_collected": len(raw_entries),
            "total_processed": len(processed_entries),
            "total_saved": len(saved_entries),
            "processing_time": processing_time,
            "high_priority_count": len(self.processor.get_high_priority_entries(processed_entries)),
            "medium_priority_count": len(self.processor.get_medium_priority_entries(processed_entries))
        }
        
        logger.info(f"統計情報: {statistics}")
        return statistics
    
    def _cleanup(self):
        """クリーンアップ"""
        logger.info("クリーンアップ開始")
        
        try:
            # 古いデータの削除
            self.db_manager.cleanup_old_data(days=settings.data_retention_days)
            
            # 古いログファイルの削除（7日以上前）
            self._cleanup_old_logs()
            
            logger.info("クリーンアップ完了")
            
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
    
    def _cleanup_old_logs(self):
        """古いログファイルの削除"""
        try:
            import glob
            from datetime import datetime, timedelta
            
            log_files = glob.glob("logs/*.log")
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in log_files:
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        logger.info(f"古いログファイル削除: {log_file}")
                except Exception as e:
                    logger.warning(f"ログファイル削除エラー: {e}")
                    
        except Exception as e:
            logger.warning(f"ログクリーンアップエラー: {e}")

def main():
    """メイン関数"""
    try:
        # システム実行
        system = BidCollectionSystem()
        system.run()
        
    except KeyboardInterrupt:
        logger.info("ユーザーによりシステムが中断されました")
        sys.exit(0)
    except Exception as e:
        logger.error(f"システム実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()