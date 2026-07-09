-- ==========================================
-- Migration 001：新增 monitored_stocks 表
-- 用於動態管理 Celery 排程的抓取標的
-- ==========================================

CREATE TABLE IF NOT EXISTS monitored_stocks (
    code        VARCHAR(20) PRIMARY KEY,
    market      VARCHAR(4) NOT NULL DEFAULT 'TW',
    added_at    TIMESTAMP DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_monitored_stocks_active
    ON monitored_stocks (is_active)
    WHERE is_active = TRUE;

COMMENT ON TABLE monitored_stocks IS '監控股票清單（Celery 排程與一次性初始化均從此表讀取抓取標的）';
COMMENT ON COLUMN monitored_stocks.code IS '股票代碼（主鍵）';
COMMENT ON COLUMN monitored_stocks.market IS '市場：TW=台股，US=美股，HK=港股';
COMMENT ON COLUMN monitored_stocks.added_at IS '加入時間';
COMMENT ON COLUMN monitored_stocks.is_active IS '是否啟用（軟刪除）';