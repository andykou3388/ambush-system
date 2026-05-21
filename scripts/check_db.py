"""
PostgreSQL 連線測試腳本

可在以下環境執行：
1. 本機環境：python scripts/check_db.py
2. Docker 容器內：python check_db.py --docker（需先複製到容器）

用法:
  python scripts/check_db.py              # 使用 .env 的 DB_HOST/DB_PORT 等變數
  python scripts/check_db.py --docker     # 使用 DATABASE_URL（容器內用）
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 如果傳入 --docker 參數，直接從 DATABASE_URL 解析
if "--docker" in sys.argv:
    # DATABASE_URL 格式: postgresql://user:password@host:port/dbname
    db_url = os.getenv("DATABASE_URL", "postgresql://dev_user:dev_pass_123@db:5432/ambush_dev")
    # 簡單解析 URL
    parts = db_url.replace("postgresql://", "").split("@")
    user_pass, host_part = parts[0], parts[1]
    user, password = user_pass.split(":")
    host_port, dbname = host_part.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host, port = host_port, "5432"

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
else:
    # 本機環境使用個別變數
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "ambush_dev"),
        user=os.getenv("DB_USER", "dev_user"),
        password=os.getenv("DB_PASSWORD", "dev_pass_123"),
    )

cur = conn.cursor()
cur.execute("SELECT version();")
print(f"[OK] PostgreSQL 連線成功: {cur.fetchone()[0]}")
cur.close()
conn.close()
