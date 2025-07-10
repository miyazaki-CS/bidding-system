import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """通知サービスクラス"""
    
    def __init__(self):
        self.email_user = settings.email_user
        self.email_password = settings.email_password
        self.email_to = settings.email_to
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.teams_webhook_url = settings.teams_webhook_url
        self.max_daily_notifications = settings.max_daily_notifications
        self.notification_count = 0
        
    def send_high_priority_alert(self, entries: List[Dict]) -> bool:
        """高優先度案件のアラート送信"""
        if not entries:
            return True
            
        if self.notification_count >= self.max_daily_notifications:
            logger.warning("Daily notification limit reached")
            return False
        
        try:
            # メール送信
            email_sent = self._send_email_alert(entries, "高優先度案件アラート")
            
            # Teams送信
            teams_sent = self._send_teams_alert(entries, "🚨 高優先度案件発見")
            
            if email_sent or teams_sent:
                self.notification_count += 1
                logger.info(f"High priority alert sent for {len(entries)} entries")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send high priority alert: {e}")
            
        return False
    
    def send_daily_report(self, 
                         all_entries: List[Dict], 
                         high_priority: List[Dict],
                         medium_priority: List[Dict],
                         statistics: Dict) -> bool:
        """日次レポート送信"""
        try:
            # メールレポート送信
            email_sent = self._send_email_report(all_entries, high_priority, medium_priority, statistics)
            
            # Teamsレポート送信
            teams_sent = self._send_teams_report(all_entries, high_priority, medium_priority, statistics)
            
            if email_sent or teams_sent:
                logger.info("Daily report sent successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
            
        return False
    
    def _send_email_alert(self, entries: List[Dict], subject: str) -> bool:
        """メールアラート送信"""
        if not self.email_user or not self.email_password or not self.email_to:
            logger.warning("Email configuration not complete")
            return False
        
        try:
            # メール内容作成
            body = self._create_email_body(entries)
            
            # メール作成
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_to
            msg['Subject'] = f"[入札案件アラート] {subject} - {len(entries)}件"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {self.email_to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_teams_alert(self, entries: List[Dict], title: str) -> bool:
        """Teamsアラート送信"""
        if not self.teams_webhook_url:
            logger.warning("Teams webhook URL not configured")
            return False
        
        try:
            # Teams メッセージ作成
            message = self._create_teams_message(entries, title)
            
            # Webhook送信
            response = requests.post(
                self.teams_webhook_url,
                json=message,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Teams alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Teams alert: {e}")
            return False
    
    def _send_email_report(self, 
                          all_entries: List[Dict], 
                          high_priority: List[Dict],
                          medium_priority: List[Dict],
                          statistics: Dict) -> bool:
        """メール日次レポート送信"""
        if not self.email_user or not self.email_password or not self.email_to:
            return False
        
        try:
            # レポート内容作成
            body = self._create_email_report_body(all_entries, high_priority, medium_priority, statistics)
            
            # メール作成
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_to
            msg['Subject'] = f"[入札案件] 日次レポート - {datetime.now().strftime('%Y/%m/%d')}"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info("Email report sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def _send_teams_report(self, 
                          all_entries: List[Dict], 
                          high_priority: List[Dict],
                          medium_priority: List[Dict],
                          statistics: Dict) -> bool:
        """Teams日次レポート送信"""
        if not self.teams_webhook_url:
            return False
        
        try:
            # レポートメッセージ作成
            message = self._create_teams_report_message(all_entries, high_priority, medium_priority, statistics)
            
            # Webhook送信
            response = requests.post(
                self.teams_webhook_url,
                json=message,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Teams report sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Teams report: {e}")
            return False
    
    def _create_email_body(self, entries: List[Dict]) -> str:
        """メール本文作成"""
        body = f"新しい入札案件 {len(entries)}件が見つかりました。\n\n"
        
        for i, entry in enumerate(entries, 1):
            body += f"【案件 {i}】\n"
            body += f"タイトル: {entry.get('title', '')}\n"
            body += f"発注機関: {entry.get('organization', '')}\n"
            body += f"地域: {entry.get('region', '')}\n"
            body += f"適合度: {entry.get('relevance_score', 0)}点\n"
            
            if entry.get('budget_amount'):
                body += f"予算: {entry['budget_amount']:,}円\n"
            
            if entry.get('deadline_date'):
                body += f"締切: {entry['deadline_date']}\n"
            
            if entry.get('source_url'):
                body += f"URL: {entry['source_url']}\n"
            
            body += f"説明: {entry.get('description', '')[:200]}...\n"
            body += "\n" + "="*50 + "\n\n"
        
        body += f"送信時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
        
        return body
    
    def _create_teams_message(self, entries: List[Dict], title: str) -> Dict:
        """Teamsメッセージ作成"""
        text = f"{title}\n新しい入札案件 {len(entries)}件が見つかりました。"
        
        # Teams Adaptive Card形式
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": f"{title} - {len(entries)}件",
            "sections": [
                {
                    "activityTitle": title,
                    "activitySubtitle": f"{len(entries)}件の新着案件",
                    "activityImage": "https://via.placeholder.com/64x64.png?text=📋",
                    "facts": [
                        {
                            "name": "収集時刻",
                            "value": datetime.now().strftime('%Y/%m/%d %H:%M')
                        },
                        {
                            "name": "案件数",
                            "value": f"{len(entries)}件"
                        }
                    ]
                }
            ]
        }
        
        # 案件詳細を追加（最大3件）
        for i, entry in enumerate(entries[:3]):
            section = {
                "activityTitle": f"案件 {i+1}: {entry.get('title', '')}",
                "facts": [
                    {
                        "name": "発注機関",
                        "value": entry.get('organization', '')
                    },
                    {
                        "name": "地域",
                        "value": entry.get('region', '')
                    },
                    {
                        "name": "適合度",
                        "value": f"{entry.get('relevance_score', 0)}点"
                    }
                ]
            }
            
            if entry.get('source_url'):
                section["potentialAction"] = [
                    {
                        "@type": "OpenUri",
                        "name": "詳細を見る",
                        "targets": [
                            {
                                "os": "default",
                                "uri": entry['source_url']
                            }
                        ]
                    }
                ]
            
            card["sections"].append(section)
        
        if len(entries) > 3:
            card["sections"].append({
                "activityTitle": f"その他 {len(entries) - 3}件の案件があります"
            })
        
        return card
    
    def _create_email_report_body(self, 
                                 all_entries: List[Dict], 
                                 high_priority: List[Dict],
                                 medium_priority: List[Dict],
                                 statistics: Dict) -> str:
        """メール日次レポート本文作成"""
        body = f"【入札案件 日次レポート】 {datetime.now().strftime('%Y/%m/%d')}\n\n"
        
        # 統計情報
        body += "【統計情報】\n"
        body += f"総収集件数: {statistics.get('total_collected', 0)}件\n"
        body += f"処理完了件数: {statistics.get('total_processed', 0)}件\n"
        body += f"高優先度案件: {len(high_priority)}件\n"
        body += f"中優先度案件: {len(medium_priority)}件\n"
        body += f"処理時間: {statistics.get('processing_time', 0):.2f}秒\n\n"
        
        # 高優先度案件
        if high_priority:
            body += "【高優先度案件】\n"
            for entry in high_priority:
                body += f"・{entry.get('title', '')} ({entry.get('relevance_score', 0)}点)\n"
                body += f"  {entry.get('organization', '')} - {entry.get('region', '')}\n"
        else:
            body += "【高優先度案件】\n該当なし\n"
        
        body += "\n"
        
        # 中優先度案件
        if medium_priority:
            body += "【中優先度案件】\n"
            for entry in medium_priority[:10]:  # 最大10件
                body += f"・{entry.get('title', '')} ({entry.get('relevance_score', 0)}点)\n"
            if len(medium_priority) > 10:
                body += f"...他 {len(medium_priority) - 10}件\n"
        else:
            body += "【中優先度案件】\n該当なし\n"
        
        body += f"\n生成時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
        
        return body
    
    def _create_teams_report_message(self, 
                                   all_entries: List[Dict], 
                                   high_priority: List[Dict],
                                   medium_priority: List[Dict],
                                   statistics: Dict) -> Dict:
        """Teams日次レポートメッセージ作成"""
        
        # Teams Adaptive Card形式
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "28A745",
            "summary": f"入札案件 日次レポート ({datetime.now().strftime('%m/%d')})",
            "sections": [
                {
                    "activityTitle": f"📊 入札案件 日次レポート",
                    "activitySubtitle": datetime.now().strftime('%Y年%m月%d日'),
                    "activityImage": "https://via.placeholder.com/64x64.png?text=📊",
                    "facts": [
                        {
                            "name": "総収集件数",
                            "value": f"{statistics.get('total_collected', 0)}件"
                        },
                        {
                            "name": "処理完了件数",
                            "value": f"{statistics.get('total_processed', 0)}件"
                        },
                        {
                            "name": "高優先度案件",
                            "value": f"{len(high_priority)}件"
                        },
                        {
                            "name": "中優先度案件",
                            "value": f"{len(medium_priority)}件"
                        },
                        {
                            "name": "処理時間",
                            "value": f"{statistics.get('processing_time', 0):.1f}秒"
                        }
                    ]
                }
            ]
        }
        
        # 高優先度案件の詳細
        if high_priority:
            section = {
                "activityTitle": "🚨 高優先度案件",
                "facts": []
            }
            
            for i, entry in enumerate(high_priority[:5]):  # 最大5件
                section["facts"].append({
                    "name": f"案件 {i+1}",
                    "value": f"{entry.get('title', '')} ({entry.get('relevance_score', 0)}点)\n{entry.get('organization', '')}"
                })
            
            if len(high_priority) > 5:
                section["facts"].append({
                    "name": "その他",
                    "value": f"{len(high_priority) - 5}件の高優先度案件があります"
                })
            
            card["sections"].append(section)
        
        return card

# テスト用クラス
class NotificationTester:
    """通知テスト用クラス"""
    
    @staticmethod
    def test_notifications():
        """通知テスト実行"""
        # テスト用設定
        notifier = NotificationService()
        
        # サンプルデータ
        sample_entries = [
            {
                "title": "コールセンター業務委託",
                "organization": "○○市",
                "region": "東京都",
                "relevance_score": 85,
                "budget_amount": 5000000,
                "deadline_date": "2025-08-01",
                "source_url": "https://example.com/bid/1",
                "description": "市民からの問い合わせ対応業務"
            }
        ]
        
        statistics = {
            "total_collected": 150,
            "total_processed": 10,
            "processing_time": 45.2
        }
        
        # アラートテスト
        print("Testing high priority alert...")
        notifier.send_high_priority_alert(sample_entries)
        
        # レポートテスト
        print("Testing daily report...")
        notifier.send_daily_report(sample_entries, sample_entries, [], statistics)

if __name__ == "__main__":
    NotificationTester.test_notifications()