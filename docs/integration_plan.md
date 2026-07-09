# 一分鐘伏擊系統整合執行計畫

> **版本**：V1.0｜**最後更新**：2026-06-01  
> **負責人**：後端 / DevOps  
> **狀態**：待審批

---

## 目錄

1. [現狀分析](#1-現狀分析)
2. [整合目標](#2-整合目標)
3. [執行階段](#3-執行階段)
4. [詳細任務清單](#4-詳細任務清單)
5. [檔案修改對照表](#5-檔案修改對照表)
6. [風險與對策](#6-風險與對策)
7. [驗收標準](#7-驗收標準)

---

## 1. 現狀分析

### 1.1 系統架構總覽

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Vite)                    │
│  Front.vue → StockCard.vue → StockDetail.vue             │
│  API 串接: /api/v1/screener/stocks/batch                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────┐
│                  後端 (FastAPI)                          │
│  routers/screener.py → tasks_helper.py                   │
│  engine/rule_engine.py → classifier/zone_classifier.py   │
└──────────────────────┬──────────────────────────────────┘
                       │ SQLAlchemy ORM
┌──────────────────────▼──────────────────────────────────┐
│               PostgreSQL 16 (7 張表)                     │
│  stock_bar / stock_fundamental / stock_signal_log        │
│  audit_log / user_notification_config / media_heat       │
│  system_config                                           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 目前存在的問題

| 問題 | 說明 | 嚴重性 |
|------|------|--------|
| **模擬數據** | `tasks_helper.py` 中所有函數回傳硬編碼數據 | 🔴 高 |
| **缺少 ORM** | 後端沒有資料庫連線層，無法讀寫資料 | 🔴 高 |
| **Schema 不一致** | `docs/initDB.pgsql` 與新的 `init.sql` 不同步 | 🟡 中 |
| **Zone 命名混亂** | 系統中存在 4 種不同的 zone 命名方式 | 🟡 中 |
| **前端缺欄位** | `Front.vue` 部分欄位仍是 mock 數據 | 🟢 低 |

### 1.3 現有檔案結構

```
backend/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── celery_app.py              # Celery 配置
│   ├── service_task.py            # 週期性分析任務
│   ├── tasks_helper.py            # ⚠️ 模擬數據，需改寫
│   ├── routers/
│   │   ├── health.py
│   │   ├── screener.py            # ⚠️ 需串接資料庫
│   │   └── stock_detail.py
│   └── models/                    # 📦 需新增
│       ├── __init__.py
│       ├── base.py
│       ├── stock_bar.py
│       ├── stock_fundamental.py
│       ├── stock_signal_log.py
│       ├── audit_log.py
│       ├── user_notification_config.py
│       ├── media_heat.py
│       └── system_config.py
├── engine/
│   └── rule_engine.py             # ⚠️ 需支援資料庫讀取
└── classifier/
    └── zone_classifier.py         # ✅ 可沿用

db/
├── init.sql                       # 📦 需更新為新 Schema
└── postgresql.conf

frontend/src/
├── views/
│   └── Front.vue                  # ⚠️ 需調整 zone 映射
├── components/
│   ├── StatCard.vue               # ✅ 可沿用
│   ├── StockCard.vue              # ✅ 可沿用
│   ├── StockCardList.vue          # ✅ 可沿用
│   └── ZonePanel.vue              # ✅ 可沿用
└── composables/
    └── useStockData.js            # ✅ 可沿用
```

---

## 2. 整合目標

### 2.1 核心目標

1. **打通資料流**：讓 Celery 任務真正計算技術指標、執行規則引擎、寫入資料庫
2. **建立 ORM 層**：使用 SQLAlchemy 統一管理資料庫操作
3. **統一資料格式**：前後端使用一致的 zone 命名和資料結構
4. **前端顯示真實數據**：取代所有 mock 數據

### 2.2 非目標

- ❌ 不修改前端 UI 設計（保留現有風格）
- ❌ 不新增功能（只整合現有功能）
- ❌ 不修改規則引擎邏輯（只改資料讀取方式）

---

## 3. 開發策略

### 3.1 策略選擇：先建立資料庫 + 模擬資料，讓前端先看到效果 ✅

#### 為什麼選擇這個策略？

| 項目 | 先建立資料庫+模擬資料 ✅ | 全部完成再測試 ❌ |
|------|------------------------|-----------------|
| **看到效果的時間** | 第 1 天 | 第 5 天 |
| **發現問題的時間** | 第 1 天（立即發現） | 第 5 天（最後才知） |
| **修改成本** | 低（剛開始，易調整） | 高（全部寫完，難改） |
| **開發信心** | 高（逐步驗證） | 低（最後才知道對不對） |
| **風險控制** | 佳（及早發現問題） | 差（問題累積到最後） |

#### 迭代開發流程

```
Day 1 (上午): 建立資料庫表格 + ORM Models + database.py
Day 1 (下午): 寫入模擬資料腳本 → 前端串接測試
              → ✅ 此時前端就能看到真實資料庫的數據了！

Day 2-3: 逐步替換 tasks_helper.py 的真實邏輯
         （一個函數一個函數替換，隨時測試）

Day 4: 前端微調 + 補齊欄位

Day 5: 整合測試 + 壓力測試
```

---

## 4. 詳細任務清單

### 階段一：基礎建設 + 模擬資料（預計 1 天）

```
Day 1: 建立 ORM 層 + 更新資料庫 Schema + 寫入模擬資料 + 前端串接測試
```

#### 任務 1.1：更新 `db/init.sql`

**說明**：將現有的 `init.sql` 更新為新的 Schema 設計，增加 `market`、`name`、`change_pct` 欄位。

**修改內容**：
- `stock_bar` 表增加：`name VARCHAR(100)`, `market VARCHAR(4)`, `change_pct NUMERIC(6,2)`
- `stock_fundamental` 表增加：`market VARCHAR(4)`
- `stock_signal_log` 表增加：`market VARCHAR(4)`
- 增加對應的索引和註釋

**參考檔案**：`docs/integration_plan.md` 中的完整 DDL

**驗收標準**：
```bash
# 使用 podman 進入 psql 檢查
podman compose exec db psql -U dev_user -d ambush_dev -c "\dt"

# 檢查 stock_bar 欄位
podman compose exec db psql -U dev_user -d ambush_dev -c "\d stock_bar"
# 應包含: code, name, market, trade_date, close, change_pct, ma10_w, ma30_w, volume_ma5_w
```

---

#### 任務 1.2：建立 ORM Models

**說明**：在 `backend/app/models/` 下建立 SQLAlchemy ORM 模型。

**新增檔案**：

| 檔案 | 對應資料表 | 主要欄位 |
|------|-----------|---------|
| `models/__init__.py` | - | 匯出所有模型 |
| `models/base.py` | - | Base 宣告 |
| `models/stock_bar.py` | `stock_bar` | code, name, market, trade_date, close, ma10_w, ma30_w |
| `models/stock_fundamental.py` | `stock_fundamental` | code, market, pe_ttm, eps_ttm, float_shares |
| `models/stock_signal_log.py` | `stock_signal_log` | code, market, trade_date, zone, confidence, trigger_rules |
| `models/audit_log.py` | `audit_log` | user_id, action_type, compliance_hash |
| `models/user_notification_config.py` | `user_notification_config` | user_id, channel, zone_filter |
| `models/media_heat.py` | `media_heat` | code, record_date, heat_score |
| `models/system_config.py` | `system_config` | config_key, config_value |

**程式碼範例**（`models/stock_bar.py`）：
```python
from sqlalchemy import Column, BigInteger, String, Numeric, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class StockBar(Base):
    __tablename__ = "stock_bar"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    market = Column(String(4), nullable=False, default="TW")
    trade_date = Column(Date, nullable=False)
    close = Column(Numeric(12, 4))
    change_pct = Column(Numeric(6, 2))
    ma10_w = Column(Numeric(12, 4))
    ma30_w = Column(Numeric(12, 4))
    volume_ma5_w = Column(Numeric(12, 4))
    
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uq_bar_code_date"),
        Index("idx_bar_code_date", "code", "trade_date"),
    )
```

---

#### 任務 1.3：建立資料庫連線層

**說明**：新增 `backend/app/database.py`，管理資料庫連線。

**新增檔案**：`backend/app/database.py`

```python
"""
資料庫連線管理
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 從環境變數讀取資料庫連線資訊
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "dev_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "dev_pass_123")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "ambush_dev")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI 依賴注入：獲取資料庫連線"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化資料庫表格（開發環境使用）"""
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)
```

---

### 階段二：後端整合

#### 任務 2.1：改寫 `tasks_helper.py`

**說明**：將模擬函數改為真實的資料庫操作。

**修改檔案**：`backend/app/tasks_helper.py`

**改寫內容**：

```python
"""
任務輔助函數 - 使用 SQLAlchemy ORM 操作資料庫
"""
from app.database import SessionLocal
from app.models.stock_bar import StockBar
from app.models.stock_fundamental import StockFundamental
from app.models.stock_signal_log import StockSignalLog
from app.engine.rule_engine import RuleEngine
from classifier.zone_classifier import ThreeZoneClassifier

def get_stock_list(market: str) -> list:
    """從 stock_bar 獲取指定市場的股票列表"""
    db = SessionLocal()
    try:
        stocks = (
            db.query(StockBar.code)
            .filter(StockBar.market == market)
            .distinct()
            .all()
        )
        return [s.code for s in stocks]
    finally:
        db.close()

def calculate_indicators(symbol: str) -> dict:
    """計算技術指標並更新 stock_bar"""
    db = SessionLocal()
    try:
        # 讀取最近 60 筆週線數據
        bars = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .limit(60)
            .all()
        )
        
        # 計算 MA10, MA30, Volume MA5
        # ... (調用 TA-Lib 或自定義計算)
        
        db.commit()
        return {"symbol": symbol, "status": "success"}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def run_rule_engine(symbol: str) -> dict:
    """執行規則引擎"""
    db = SessionLocal()
    try:
        # 讀取最新行情
        bar = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .first()
        )
        
        # 讀取最新基本面
        fund = (
            db.query(StockFundamental)
            .filter(StockFundamental.code == symbol)
            .order_by(StockFundamental.report_date.desc())
            .first()
        )
        
        # 執行規則引擎
        engine = RuleEngine()
        result = engine.run_from_db(bar, fund)
        
        return result
    finally:
        db.close()

def classify_stock(symbol: str) -> dict:
    """執行三區分類並寫入 stock_signal_log"""
    db = SessionLocal()
    try:
        # 讀取最新行情
        bar = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .first()
        )
        
        # 讀取最新基本面
        fund = (
            db.query(StockFundamental)
            .filter(StockFundamental.code == symbol)
            .order_by(StockFundamental.report_date.desc())
            .first()
        )
        
        # 執行規則引擎
        engine = RuleEngine()
        rule_result = engine.run_from_db(bar, fund)
        
        # 執行三區分類
        classifier = ThreeZoneClassifier()
        result = classifier.classify_stock(rule_result)
        
        # 寫入 stock_signal_log
        signal = StockSignalLog(
            code=symbol,
            market=bar.market,
            trade_date=bar.trade_date,
            zone=result["zone"],        # UPTREND/POTENTIAL/DOWNTREND
            confidence=result["confidence"],
            trigger_rules=rule_result,
            reason=result["explanation"],
            engine_version="V2.2"
        )
        db.add(signal)
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

---

#### 任務 2.2：更新 `rule_engine.py`

**說明**：增加 `run_from_db()` 方法，支援直接從 ORM 物件讀取數據。

**修改檔案**：`backend/engine/rule_engine.py`

**新增方法**：

```python
def run_from_db(self, bar: 'StockBar', fund: 'StockFundamental') -> dict:
    """
    從 ORM 物件執行規則引擎
    
    Args:
        bar: StockBar ORM 物件
        fund: StockFundamental ORM 物件
    
    Returns:
        規則引擎結果（含各層規則狀態）
    """
    row = {
        "code": bar.code,
        "datetime": bar.trade_date.isoformat(),
        "close": float(bar.close),
        "ma10": float(bar.ma10_w),
        "ma30": float(bar.ma30_w),
        "volume": bar.volume,
        "pe": float(fund.pe_ttm) if fund else None,
        "market_cap": fund.float_shares * float(bar.close) if fund else None,
        "debt_ratio": float(fund.debt_ratio) if fund else None,
        "insider_buy": fund.insider_net_buy_3m if fund else 0,
    }
    
    # 執行 5 層規則
    r1 = self.evaluate_rule1(row)
    r2 = self.evaluate_rule2(row)
    r3 = self.evaluate_rule3(row)
    r4 = self.evaluate_rule4(row)
    r5 = self.evaluate_rule5(row)
    
    # 分類
    label = self.classify(r1, r2, r3, r4, r5)
    
    return {
        "code": bar.code,
        "datetime": bar.trade_date.isoformat(),
        "label": label,
        "rule1": r1,
        "rule2": r2,
        "rule3": r3,
        "rule4": r4,
        "rule5": r5,
    }
```

---

#### 任務 2.3：更新 API Router

**說明**：讓 `/api/v1/screener/stocks/batch` 回傳真實資料。

**修改檔案**：`backend/app/routers/screener.py`

**改寫內容**：

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.stock_bar import StockBar
from app.models.stock_signal_log import StockSignalLog

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])

@router.get("/stocks/batch")
def get_stocks_batch(db: Session = Depends(get_db)):
    """獲取所有股票的最新三區分類結果"""
    
    # 獲取最新交易日
    latest_date = (
        db.query(func.max(StockSignalLog.trade_date))
        .scalar()
    )
    
    if not latest_date:
        return []
    
    # JOIN 查詢：stock_bar + stock_signal_log
    results = (
        db.query(
            StockBar.code,
            StockBar.name,
            StockBar.market,
            StockBar.close,
            StockBar.change_pct,
            StockBar.ma10_w,
            StockBar.ma30_w,
            StockSignalLog.zone,
            StockSignalLog.confidence,
            StockSignalLog.trigger_rules,
        )
        .join(
            StockSignalLog,
            (StockBar.code == StockSignalLog.code) &
            (StockBar.trade_date == StockSignalLog.trade_date)
        )
        .filter(StockSignalLog.trade_date == latest_date)
        .order_by(StockSignalLog.confidence.desc())
        .all()
    )
    
    return [
        {
            "symbol": r.code,
            "name": r.name or "",
            "market": r.market,
            "price": float(r.close) if r.close else 0,
            "changePct": float(r.change_pct) if r.change_pct else 0,
            "zone": r.zone,  # UPTREND/POTENTIAL/DOWNTREND
            "ma10": float(r.ma10_w) if r.ma10_w else 0,
            "ma30": float(r.ma30_w) if r.ma30_w else 0,
            "score": float(r.confidence) if r.confidence else 0,
        }
        for r in results
    ]
```

---

### 階段三：前端調整

#### 任務 3.1：調整 Zone 映射

**說明**：更新 `Front.vue` 中的 zone 映射，配合新的資料庫命名。

**修改檔案**：`frontend/src/views/Front.vue`

**修改內容**：

```javascript
// 修改前
const zoneMap = { buy: 'up', hold: 'pot', sell: 'down' }

// 修改後
const zoneMap = { 
    'UPTREND': 'up',      // 交易區
    'POTENTIAL': 'pot',   // 驗證區
    'DOWNTREND': 'down'   // 避雷區
}
const zoneLabelMap = { 
    'UPTREND': '交易區', 
    'POTENTIAL': '驗證區', 
    'DOWNTREND': '避雷區' 
}
```

---

#### 任務 3.2：補齊前端欄位

**說明**：確保 `fetchStocks()` 中所有欄位都有真實數據。

**修改檔案**：`frontend/src/views/Front.vue`

**修改內容**：

```javascript
// 修改前 - 部分欄位是 mock
stocks.value = data.map(stock => {
    return {
        ...stock,
        zone: zoneMap[zoneKey] || zoneKey,
        zoneLabel: zoneLabelMap[zoneKey] || '未知',
        volChange: 0,           // mock
        eps: '0%',              // mock
        mktCap: '0億',          // mock
        insider: '無異動',      // mock
        topic: '未定義',        // mock
        lastUpdate: '05/19',    // mock
        signals: [],            // mock
        rules: [],              // mock
        suggestion: '請查看詳細資訊'  // mock
    }
})

// 修改後 - 從 API 獲取真實數據
stocks.value = data.map(stock => {
    const zoneKey = (stock.zone || '').toUpperCase()
    return {
        symbol: stock.symbol,
        name: stock.name,
        price: stock.price,
        changePct: stock.changePct,
        zone: zoneMap[zoneKey] || 'pot',
        zoneLabel: zoneLabelMap[zoneKey] || '驗證區',
        ma10: stock.ma10,
        ma30: stock.ma30,
        score: stock.score,
        // 從 trigger_rules 解析信號
        signals: parseSignals(stock.triggerRules),
        // 從 trigger_rules 解析規則
        rules: parseRules(stock.triggerRules),
        // 後續可從其他 API 補齊
        volChange: stock.volChange || 0,
        eps: stock.eps || '0%',
        mktCap: stock.mktCap || '0億',
        insider: stock.insider || '無異動',
        topic: stock.topic || '未定義',
        lastUpdate: stock.lastUpdate || '',
        suggestion: stock.suggestion || '請查看詳細資訊'
    }
})
```

---

### 階段四：測試與驗收

#### 任務 4.1：整合測試

**測試項目**：

| 測試項目 | 預期結果 | 測試方式 |
|---------|---------|---------|
| 資料庫初始化 | 7 張表建立成功 | `podman compose exec db psql -U dev_user -d ambush_dev -c "\dt"` |
| ORM 連線 | 可正常讀寫 | `podman compose exec backend python -c "from app.database import engine; engine.connect(); print('OK')"` |
| Celery 任務 | 分析完成並寫入資料庫 | `podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT COUNT(*) FROM stock_signal_log;"` |
| API 回傳 | 回傳真實數據 | `curl http://localhost:8000/api/v1/screener/stocks/batch` |
| 前端顯示 | 顯示真實數據 | 瀏覽器檢查 `http://localhost:3000` |

#### 任務 4.2：壓力測試

```bash
# 模擬 100 隻股票的並行分析
python scripts/stress_test.py --stocks 100 --parallel 10
```

#### 任務 4.3：文件更新

- 更新 `README.md` 加入新的資料庫結構說明
- 更新 API 文檔

---

## 5. 檔案修改對照表

### 5.1 新增檔案

| 檔案路徑 | 說明 | 預計行數 |
|---------|------|---------|
| `backend/app/database.py` | 資料庫連線管理 | 30 行 |
| `backend/app/models/__init__.py` | 模型匯出 | 10 行 |
| `backend/app/models/base.py` | Base 宣告 | 5 行 |
| `backend/app/models/stock_bar.py` | StockBar ORM | 40 行 |
| `backend/app/models/stock_fundamental.py` | StockFundamental ORM | 35 行 |
| `backend/app/models/stock_signal_log.py` | StockSignalLog ORM | 40 行 |
| `backend/app/models/audit_log.py` | AuditLog ORM | 45 行 |
| `backend/app/models/user_notification_config.py` | UserNotificationConfig ORM | 40 行 |
| `backend/app/models/media_heat.py` | MediaHeat ORM | 35 行 |
| `backend/app/models/system_config.py` | SystemConfig ORM | 25 行 |

### 5.2 修改檔案

| 檔案路徑 | 修改內容 | 預計變更行數 |
|---------|---------|-------------|
| `db/init.sql` | 增加 market/name/change_pct 欄位 | +20 行 |
| `backend/app/tasks_helper.py` | 全部改寫為 ORM 操作 | 全部重寫 (~180 行) |
| `backend/engine/rule_engine.py` | 增加 run_from_db() 方法 | +40 行 |
| `backend/app/routers/screener.py` | 改為 ORM 查詢 | +30 行 |
| `frontend/src/views/Front.vue` | 調整 zone 映射 + 補齊欄位 | +15 行 |

### 5.3 不修改檔案

| 檔案路徑 | 原因 |
|---------|------|
| `backend/app/main.py` | 不需要修改，路由已註冊 |
| `backend/app/celery_app.py` | 不需要修改，任務配置正確 |
| `backend/app/service_task.py` | 不需要修改，調用 tasks_helper 的函數 |
| `classifier/zone_classifier.py` | 邏輯正確，只需確保輸出格式一致 |
| `frontend/src/components/*.vue` | 組件設計良好，不需要修改 |
| `docker-compose.yml` | 不需要修改，服務配置正確 |

---

## 6. 風險與對策

### 6.1 風險矩陣

| 風險 | 機率 | 影響 | 對策 |
|------|------|------|------|
| 資料庫連線失敗 | 低 | 高 | 增加重試機制 + 健康檢查 |
| ORM 與 Schema 不一致 | 中 | 高 | 使用 Alembic 管理遷移 |
| 規則引擎相容性問題 | 低 | 中 | 保留舊的 run() 方法作為備用 |
| 前端顯示異常 | 低 | 中 | 增加錯誤處理 + fallback 顯示 |
| Celery 任務超時 | 中 | 低 | 增加任務超時設定 + 並行處理 |

### 6.2 回滾計畫

如果整合過程中出現問題，可以：

1. **保留舊的 `tasks_helper.py`**：改名為 `tasks_helper_old.py` 作為備份
2. **保留舊的 `db/init.sql`**：改名為 `db/init_old.sql`
3. **資料庫回滾**：使用 `DROP TABLE IF EXISTS` 重新執行舊的 init.sql

---

## 7. 驗收標準

### 7.1 功能驗收

- [ ] `db/init.sql` 執行後成功建立 7 張分區表
- [ ] ORM 模型可正常連線並讀寫資料庫
- [ ] Celery 任務執行後，`stock_signal_log` 有數據
- [ ] API `/api/v1/screener/stocks/batch` 回傳真實數據
- [ ] 前端顯示真實數據，無 mock 數據

### 7.2 效能驗收

- [ ] API 回應時間 < 500ms（100 隻股票）
- [ ] Celery 任務執行時間 < 30 分鐘（100 隻股票）
- [ ] 資料庫查詢使用索引，無全表掃描

### 7.3 程式碼驗收

- [ ] 所有新增檔案符合 PEP 8 規範
- [ ] 所有函數有 docstring
- [ ] 所有 SQL 有對應的 ORM 方法
- [ ] 前端無 console error

---

## 附錄 A：Zone 命名對照表

| 系統層 | 原始命名 | 統一命名 |
|--------|---------|---------|
| 規則引擎輸出 | `上升交易（买点）` | `UPTREND` |
| 規則引擎輸出 | `潜在实力股（观察）` | `POTENTIAL` |
| 規則引擎輸出 | `下跌参考（警示）` | `DOWNTREND` |
| 三區分類器 | `buy` | `UPTREND` |
| 三區分類器 | `hold` | `POTENTIAL` |
| 三區分類器 | `sell` | `DOWNTREND` |
| 資料庫 `stock_signal_log` | - | `UPTREND / POTENTIAL / DOWNTREND` |
| 前端顯示 | `up / pot / down` | `up / pot / down`（顯示用） |
| 前端標籤 | `交易區 / 驗證區 / 避雷區` | 不變 |

## 附錄 B：API 回應格式

```json
// GET /api/v1/screener/stocks/batch
[
    {
        "symbol": "2330.TW",
        "name": "台積電",
        "market": "TW",
        "price": 585.0,
        "changePct": 1.2,
        "zone": "UPTREND",
        "ma10": 575.0,
        "ma30": 560.0,
        "score": 0.85
    }
]
```

## 附錄 C：Podman 開發環境啟動流程

> **注意**：以下指令使用 `dev_user` / `ambush_dev`（與 `docker-compose.yml` 一致）。

```bash
# 1. 停止現有容器
podman compose down

# 2. 更新 db/init.sql
# （將新的 init.sql 複製到 db/ 目錄）

# 3. 重新建立並啟動容器
podman compose up -d

# 4. 檢查資料庫初始化
podman compose exec db psql -U dev_user -d ambush_dev -c "\dt"

# 5. 檢查 ORM 連線
podman compose exec backend python -c "
from app.database import engine
engine.connect()
print('Database connection OK')
"

# 6. 手動觸發 Celery 任務測試
podman compose exec backend celery -A app.celery_app call app.service_task.run_weekly_analysis --kwargs='{\"market\":\"TW\"}'

# 7. 檢查結果
podman compose exec db psql -U dev_user -d ambush_dev -c "
SELECT zone, COUNT(*) FROM stock_signal_log 
WHERE trade_date = (SELECT MAX(trade_date) FROM stock_signal_log)
GROUP BY zone;
"

# 8. 測試 API
curl http://localhost:8000/api/v1/screener/stocks/batch

# 9. 開啟前端
start http://localhost:3000
```

## 附錄 D：monitored_stocks 管理指令

若已實作 `monitored_stocks` 功能，可使用以下指令管理：

```bash
# 查看監控股票清單
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT * FROM monitored_stocks;"

# 查看活躍監控股票數量
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT COUNT(*) as active_monitored FROM monitored_stocks WHERE is_active = true;"

# 執行 migration（新增 monitored_stocks 表）
podman compose exec -T db psql -U dev_user -d ambush_dev < db/migrations/001_add_monitored_stocks.sql

# 驗證表已建立
podman compose exec db psql -U dev_user -d ambush_dev -c "\dt monitored_stocks"
```

---

> **文件狀態**：待審批  
> **審批人**：_______________  
> **審批日期**：_______________  
> **備註**：_______________