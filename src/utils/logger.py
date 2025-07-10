import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(name: str = "bid_collector", level: str = "INFO") -> logging.Logger:
    """ログ設定"""
    
    # ログディレクトリ作成
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # ログファイル名
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    
    # ログレベル設定
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ログ設定
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 既存のハンドラーを削除（重複防止）
    if logger.handlers:
        logger.handlers.clear()
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger