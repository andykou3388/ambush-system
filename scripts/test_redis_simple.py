#!/usr/bin/env python3
"""
簡單的 Redis 連線測試腳本
"""

import redis
import sys

def test_redis_connection():
    try:
        # 嘗試連接到 Redis
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # 測試連線
        result = r.ping()
        print("SUCCESS: Redis 連線成功")
        print(f"Ping 回應: {result}")
        return True
        
    except Exception as e:
        print(f"ERROR: Redis 連線失敗 - {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)