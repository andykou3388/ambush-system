-- ==========================================
-- 清理 stock_bar 表中可能導致 JSON 序列化錯誤的 NaN / Inf 值
-- 適用於 PostgreSQL 13+
-- 對應錯誤：ValueError: Out of range float values are not JSON compliant
-- 說明：x = x 在 IEEE 754 中對 NaN 永遠為 False，可用此特性判斷
-- ==========================================

BEGIN;

-- 1. 清理技術指標欄位的 NaN/Inf
UPDATE stock_bar SET ma10_w = NULL WHERE NOT (ma10_w = ma10_w);
UPDATE stock_bar SET ma30_w = NULL WHERE NOT (ma30_w = ma30_w);
UPDATE stock_bar SET volume_ma5_w = NULL WHERE NOT (volume_ma5_w = volume_ma5_w);
UPDATE stock_bar SET change_pct = NULL WHERE NOT (change_pct = change_pct);

-- 2. 清理 OHLCV 的 NaN/Inf
UPDATE stock_bar SET open  = NULL WHERE NOT (open  = open);
UPDATE stock_bar SET high  = NULL WHERE NOT (high  = high);
UPDATE stock_bar SET low   = NULL WHERE NOT (low   = low);
UPDATE stock_bar SET close = NULL WHERE NOT (close = close);

-- 3. 清理負值 volume（防呆）
UPDATE stock_bar SET volume = NULL WHERE volume < 0;

-- 4. 同步清理 stock_bar_minute 與 ram_stop_loss 表
UPDATE stock_bar_minute SET open  = NULL WHERE NOT (open  = open);
UPDATE stock_bar_minute SET high  = NULL WHERE NOT (high  = high);
UPDATE stock_bar_minute SET low   = NULL WHERE NOT (low   = low);
UPDATE stock_bar_minute SET close = NULL WHERE NOT (close = close);
UPDATE stock_bar_minute SET corrected_open  = NULL WHERE NOT (corrected_open  = corrected_open);
UPDATE stock_bar_minute SET corrected_close = NULL WHERE NOT (corrected_close = corrected_close);

-- 5. 統計清理結果
SELECT
    (SELECT COUNT(*) FROM stock_bar WHERE ma10_w IS NULL)    AS stock_bar_ma10_null,
    (SELECT COUNT(*) FROM stock_bar WHERE ma30_w IS NULL)    AS stock_bar_ma30_null,
    (SELECT COUNT(*) FROM stock_bar WHERE volume_ma5_w IS NULL) AS stock_bar_volma5_null,
    (SELECT COUNT(*) FROM stock_bar WHERE change_pct IS NULL) AS stock_bar_chgpct_null;

COMMIT;
