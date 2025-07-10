import requests
import xml.etree.ElementTree as ET
import json
import time
from typing import List, Dict, Optional
from datetime import datetime, date
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class GovernmentProcurementAPI:
    """官公需情報ポータルサイトAPI連携クラス"""
    
    def __init__(self):
        self.base_url = "http://www.kkj.go.jp/api/"  # 実際のAPIエンドポイント
        self.timeout = settings.api_timeout
        self.retry_count = settings.api_retry_count
        self.retry_delay = settings.api_retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """API リクエスト実行（リトライ付き）"""
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"APIリクエスト実行 (試行 {attempt + 1}/{self.retry_count}): {params}")
                
                response = self.session.get(
                    self.base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return self._parse_xml_response(response.text)
                else:
                    logger.warning(f"HTTP {response.status_code}: {response.text[:200]}")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"API request failed after {self.retry_count} attempts")
                    return None
                    
        return None
    
    def _parse_xml_response(self, xml_content: str) -> Dict:
        """XMLレスポンスをパース"""
        try:
            root = ET.fromstring(xml_content)
            
            # 検索結果を取得
            search_results = root.find('SearchResults')
            if search_results is None:
                logger.warning("SearchResults要素が見つかりません")
                return {"entries": [], "total_count": 0}
            
            search_hits = search_results.find('SearchHits')
            total_count = int(search_hits.text) if search_hits is not None else 0
            
            # 個別の検索結果を解析
            entries = []
            search_result_items = search_results.findall('SearchResult')
            
            for item in search_result_items:
                entry = self._parse_search_result_item(item)
                if entry:
                    entries.append(entry)
            
            logger.info(f"XML解析完了: 総件数={total_count}, 解析件数={len(entries)}")
            
            return {
                "entries": entries,
                "total_count": total_count
            }
            
        except ET.ParseError as e:
            logger.error(f"XML解析エラー: {e}")
            return {"entries": [], "total_count": 0}
    
    def _parse_search_result_item(self, item: ET.Element) -> Optional[Dict]:
        """個別の検索結果アイテムをパース"""
        try:
            def get_text_safe(element: ET.Element, tag: str) -> str:
                child = element.find(tag)
                return child.text if child is not None and child.text is not None else ""
            
            return {
                "title": get_text_safe(item, 'ProjectName'),
                "description": get_text_safe(item, 'ProjectDescription'),
                "organization": get_text_safe(item, 'OrganizationName'),
                "region": get_text_safe(item, 'PrefectureName'),
                "budget_amount": None,  # XMLには予算情報が含まれていない場合が多い
                "published_date": self._parse_date(get_text_safe(item, 'Date')),
                "deadline_date": self._parse_date(get_text_safe(item, 'CftIssueDate')),
                "source_url": get_text_safe(item, 'ExternalDocumentURI'),
                "source_type": "government_api",
                "category": get_text_safe(item, 'Category'),
                "city_name": get_text_safe(item, 'CityName'),
                "lg_code": get_text_safe(item, 'LgCode')
            }
            
        except Exception as e:
            logger.warning(f"検索結果アイテムの解析エラー: {e}")
            return None
    
    def search_bids(self, 
                    keywords: List[str],
                    region: Optional[str] = None,
                    organization: Optional[str] = None,
                    date_from: Optional[date] = None,
                    date_to: Optional[date] = None) -> List[Dict]:
        """入札情報検索"""
        
        all_entries = []
        
        # キーワード毎に検索実行（英語に変換して実行）
        keyword_translation = {
            "データ入力": "data entry",
            "データ入力案件": "data entry",
            "入力作業": "data entry",
            "キッティング": "kitting",
            "PC設定": "PC setup",
            "システム構築": "system construction",
            "コールセンター": "call center",
            "電話受付": "telephone reception",
            "事務業務": "office work"
        }
        
        for keyword in keywords:
            # 英語キーワードを使用（文字化け回避）
            search_keyword = keyword_translation.get(keyword, keyword)
            params = {"Query": search_keyword}
            
            if region:
                params["LG_Code"] = region
            if organization:
                params["Organization_Name"] = organization
            if date_from:
                params["Date_From"] = date_from.strftime("%Y-%m-%d")
            if date_to:
                params["Date_To"] = date_to.strftime("%Y-%m-%d")
                
            logger.info(f"Searching bids for keyword '{keyword}' -> '{search_keyword}' with params: {params}")
            
            response = self._make_request(params)
            if response:
                entries = response.get("entries", [])
                all_entries.extend(entries)
                logger.info(f"Found {len(entries)} entries for keyword '{keyword}' -> '{search_keyword}'")
            
            # レート制限を考慮して少し待機
            time.sleep(1)
        
        logger.info(f"Total found {len(all_entries)} entries from government API")
        return all_entries
    
    def _normalize_entries(self, entries: List[Dict]) -> List[Dict]:
        """API レスポンスを標準形式に変換"""
        normalized = []
        
        for entry in entries:
            try:
                normalized_entry = {
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "organization": entry.get("organization", ""),
                    "region": entry.get("region", ""),
                    "budget_amount": self._parse_budget(entry.get("budget", "")),
                    "published_date": self._parse_date(entry.get("published_date", "")),
                    "deadline_date": self._parse_date(entry.get("deadline_date", "")),
                    "source_url": entry.get("url", ""),
                    "source_type": "government_api"
                }
                normalized.append(normalized_entry)
                
            except Exception as e:
                logger.warning(f"Failed to normalize entry: {e}")
                continue
                
        return normalized
    
    def _parse_budget(self, budget_str: str) -> Optional[int]:
        """予算文字列を数値に変換"""
        if not budget_str:
            return None
            
        # 数値以外の文字を除去
        import re
        numbers = re.findall(r'\d+', budget_str.replace(',', ''))
        if numbers:
            return int(''.join(numbers))
        return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """日付文字列をdateオブジェクトに変換"""
        if not date_str:
            return None
            
        try:
            # 一般的な日付フォーマットを試行
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            
        return None
    
    def get_bid_details(self, bid_id: str) -> Optional[Dict]:
        """案件詳細情報取得"""
        params = {"id": bid_id}
        response = self._make_request("detail", params)
        
        if response:
            return self._normalize_entries([response])[0]
        return None

# モックデータ生成（開発・テスト用）
class MockGovernmentAPI(GovernmentProcurementAPI):
    """開発用モックAPI"""
    
    def search_bids(self, keywords: List[str], **kwargs) -> List[Dict]:
        """モックデータを返す"""
        logger.info(f"Mock API: Searching for keywords: {keywords}")
        
        mock_entries = [
            {
                "title": "コールセンター業務委託",
                "description": "市民からの問い合わせ対応業務",
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
            }
        ]
        
        # キーワードに基づいてフィルタリング
        filtered_entries = []
        for entry in mock_entries:
            text_to_search = f"{entry['title']} {entry['description']}".lower()
            if any(keyword.lower() in text_to_search for keyword in keywords):
                filtered_entries.append(entry)
        
        return filtered_entries