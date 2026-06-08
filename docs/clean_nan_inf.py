"""
清理 stock_bar / stock_bar_minute / ram_stop_loss 表中的 NaN / Inf 值
適用於 PostgreSQL 13+
執行：python docs/clean_nan_inf.py
"""
import os
import sys
from pathlib import Path

# 確保可以 import app 模組
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402


CLEAN_QUERIES = [
    # 1. 清理 stock_bar 技術指標欄位的 NaN/Inf
    "UPDATE stock_bar SET ma10_w = NULL WHERE NOT (ma10_w = ma10_w);",
    "UPDATE stock_bar SET ma30_w = NULL WHERE NOT (ma30_w = ma30_w);",
    "UPDATE stock_bar SET volume_ma5_w = NULL WHERE NOT (volume_ma5_w = volume_ma5_w);",
    "UPDATE stock_bar SET change_pct = NULL WHERE NOT (change_pct = change_pct);",
    # 2. 清理 OHLCV 的 NaN/Inf
    "UPDATE stock_bar SET open  = NULL WHERE NOT (open  = open);",
    "UPDATE stock_bar SET high  = NULL WHERE NOT (high  = high);",
    "UPDATE stock_bar SET low   = NULL WHERE NOT (low   = low);",
    "UPDATE stock_bar SET close = NULL WHERE NOT (close = close);",
    # 3. 負值 volume 防呆
    "UPDATE stock_bar SET volume = NULL WHERE volume < 0;",
    # 4. 清理 stock_bar_minute
    "UPDATE stock_bar_minute SET open  = NULL WHERE NOT (open  = open);",
    "UPDATE stock_bar_minute SET high  = NULL WHERE NOT (high  = high);",
    "UPDATE stock_bar_minute SET low   = NULL WHERE NOT (low   = low);",
    "UPDATE stock_bar_minute SET close = NULL WHERE NOT (close = close);",
    "UPDATE stock_bar_minute SET corrected_open  = NULL WHERE NOT (corrected_open  = corrected_open);",
    "UPDATE stock_bar_minute SET corrected_close = NULL WHERE NOT (corrected_close = corrected_close);",
]


def main():
    print("🧹 開始清理 NaN / Inf 值...")
    db = SessionLocal()
    try:
        for sql in CLEAN_QUERIES:
            result = db.execute(text(sql))
            print(f"  ✅ {sql[:80]}... → {result.rowcount} 筆受影響")
        db.commit()

        # 統計結果
        stats = db.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM stock_bar WHERE ma10_w IS NULL)        AS stock_bar_ma10_null,
                    (SELECT COUNT(*) FROM stock_bar WHERE ma30_w IS NULL)        AS stock_bar_ma30_null,
                    (SELECT COUNT(*) FROM stock_bar WHERE volume_ma5_w IS NULL)  AS stock_bar_volma5_null,
                    (SELECT COUNT(*) FROM stock_bar WHERE change_pct IS NULL)    AS stock_bar_chgpct_null;
                """
            )
        ).fetchone()
        print("\n📊 清理後 NULL 計數：")
        print(f"   stock_bar.ma10_w        = {stats[0]}")
        print(f"   stock_bar.ma30_w        = {stats[1]}")
        print(f"   stock_bar.volume_ma5_w  = {stats[2]}")
        print(f"   stock_bar.change_pct    = {stats[3]}")
        print("\n🎉 清理完成！")
    except Exception as e:
        db.rollback()
        print(f"❌ 清理失敗: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
