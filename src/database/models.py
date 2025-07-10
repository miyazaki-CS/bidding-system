try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, Date, BigInteger, Boolean, DateTime, Index
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

import sqlite3
from datetime import datetime, date
from typing import Optional

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
else:
    Base = None

class ProcurementEntry(Base):
    """入札案件テーブル"""
    __tablename__ = "procurement_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    organization = Column(String(200))
    region = Column(String(100))
    budget_amount = Column(BigInteger)
    published_date = Column(Date)
    deadline_date = Column(Date)
    source_url = Column(String(500))
    source_type = Column(String(50))  # 'government_api', 'rss_feed', 'scraping'
    relevance_score = Column(Integer, default=0)  # 適合度スコア
    keywords_matched = Column(Text)  # マッチしたキーワード（JSON形式）
    processed = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # インデックス定義
    __table_args__ = (
        Index('idx_published_date', 'published_date'),
        Index('idx_relevance_score', 'relevance_score'),
        Index('idx_source_type', 'source_type'),
        Index('idx_processed', 'processed'),
        Index('idx_notified', 'notified'),
    )

class FilterKeyword(Base):
    """キーワード設定テーブル"""
    __tablename__ = "filter_keywords"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False)
    category = Column(String(50))  # 'include', 'exclude'
    priority = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class NotificationHistory(Base):
    """通知履歴テーブル"""
    __tablename__ = "notification_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(Integer, nullable=False)
    notification_type = Column(String(50))  # 'email', 'slack'
    recipient = Column(String(200))
    sent_at = Column(DateTime, default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text)

class SystemLog(Base):
    """システムログテーブル"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20))  # 'INFO', 'WARNING', 'ERROR'
    message = Column(Text)
    module = Column(String(100))
    execution_time = Column(DateTime, default=func.now())
    additional_data = Column(Text)  # JSON形式の追加データ

# データベース接続とセッション管理
class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """テーブル作成"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """セッション取得"""
        return self.SessionLocal()
        
    def close(self):
        """接続クローズ"""
        self.engine.dispose()

# ヘルパー関数
def create_procurement_entry(
    title: str,
    description: str = "",
    organization: str = "",
    region: str = "",
    budget_amount: Optional[int] = None,
    published_date: Optional[date] = None,
    deadline_date: Optional[date] = None,
    source_url: str = "",
    source_type: str = "",
    relevance_score: int = 0,
    keywords_matched: str = ""
) -> ProcurementEntry:
    """入札案件エントリー作成"""
    return ProcurementEntry(
        title=title,
        description=description,
        organization=organization,
        region=region,
        budget_amount=budget_amount,
        published_date=published_date,
        deadline_date=deadline_date,
        source_url=source_url,
        source_type=source_type,
        relevance_score=relevance_score,
        keywords_matched=keywords_matched
    )