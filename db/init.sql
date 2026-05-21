-- PostgreSQL 初始化腳本 - 開發環境
-- 注意：POSTGRES_DB=ambush_dev 已由 docker-compose 自動建立

-- 建立擴展（金融數據分析常用）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- 效能監控

-- 設定時區
ALTER DATABASE ambush_dev SET timezone TO 'Asia/Taipei';
