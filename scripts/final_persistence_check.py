"""
最終持久化驗證腳本
用於確認資料庫在容器重啟後資料是否持續存在
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def final_persistence_check():
    """最終持久化檢查"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "ambush_dev"),
            user=os.getenv("DB_USER", "dev_user"),
            password=os.getenv("DB_PASSWORD", "dev_pass_123"),
        )
        
        cur = conn.cursor()
        
        # 查詢測試資料
        select_query = "SELECT id, name, value, created_at FROM test_persistence ORDER BY id;"
        cur.execute(select_query)
        
        rows = cur.fetchall()
        
        if rows:
            print("=" * 60)
            print("✅ 持久化驗證成功!")
            print("=" * 60)
            print("在資料庫中找到測試資料:")
            print("-" * 60)
            for row in rows:
                print(f"ID: {row[0]}, 名稱: {row[1]}, 值: {row[2]}, 創建時間: {row[3]}")
            print("-" * 60)
            print(f"總共找到 {len(rows)} 條記錄")
            print("=" * 60)
            print("💡 資料庫持久化功能驗證通過!")
            print("   容器重啟後資料依然存在，持久化功能正常。")
        else:
            print("❌ 在資料庫中未找到測試資料")
            print("   持久化功能可能有問題")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")

if __name__ == "__main__":
    final_persistence_check()