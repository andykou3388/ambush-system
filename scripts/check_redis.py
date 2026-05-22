"""
Redis 連線測試腳本

可在以下環境執行：
1. 本機環境：python scripts/check_redis.py
2. Docker 容器內：python check_redis.py --docker（需先複製到容器）

用法:
  python scripts/check_redis.py              # 使用 .env 的 REDIS_HOST/REDIS_PORT 等變數
  python scripts/check_redis.py --docker     # 使用 REDIS_URL（容器內用）
"""

import redis
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 如果傳入 --docker 參數，直接從 REDIS_URL 解析
if "--docker" in sys.argv:
    # REDIS_URL 格式: redis://:password@host:port/db
    redis_url = os.getenv("REDIS_URL", "redis://:dev_redis_pass@redis:6379")
    # 簡單解析 URL
    parts = redis_url.replace("redis://", "").split("@")
    if len(parts) > 1:
        password_host_part = parts[0]
        host_port = parts[1]
    else:
        password_host_part = ""
        host_port = parts[0]
    
    # 解析密碼和主機資訊
    if ":" in password_host_part:
        password, host = password_host_part.split(":")
    else:
        password = ""
        host = password_host_part
    
    # 解析主機和埠
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "6379"

    r = redis.Redis(
        host=host,
        port=int(port),
        password=password if password else None,
        decode_responses=True,
    )
else:
    # 本機環境使用個別變數
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )

try:
    r.ping()
    print(f"SUCCESS: Redis 連線成功: {r.ping()}")
except Exception as e:
    print(f"ERROR: Redis 連線失敗: {e}")
    sys.exit(1)