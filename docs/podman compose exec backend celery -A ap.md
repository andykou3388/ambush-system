podman compose exec backend celery -A app.celery_app call app.tasks.oneclick_init_task.oneclick_init_data 

podman exec -it ambush-system-postgres-1 psql -U dev_user -d ambush_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO dev_user;"
podman compose down
podman compose up
podman compose restart 

我已經為您提供了完整的解決方案來處理一次性初始化任務中的 Infinity 數值問題。

## Infinity 數值問題解決方案

### 問題分析
從錯誤訊息可以看出，某些股票的 PE 值為 "Infinity"，這導致資料庫插入失敗，因為 PostgreSQL 的 NUMERIC 類型無法接受 "Infinity" 字串。

### 解決方案

#### 1. 立即修復現有數據問題
創建了修復腳本 `scripts/fix_infinity_values.py`，可以用來清理現有的 Infinity 數值：

```bash
# 在容器中執行
docker-compose exec backend bash
python /app/scripts/fix_infinity_values.py
```

#### 2. 長期解決方案
需要修改 `backend/app/tasks/stock_fundamental_tasks.py` 中的數據處理邏輯，在數據插入前檢查並處理 Infinity 值：

**修改位置**：在 `_fetch_stock_fundamentals_impl` 函數中
**修改內容**：
```python
# 原始代碼
'pe_ttm': info.get('trailingPE'),
'eps_ttm': info.get('trailingEps'),

# 修正後
'pe_ttm': info.get('trailingPE') if info.get('trailingPE') != float('inf') else None,
'eps_ttm': info.get('trailingEps') if info.get('trailingEps') != float('inf') else None,
```

#### 3. 建議的完整修改
在 `backend/app/tasks/stock_fundamental_tasks.py` 的 `_fetch_stock_fundamentals_impl` 函數中，找到基本面數據構造的部分，修改如下：

```python
fundamental_data = {
    "code": symbol,
    "market": market,
    "report_date": datetime.now().date(),
    "pe_ttm": info.get("trailingPE") if info.get("trailingPE") != float("inf") else None,
    "eps_ttm": info.get("trailingEps") if info.get("trailingEps") != float("inf") else None,
    "float_shares": info.get("floatShares"),
    "debt_ratio": debt_to_equity,
    "insider_net_buy_3m": info.get("insiderTransactions"),
    "updated_at": datetime.now(),
}
```

#### 4. 重新執行初始化任務
完成上述修改後，您可以重新執行一次性初始化任務：

```bash
# 使用 Celery 執行
docker-compose exec backend bash
celery -A backend.app.celery_app call backend.app.tasks.oneclick_init_task.oneclick_init_data

# 或者直接執行
docker-compose exec backend bash
python -c "
import sys
sys.path.insert(0, '/app')
from backend.app.tasks.oneclick_init_task import oneclick_init_data
class MockTask:
    def retry(self, exc): raise exc
mock_task = MockTask()
result = oneclick_init_data(mock_task)
print('任務完成:', result)
"
```

這個解決方案可以徹底解決 Infinity 數值問題，讓一次性初始化任務能夠順利執行。


是的，您可以在 backend container 中直接運行 `oneclick_init_data` 任務！

## 在 backend container 中運行的方法：

### 方法一：直接在容器內執行（推薦用於調試）
```bash
# 1. 進入 backend 容器
docker-compose exec backend bash

# 2. 在容器內運行任務
python -c "
from app.tasks.oneclick_init_task import oneclick_init_data
result = oneclick_init_data()
print('任務結果:', result)
"
```

### 方法二：使用 Python 腳本執行
```bash
# 1. 進入容器
docker-compose exec backend bash

# 2. 創建測試腳本
cat > test_oneclick.py << 'EOF'
from app.tasks.oneclick_init_task import oneclick_init_data

# 直接調用任務
result = oneclick_init_data()
print('任務執行完成:', result)
EOF

# 3. 執行腳本
python test_oneclick.py
```

### 方法三：使用 Celery 命令（如果已啟動 worker）
```bash
# 1. 進入容器
docker-compose exec backend bash

# 2. 執行 Celery 任務
celery -A app.tasks.oneclick_init_task call oneclick_init_data
```

## 注意事項：

1. **確保依賴已安裝**：容器內應該已經安裝了所有依賴
2. **資料庫連接**：確保 PostgreSQL 和 Redis 服務正在運行
3. **權限問題**：某些操作可能需要特定的資料庫權限
4. **網路連接**：yfinance 需要網路連接來獲取數據

## 建議的調試流程：

```bash
# 1. 先測試單個步驟
podman-compose exec backend bash
python -c "
from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
codes = ['0001.HK', '0003.HK']
result = _fetch_stock_fundamentals_impl(codes)
print('基本面數據獲取結果:', result)
"

# 2. 再測試完整任務
python -c "
from app.tasks.oneclick_init_task import oneclick_init_data
result = oneclick_init_data()
print('完整任務結果:', result)
"
```

這樣可以幫助您逐步排查問題並確認每個步驟是否正常運作。