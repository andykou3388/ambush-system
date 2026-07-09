-- ==========================================
-- Ambush System 資料庫初始化腳本
-- 版本：V2.0（含拉姆動態止損）
-- ==========================================

-- 建立基礎資料表

-- 1. StockBar - K 棒數據表
CREATE TABLE IF NOT EXISTS stock_bar (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12,4),
    high_price      DECIMAL(12,4),
    low_price       DECIMAL(12,4),
    close_price     DECIMAL(12,4),
    volume          BIGINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_stock_bar UNIQUE(code, timestamp)
);

CREATE INDEX idx_stock_bar_code_time ON stock_bar(code, timestamp DESC);

COMMENT ON TABLE stock_bar IS '股票 K 棒數據';
COMMENT ON COLUMN stock_bar.code IS '股票代碼';
COMMENT ON COLUMN stock_bar.timestamp IS '時間戳記';

-- 2. StockFundamental - 基本面數據表
CREATE TABLE IF NOT EXISTS stock_fundamental (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    fetch_date      DATE NOT NULL,
    market_cap      DECIMAL(20,2),         -- 市值
    pe_ratio        DECIMAL(10,2),         -- PE 比率
    pb_ratio        DECIMAL(10,2),         -- PB 比率
    dividend_yield  DECIMAL(10,2),         -- 殖利率
    roe             DECIMAL(10,2),         -- ROE
    total_assets    DECIMAL(20,2),         -- 總資產
    total_liability DECIMAL(20,2),         -- 總負債
    equity          DECIMAL(20,2),         -- 權益
    net_income      DECIMAL(20,2),         -- 淨利
    revenue         DECIMAL(20,2),         -- 營收
    eps             DECIMAL(10,4),         -- EPS
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_stock_fundamental UNIQUE(code, fetch_date)
);

CREATE INDEX idx_stock_fundamental_code ON stock_fundamental(code);

COMMENT ON TABLE stock_fundamental IS '股票基本面歷史數據';
COMMENT ON COLUMN stock_fundamental.code IS '股票代碼';

-- 3. StockSignalLog - 信號日誌表
CREATE TABLE IF NOT EXISTS stock_signal_log (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    signal_type     VARCHAR(50) NOT NULL,
    signal_time     TIMESTAMPTZ NOT NULL,
    price           DECIMAL(12,4),
    details         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_signal_code_time ON stock_signal_log(code, signal_time DESC);

COMMENT ON TABLE stock_signal_log IS '交易信號日誌';

-- 4. AuditLog - 系統審計日誌
CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    action          VARCHAR(100) NOT NULL,
    user_id         INTEGER,
    entity_type     VARCHAR(50),
    entity_id       INTEGER,
    changes         JSONB,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_time ON audit_log(created_at DESC);

COMMENT ON TABLE audit_log IS '系統操作審計日誌';

-- 5. UserNotificationConfig - 用戶通知設定
CREATE TABLE IF NOT EXISTS user_notification_config (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    enable_email    BOOLEAN DEFAULT TRUE,
    enable_push     BOOLEAN DEFAULT TRUE,
    email_address   VARCHAR(255),
    min_pe_threshold DECIMAL(10,2),
    max_pe_threshold DECIMAL(10,2),
    min_roe_threshold DECIMAL(10,2),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_notification UNIQUE(user_id)
);

COMMENT ON TABLE user_notification_config IS '用戶通知偏好設定';

-- 6. MediaHeat - 媒體熱度分析
CREATE TABLE IF NOT EXISTS media_heat (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    heat_score      INTEGER DEFAULT 0,
    news_count      INTEGER DEFAULT 0,
    sentiment_score DECIMAL(5,2),
    analyzed_at     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_media_heat UNIQUE(code, analyzed_at)
);

CREATE INDEX idx_media_heat_code ON media_heat(code);

COMMENT ON TABLE media_heat IS '媒體熱度分析數據';

-- 7. SystemConfig - 系統配置
CREATE TABLE IF NOT EXISTS system_config (
    id              SERIAL PRIMARY KEY,
    config_key      VARCHAR(100) UNIQUE NOT NULL,
    config_value    JSONB NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE system_config IS '系統配置';

-- 8. StockFundamentalLatest - 基本面最新數據快照
CREATE TABLE IF NOT EXISTS stock_fundamental_latest (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) PRIMARY KEY,
    market_cap      DECIMAL(20,2),
    pe_ratio        DECIMAL(10,2),
    pb_ratio        DECIMAL(10,2),
    dividend_yield  DECIMAL(10,2),
    roe             DECIMAL(10,2),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE stock_fundamental_latest IS '基本面最新快照（用於快速篩選）';

-- 9. StockBarMinute - 分鐘 K 棒數據
CREATE TABLE IF NOT EXISTS stock_bar_minute (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    open_price      DECIMAL(12,4),
    high_price      DECIMAL(12,4),
    low_price       DECIMAL(12,4),
    close_price     DECIMAL(12,4),
    volume          BIGINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_stock_bar_minute UNIQUE(code, timestamp)
);

CREATE INDEX idx_stock_bar_minute_code_time ON stock_bar_minute(code, timestamp DESC);

COMMENT ON TABLE stock_bar_minute IS '分鐘 K 棒數據';

-- 10. RamStopLoss - 拉姆動態止損狀態
CREATE TABLE IF NOT EXISTS ram_stop_loss (
    code            VARCHAR(20) PRIMARY KEY,
    buy_date        DATE NOT NULL,
    buy_price       DECIMAL(12,4) NOT NULL,
    highest_price   DECIMAL(12,4) NOT NULL,
    current_price   DECIMAL(12,4) NOT NULL,
    stop_loss_price DECIMAL(12,4) NOT NULL,
    drawdown_pct    DECIMAL(10,4) NOT NULL,
    is_triggered    BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_ram_code UNIQUE(code)
);

CREATE INDEX idx_ram_active ON ram_stop_loss(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE ram_stop_loss IS '拉姆動態止損狀態表';
COMMENT ON COLUMN ram_stop_loss.code IS '股票代碼（唯一）';
COMMENT ON COLUMN ram_stop_loss.buy_date IS '買入日期';
COMMENT ON COLUMN ram_stop_loss.buy_price IS '買入價格';
COMMENT ON COLUMN ram_stop_loss.highest_price IS '持有期間最高價（動態更新）';
COMMENT ON COLUMN ram_stop_loss.current_price IS '當前價格';
COMMENT ON COLUMN ram_stop_loss.stop_loss_price IS '止損價格（最高價 × (1 - drawdown_ratio)）';
COMMENT ON COLUMN ram_stop_loss.drawdown_pct IS '當前回撤比例';
COMMENT ON COLUMN ram_stop_loss.is_triggered IS '是否已觸發止損';
COMMENT ON COLUMN ram_stop_loss.is_active IS '是否啟用中';

-- 11. 監控股票清單表（動態管理抓取標的）
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