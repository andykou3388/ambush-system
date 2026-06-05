podman compose exec backend celery -A app.celery_app call app.tasks.oneclick_init_task
oneclick_init_data 

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