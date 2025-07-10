import re
import json
from typing import List, Dict, Set, Tuple
from datetime import datetime, date
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class BidDataProcessor:
    """入札データ処理クラス"""
    
    def __init__(self):
        self.target_keywords = [kw.lower() for kw in settings.target_keywords]
        self.exclude_keywords = [kw.lower() for kw in settings.exclude_keywords]
        
    def process_entries(self, entries: List[Dict]) -> List[Dict]:
        """入札データの処理"""
        processed_entries = []
        
        for entry in entries:
            try:
                # 重複チェック
                if self._is_duplicate(entry, processed_entries):
                    continue
                
                # フィルタリング
                if not self._passes_filters(entry):
                    continue
                
                # 適合度スコア計算
                entry['relevance_score'] = self._calculate_relevance_score(entry)
                
                # マッチしたキーワードを記録
                entry['keywords_matched'] = self._get_matched_keywords(entry)
                
                processed_entries.append(entry)
                
            except Exception as e:
                logger.warning(f"Failed to process entry: {e}")
                continue
        
        # 適合度でソート
        processed_entries.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Processed {len(processed_entries)} entries from {len(entries)} raw entries")
        return processed_entries
    
    def _is_duplicate(self, entry: Dict, existing_entries: List[Dict]) -> bool:
        """重複チェック"""
        for existing in existing_entries:
            # タイトルの類似度チェック
            if self._calculate_similarity(entry.get('title', ''), existing.get('title', '')) > 0.8:
                return True
            
            # URL完全一致チェック
            if entry.get('source_url') and entry['source_url'] == existing.get('source_url'):
                return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算（簡易版）"""
        if not text1 or not text2:
            return 0.0
        
        # 単語に分割
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard係数
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _passes_filters(self, entry: Dict) -> bool:
        """フィルタリング条件チェック"""
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        text_to_check = f"{title} {description}"
        
        # 除外キーワードチェック
        for exclude_keyword in self.exclude_keywords:
            if exclude_keyword in text_to_check:
                logger.debug(f"Entry excluded by keyword '{exclude_keyword}': {entry.get('title', '')}")
                return False
        
        # 対象キーワードチェック
        for target_keyword in self.target_keywords:
            if target_keyword in text_to_check:
                return True
        
        return False
    
    def _calculate_relevance_score(self, entry: Dict) -> int:
        """適合度スコア計算"""
        score = 0
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        text_to_check = f"{title} {description}"
        
        # キーワードマッチによる加点
        for keyword in self.target_keywords:
            if keyword in text_to_check:
                # タイトルにあるキーワードは高得点
                if keyword in title:
                    score += 30
                else:
                    score += 10
        
        # 予算規模による加点
        budget = entry.get('budget_amount')
        if budget:
            if budget >= 10000000:  # 1000万円以上
                score += 20
            elif budget >= 5000000:  # 500万円以上
                score += 15
            elif budget >= 1000000:  # 100万円以上
                score += 10
        
        # 地域による加点（本社近郊優遇）
        region = entry.get('region', '').lower()
        if any(pref in region for pref in ['東京', '神奈川', '千葉', '埼玉']):
            score += 15
        elif any(pref in region for pref in ['大阪', '京都', '兵庫']):
            score += 10
        
        # 発注機関による加点
        organization = entry.get('organization', '').lower()
        if any(org in organization for org in ['市', '区', '町', '村']):
            score += 5  # 基礎自治体
        
        # 締切日による加点（余裕がある案件を優遇）
        deadline = entry.get('deadline_date')
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
                
                days_until_deadline = (deadline - date.today()).days
                if days_until_deadline >= 14:  # 2週間以上
                    score += 10
                elif days_until_deadline >= 7:  # 1週間以上
                    score += 5
            except Exception:
                pass
        
        return min(score, 100)  # 最大100点
    
    def _get_matched_keywords(self, entry: Dict) -> str:
        """マッチしたキーワードを取得"""
        matched = []
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        text_to_check = f"{title} {description}"
        
        for keyword in self.target_keywords:
            if keyword in text_to_check:
                matched.append(keyword)
        
        return json.dumps(matched, ensure_ascii=False)
    
    def filter_by_score(self, entries: List[Dict], min_score: int = 0) -> List[Dict]:
        """スコアによるフィルタリング"""
        return [entry for entry in entries if entry.get('relevance_score', 0) >= min_score]
    
    def get_high_priority_entries(self, entries: List[Dict]) -> List[Dict]:
        """高優先度案件の抽出"""
        return self.filter_by_score(entries, settings.high_score_threshold)
    
    def get_medium_priority_entries(self, entries: List[Dict]) -> List[Dict]:
        """中優先度案件の抽出"""
        return self.filter_by_score(entries, settings.medium_score_threshold)
    
    def clean_old_data(self, entries: List[Dict]) -> List[Dict]:
        """古いデータの除去"""
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=settings.data_retention_days)
        
        filtered_entries = []
        for entry in entries:
            published_date = entry.get('published_date')
            if published_date:
                try:
                    if isinstance(published_date, str):
                        published_date = datetime.strptime(published_date, '%Y-%m-%d').date()
                    
                    if published_date >= cutoff_date:
                        filtered_entries.append(entry)
                except Exception:
                    # 日付パースに失敗した場合は保持
                    filtered_entries.append(entry)
            else:
                # 日付情報がない場合は保持
                filtered_entries.append(entry)
        
        return filtered_entries
    
    def validate_entry(self, entry: Dict) -> bool:
        """エントリデータの検証"""
        required_fields = ['title', 'organization', 'source_url']
        
        for field in required_fields:
            if not entry.get(field):
                logger.warning(f"Entry missing required field '{field}': {entry}")
                return False
        
        # タイトルの長さチェック
        if len(entry.get('title', '')) > 500:
            logger.warning(f"Entry title too long: {entry.get('title', '')[:100]}...")
            return False
        
        return True
    
    def normalize_entry_data(self, entry: Dict) -> Dict:
        """エントリデータの正規化"""
        normalized = {}
        
        # 必須フィールド
        normalized['title'] = entry.get('title', '').strip()[:500]
        normalized['description'] = entry.get('description', '').strip()
        normalized['organization'] = entry.get('organization', '').strip()[:200]
        normalized['region'] = entry.get('region', '').strip()[:100]
        normalized['source_url'] = entry.get('source_url', '').strip()[:500]
        normalized['source_type'] = entry.get('source_type', '').strip()[:50]
        
        # 任意フィールド
        normalized['budget_amount'] = entry.get('budget_amount')
        normalized['published_date'] = entry.get('published_date')
        normalized['deadline_date'] = entry.get('deadline_date')
        normalized['relevance_score'] = entry.get('relevance_score', 0)
        normalized['keywords_matched'] = entry.get('keywords_matched', '[]')
        
        return normalized

# デバッグ用のサンプルデータ生成
class DataProcessorTester:
    """データ処理テスト用クラス"""
    
    @staticmethod
    def generate_sample_entries() -> List[Dict]:
        """サンプルエントリ生成"""
        return [
            {
                "title": "コールセンター業務委託",
                "description": "市民からの問い合わせ対応業務。電話受付とデータ入力作業を含む。",
                "organization": "○○市",
                "region": "東京都",
                "budget_amount": 5000000,
                "published_date": date.today(),
                "deadline_date": date.today(),
                "source_url": "https://example.com/bid/1",
                "source_type": "government_api"
            },
            {
                "title": "データ入力業務",
                "description": "アンケート結果のデータ入力作業",
                "organization": "△△県",
                "region": "大阪府",
                "budget_amount": 2000000,
                "published_date": date.today(),
                "deadline_date": date.today(),
                "source_url": "https://example.com/bid/2",
                "source_type": "government_api"
            },
            {
                "title": "建設工事",
                "description": "道路建設工事",
                "organization": "☆☆市",
                "region": "愛知県",
                "budget_amount": 50000000,
                "published_date": date.today(),
                "deadline_date": date.today(),
                "source_url": "https://example.com/bid/3",
                "source_type": "government_api"
            }
        ]
    
    @staticmethod
    def test_processing():
        """処理テスト実行"""
        processor = BidDataProcessor()
        sample_entries = DataProcessorTester.generate_sample_entries()
        
        print("=== Original Entries ===")
        for entry in sample_entries:
            print(f"Title: {entry['title']}")
            print(f"Description: {entry['description']}")
            print()
        
        processed = processor.process_entries(sample_entries)
        
        print("=== Processed Entries ===")
        for entry in processed:
            print(f"Title: {entry['title']}")
            print(f"Score: {entry['relevance_score']}")
            print(f"Keywords: {entry['keywords_matched']}")
            print()

if __name__ == "__main__":
    DataProcessorTester.test_processing()