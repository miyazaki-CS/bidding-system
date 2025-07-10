"""
RSS収集フォールバック機能
feedparserが利用できない環境での代替実装
"""

import urllib.request
import urllib.parse
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SimpleFeedParser:
    """シンプルなフィードパーサー（feedparser代替）"""
    
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 10
    
    def parse_feed(self, url: str) -> Dict[str, Any]:
        """フィードを解析してエントリを返す"""
        try:
            # RSS取得
            req = urllib.request.Request(url, headers=self.session_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # 基本的なフィード情報
            feed_info = {
                'feed': self._extract_feed_info(content),
                'entries': self._extract_entries(content)
            }
            
            return feed_info
            
        except Exception as e:
            logger.error(f"フィード取得エラー: {url} - {e}")
            return {'feed': {}, 'entries': []}
    
    def _extract_feed_info(self, content: str) -> Dict[str, str]:
        """フィード基本情報を抽出"""
        info = {}
        
        # タイトル抽出
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.DOTALL | re.IGNORECASE)
        if title_match:
            info['title'] = self._clean_text(title_match.group(1))
        
        # 説明抽出
        desc_match = re.search(r'<description[^>]*>(.*?)</description>', content, re.DOTALL | re.IGNORECASE)
        if desc_match:
            info['description'] = self._clean_text(desc_match.group(1))
        
        return info
    
    def _extract_entries(self, content: str) -> List[Dict[str, Any]]:
        """エントリを抽出"""
        entries = []
        
        try:
            # <item>または<entry>タグを検索
            item_patterns = [
                r'<item[^>]*>(.*?)</item>',
                r'<entry[^>]*>(.*?)</entry>'
            ]
            
            for pattern in item_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    entry = self._parse_entry(match)
                    if entry:
                        entries.append(entry)
                
                if matches:
                    break  # 最初にマッチしたパターンを使用
        
        except Exception as e:
            logger.error(f"エントリ抽出エラー: {e}")
        
        return entries
    
    def _parse_entry(self, entry_content: str) -> Optional[Dict[str, Any]]:
        """個別エントリを解析"""
        try:
            entry = {}
            
            # タイトル
            title_match = re.search(r'<title[^>]*>(.*?)</title>', entry_content, re.DOTALL | re.IGNORECASE)
            if title_match:
                entry['title'] = self._clean_text(title_match.group(1))
            
            # リンク
            link_patterns = [
                r'<link[^>]*href=["\']([^"\']*)["\']',
                r'<link[^>]*>(.*?)</link>',
                r'<guid[^>]*>(.*?)</guid>'
            ]
            
            for pattern in link_patterns:
                link_match = re.search(pattern, entry_content, re.DOTALL | re.IGNORECASE)
                if link_match:
                    entry['link'] = link_match.group(1).strip()
                    break
            
            # 説明
            desc_patterns = [
                r'<description[^>]*>(.*?)</description>',
                r'<summary[^>]*>(.*?)</summary>',
                r'<content[^>]*>(.*?)</content>'
            ]
            
            for pattern in desc_patterns:
                desc_match = re.search(pattern, entry_content, re.DOTALL | re.IGNORECASE)
                if desc_match:
                    entry['summary'] = self._clean_text(desc_match.group(1))
                    break
            
            # 公開日
            date_patterns = [
                r'<pubDate[^>]*>(.*?)</pubDate>',
                r'<published[^>]*>(.*?)</published>',
                r'<updated[^>]*>(.*?)</updated>'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, entry_content, re.DOTALL | re.IGNORECASE)
                if date_match:
                    entry['published'] = date_match.group(1).strip()
                    break
            
            return entry if entry.get('title') else None
            
        except Exception as e:
            logger.error(f"エントリ解析エラー: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """テキストクリーニング"""
        if not text:
            return ""
        
        # HTMLタグ除去
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTMLエンティティ変換
        replacements = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&apos;': "'"
        }
        
        for entity, char in replacements.items():
            text = text.replace(entity, char)
        
        # CDATA除去
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        
        # 余分な空白除去
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class FallbackRSSCollector:
    """フォールバックRSS収集器"""
    
    def __init__(self):
        self.parser = SimpleFeedParser()
        self.delay = 3  # より長い間隔
        
        # 実在する可能性の高い自治体情報サイト
        self.fallback_sources = [
            {
                "name": "政府インターネットテレビ",
                "rss_url": "https://nettv.gov-online.go.jp/rss.xml",
                "website_url": "https://nettv.gov-online.go.jp/",
                "type": "government"
            },
            {
                "name": "電子政府RSS",
                "rss_url": "https://www.e-gov.go.jp/rss/shinsei.xml",
                "website_url": "https://www.e-gov.go.jp/",
                "type": "government"
            }
        ]
        
        # 対象キーワード
        self.target_keywords = [
            "入札", "調達", "委託", "業務", "データ", "システム", "IT",
            "コンピュータ", "情報", "運用", "保守", "構築"
        ]
    
    def collect_fallback_data(self) -> List[Dict[str, Any]]:
        """フォールバック方式でデータ収集"""
        logger.info("フォールバック方式でRSS収集開始")
        
        all_entries = []
        
        for source in self.fallback_sources:
            try:
                logger.info(f"収集中: {source['name']}")
                
                # フィード解析
                feed_data = self.parser.parse_feed(source['rss_url'])
                
                # エントリ処理
                for entry in feed_data.get('entries', [])[:10]:  # 最大10件
                    processed_entry = self._process_fallback_entry(entry, source)
                    if processed_entry:
                        all_entries.append(processed_entry)
                
                logger.info(f"収集完了: {source['name']} - {len(feed_data.get('entries', []))}件")
                
                # 間隔をあける
                time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"フォールバック収集エラー: {source['name']} - {e}")
                continue
        
        logger.info(f"フォールバック収集完了: 総計{len(all_entries)}件")
        return all_entries
    
    def _process_fallback_entry(self, entry: Dict[str, Any], source: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """フォールバックエントリを処理"""
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # 関連性チェック
            relevance_score = self._calculate_fallback_relevance(title, entry.get('summary', ''))
            if relevance_score < 20:  # より低い閾値
                return None
            
            # 基本情報
            processed_entry = {
                "title": title[:500],
                "description": entry.get('summary', '')[:1000],
                "organization": source['name'],
                "region": "全国",
                "budget_amount": None,
                "published_date": self._parse_fallback_date(entry.get('published', '')),
                "deadline_date": None,
                "source_url": entry.get('link', ''),
                "source_type": "rss_fallback",
                "relevance_score": relevance_score,
                "keywords_matched": self._get_fallback_keywords(title + " " + entry.get('summary', '')),
                "processed": False,
                "notified": False
            }
            
            return processed_entry
            
        except Exception as e:
            logger.error(f"フォールバックエントリ処理エラー: {e}")
            return None
    
    def _calculate_fallback_relevance(self, title: str, description: str) -> int:
        """フォールバック関連性スコア計算"""
        text = (title + " " + description).lower()
        score = 0
        
        # 基本キーワード
        for keyword in self.target_keywords:
            if keyword in text:
                if keyword in ["入札", "調達"]:
                    score += 15
                elif keyword in ["委託", "業務"]:
                    score += 10
                else:
                    score += 5
        
        return min(score, 100)
    
    def _get_fallback_keywords(self, text: str) -> List[str]:
        """フォールバックキーワード取得"""
        matched = []
        text_lower = text.lower()
        
        for keyword in self.target_keywords:
            if keyword in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _parse_fallback_date(self, date_str: str) -> str:
        """フォールバック日付解析"""
        try:
            if not date_str:
                return datetime.now().strftime('%Y-%m-%d')
            
            # 簡単な日付抽出
            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
            if date_match:
                year, month, day = date_match.groups()
                try:
                    date = datetime(int(year), int(month), int(day))
                    return date.strftime('%Y-%m-%d')
                except:
                    pass
            
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')


def test_fallback_rss():
    """フォールバックRSS機能テスト"""
    print("=== フォールバックRSS機能テスト ===")
    
    collector = FallbackRSSCollector()
    
    # データ収集テスト
    entries = collector.collect_fallback_data()
    
    print(f"収集結果: {len(entries)}件")
    
    # 結果表示
    for i, entry in enumerate(entries[:3]):
        print(f"\n--- 案件 {i+1} ---")
        print(f"タイトル: {entry['title'][:80]}...")
        print(f"組織: {entry['organization']}")
        print(f"適合度: {entry['relevance_score']}点")
        print(f"キーワード: {entry['keywords_matched']}")
        print(f"公開日: {entry['published_date']}")
        print(f"URL: {entry['source_url'][:50]}...")
    
    return len(entries) > 0


if __name__ == "__main__":
    # フォールバック機能テスト
    success = test_fallback_rss()
    
    if success:
        print("\n✅ フォールバックRSS機能は正常に動作しています！")
    else:
        print("\n❌ フォールバックRSS機能でエラーが発生しました。")