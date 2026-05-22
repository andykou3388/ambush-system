"""
測試資料檢查腳本
用於驗證資料庫持久化功能
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_test_data():
    """檢查測試資料是否存在"""
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
        print("[OK] 在資料庫中找到測試資料:")
        print("-" * 60)
        for row in rows:
            print(f"ID: {row[0]}, 名稱: {row[1]}, 值: {row[2]}, 創建時間: {row[3]}")
        print("-" * 60)
        print(f"總共找到 {len(rows)} 條記錄")
    else:
        print("[ERROR] 在資料庫中未找到測試資料")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_test_data()