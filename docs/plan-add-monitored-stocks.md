# 新增「股票監控清單」功能 — 執行計畫 (v2)

## 問題

系統中存在多處「硬編碼股票代碼」，無法動態管理監控標的：

| 位置 | 內容 | 狀態 |
|------|------|------|
| `celery_app.py:37` | `args: ["2330.TW", "2317.TW", "2454.TW"]` | 需改為從 DB 讀取 |
| `oneclick_init_task.py:31-48` | 100+ 檔港股硬編碼 | 需改為從 DB 讀取 + fallback |
| `stock_fundamental_tasks.py:166` | 由呼叫者傳入，無硬編碼 | 整合即可 |
| `weekly_tasks.py:32` `_fetch_weekly_bars_impl` | 由呼叫者傳入（oneclick_init_task 傳硬編碼） | 需改為從 DB 讀取 |
| `weekly_tasks.py:192` `_run_weekly_rule_engine_impl` | 從 stock_bar 查所有 distinct code | ✅ 本身就是動態，不用改 |
| `minute_data_tasks.py:82` | 從 ram_stop_loss 活躍部位查 | ✅ 專用資料來源，不用改 |

## 解決方案

新增 `monitored_stocks` 資料表 + 共用工具函式 + API + 前端 UI，讓用戶可以：

- 首次使用時手動輸入股票代碼
- 加入後立即從 YFinance 抓取基本面資料
- Celery 排程任務自動讀取此表抓取全市場資料
- 所有需要股票清單的任務統一從此表讀取，支援 bootstrap fallback

---

## 修改列表（共 11 處）

### 1️⃣ 新增 Model：`backend/app/models/monitored_stock.py`（新檔案）

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

### 2️⃣ 新增 Model 匯出：`backend/app/models/__init__.py`

```python
from app.models.monitored_stock import MonitoredStock
```

並在 `__all__` 中加入 `"MonitoredStock"`。

### 3️⃣ 新增共用工具模組：`backend/app/utils/stock_utils.py`（新檔案）

> **v2 改進**：`get_tracked_stock_codes()` 從 `stock_fundamental_tasks.py` 搬到獨立模組，避免跨模組職責耦合。所有需要股票清單的模組改從此處匯入。

```python
"""
股票相關共用工具函式
提供 get_tracked_stock_codes() 供多個 task 模組共用
"""
import logging

logger = logging.getLogger(__name__)

# v2 改進：種子清單抽成模組層級常數，兩處共用同一份，避免維護不一致
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
    此函式會同時被基本面任務、週線任務、一次性初始化任務呼叫。

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

### 4️⃣ 新增 API Router：`backend/app/routers/monitored_stocks_api.py`（新檔案）

> **v2 改進**：
> - 將 `POST /`（純加入）和 `POST /fetch-and-add`（加入+抓取）**合併成一個端點**，預設 `fetch=true`。因為實務上使用者永遠想加入後立即看到資料，不再需要兩個獨立端點。
> - 刪除改用 `POST /remove` 搭配 body，避免股票代碼中的點號在路徑參數中被錯誤解析。
> - 加入 Pydantic `Field` 驗證，限制 market 只能接受 `"TW"`、`"US"`、`"HK"` 三種值。
> - **先抓取基本面資料，成功後才寫入資料庫**，避免狀態不一致。

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
    fetch: bool = True  # v2 改進：預設為 True，加入後立即抓取


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
    若 fetch=False，僅寫入資料庫不抓取資料。
    """
    # v2 改進：若 fetch=True，先抓取資料驗證股票代碼有效性，成功後才寫入
    fetch_result = None
    if req.fetch:
        try:
            fetch_result = _fetch_stock_fundamentals_impl([req.code])
            # 檢查抓取結果是否成功
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

### 5️⃣ 註冊路由：`backend/app/main.py`

```python
from app.routers.monitored_stocks_api import router as monitored_stocks_router

# ... 在 include_router 區塊中增加這行
app.include_router(monitored_stocks_router)
```

### 6️⃣ 修改 `stock_fundamental_tasks.py`：匯入共用函式 + 任務支援空參數 + 處理空清單

> **v2 改進**：
> - 移除 `get_tracked_stock_codes()` 定義（搬到 `stock_utils.py`）
> - 從 `app.utils.stock_utils` 匯入
> - `fetch_stock_fundamentals` 在開頭檢查空清單，避免無意義的 API 呼叫

```python
# 在檔案頂部加入匯入
from app.utils.stock_utils import get_tracked_stock_codes

# 修改任務函式
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_stock_fundamentals(self, stock_codes: list = None):
    """
    批量獲取股票基本面數據的通用任務
    支援兩種調用方式：
      1. 有參數：使用傳入的 stock_codes（向後相容）
      2. 無參數：自動從 monitored_stocks 表讀取待監控股票清單

    Args:
        stock_codes: 可選，股票代碼列表
    """
    try:
        if not stock_codes:
            stock_codes = get_tracked_stock_codes()
            logger.info(f"自動從 monitored_stocks 讀取股票清單")

        # v2 改進：處理空清單邊界情況
        if not stock_codes:
            logger.warning("股票清單為空，跳過本次基本面抓取")
            return {"status": "skipped", "reason": "股票清單為空"}

        return _fetch_stock_fundamentals_impl(stock_codes)
    except Exception as exc:
        logger.error(f"獲取股票數據失敗: {exc}")
        raise self.retry(exc=exc)
```

### 7️⃣ 修改 Celery 排程：`backend/app/celery_app.py`

```python
celery_app.conf.beat_schedule = {
    "fetch-daily-fundamentals": {
        "task": "app.tasks.stock_fundamental_tasks.fetch_stock_fundamentals",
        "schedule": crontab(hour="14", minute="0", day_of_week="1-5"),
        # args 不傳入，由任務內部從 monitored_stocks 表讀取
        "options": {"queue": "fundamental"},
    },
    # ... 其餘任務保持不變
}
```

### 8️⃣ 修改 `oneclick_init_task.py`：從 DB 讀取代碼

```python
# 修改匯入：從共用工具函式匯入
from app.utils.stock_utils import get_tracked_stock_codes

@shared_task(bind=True, max_retries=3)
def oneclick_init_data(self):
    try:
        logger.info("🚀 開始一次性初始化所有任務")

        # 從 monitored_stocks 表讀取，若無資料則用預設種子清單
        stock_codes = get_tracked_stock_codes()
        logger.info(f"取得 {len(stock_codes)} 隻股票代碼")

        # 1. 股票基本面數據獲取
        logger.info("正在獲取股票基本面數據...")
        result1 = _fetch_stock_fundamentals_impl(stock_codes)

        # 2. 週線 K 線數據
        logger.info("正在獲取週線 K 線資料...")
        result_weekly = _fetch_weekly_bars_impl(stock_codes)

        # 3. 規則引擎分析
        logger.info("正在執行規則引擎分析...")
        result3 = _run_weekly_rule_engine_impl("HK")

        # 4. 每日分鐘線數據校驗
        logger.info("正在執行每日分鐘線資料校驗...")
        result4 = _daily_minute_validation_impl()

        logger.info("🎉 所有任務初始化完成")
        return {
            "status": "success",
            "message": "所有任務初始化完成",
            "tasks": ["fundamentals", "weekly_bars", "indicators", "rule_engine", "minute_validation"]
        }
    except Exception as exc:
        logger.error(f"❌ 一次性初始化任務失敗: {exc}")
        raise self.retry(exc=exc)
```

### 9️⃣ 前端修改：`frontend/src/views/StockPool.vue`

> **v2 改進**：
> - 分離「首次使用引導」和「常態手動新增」為兩個不同區塊，在清單為空時自動顯示引導
> - 加入「已監控股票管理面板」，讓使用者可以看到目前監控了哪些股票、並可移除
> - 支援批次輸入（逗號或換行分隔多個代碼）

#### 在 `<script setup>` 中新增：

```javascript
// ==================== 新增：監控股票清單操作（v2） ====================
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
    await fetchStocks()       // 重新載入股票列表
    await fetchMonitoredStocks()  // 更新監控清單
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

#### 在 `onMounted` 中加入：

```javascript
onMounted(() => {
  fetchStocks()
  loadTrackedSymbols()
  fetchMonitoredStocks()  // v2 新增：載入監控清單
  const saved = localStorage.getItem('my_watchlist_v2')
  if (saved) {
    try { watchlist.value = JSON.parse(saved) } catch(e) {}
  }
})
```

#### 在 `<template>` 中新增（放在「篩選控制列」和「統計列」之間）：

```html
<!-- ==================== 新增：監控股票管理區塊（v2） ==================== -->
<div
  class="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-4"
  :class="{ 'ring-2 ring-amber-500/50': stocks.length === 0 }"
>
  <!-- v2 改進：分離首次引導和常態新增 -->
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

  <!-- 新增區塊 -->
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
      <i v-if="isFetchingStock" class="ph-bold ph-spinner animate-spin"></i>
      <span v-else>＋</span>
      {{ isFetchingStock ? '抓取中...' : '加入並立即抓取基本面' }}
    </button>
  </div>

  <!-- 已監控清單面板（v2 新增） -->
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

### 🔟 新增資料庫 Migration 腳本：`db/migrations/001_add_monitored_stocks.sql`（新檔案）

> **v2 改進**：提供獨立的 SQL migration 腳本，而非僅在 `db/init.sql` 末尾加入。已上線的資料庫可以直接執行此腳本。

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

同時在 `db/init.sql` 末尾也加入相同 DDL（供全新部署使用）。

### 1️⃣1️⃣ 修改 `weekly_tasks.py` 中的 `_fetch_weekly_bars_impl`（僅改呼叫端）

`oneclick_init_task.py` 已是新的呼叫方式，`_fetch_weekly_bars_impl` 本身不需要修改。但若 `weekly_tasks.py` 中有其他獨立排程任務也需要從 DB 讀取股票清單，則比照辦理。此處僅確認現狀不需修改。

---

## Bootstrap 機制說明

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

## 完整運作流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 第一天：資料庫全空                                               │
│                                                                   │
│  StockPool.vue                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ 📡 首次使用？請加入要監控的股票                           │     │
│  │ 股票代碼：[2330.TW, AAPL, 0700.HK      ]  (支援批次)     │     │
│  │ 市場：[🇹🇼 台股 ▼]  [＋ 加入並立即抓取基本面]  ← 點下去   │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                          │
│       ▼                                                          │
│  1. POST /api/v1/monitored-stocks/ (fetch=true)                  │
│     → 先呼叫 _fetch_stock_fundamentals_impl(['2330.TW'])        │
│     → 從 YFinance 抓取 → 寫入 stock_fundamental_latest 表       │
│     → 成功後才寫入 monitored_stocks 表                           │
│     → 回傳成功                                                   │
│       │                                                          │
│       ▼                                                          │
│  2. StockPool.vue 重新載入 → fetchStocks()                      │
│     → GET /api/v1/stock-fundamental/list                          │
│     → 顯示 2330.TW 的 PE, EPS, 流通股 ...                        │
│                                                                   │
│  用戶重複操作，加入 AAPL, 0700.HK ...                            │
│  每加入一隻即時抓取，立即顯示                                     │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 每天下午 2:00（Celery 排程）                                     │
│                                                                   │
│  fetch_stock_fundamentals()  // 不傳參數                         │
│     → get_tracked_stock_codes()                                  │
│     → SELECT code FROM monitored_stocks WHERE is_active = true   │
│     → 回傳 ["2330.TW", "AAPL", "0700.HK", ...]                   │
│     → _fetch_stock_fundamentals_impl(codes)  // 一次抓全部      │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 用戶執行「一次性初始化」（手動觸發）                              │
│                                                                   │
│  oneclick_init_data()                                            │
│     → get_tracked_stock_codes()  // 同上，從 DB 讀取            │
│     → 基本面、週線、規則引擎 ...                                 │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ StockPool.vue 頁面上                                             │
│                                                                   │
│  每一隻股票右側的操作按鈕區：                                     │
│  [＋ 追蹤] → ram_stop_loss（止損追蹤，獨立功能）                  │
│  [⭐ 加入關注] → localStorage 關注清單（純前端）                  │
│  頂部新區塊：[＋ 加入並立即抓取基本面] → monitored_stocks         │
│  頂部右側：[📋 已監控 X 檔] → 下拉顯示管理面板（可移除）         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 注意事項

1. **Bootstrap 順序**：首次部署時 `monitored_stocks` 表為空，`get_tracked_stock_codes()` 會回傳 `DEFAULT_SEED_CODES`，確保系統可以正常啟動和抓取資料。

2. **向後相容**：`fetch_stock_fundamentals` 任務仍支援 `stock_codes` 參數，舊的調用方式不受影響。

3. **無 FK 衝突**：`monitored_stocks` 表是完全獨立的，與其他現有 table 無外部鍵關聯。

4. **前端既有「追蹤」功能不受影響**：StockPool.vue 中原有的 `＋ 追蹤` 按鈕對應的是 `ram_stop_loss` 止損追蹤，與新增的 `monitored_stocks` 監控清單是兩個獨立功能。

5. **`_run_weekly_rule_engine_impl` 不需要改**：它的邏輯是從 `stock_bar` 查所有已有資料的股票 code，本身就是動態的。

6. **API 先抓資料再寫入**（v2 改進）：`POST /api/v1/monitored-stocks/` 在 `fetch=true` 時，會先從 YFinance 抓取基本面資料，成功後才寫入 `monitored_stocks` 表。若抓取失敗（如無效股票代碼），不會寫入髒資料。

7. **批次輸入支援**（v2 改進）：前端輸入框支援逗號、空格、換行分隔多個股票代碼，一次加入多檔。

8. **Pydantic 驗證**（v2 改進）：`market` 欄位限制只能接受 `"TW"`、`"US"`、`"HK"` 三種值，避免髒資料。

---

## 檔案異動摘要

| 檔案 | 動作 | 說明 |
|------|------|------|
| `backend/app/models/monitored_stock.py` | **新增** | MonitoredStock ORM Model |
| `backend/app/models/__init__.py` | **修改** | 加入 Model 匯出 |
| `backend/app/utils/stock_utils.py` | **新增** | 共用工具模組：`get_tracked_stock_codes()` + `DEFAULT_SEED_CODES` |
| `backend/app/routers/monitored_stocks_api.py` | **新增** | 監控股票 API（v2：合併端點、先抓再寫、Pydantic 驗證） |
| `backend/app/main.py` | **修改** | 註冊新路由 |
| `backend/app/tasks/stock_fundamental_tasks.py` | **修改** | 移除 `get_tracked_stock_codes()` 定義，改從 `stock_utils` 匯入；任務支援空參數 + 空清單檢查 |
| `backend/app/celery_app.py` | **修改** | 移除 `fetch-daily-fundamentals` 的 args |
| `backend/app/tasks/oneclick_init_task.py` | **修改** | 改用 `get_tracked_stock_codes()` + 移除 100+ 行硬編碼 |
| `backend/app/tasks/weekly_tasks.py` | **不需修改** | 呼叫端（oneclick_init_task）已改為從 DB 讀取 |
| `frontend/src/views/StockPool.vue` | **修改** | 加入監控管理區塊（首次引導、批次輸入、監控面板） |
| `db/migrations/001_add_monitored_stocks.sql` | **新增** | 獨立 SQL migration 腳本 |
| `db/init.sql` | **修改** | 在末尾新增 monitored_stocks 表 DDL |
| 既有容器內資料庫 | **執行 SQL** | 執行 `db/migrations/001_add_monitored_stocks.sql` |

總計：**4 個新檔案 + 5 處修改 + 1 處 SQL 執行**