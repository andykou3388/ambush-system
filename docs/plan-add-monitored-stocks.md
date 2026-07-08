# 新增「股票監控清單」功能 — 執行計畫（更新版）

## 問題


先要看看podman compose 

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

新增 `monitored_stocks` 資料表 + API + 前端 UI，讓用戶可以：

- 首次使用時手動輸入股票代碼
- 加入後立即從 YFinance 抓取基本面資料
- Celery 排程任務自動讀取此表抓取全市場資料
- 所有需要股票清單的任務統一從此表讀取，支援 bootstrap fallback

---

## 修改列表（共 9 處）

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

### 3️⃣ 新增 API Router：`backend/app/routers/monitored_stocks_api.py`（新檔案）

```python
"""
監控股票清單 API
提供新增、查詢、刪除監控股票的功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.monitored_stock import MonitoredStock
from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
from sqlalchemy.dialects.postgresql import insert

router = APIRouter(prefix="/api/v1/monitored-stocks", tags=["monitored-stocks"])


class AddStockRequest(BaseModel):
    code: str
    market: str = "TW"


class FetchAndAddRequest(BaseModel):
    code: str
    market: str = "TW"


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
    """將股票加入監控清單（不抓取資料）"""
    db = SessionLocal()
    try:
        stmt = insert(MonitoredStock).values(
            code=req.code,
            market=req.market,
        )
        stmt = stmt.on_conflict_do_nothing()
        db.execute(stmt)
        db.commit()
        return {"status": "ok", "code": req.code, "market": req.market}
    finally:
        db.close()


@router.post("/fetch-and-add")
def add_and_fetch_stock(req: FetchAndAddRequest):
    """
    將股票加入監控清單 + 立即從 YFinance 抓取基本面資料
    用戶點擊後可立即在 StockPool 頁面看到資料
    """
    db = SessionLocal()
    try:
        # 1. 寫入監控清單（重複加入不會報錯）
        stmt = insert(MonitoredStock).values(
            code=req.code,
            market=req.market,
        )
        stmt = stmt.on_conflict_do_nothing()
        db.execute(stmt)
        db.commit()

        # 2. 立即從 YFinance 抓取該股票的基本面資料
        result = _fetch_stock_fundamentals_impl([req.code])

        return {
            "status": "ok",
            "code": req.code,
            "market": req.market,
            "fetch_result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{code}")
def remove_monitored_stock(code: str):
    """從監控清單移除股票（軟刪除：設為 inactive）"""
    db = SessionLocal()
    try:
        row = db.query(MonitoredStock).filter(MonitoredStock.code == code).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"股票 {code} 不在監控清單中")
        row.is_active = False
        db.commit()
        return {"status": "ok", "code": code, "action": "removed"}
    finally:
        db.close()
```

### 4️⃣ 註冊路由：`backend/app/main.py`

```python
from app.routers.monitored_stocks_api import router as monitored_stocks_router

# ... 在 include_router 區塊中增加這行
app.include_router(monitored_stocks_router)
```

### 5️⃣ 新增共用函式：`backend/app/tasks/stock_fundamental_tasks.py`

在 `save_to_database` 之後、`_fetch_stock_fundamentals_impl` 之前加入 `get_tracked_stock_codes()`：

```python
# ==================== 新增：從資料庫讀取監控股票清單 ====================
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

            # 若資料庫無資料，使用預設種子清單
            if not codes:
                logger.info("monitored_stocks 表無資料，使用預設種子清單")
                codes = [
                    # 台股
                    "2330.TW", "2317.TW", "2454.TW", "2308.TW",
                    "1301.TW", "2881.TW", "2882.TW", "1101.TW",
                    # 美股
                    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
                    # 港股
                    "0700.HK", "9988.HK", "3690.HK", "9618.HK",
                ]

            logger.info(f"取得 {len(codes)} 隻待監控股票")
            return codes

        finally:
            db.close()

    except Exception as e:
        logger.error(f"讀取股票清單失敗: {e}，使用預設清單")
        return [
            "2330.TW", "2317.TW", "2454.TW",
            "AAPL", "MSFT", "0700.HK", "9988.HK",
        ]
```

### 6️⃣ 修改 `fetch_stock_fundamentals` 任務：`backend/app/tasks/stock_fundamental_tasks.py`

```python
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
from app.tasks.stock_fundamental_tasks import (
    _fetch_stock_fundamentals_impl,
    get_tracked_stock_codes,  # 新增匯入
)
from app.tasks.weekly_tasks import (
    _fetch_weekly_bars_impl,
    _run_weekly_rule_engine_impl
)

@shared_task(bind=True, max_retries=3)
def oneclick_init_data(self):
    try:
        logger.info("🚀 開始一次性初始化所有任務")

        # === 修改：從 monitored_stocks 表讀取，若無資料則用預設種子清單 ===
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

### 9️⃣ 修改前端：`frontend/src/views/StockPool.vue`

#### 在 `<script setup>` 中新增（在 `fetchStocks` 之後）：

```javascript
// ==================== 新增：監控股票清單操作 ====================
const newStockCode = ref('')
const newStockMarket = ref('TW')
const isFetchingStock = ref(false)

async function addAndFetchStock() {
  if (!newStockCode.value.trim()) {
    showToast('請輸入股票代碼', 'error', '❌')
    return
  }

  isFetchingStock.value = true
  const code = newStockCode.value.trim().toUpperCase()

  try {
    const response = await fetch('/api/v1/monitored-stocks/fetch-and-add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code,
        market: newStockMarket.value,
      }),
    })

    if (!response.ok) throw new Error('加入監控失敗')

    showToast(`✅ ${code} 已加入監控並取得基本面資料`, 'success', '✅')
    newStockCode.value = ''
    await fetchStocks()  // 重新載入股票列表
  } catch (error) {
    showToast(`❌ ${code} 加入失敗: ${error.message}`, 'error', '❌')
  } finally {
    isFetchingStock.value = false
  }
}
```

#### 在 `<template>` 中新增（放在「篩選控制列」和「統計列」之間）：

```html
<!-- ==================== 新增：手動新增監控區塊 ==================== -->
<div
  class="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-4"
  :class="{ 'ring-2 ring-amber-500/50': stocks.length === 0 }"
>
  <h3 class="text-sm font-bold text-amber-400 mb-2 flex items-center gap-2">
    <span>📡</span>
    {{ stocks.length === 0 ? '首次使用？請先加入要監控的股票' : '手動新增監控股票' }}
  </h3>
  <div class="flex flex-wrap items-end gap-3">
    <div>
      <label class="text-xs text-slate-400 mb-1 block">股票代碼</label>
      <input
        v-model="newStockCode"
        placeholder="例: 2330.TW, AAPL, 0700.HK"
        class="bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400 w-48"
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
  <p class="text-xs text-slate-500 mt-2">
    新股票將加入監控清單，Celery 排程會自動持續更新其基本面資料
  </p>
</div>
```

---

## 資料庫 Migration

在 `db/init.sql` 末尾加入：

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
使用預設種子清單（台股 8 檔 + 美股 5 檔 + 港股 4 檔）
        │
        ▼
用戶在 UI 加入新股票 → POST /api/v1/monitored-stocks/fetch-and-add
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
│  │ 📡 首次使用？請先加入要監控的股票                         │     │
│  │ 股票代碼：[2330.TW  ]  市場：[🇹🇼 台股 ▼]               │     │
│  │ [＋ 加入並立即抓取基本面]  ← 點下去                       │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                          │
│       ▼                                                          │
│  1. POST /api/v1/monitored-stocks/fetch-and-add                  │
│     → 寫入 monitored_stocks 表 (2330.TW, TW)                    │
│     → 立即呼叫 _fetch_stock_fundamentals_impl(['2330.TW'])      │
│     → 從 YFinance 抓取 → 寫入 stock_fundamental_latest 表       │
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
└─────────────────────────────────────────────────────────────────┘
```

---

## 注意事項

1. **Bootstrap 順序**：首次部署時 `monitored_stocks` 表為空，`get_tracked_stock_codes()` 會回傳預設種子清單，確保系統可以正常啟動和抓取資料。

2. **向後相容**：`fetch_stock_fundamentals` 任務仍支援 `stock_codes` 參數，舊的調用方式不受影響。

3. **無 FK 衝突**：`monitored_stocks` 表是完全獨立的，與其他現有 table 無外部鍵關聯。

4. **前端既有「追蹤」功能不受影響**：StockPool.vue 中原有的 `＋ 追蹤` 按鈕對應的是 `ram_stop_loss` 止損追蹤，與新增的 `monitored_stocks` 監控清單是兩個獨立功能。

5. **`_run_weekly_rule_engine_impl` 不需要改**：它的邏輯是從 `stock_bar` 查所有已有資料的股票 code，本身就是動態的。

---

## 檔案異動摘要

| 檔案 | 動作 | 說明 |
|------|------|------|
| `backend/app/models/monitored_stock.py` | **新增** | MonitoredStock ORM Model |
| `backend/app/models/__init__.py` | **修改** | 加入 Model 匯出 |
| `backend/app/routers/monitored_stocks_api.py` | **新增** | 監控股票 API（含即時抓取） |
| `backend/app/main.py` | **修改** | 註冊新路由 |
| `backend/app/tasks/stock_fundamental_tasks.py` | **修改** | 加入 `get_tracked_stock_codes()` + 修改任務為可選參數 |
| `backend/app/celery_app.py` | **修改** | 移除 `fetch-daily-fundamentals` 的 args |
| `backend/app/tasks/oneclick_init_task.py` | **修改** | 改用 `get_tracked_stock_codes()` + 移除硬編碼 |
| `backend/app/tasks/weekly_tasks.py` | **不需修改** | `_fetch_weekly_bars_impl` 的呼叫端（oneclick_init_task）已改為從 DB 讀取，此函式本身不須改 |
| `frontend/src/views/StockPool.vue` | **修改** | 加入手動新增監控區塊 |
| `db/init.sql` | **修改** | 在末尾新增 monitored_stocks 表 |
| 既有容器內資料庫 | **執行 SQL** | 手動執行 CREATE TABLE |

總計：**2 個新檔案 + 5 處修改 + 1 處 SQL 執行**

已將 `docs/plan-add-monitored-stocks.md` 更新完畢，主要變更如下：

## 更新摘要

### 1️⃣ 問題範圍擴大
從原本只處理 `celery_app.py` 一處硬編碼，擴大到**全面盤點**系統中所有股票清單來源，共發現 6 處，其中 4 處需要修改、2 處維持不變。

### 2️⃣ 修改數量從 6 處 → 9 處
新增了以下修改點：

| 新增項目 | 原因 |
|---------|------|
| `oneclick_init_task.py` 修改 | 移除 100+ 檔港股硬編碼，改用 `get_tracked_stock_codes()` |
| `db/init.sql` 修改 | 在末尾新增 `monitored_stocks` 表 DDL |
| 注意事項章節 | 說明 bootstrap 機制、向後相容、無 FK 衝突等 |

### 3️⃣ 新增 Bootstrap 機制說明
首次部署時 `monitored_stocks` 表為空，`get_tracked_stock_codes()` 會回傳預設種子清單（台股 8 檔 + 美股 5 檔 + 港股 4 檔），確保系統可以正常啟動。

### 4️⃣ 釐清三個獨立功能
在 StockPool.vue 頁面上，三個按鈕各自對應不同功能：
- **`＋ 追蹤`** → `ram_stop_loss`（止損追蹤，既有功能）
- **`⭐ 加入關注`** → `localStorage`（純前端，既有功能）
- **`＋ 加入並立即抓取基本面`** → `monitored_stocks`（本次新增）

三者互不衝突。

---
