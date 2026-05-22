"""
測試資料寫入腳本
用於驗證資料庫持久化功能
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_test_table():
    """建立測試表格"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "ambush_dev"),
        user=os.getenv("DB_USER", "dev_user"),
        password=os.getenv("DB_PASSWORD", "dev_pass_123"),
    )
    
    cur = conn.cursor()
    
    # 建立測試表格
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_persistence (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cur.execute(create_table_query)
    
    # 插入測試資料
    insert_query = """
    INSERT INTO test_persistence (name, value) VALUES (%s, %s);
    """
    test_data = [
        ("test_item_1", "測試值 1"),
        ("test_item_2", "測試值 2"),
        ("test_item_3", "測試值 3")
    ]
    
    for name, value in test_data:
        cur.execute(insert_query, (name, value))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("[OK] 測試資料已成功寫入資料庫")

if __name__ == "__main__":
    create_test_table()