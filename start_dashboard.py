#!/usr/bin/env python3
"""
ローカルダッシュボードサーバー起動スクリプト
"""

import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

def start_dashboard_server():
    """ダッシュボードサーバーを起動"""
    
    # docsディレクトリに移動
    docs_dir = os.path.join(os.getcwd(), 'docs')
    
    if not os.path.exists(docs_dir):
        print("❌ docs/ディレクトリが見つかりません")
        print("先にダッシュボードを生成してください: python src/web/dashboard_generator.py")
        return False
    
    os.chdir(docs_dir)
    
    # サーバー設定
    port = 8080
    host = 'localhost'
    
    # HTTPサーバー起動
    try:
        server = HTTPServer((host, port), SimpleHTTPRequestHandler)
        
        print("🚀 入札案件ダッシュボード起動中...")
        print(f"📍 URL: http://{host}:{port}")
        print("✨ ブラウザが自動で開きます")
        print("🛑 終了するには Ctrl+C を押してください")
        print("-" * 50)
        
        # ブラウザを自動で開く（少し遅延）
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://{host}:{port}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # サーバー開始
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しています...")
        server.shutdown()
        print("✅ ダッシュボードサーバーが停止しました")
        return True
        
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ ポート {port} は既に使用されています")
            print("他のサーバーを停止するか、別のポートを使用してください")
        else:
            print(f"❌ サーバー起動エラー: {e}")
        return False
    
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def check_dashboard_files():
    """ダッシュボードファイルの確認"""
    print("📋 ダッシュボードファイル確認中...")
    
    required_files = [
        'docs/index.html',
        'docs/dashboard_data.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - ファイルが見つかりません")
    
    if missing_files:
        print("\n⚠️  不足しているファイルがあります")
        print("以下のコマンドでダッシュボードを生成してください:")
        print("python src/web/dashboard_generator.py")
        return False
    
    print("✅ 全ての必要ファイルが揃っています\n")
    return True

def show_dashboard_info():
    """ダッシュボード情報表示"""
    print("📊 入札案件自動収集システム - Webダッシュボード")
    print("=" * 60)
    print("機能:")
    print("  📈 リアルタイム統計表示")
    print("  🔍 案件検索・フィルタリング")
    print("  📋 案件一覧表示")
    print("  📥 CSVエクスポート")
    print("  📱 レスポンシブデザイン")
    print()
    print("操作方法:")
    print("  • 検索ボックス: 案件名・発注機関で検索")
    print("  • 優先度フィルタ: 高・中・低優先度で絞り込み")
    print("  • 詳細ボタン: 案件の詳細ページを開く")
    print("  • エクスポートボタン: CSV形式でダウンロード")
    print("=" * 60)

def main():
    """メイン実行"""
    show_dashboard_info()
    
    # ファイル確認
    if not check_dashboard_files():
        sys.exit(1)
    
    # サーバー起動
    try:
        start_dashboard_server()
    except KeyboardInterrupt:
        print("\n👋 ダッシュボードを終了しました")

if __name__ == "__main__":
    main()