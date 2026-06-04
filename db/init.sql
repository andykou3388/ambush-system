-- ==========================================
-- 一分鐘伏擊超級強勢股智能監控系統
-- 資料庫初始化腳本 (init.sql)
-- 適用於 PostgreSQL 16
-- 版本：V2.0 | 2026-06-03（優化版：雙表基本面 + 分鐘線 + 拉姆止損）
-- ==========================================

-- 啟用必要擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ==========================================
-- 1. 週線行情與指標表 (stock_bar)
-- ==========================================
CREATE TABLE stock_bar (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    market VARCHAR(4) NOT NULL DEFAULT 'TW',
    trade_date DATE NOT NULL,
    freq VARCHAR(2) NOT NULL DEFAULT 'W' CHECK (freq IN ('D','W','M')),
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    amount BIGINT,
    change_pct NUMERIC(6,2),
    ma10_w NUMERIC(12,4),
    ma30_w NUMERIC(12,4),
    volume_ma5_w NUMERIC(12,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, trade_date)
) PARTITION BY RANGE (trade_date);

-- 按年分區
CREATE TABLE stock_bar_2025 PARTITION OF stock_bar FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE stock_bar_2026 PARTITION OF stock_bar FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE stock_bar_2027 PARTITION OF stock_bar FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
CREATE TABLE stock_bar_2028 PARTITION OF stock_bar FOR VALUES FROM ('2028-01-01') TO ('2029-01-01');

-- 索引
CREATE UNIQUE INDEX idx_bar_code_date ON stock_bar(code, trade_date DESC);
CREATE INDEX idx_bar_date ON stock_bar(trade_date DESC);
CREATE INDEX idx_bar_market ON stock_bar(market);
CREATE INDEX idx_bar_ma30 ON stock_bar(ma30_w) WHERE ma30_w IS NOT NULL;

COMMENT ON TABLE stock_bar IS '週線行情與技術指標表（OHLCV+MA10/MA30/VolumeMA5）';
COMMENT ON COLUMN stock_bar.code IS '股票代碼';
COMMENT ON COLUMN stock_bar.name IS '股票名稱（前端顯示用）';
COMMENT ON COLUMN stock_bar.market IS '市場：TW=台股, US=美股, HK=港股';
COMMENT ON COLUMN stock_bar.trade_date IS '交易日（週五收盤日）';
COMMENT ON COLUMN stock_bar.freq IS '頻率：D=日線, W=週線, M=月線';
COMMENT ON COLUMN stock_bar.amount IS '成交金額';
COMMENT ON COLUMN stock_bar.change_pct IS '週漲跌幅百分比（前端顯示用）';
COMMENT ON COLUMN stock_bar.ma10_w IS '10週移動平均線（策略生命線）';
COMMENT ON COLUMN stock_bar.ma30_w IS '30週移動平均線（趨勢錨點）';
COMMENT ON COLUMN stock_bar.volume_ma5_w IS '5週均量';

-- ==========================================
-- 2. 基本面與籌碼表 (stock_fundamental)
-- ==========================================
CREATE TABLE stock_fundamental (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    market VARCHAR(4) NOT NULL DEFAULT 'TW',
    report_date DATE NOT NULL,
    pe_ttm NUMERIC(10,4),
    eps_ttm NUMERIC(10,4),
    float_shares BIGINT,
    debt_ratio NUMERIC(6,4),
    insider_net_buy_3m BIGINT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_code_report UNIQUE(code, report_date)
);

CREATE INDEX idx_fund_market ON stock_fundamental(market);
CREATE INDEX idx_fund_pe ON stock_fundamental(pe_ttm) WHERE pe_ttm IS NOT NULL;
CREATE INDEX idx_fund_eps ON stock_fundamental(eps_ttm) WHERE eps_ttm > 0;

COMMENT ON TABLE stock_fundamental IS '基本面濾網（PE/EPS/流通股本/負債/內部持股）';
COMMENT ON COLUMN stock_fundamental.code IS '股票代碼';
COMMENT ON COLUMN stock_fundamental.market IS '市場：TW=台股, US=美股';
COMMENT ON COLUMN stock_fundamental.report_date IS '報告日期';
COMMENT ON COLUMN stock_fundamental.pe_ttm IS '滾動本益比（TTM），Layer 3 篩選：< 10';
COMMENT ON COLUMN stock_fundamental.eps_ttm IS '滾動每股盈餘（TTM），Layer 3 篩選：> 0';
COMMENT ON COLUMN stock_fundamental.float_shares IS '流通股本（股），Layer 3 篩選：5000萬~5億';
COMMENT ON COLUMN stock_fundamental.debt_ratio IS '資產負債率，Layer 3 篩選：低負債';
COMMENT ON COLUMN stock_fundamental.insider_net_buy_3m IS '內部人近3月淨買入股數，Layer 3 篩選：> 0';

-- ==========================================
-- 3. 信號狀態機與規則快照表 (stock_signal_log)
-- ==========================================
CREATE TABLE stock_signal_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(20) NOT NULL,
    market VARCHAR(4) NOT NULL DEFAULT 'TW',
    trade_date DATE NOT NULL,
    zone VARCHAR(12) NOT NULL CHECK (zone IN ('POTENTIAL','UPTREND','DOWNTREND')),
    confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0.00 AND 1.00),
    trigger_rules JSONB DEFAULT '{}',
    reason TEXT,
    engine_version VARCHAR(10) DEFAULT 'V2.2',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, trade_date)
) PARTITION BY RANGE (trade_date);

CREATE TABLE stock_signal_log_2025 PARTITION OF stock_signal_log FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE stock_signal_log_2026 PARTITION OF stock_signal_log FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE stock_signal_log_2027 PARTITION OF stock_signal_log FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
CREATE TABLE stock_signal_log_2028 PARTITION OF stock_signal_log FOR VALUES FROM ('2028-01-01') TO ('2029-01-01');

-- 索引
CREATE UNIQUE INDEX idx_sig_code_date ON stock_signal_log(code, trade_date DESC);
CREATE INDEX idx_sig_market ON stock_signal_log(market);
CREATE INDEX idx_sig_zone_conf ON stock_signal_log(zone, confidence DESC);
CREATE INDEX idx_sig_rules ON stock_signal_log USING GIN(trigger_rules);
CREATE INDEX idx_sig_engine ON stock_signal_log(engine_version);

COMMENT ON TABLE stock_signal_log IS '策略狀態機輸出（三區判定+JSONB規則快照+置信度）';
COMMENT ON COLUMN stock_signal_log.code IS '股票代碼';
COMMENT ON COLUMN stock_signal_log.market IS '市場：TW=台股, US=美股';
COMMENT ON COLUMN stock_signal_log.trade_date IS '交易日';
COMMENT ON COLUMN stock_signal_log.zone IS '三區分類：POTENTIAL=驗證區, UPTREND=交易區, DOWNTREND=避雷區';
COMMENT ON COLUMN stock_signal_log.confidence IS '置信度（0.00~1.00）';
COMMENT ON COLUMN stock_signal_log.trigger_rules IS '觸發規則快照（JSONB格式），記錄各層規則狀態';
COMMENT ON COLUMN stock_signal_log.engine_version IS '規則引擎版本號';

-- ==========================================
-- 4. 審計日誌表 (audit_log)
-- ==========================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(64) NOT NULL,
    action_type VARCHAR(20) NOT NULL CHECK (
        action_type IN ('VIEW', 'BUY', 'SELL', 'IGNORE', 'LOGIN', 'LOGOUT', 'CONFIG_CHANGE')
    ),
    stock_ticker VARCHAR(20),
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_info JSONB,
    rule_snapshot JSONB,
    deviation_reason TEXT,
    compliance_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_time ON audit_log(user_id, executed_at);
CREATE INDEX idx_audit_action_type ON audit_log(action_type);
CREATE INDEX idx_audit_executed_at ON audit_log(executed_at);
CREATE INDEX idx_audit_compliance_hash ON audit_log(compliance_hash);

COMMENT ON TABLE audit_log IS '操作審計日誌（哈希鏈防篡改）';
COMMENT ON COLUMN audit_log.action_type IS '操作類型';
COMMENT ON COLUMN audit_log.compliance_hash IS 'SHA256(關鍵字段) 用於防篡改';
COMMENT ON COLUMN audit_log.previous_hash IS '上一條日誌的哈希，形成鏈';

-- ==========================================
-- 5. 用戶通知偏好表 (user_notification_config)
-- ==========================================
CREATE TABLE user_notification_config (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    channel VARCHAR(10) NOT NULL CHECK (channel IN ('APP', 'WECHAT', 'EMAIL')),
    zone_filter VARCHAR(12)[] DEFAULT '{UPTREND,DOWNTREND}',
    min_confidence NUMERIC(3,2) DEFAULT 0.5,
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_channel UNIQUE(user_id, channel)
);

CREATE INDEX idx_notif_user ON user_notification_config(user_id);

COMMENT ON TABLE user_notification_config IS '用戶通知偏好配置';
COMMENT ON COLUMN user_notification_config.channel IS '推送通道：APP/企微/郵件';
COMMENT ON COLUMN user_notification_config.zone_filter IS '感興趣的區域（可多選）';
COMMENT ON COLUMN user_notification_config.min_confidence IS '最低置信度閾值';

-- ==========================================
-- 6. 媒體熱度表 (media_heat)
-- ==========================================
CREATE TABLE media_heat (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    record_date DATE NOT NULL,
    heat_score NUMERIC(5,2) DEFAULT 0,
    news_count INT DEFAULT 0,
    forum_mention_count INT DEFAULT 0,
    social_media_mentions INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_code_heat_date UNIQUE(code, record_date)
);

CREATE INDEX idx_heat_code_date ON media_heat(code, record_date DESC);
CREATE INDEX idx_heat_score ON media_heat(heat_score DESC) WHERE heat_score > 0;

COMMENT ON TABLE media_heat IS '媒體熱度數據（輔助Layer 4賣點判斷）';
COMMENT ON COLUMN media_heat.heat_score IS '綜合熱度評分（0~100）';

-- ==========================================
-- 7. 系統配置表 (system_config)
-- ==========================================
CREATE TABLE system_config (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    config_key VARCHAR(64) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE system_config IS '系統配置（規則參數、閾值等）';

-- 插入默認配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('rule_engine.version', '"V2.2"', '當前規則引擎版本'),
('rule_engine.params', '{
    "ma10_buffer_pct": 1.5,
    "buy_deviation_pct": 3.0,
    "buy_volume_ratio": 0.7,
    "volume_surge_ratio": 2.0,
    "max_pe": 10,
    "risk_weekly_drop_pct": 15,
    "risk_consecutive_weeks": 2
}', '規則引擎參數配置'),
('data_source.primary', '"yfinance"', '主數據源'),
('data_source.fallback', '"yfinance"', '備用數據源（暫與主數據源相同）'),
('ram_stop_loss.params', '{
    "drawdown_ratio": 0.08,
    "trailing_high_period": "all",
    "check_interval_seconds": 60
}', '拉姆止損參數配置');

-- ==========================================
-- 8. 最新基本面緩存表（優化批量篩選性能）
-- ==========================================
CREATE TABLE stock_fundamental_latest (
    code VARCHAR(20) PRIMARY KEY,
    market VARCHAR(4) NOT NULL DEFAULT 'TW',
    report_date DATE NOT NULL,
    pe_ttm NUMERIC(10,4),
    eps_ttm NUMERIC(10,4),
    float_shares BIGINT,
    debt_ratio NUMERIC(6,4),
    insider_net_buy_3m BIGINT,
    pb NUMERIC(10,4),
    dividend_yield NUMERIC(8,4),
    total_market_cap NUMERIC(18,2),
    net_profit_ttm NUMERIC(18,2),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fund_latest_pe_eps ON stock_fundamental_latest(pe_ttm, eps_ttm);
CREATE INDEX idx_fund_latest_market ON stock_fundamental_latest(market);

COMMENT ON TABLE stock_fundamental_latest IS '最新基本面緩存表（每隻股票僅保留最新一筆，用於批量篩選）';
COMMENT ON COLUMN stock_fundamental_latest.code IS '股票代碼（主鍵）';
COMMENT ON COLUMN stock_fundamental_latest.market IS '市場：TW=台股, US=美股, HK=港股';
COMMENT ON COLUMN stock_fundamental_latest.report_date IS '報告日期';
COMMENT ON COLUMN stock_fundamental_latest.pe_ttm IS '滾動本益比（TTM）';
COMMENT ON COLUMN stock_fundamental_latest.eps_ttm IS '滾動每股盈餘（TTM）';
COMMENT ON COLUMN stock_fundamental_latest.pb IS '股價淨值比';
COMMENT ON COLUMN stock_fundamental_latest.dividend_yield IS '股息率（%）';
COMMENT ON COLUMN stock_fundamental_latest.total_market_cap IS '總市值';
COMMENT ON COLUMN stock_fundamental_latest.net_profit_ttm IS '滾動淨利潤（TTM）';

-- ==========================================
-- 9. 分鐘線行情表（拉姆止損專用）
-- ==========================================
CREATE TABLE stock_bar_minute (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    trade_time TIMESTAMPTZ NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    is_valid BOOLEAN DEFAULT TRUE,
    corrected_open NUMERIC(12,4),
    corrected_close NUMERIC(12,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_code_minute UNIQUE(code, trade_time)
);

CREATE INDEX idx_minute_code_time ON stock_bar_minute(code, trade_time DESC);

COMMENT ON TABLE stock_bar_minute IS '分鐘線行情表（拉姆動態止損專用）';
COMMENT ON COLUMN stock_bar_minute.code IS '股票代碼';
COMMENT ON COLUMN stock_bar_minute.trade_time IS '交易時間（分鐘級）';
COMMENT ON COLUMN stock_bar_minute.is_valid IS '數據是否有效（FALSE表示可疑記錄）';
COMMENT ON COLUMN stock_bar_minute.corrected_open IS '修正後開盤價';
COMMENT ON COLUMN stock_bar_minute.corrected_close IS '修正後收盤價（止損計算使用此字段）';

-- ==========================================
-- 10. 拉姆止損狀態表
-- ==========================================
CREATE TABLE ram_stop_loss (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    market VARCHAR(4) NOT NULL DEFAULT 'TW',
    buy_date DATE NOT NULL,
    buy_price NUMERIC(12,4) NOT NULL,
    highest_price NUMERIC(12,4) NOT NULL,
    current_price NUMERIC(12,4) NOT NULL,
    stop_loss_price NUMERIC(12,4) NOT NULL,
    drawdown_pct NUMERIC(6,4) DEFAULT 0,
    is_triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
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
