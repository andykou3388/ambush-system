# 新增「股票監控清單」功能 — 執行文件（完整版）

> **版本**：V1.0｜**最後更新**：2026-07-09  
> **負責人**：後端 / 前端  
> **狀態**：待實施

---

## 目錄

1. [現狀分析](#1-現狀分析)
2. [執行階段總覽](#2-執行階段總覽)
3. [階段一：資料庫與模型（Day 1）](#3-階段一資料庫與模型day-1)
4. [階段二：後端工具與 API（Day 2）](#4-階段二後端工具與-apiday-2)
5. [階段三：任務整合（Day 3）](#5-階段三任務整合day-3)
6. [階段四：前端調整（Day 4）](#6-階段四前端調整day-4)
7. [階段五：測試驗收（Day 5）](#7-階段五測試驗收day-5)
8. [檔案異動一覽](#8-檔案異動一覽)
9. [附錄：API 測試指令](#9-附錄api-測試指令)

---

## 1. 現狀分析

### 1.1 問題描述

系統中存在多處「硬編碼股票代碼」，無法動態管理監控標的：

| 位置 | 內容 | 狀態 |
|------|------|------|
| `celery_app.py:37` | `args: ["2330.TW", "2317.TW", "2454.TW"]` | 需改為從 DB 讀取 |
| `oneclick_init_task.py:31-48` | 100+ 檔港股硬編碼 | 需改為從 DB 讀取 + fallback |
| `stock_fundamental_tasks.py:166` | `_fetch_stock_fundamentals_impl()` | ✅ 已存在，可直接調用 |
| `weekly_tasks.py:32` | `_fetch_weekly_bars_impl` | 由呼叫者傳入硬編碼，需改 |
| `weekly_tasks.py:192` | `_run_weekly_rule_engine_impl` | ✅ 本身就是動態 |
| `minute_data_tasks.py:82` | 從 `ram_stop_loss` 查 | ✅ 專用資料來源 |

### 1.2 現有可用資源（已檢查）

| 資源 | 路徑 | 狀態 |
|------|------|------|
| `database.py` | `backend/app/database.py` | ✅ 已存在，可用 |
| `base.py` | `backend/app/models/base.py` | ✅ 已存在，可用 |
| `_fetch_stock_fundamentals_impl` | `backend/app/tasks/stock_fundamental_tasks.py:166` | ✅ 已存在，可直接調用 |
| `models/__init__.py` | `backend/app/models/__init__.py` | ✅ 需新增 MonitoredStock 匯出 |
| `monitored_stocks` 資料表 | 資料庫 | ❌ 尚未建立 |
| `utils/` 目錄 | `backend/app/utils/` | ❌ 整個目錄不存在 |
| 前端監控 UI | `frontend/src/views/StockPool.vue` | ❌ 尚未實作 |

---

## 2. 執行階段總覽

```
階段一 (Day 1): 資料庫 Migration + ORM Model
階段二 (Day 2): 後端工具模組 + API Router
階段三 (Day 3): 任務檔案整合（Celery 排程 + oneclick_init）
階段四 (Day 4): 前端 UI 更新
階段五 (Day 5): 測試驗收
```

---

## 3. 階段一：資料庫與模型（Day 1）

### 3.1 步驟 1：建立 `db/migrations/001_add_monitored_stocks.sql`

**檔案路徑**：`db/migrations/001_add_monitored_stocks.sql`

**動作**：🆕 新增檔案

```sql
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
COMMENT ON COLUMN monitored_stocks.market IS '市場：TW=台股, US=美股, HK=港股';
COMMENT ON COLUMN monitored_stocks.added_at IS '加入時間';
COMMENT ON COLUMN monitored_stocks.is_active IS '是否啟用（軟刪除）';
```

**執行方式**：
```bash
podman compose exec -T db psql -U dev_user -d ambush_dev < db/migrations/001_add_monitored_stocks.sql
```

---

### 3.2 步驟 2：更新 `db/init.sql` — 末尾追加 monitored_stocks 表

**檔案路徑**：`db/init.sql`

**動作**：✏️ 修改（在最後一行 `INSERT` 之後追加）

**新增內容**（緊接在第 335 行之後）：

```sql
-- ==========================================
-- 11. 監控股票清單表（動態管理抓取標的）
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
COMMENT ON COLUMN monitored_stocks.market IS '市場：TW=台股, US=美股, HK=港股';
COMMENT ON COLUMN monitored_stocks.added_at IS '加入時間';
COMMENT ON COLUMN monitored_stocks.is_active IS '是否啟用（軟刪除）';
```

---

### 3.3 步驟 3：建立 MonitoredStock ORM Model

**檔案路徑**：`backend/app/models/monitored_stock.py`

**動作**：🆕 新增檔案

```python
"""
MonitoredStock ORM Model - 基本面監控股票清單
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.models.base import Base


class MonitoredStock(Base):
    __tablename__ = "monitored_stocks"

    code = Column(String(20), primary_key=True)
    market = Column(String(4), nullable=False, default="TW")
    added_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<MonitoredStock(code={self.code}, market={self.market})>"
```

---

### 3.4 步驟 4：更新 `models/__init__.py` — 加入 MonitoredStock 匯出

**檔案路徑**：`backend/app/models/__init__.py`

**動作**：✏️ 修改（2 處）

**修改 1**：在第 10-14 行區域新增 import

```python
from app.models.monitored_stock import MonitoredStock
```

**完整 import 區塊變成**：

```python
from app.models.base import Base
from app.models.stock_bar import StockBar
from app.models.stock_fundamental import StockFundamental
from app.models.stock_signal_log import StockSignalLog
from app.models.audit_log import AuditLog
from app.models.user_notification_config import UserNotificationConfig
from app.models.media_heat import MediaHeat
from app.models.system_config import SystemConfig
from app.models.stock_fundamental_latest import StockFundamentalLatest
from app.models.stock_bar_minute import StockBarMinute
from app.models.ram_stop_loss import RamStopLoss
from app.models.monitored_stock import MonitoredStock  # ← 新增這行
```

**修改 2**：在 `__all__` 列表（第 16-28 行）中新增

```python
__all__ = [
    "Base",
    "StockBar",
    "StockFundamental",
    "StockFundamentalLatest",
    "StockBarMinute",
    "RamStopLoss",
    "StockSignalLog",
    "AuditLog",
    "UserNotificationConfig",
    "MediaHeat",
    "SystemConfig",
    "MonitoredStock",  # ← 新增這行
]
```

---

## 4. 階段二：後端工具與 API（Day 2）

### 4.1 步驟 5：建立 `utils/__init__.py`

**檔案路徑**：`backend/app/utils/__init__.py`

**動作**：🆕 新增檔案

```python
"""
共用工具函式目錄
"""
```

---

### 4.2 步驟 6：建立 `stock_utils.py`

**檔案路徑**：`backend/app/utils/stock_utils.py`

**動作**：🆕 新增檔案（約 50 行）

```python
"""
股票相關共用工具函式
提供 get_tracked_stock_codes() 供多個 task 模組共用
"""
import logging

logger = logging.getLogger(__name__)

# 種子清單：資料庫無資料時使用此預設清單進行 bootstrap
DEFAULT_SEED_CODES = [
    # 台股
    "2330.TW", "2317.TW", "2454.TW", "2308.TW",
    "1301.TW", "2881.TW", "2882.TW", "1101.TW",
    # 美股
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    # 港股
    "0700.HK", "9988.HK", "3690.HK", "9618.HK",
]


def get_tracked_stock_codes() -> list:
    """
    從 monitored_stocks 表讀取需要定期抓取基本面的股票清單。
    若資料庫無資料，則回傳預設種子清單以便系統 bootstrap。

    Returns:
        list: 股票代碼列表，例如 ['2330.TW', '0700.HK', 'AAPL']
    """
    try:
        from app.database import SessionLocal
        from app.models.monitored_stock import MonitoredStock

        db = SessionLocal()
        try:
            rows = (
                db.query(MonitoredStock.code)
                .filter(MonitoredStock.is_active == True)
                .all()
            )
            codes = [row.code for row in rows if row.code]

            if not codes:
                logger.info("monitored_stocks 表無資料，使用預設種子清單")
                codes = DEFAULT_SEED_CODES.copy()

            logger.info(f"取得 {len(codes)} 隻待監控股票")
            return codes

        finally:
            db.close()

    except Exception as e:
        logger.error(f"讀取股票清單失敗: {e}，使用預設清單")
        return DEFAULT_SEED_CODES.copy()
```

---

### 4.3 步驟 7：建立 `monitored_stocks_api.py`

**檔案路徑**：`backend/app/routers/monitored_stocks_api.py`

**動作**：🆕 新增檔案（約 88 行）

```python
"""
監控股票清單 API
提供新增、查詢、刪除監控股票的功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.database import SessionLocal
from app.models.monitored_stock import MonitoredStock
from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
from sqlalchemy.dialects.postgresql import insert

router = APIRouter(prefix="/api/v1/monitored-stocks", tags=["monitored-stocks"])


class AddStockRequest(BaseModel):
    code: str
    market: str = Field(default="TW", pattern=r"^(TW|US|HK)$")
    fetch: bool = True


class RemoveStockRequest(BaseModel):
    code: str


@router.get("/")
def list_monitored_stocks():
    """列出所有監控中的股票"""
    db = SessionLocal()
    try:
        rows = db.query(MonitoredStock).filter(
            MonitoredStock.is_active == True
        ).order_by(MonitoredStock.added_at).all()
        return [
            {
                "code": r.code,
                "market": r.market,
                "added_at": r.added_at.isoformat() if r.added_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


@router.post("/")
def add_monitored_stock(req: AddStockRequest):
    """
    將股票加入監控清單。
    若 fetch=True（預設），會先從 YFinance 抓取基本面資料，成功後才寫入資料庫。
    """
    fetch_result = None
    if req.fetch:
        try:
            fetch_result = _fetch_stock_fundamentals_impl([req.code])
            if fetch_result.get("failed", 0) > 0:
                raise HTTPException(
                    status_code=422,
                    detail=f"無法從 YFinance 取得 {req.code} 的資料，請確認股票代碼是否正確"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"抓取基本面資料失敗: {str(e)}"
            )

    db = SessionLocal()
    try:
        stmt = insert(MonitoredStock).values(
            code=req.code,
            market=req.market,
        )
        stmt = stmt.on_conflict_do_nothing()
        db.execute(stmt)
        db.commit()
        return {
            "status": "ok",
            "code": req.code,
            "market": req.market,
            "fetch_result": fetch_result,
        }
    finally:
        db.close()


@router.post("/remove")
def remove_monitored_stock(req: RemoveStockRequest):
    """從監控清單移除股票（軟刪除：設為 inactive）"""
    db = SessionLocal()
    try:
        row = db.query(MonitoredStock).filter(MonitoredStock.code == req.code).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"股票 {req.code} 不在監控清單中")
        row.is_active = False
        db.commit()
        return {"status": "ok", "code": req.code, "action": "removed"}
    finally:
        db.close()
```

---

### 4.4 步驟 8：註冊路由到 `main.py`

**檔案路徑**：`backend/app/main.py`

**動作**：✏️ 修改（2 處）

**修改 1**：在第 8 行（`from app.routers.ram_stop_loss_api import router as ram_stop_loss_router`）之後新增：

```python
from app.routers.monitored_stocks_api import router as monitored_stocks_router
```

**修改 2**：在最後一行 `app.include_router(ram_stop_loss_router)` 之後新增：

```python
app.include_router(monitored_stocks_router)
```

**完整 main.py 修改後樣貌**：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import health
from app.routers.screener import router as screener_router
from app.routers.stock_detail import router as stock_detail_router
from app.routers.stock_fundamental_api import router as stock_fundamental_router
from app.routers.ram_stop_loss_api import router as ram_stop_loss_router
from app.routers.monitored_stocks_api import router as monitored_stocks_router  # ← 新增
from app.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時檢查資料庫連線
    if check_db_connection():
        print("✅ 資料庫連線正常")
    else:
        print("⚠️ 資料庫連線失敗，請確認容器已啟動")
    yield
    # 關閉時清理（如有需要）


app = FastAPI(
    title="Ambush System API",
    description="伏擊系統後端 API - V2.0 含拉姆止損",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(health.router)
app.include_router(screener_router)
app.include_router(stock_detail_router)
app.include_router(stock_fundamental_router)
app.include_router(ram_stop_loss_router)
app.include_router(monitored_stocks_router)  # ← 新增
```

---

## 5. 階段三：任務整合（Day 3）

### 5.1 步驟 9：修改 `stock_fundamental_tasks.py` — 新增 Celery 任務

**檔案路徑**：`backend/app/tasks/stock_fundamental_tasks.py`

**動作**：✏️ 在檔案末尾（第 408 行後）追加 Celery 任務

**新增內容**：

```python
# ==========================================
# Celery 任務：批量獲取股票基本面數據
# 支援兩種調用方式：
#   1. 有參數：使用傳入的 stock_codes（向後相容）
#   2. 無參數：自動從 monitored_stocks 表讀取待監控股票清單
# ==========================================

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_stock_fundamentals(self, stock_codes: list = None):
    """
    批量獲取股票基本面數據的通用任務（支援自動從 monitored_stocks 讀取）
    """
    try:
        if not stock_codes:
            from app.utils.stock_utils import get_tracked_stock_codes
            stock_codes = get_tracked_stock_codes()
            logger.info(f"自動從 monitored_stocks 讀取股票清單，共 {len(stock_codes)} 隻")

        if not stock_codes:
            logger.warning("股票清單為空，跳過本次基本面抓取")
            return {"status": "skipped", "reason": "股票清單為空"}

        return _fetch_stock_fundamentals_impl(stock_codes)
    except Exception as exc:
        logger.error(f"獲取股票數據失敗: {exc}")
        raise self.retry(exc=exc)
```

---

### 5.2 步驟 10：修改 `celery_app.py` — 移除硬編碼 args

**檔案路徑**：`backend/app/celery_app.py`

**動作**：✏️ 修改（第 34-39 行）

**修改前**：

```python
    "fetch-daily-fundamentals": {
        "task": "app.tasks.stock_fundamental_tasks.fetch_stock_fundamentals",
        "schedule": crontab(hour="14", minute="0", day_of_week="1-5"),
        "args": [["2330.TW", "2317.TW", "2454.TW"]],  # 實際使用時從 DB 讀取
        "options": {"queue": "fundamental"},
    },
```

**修改後**：

```python
    "fetch-daily-fundamentals": {
        "task": "app.tasks.stock_fundamental_tasks.fetch_stock_fundamentals",
        "schedule": crontab(hour="14", minute="0", day_of_week="1-5"),
        "options": {"queue": "fundamental"},
    },
```

---

### 5.3 步驟 11：修改 `oneclick_init_task.py` — 改用 `get_tracked_stock_codes()`

**檔案路徑**：`backend/app/tasks/oneclick_init_task.py`

**動作**：✏️ 修改（第 28-48 行）

**修改前**（第 28-51 行原本包含 100+ 行硬編碼）：

```python
        # 1. 獲取股票代碼列表（這裡使用硬編碼的示例，實際應用中可能需要從資料庫獲取）
        # 精選港股列表（包含更多有價值的股票）
        stock_codes = [
                        "0700.HK", "9988.HK", 
                        "3690.HK", "1024.HK", "9618.HK", "9888.HK", "1810.HK", "2518.HK", "2018.HK", "0268.HK",
                        ... 省略 90+ 行 ...
                        "3338.HK", "3438.HK", "3538.HK", "3638.HK", "3738.HK", "3838.HK", "4038.HK", "4138.HK", "0001.HK"
                    ]
```

**修改後**（約 4 行）：

```python
        # 1. 從 monitored_stocks 表讀取股票代碼列表（無資料則用預設種子清單）
        from app.utils.stock_utils import get_tracked_stock_codes
        stock_codes = get_tracked_stock_codes()
        logger.info(f"取得 {len(stock_codes)} 隻股票代碼")
```

---

## 6. 階段四：前端調整（Day 4）

### 6.1 步驟 12：更新 `StockPool.vue`

**檔案路徑**：`frontend/src/views/StockPool.vue`

**動作**：✏️ 修改（3 處）

#### 修改 1：在 `<script setup>` 中新增變數和函數

在第 430 行（當前的 `watchlist` 相關變數區域）之後，插入以下內容：

```javascript
// ==================== 新增：監控股票清單操作 ====================
const newStockCode = ref('')
const newStockMarket = ref('TW')
const isFetchingStock = ref(false)
const monitoredStocks = ref([])
const showMonitoredPanel = ref(false)

// 取得已監控股票列表
async function fetchMonitoredStocks() {
  try {
    const response = await fetch('/api/v1/monitored-stocks/')
    if (response.ok) {
      monitoredStocks.value = await response.json()
    }
  } catch (error) {
    console.error('取得監控清單失敗:', error)
  }
}

async function addAndFetchStock() {
  if (!newStockCode.value.trim()) {
    showToast('請輸入股票代碼', 'error', '❌')
    return
  }

  isFetchingStock.value = true
  
  // 支援批次輸入：逗號、空格、換行分隔
  const codes = newStockCode.value
    .split(/[,，\n\s]+/)
    .map(c => c.trim().toUpperCase())
    .filter(Boolean)

  let successCount = 0
  let failCount = 0

  for (const code of codes) {
    try {
      const response = await fetch('/api/v1/monitored-stocks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code,
          market: newStockMarket.value,
          fetch: true,
        }),
      })

      if (response.ok) {
        successCount++
      } else {
        const errData = await response.json().catch(() => ({}))
        console.error(`${code} 加入失敗:`, errData.detail)
        failCount++
      }
    } catch (error) {
      console.error(`${code} 加入失敗:`, error)
      failCount++
    }
  }

  if (successCount > 0) {
    showToast(`✅ ${successCount} 檔股票已加入監控並取得基本面資料`, 'success', '✅')
    newStockCode.value = ''
    await fetchStocks()
    await fetchMonitoredStocks()
  }
  if (failCount > 0) {
    showToast(`❌ ${failCount} 檔股票加入失敗，請確認代碼是否正確`, 'error', '❌')
  }

  isFetchingStock.value = false
}

async function removeMonitoredStock(code) {
  try {
    const response = await fetch('/api/v1/monitored-stocks/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    })
    if (response.ok) {
      showToast(`已移除 ${code} 的監控`, 'info', 'ℹ️')
      await fetchMonitoredStocks()
    }
  } catch (error) {
    showToast(`移除 ${code} 失敗`, 'error', '❌')
  }
}
```

#### 修改 2：在 `onMounted` 中加入 `fetchMonitoredStocks()`

找到 `onMounted` 區塊（第 459 行附近），加入：

```javascript
onMounted(() => {
  fetchStocks()
  loadTrackedSymbols()
  fetchMonitoredStocks()  // ← 新增這行
  const saved = localStorage.getItem('my_watchlist_v2')
  if (saved) {
    try { watchlist.value = JSON.parse(saved) } catch(e) {}
  }
})
```

#### 修改 3：在 `<template>` 中新增監控管理區塊

在第 41 行（頂部標題列結束 `</div>`）和第 44 行（篩選控制列開始）之間插入以下 HTML：

```html
<!-- ==================== 新增：監控股票管理區塊 ==================== -->
<div
  class="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-4"
  :class="{ 'ring-2 ring-amber-500/50': stocks.length === 0 }"
>
  <div v-if="stocks.length === 0" class="mb-3">
    <h3 class="text-sm font-bold text-amber-400 mb-1 flex items-center gap-2">
      <span>📡</span> 首次使用？請加入要監控的股票
    </h3>
    <p class="text-xs text-slate-500">加入後系統會自動從 YFinance 抓取基本面資料，並每天更新。</p>
  </div>

  <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
    <h3 class="text-sm font-bold text-amber-400 flex items-center gap-2">
      <span>📡</span>
      {{ stocks.length === 0 ? '加入第一檔監控股票' : '手動新增監控股票' }}
    </h3>
    <button
      @click="showMonitoredPanel = !showMonitoredPanel"
      class="text-xs text-slate-400 hover:text-amber-400 transition flex items-center gap-1"
    >
      <span>📋</span>
      已監控 {{ monitoredStocks.length }} 檔
      <span class="text-xs">{{ showMonitoredPanel ? '▲' : '▼' }}</span>
    </button>
  </div>

  <div class="flex flex-wrap items-end gap-3">
    <div>
      <label class="text-xs text-slate-400 mb-1 block">股票代碼</label>
      <input
        v-model="newStockCode"
        placeholder="例: 2330.TW, AAPL, 0700.HK（支援批次）"
        class="bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400 w-64"
      />
    </div>
    <div>
      <label class="text-xs text-slate-400 mb-1 block">市場</label>
      <select
        v-model="newStockMarket"
        class="bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm"
      >
        <option value="TW">🇹🇼 台股</option>
        <option value="US">🇺🇸 美股</option>
        <option value="HK">🇭🇰 港股</option>
      </select>
    </div>
    <button
      @click="addAndFetchStock"
      :disabled="isFetchingStock || !newStockCode.trim()"
      class="bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 px-4 py-2 rounded-lg font-bold text-sm transition flex items-center gap-2"
    >
      <span>{{ isFetchingStock ? '抓取中...' : '＋ 加入並立即抓取基本面' }}</span>
    </button>
  </div>

  <div
    v-if="showMonitoredPanel && monitoredStocks.length > 0"
    class="mt-3 pt-3 border-t border-amber-700/30"
  >
    <div class="flex flex-wrap gap-2">
      <div
        v-for="ms in monitoredStocks"
        :key="ms.code"
        class="flex items-center gap-1 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs"
      >
        <span class="font-mono text-slate-200">{{ ms.code }}</span>
        <span class="text-slate-500">{{ ms.market }}</span>
        <button
          @click="removeMonitoredStock(ms.code)"
          class="text-red-400 hover:text-red-300 ml-1"
          title="移除監控"
        >✕</button>
      </div>
    </div>
  </div>

  <p class="text-xs text-slate-500 mt-2">
    新股票將加入監控清單，Celery 排程會自動持續更新其基本面資料
  </p>
</div>
```

---

## 7. 階段五：測試驗收（Day 5）

### 7.1 步驟 13：驗證資料庫初始化

```bash
# 確認 monitored_stocks 表已建立
podman compose exec db psql -U dev_user -d ambush_dev -c "\dt monitored_stocks"

# 確認欄位結構
podman compose exec db psql -U dev_user -d ambush_dev -c "\d monitored_stocks"
```

**預期結果**：

```
                  List of relations
 Schema |       Name       | Type  |  Owner
--------+------------------+-------+---------
 public | monitored_stocks | table | dev_user

         Table "public.monitored_stocks"
  Column   |            Type             | Default
-----------+-----------------------------+----------
 code      | character varying(20)       | not null
 market    | character varying(4)        | 'TW'::character varying
 added_at  | timestamp without time zone | NOW()
 is_active | boolean                     | true
Indexes:
    "monitored_stocks_pkey" PRIMARY KEY, btree (code)
    "idx_monitored_stocks_active" btree (is_active) WHERE is_active = TRUE
```

---

### 7.2 步驟 14：驗證 API 端點

```bash
# 1. 測試 GET 列出所有監控股票（預期空陣列）
curl -s http://localhost:8000/api/v1/monitored-stocks/ | python -m json.tool

# 2. 測試 POST 新增股票（加入 2330.TW）
curl -s -X POST http://localhost:8000/api/v1/monitored-stocks/ \
  -H "Content-Type: application/json" \
  -d '{"code": "2330.TW", "market": "TW", "fetch": true}' | python -m json.tool
# 預期結果：{"status": "ok", "code": "2330.TW", "market": "TW", "fetch_result": {...}}

# 3. 測試 POST 新增多檔股票（批次加入）
curl -s -X POST http://localhost:8000/api/v1/monitored-stocks/ \
  -H "Content-Type: application/json" \
  -d '{"code": "AAPL", "market": "US", "fetch": true}' | python -m json.tool

curl -s -X POST http://localhost:8000/api/v1/monitored-stocks/ \
  -H "Content-Type: application/json" \
  -d '{"code": "0700.HK", "market": "HK", "fetch": true}' | python -m json.tool

# 4. 測試 GET 列出所有監控股票（應包含剛才加入的股票）
curl -s http://localhost:8000/api/v1/monitored-stocks/ | python -m json.tool

# 5. 測試 POST 移除股票
curl -s -X POST http://localhost:8000/api/v1/monitored-stocks/remove \
  -H "Content-Type: application/json" \
  -d '{"code": "2330.TW"}' | python -m json.tool

# 6. 測試無效股票代碼（預期回傳 422）
curl -s -X POST http://localhost:8000/api/v1/monitored-stocks/ \
  -H "Content-Type: application/json" \
  -d '{"code": "INVALID123", "market": "TW", "fetch": true}' | python -m json.tool
```

---

### 7.3 步驟 15：驗證 Celery 排程

```bash
# 1. 確認 celery_app.py 中已移除 args
grep -n "args" backend/app/celery_app.py
# 輸出不應包含 fetch-daily-fundamentals 的 args

# 2. 檢查 ORM 連線
podman compose exec backend python -c "
from app.database import engine
engine.connect()
print('Database connection OK')
"

# 3. 驗證 get_tracked_stock_codes 可正常工作
podman compose exec backend python -c "
from app.utils.stock_utils import get_tracked_stock_codes
codes = get_tracked_stock_codes()
print(f'取得 {len(codes)} 隻股票: {codes}')
"
```

---

### 7.4 步驟 16：前端驗證

1. 開啟瀏覽器前往 `http://localhost:3000` 或 `http://localhost:5173`
2. 導航至 StockPool 頁面
3. 確認頂部出現監控股票管理區塊
4. 測試輸入 `2330.TW, AAPL, 0700.HK` 並點擊「加入並立即抓取」
5. 確認 Toast 提示成功加入
6. 點擊「📋 已監控 X 檔」展開面板
7. 確認面板顯示已加入的股票
8. 點擊 ✕ 移除股票
9. 確認 Toast 提示移除成功

---

## 8. 檔案異動一覽

### 8.1 新增檔案（6 個）

| 檔案路徑 | 說明 | 行數 |
|---------|------|------|
| `db/migrations/001_add_monitored_stocks.sql` | 資料庫 migration 腳本 | 18 行 |
| `backend/app/models/monitored_stock.py` | MonitoredStock ORM Model | 16 行 |
| `backend/app/utils/__init__.py` | utils 目錄初始化 | 2 行 |
| `backend/app/utils/stock_utils.py` | 共用工具函式 | 50 行 |
| `backend/app/routers/monitored_stocks_api.py` | 監控股票 API | 88 行 |

### 8.2 修改檔案（8 處）

| 檔案路徑 | 修改位置 | 說明 |
|---------|---------|------|
| `db/init.sql` | 第 335 行後追加 | 加入 monitored_stocks 表 DDL |
| `backend/app/models/__init__.py` | 第 14 行 + 第 28 行 | 加入 MonitoredStock 匯出 |
| `backend/app/main.py` | 第 9 行 + 第 47 行 | 註冊新路由 |
| `backend/app/tasks/stock_fundamental_tasks.py` | 第 408 行後追加 | 新增 Celery 任務 |
| `backend/app/celery_app.py` | 第 37 行 | 移除硬編碼 args |
| `backend/app/tasks/oneclick_init_task.py` | 第 28-48 行 | 改用 get_tracked_stock_codes() |
| `frontend/src/views/StockPool.vue` | 3 處 | 新增監控管理 UI |

---

## 9. 附錄：API 測試指令

### 9.1 快速測試腳本

將以下內容儲存為 `scripts/test_monitored_stocks.sh`：

```bash
#!/bin/bash
# 快速測試 monitored_stocks API

BASE_URL="http://localhost:8000/api/v1/monitored-stocks"

echo "=== 1. 列出監控清單（預期空陣列）==="
curl -s "$BASE_URL/" | python -m json.tool

echo ""
echo "=== 2. 新增 2330.TW（台股）==="
curl -s -X POST "$BASE_URL/" \
  -H "Content-Type: application/json" \
  -d '{"code": "2330.TW", "market": "TW", "fetch": true}' | python -m json.tool

echo ""
echo "=== 3. 新增 AAPL（美股）==="
curl -s -X POST "$BASE_URL/" \
  -H "Content-Type: application/json" \
  -d '{"code": "AAPL", "market": "US", "fetch": true}' | python -m json.tool

echo ""
echo "=== 4. 列出監控清單（應包含 2330.TW 和 AAPL）==="
curl -s "$BASE_URL/" | python -m json.tool

echo ""
echo "=== 5. 移除 2330.TW ==="
curl -s -X POST "$BASE_URL/remove" \
  -H "Content-Type: application/json" \
  -d '{"code": "2330.TW"}' | python -m json.tool

echo ""
echo "=== 6. 再次列出（2330.TW 應已移除）==="
curl -s "$BASE_URL/" | python -m json.tool
```

執行方式：
```bash
chmod +x scripts/test_monitored_stocks.sh
./scripts/test_monitored_stocks.sh
```

---

## 10. Bootstrap 機制說明

```
首次部署，monitored_stocks 表是空的
        │
        ▼
任何呼叫 get_tracked_stock_codes() 的地方
        │
        ▼
SELECT code FROM monitored_stocks WHERE is_active = true
        │
        ▼（回傳空清單）
使用 DEFAULT_SEED_CODES（台股 8 檔 + 美股 5 檔 + 港股 4 檔）
        │
        ▼
用戶在 UI 加入新股票 → POST /api/v1/monitored-stocks/
        │
        ▼
資料庫有資料後 → Celery 排程自動讀取全部進行更新
```

---

> **文件狀態**：待實施  
> **審批人**：_______________  
> **審批日期**：_______________  
> **備註**：實施完成後請更新本文件為「已完成」