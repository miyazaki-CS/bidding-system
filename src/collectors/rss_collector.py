"""
自治体RSS収集器
主要自治体のRSSフィードから入札情報を収集
"""

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    # フォールバック実装をインポート
    from .rss_fallback import FallbackRSSCollector
import requests
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class RSSCollector:
    """自治体RSS収集クラス"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        self.delay = 2  # RSS取得間隔（秒）
        
        # 対象キーワード
        self.target_keywords = [
            "データ入力", "入力作業", "キッティング", "PC設定",
            "コールセンター", "電話受付", "事務業務", "システム構築"
        ]
    
    def get_major_municipalities_rss(self) -> List[Dict[str, str]]:
        """主要自治体・政府機関のRSS情報を取得"""
        return [
            # 中小企業基盤整備機構（確認済み・実在）
            {
                "name": "中小企業基盤整備機構本部",
                "rss_url": "https://www.smrj.go.jp/org/info/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            {
                "name": "中小企業基盤整備機構関東",
                "rss_url": "https://www.smrj.go.jp/regional_hq/kanto/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            {
                "name": "中小企業基盤整備機構九州",
                "rss_url": "https://www.smrj.go.jp/regional_hq/kyushu/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            {
                "name": "中小企業基盤整備機構東北",
                "rss_url": "https://www.smrj.go.jp/regional_hq/tohoku/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            {
                "name": "中小企業基盤整備機構中部",
                "rss_url": "https://www.smrj.go.jp/regional_hq/chubu/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            {
                "name": "中小企業基盤整備機構近畿",
                "rss_url": "https://www.smrj.go.jp/regional_hq/kinki/bid/info_bid.xml",
                "website_url": "https://www.smrj.go.jp/",
                "type": "agency"
            },
            # 国土地理院（確認済み・実在）
            {
                "name": "国土地理院（物品・サービス）",
                "rss_url": "https://www.gsi.go.jp/nyusatu1.rdf",
                "website_url": "https://www.gsi.go.jp/",
                "type": "government"
            },
            {
                "name": "国土地理院（測量・調査）",
                "rss_url": "https://www.gsi.go.jp/nyusatu2.rdf",
                "website_url": "https://www.gsi.go.jp/",
                "type": "government"
            },
            # 産業技術総合研究所（確認済み・実在）
            {
                "name": "産業技術総合研究所",
                "rss_url": "https://www.aist.go.jp/aist_j/procure/supplyinfo/pub/feed/rss.xml",
                "website_url": "https://www.aist.go.jp/",
                "type": "research"
            },
            # その他政府機関（一般的な報道RSS）
            {
                "name": "厚生労働省報道発表",
                "rss_url": "https://www.mhlw.go.jp/stf/news.rdf",
                "website_url": "https://www.mhlw.go.jp/",
                "type": "ministry"
            },
            {
                "name": "総務省報道資料",
                "rss_url": "https://www.soumu.go.jp/menu_news/news.xml",
                "website_url": "https://www.soumu.go.jp/",
                "type": "ministry"
            },
            # 地方自治体（都道府県レベル）
            {
                "name": "東京都報道発表",
                "rss_url": "https://www.metro.tokyo.lg.jp/tosei/hodohappyo/press/rss.xml",
                "website_url": "https://www.metro.tokyo.lg.jp/",
                "type": "prefecture"
            },
            {
                "name": "大阪府報道発表",
                "rss_url": "https://www.pref.osaka.lg.jp/rss/event.xml",
                "website_url": "https://www.pref.osaka.lg.jp/",
                "type": "prefecture"
            },
            {
                "name": "愛知県報道発表",
                "rss_url": "https://www.pref.aichi.jp/uploaded/info.xml",
                "website_url": "https://www.pref.aichi.jp/",
                "type": "prefecture"
            },
            {
                "name": "福岡県報道発表",
                "rss_url": "https://www.pref.fukuoka.lg.jp/rss/jigyousya.xml",
                "website_url": "https://www.pref.fukuoka.lg.jp/",
                "type": "prefecture"
            }
        ]
    
    def collect_from_rss(self, rss_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """指定されたRSSから入札情報を収集"""
        collected_entries = []
        
        try:
            logger.info(f"RSS収集開始: {rss_info['name']} - {rss_info['rss_url']}")
            
            # RSS取得
            response = self.session.get(rss_info['rss_url'], timeout=self.timeout)
            response.raise_for_status()
            
            # RSS解析
            if HAS_FEEDPARSER:
                feed = feedparser.parse(response.content)
            else:
                # フォールバック解析
                logger.warning("feedparserが利用できません。基本的な解析を使用します。")
                return []
            
            if not feed.entries:
                logger.warning(f"RSSエントリが見つかりません: {rss_info['name']}")
                return []
            
            # エントリ処理
            for entry in feed.entries[:20]:  # 最新20件まで
                processed_entry = self._process_rss_entry(entry, rss_info)
                if processed_entry:
                    collected_entries.append(processed_entry)
            
            logger.info(f"RSS収集完了: {rss_info['name']} - {len(collected_entries)}件")
            
        except requests.RequestException as e:
            logger.error(f"RSS取得エラー: {rss_info['name']} - {e}")
        except Exception as e:
            logger.error(f"RSS処理エラー: {rss_info['name']} - {e}")
        
        return collected_entries
    
    def _process_rss_entry(self, entry: Any, rss_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """RSSエントリを処理して統一形式に変換"""
        try:
            # タイトル取得
            title = getattr(entry, 'title', '').strip()
            if not title:
                return None
            
            # キーワードフィルタリング
            relevance_score = self._calculate_relevance_score(title)
            if relevance_score < 30:  # 最低閾値
                return None
            
            # 説明文取得
            description = ""
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description
            
            # HTML除去
            description = self._clean_html(description)
            
            # URL取得
            source_url = getattr(entry, 'link', '')
            if source_url and not source_url.startswith('http'):
                source_url = urljoin(rss_info['website_url'], source_url)
            
            # 公開日取得
            published_date = self._parse_date(entry)
            
            # 地域情報
            region = self._extract_region(rss_info['name'])
            
            # 予算情報抽出
            budget_amount = self._extract_budget(title + " " + description)
            
            # 締切日抽出
            deadline_date = self._extract_deadline(description)
            
            return {
                "title": title[:500],  # 長さ制限
                "description": description[:2000],  # 長さ制限
                "organization": rss_info['name'],
                "region": region,
                "budget_amount": budget_amount,
                "published_date": published_date,
                "deadline_date": deadline_date,
                "source_url": source_url,
                "source_type": "rss",
                "relevance_score": relevance_score,
                "keywords_matched": self._get_matched_keywords(title + " " + description),
                "processed": False,
                "notified": False
            }
            
        except Exception as e:
            logger.error(f"RSSエントリ処理エラー: {e}")
            return None
    
    def _calculate_relevance_score(self, text: str) -> int:
        """適合度スコアを計算"""
        text_lower = text.lower()
        score = 0
        matched_keywords = []
        
        # キーワードマッチング
        keyword_scores = {
            "データ入力": 25,
            "入力作業": 25,
            "キッティング": 30,
            "pc設定": 25,
            "コールセンター": 30,
            "電話受付": 20,
            "事務業務": 15,
            "システム構築": 20,
            "運用保守": 15,
            "業務委託": 10,
            "アウトソーシング": 10
        }
        
        for keyword, points in keyword_scores.items():
            if keyword in text_lower:
                score += points
                matched_keywords.append(keyword)
        
        # ボーナス条件
        if "委託" in text_lower:
            score += 5
        if "業務" in text_lower:
            score += 5
        if any(word in text_lower for word in ["it", "システム", "コンピュータ"]):
            score += 10
        
        return min(score, 100)  # 最大100点
    
    def _get_matched_keywords(self, text: str) -> List[str]:
        """マッチしたキーワードのリストを取得"""
        text_lower = text.lower()
        matched = []
        
        for keyword in self.target_keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _clean_html(self, text: str) -> str:
        """HTMLタグを除去"""
        if not text:
            return ""
        
        # HTMLタグ除去
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTMLエンティティ変換
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # 余分な空白除去
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _parse_date(self, entry: Any) -> str:
        """RSSエントリから日付を解析"""
        try:
            # published, updated, pubDate等を確認
            for attr in ['published', 'updated', 'pubdate']:
                if hasattr(entry, attr):
                    date_str = getattr(entry, attr)
                    if date_str:
                        # feedparserが解析した時間構造体を使用
                        if hasattr(entry, f'{attr}_parsed') and getattr(entry, f'{attr}_parsed'):
                            time_struct = getattr(entry, f'{attr}_parsed')
                            return datetime(*time_struct[:6]).strftime('%Y-%m-%d')
                        
                        # 文字列から解析を試行
                        try:
                            parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            return parsed_date.strftime('%Y-%m-%d')
                        except:
                            continue
            
            # デフォルトは今日の日付
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_region(self, organization_name: str) -> str:
        """組織名から地域を抽出"""
        region_mapping = {
            # 都道府県レベル
            "東京都": "東京都",
            "大阪府": "大阪府", 
            "愛知県": "愛知県",
            "福岡県": "福岡県",
            "神奈川県": "神奈川県",
            "北海道": "北海道",
            "京都府": "京都府",
            "宮崎県": "宮崎県",
            
            # 政令指定都市
            "大阪市": "大阪府",
            "横浜市": "神奈川県", 
            "福岡市": "福岡県",
            "札幌市": "北海道",
            "京都市": "京都府",
            
            # 政府機関・独立行政法人
            "中小企業基盤整備機構本部": "全国",
            "中小企業基盤整備機構関東": "関東地方",
            "中小企業基盤整備機構九州": "九州地方", 
            "中小企業基盤整備機構東北": "東北地方",
            "中小企業基盤整備機構中部": "中部地方",
            "中小企業基盤整備機構近畿": "近畿地方",
            "国土地理院": "全国",
            "産業技術総合研究所": "全国",
            "厚生労働省": "全国",
            "総務省": "全国"
        }
        
        # 部分マッチング検索
        for key, value in region_mapping.items():
            if key in organization_name:
                return value
        
        return "全国"
    
    def _extract_budget(self, text: str) -> Optional[int]:
        """テキストから予算金額を抽出"""
        try:
            # 金額パターン検索
            patterns = [
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:万円|万)',
                r'(\d{1,3}(?:,\d{3})*)\s*(?:円)',
                r'予算[：:]\s*(\d{1,3}(?:,\d{3})*)',
                r'契約金額[：:]\s*(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    amount_str = matches[0].replace(',', '')
                    amount = int(amount_str)
                    
                    # 万円単位の場合
                    if '万' in pattern:
                        amount *= 10000
                    
                    if 1000 <= amount <= 1000000000:  # 妥当な範囲
                        return amount
            
            return None
            
        except Exception:
            return None
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """テキストから締切日を抽出"""
        try:
            # 日付パターン検索
            patterns = [
                r'締切[：:]?\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
                r'期限[：:]?\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
                r'まで[：:]?\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
                r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2}).*まで'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    year, month, day = matches[0]
                    try:
                        date = datetime(int(year), int(month), int(day))
                        # 未来の日付のみ有効
                        if date > datetime.now():
                            return date.strftime('%Y-%m-%d')
                    except:
                        continue
            
            return None
            
        except Exception:
            return None
    
    def collect_all_rss_sources(self) -> List[Dict[str, Any]]:
        """全RSS源から収集"""
        # feedparserが利用できない場合はフォールバック
        if not HAS_FEEDPARSER:
            logger.warning("feedparserが利用できません。フォールバック方式を使用します。")
            fallback_collector = FallbackRSSCollector()
            return fallback_collector.collect_fallback_data()
        
        all_entries = []
        rss_sources = self.get_major_municipalities_rss()
        
        logger.info(f"RSS収集開始: {len(rss_sources)}の自治体")
        
        for i, rss_info in enumerate(rss_sources):
            try:
                # 収集実行
                entries = self.collect_from_rss(rss_info)
                all_entries.extend(entries)
                
                # 進捗表示
                logger.info(f"進捗: {i+1}/{len(rss_sources)} - {rss_info['name']}: {len(entries)}件")
                
                # 間隔をあける（サーバー負荷軽減）
                if i < len(rss_sources) - 1:
                    time.sleep(self.delay)
                    
            except Exception as e:
                logger.error(f"RSS収集エラー: {rss_info['name']} - {e}")
                continue
        
        logger.info(f"RSS収集完了: 総計{len(all_entries)}件")
        return all_entries


class RSSCollectorTester:
    """RSS収集テスト用クラス"""
    
    @staticmethod
    def test_rss_collection():
        """RSS収集テスト"""
        print("=== RSS収集テスト ===")
        
        collector = RSSCollector()
        
        # テスト用RSS（1つだけ）
        test_rss = {
            "name": "東京都（テスト）",
            "rss_url": "https://www.metro.tokyo.lg.jp/rss/choutatu.rss",
            "website_url": "https://www.metro.tokyo.lg.jp/",
            "type": "prefecture"
        }
        
        print(f"テスト対象: {test_rss['name']}")
        print(f"URL: {test_rss['rss_url']}")
        
        # 収集実行
        entries = collector.collect_from_rss(test_rss)
        
        print(f"\n収集結果: {len(entries)}件")
        
        # 結果表示
        for i, entry in enumerate(entries[:3]):  # 最初の3件のみ表示
            print(f"\n--- 案件 {i+1} ---")
            print(f"タイトル: {entry['title']}")
            print(f"組織: {entry['organization']}")
            print(f"地域: {entry['region']}")
            print(f"適合度: {entry['relevance_score']}点")
            print(f"キーワード: {entry['keywords_matched']}")
            print(f"公開日: {entry['published_date']}")
            if entry['budget_amount']:
                print(f"予算: {entry['budget_amount']:,}円")
            if entry['deadline_date']:
                print(f"締切: {entry['deadline_date']}")
            print(f"URL: {entry['source_url']}")
        
        return len(entries) > 0


if __name__ == "__main__":
    # テスト実行
    RSSCollectorTester.test_rss_collection()