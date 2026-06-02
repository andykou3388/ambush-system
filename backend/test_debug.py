import traceback
from app.tasks_helper import classify_stock

try:
    result = classify_stock('2330.TW')
    print('測試結果:', result)
except Exception as e:
    print('完整錯誤訊息:')
    traceback.print_exc()