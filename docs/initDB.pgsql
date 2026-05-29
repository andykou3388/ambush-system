-- 1. 股票基本資料表
CREATE TABLE stock (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(50),
    market VARCHAR(10), -- HK / TW / US
    industry VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (code, market)
);

-- 2. K線資料表（日線 + 周線）
CREATE TABLE stock_kline (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    time DATE NOT NULL,
    open DECIMAL(12,2),
    high DECIMAL(12,2),
    low DECIMAL(12,2),
    close DECIMAL(12,2),
    volume BIGINT,
    ma30 DECIMAL(12,2),
    type VARCHAR(10), -- day / week
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (symbol, time, type)
);

-- 3. 分鐘級實時數據（放量監控專用）
CREATE TABLE realtime_minute_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    time TIMESTAMP NOT NULL,
    open DECIMAL(12,2),
    high DECIMAL(12,2),
    low DECIMAL(12,2),
    close DECIMAL(12,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. 每周分析報告（三區分類 + 超級強勢股）
CREATE TABLE weekly_analysis_report (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    market VARCHAR(10),
    close DECIMAL(12,2),
    ma30 DECIMAL(12,2),
    volume_ratio DECIMAL(10,2),
    zone VARCHAR(20), -- 強勢區 / 弱勢區 / 徘徊區
    analyze_time TIMESTAMP DEFAULT NOW()
);