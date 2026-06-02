#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../backend')

from app.database import SessionLocal
from app.models.stock_bar import StockBar
from app.models.stock_fundamental import StockFundamental
from app.tasks_helper import classify_stock

print("開始測試 classify_stock...")

# 先檢查資料
db = SessionLocal()
try:
    bar = db.query(StockBar).filter(StockBar.code == '2330.TW').order_by(StockBar.trade_date.desc()).first()
    if bar:
        print(f"找到 2330.TW 資料:")
        print(f"  close: {repr(bar.close)}")
        print(f"  ma10_w: {repr(bar.ma10_w)}")
        print(f"  ma30_w: {repr(bar.ma30_w)}")
    else:
        print("找不到 2330.TW 資料")
        
    fund = db.query(StockFundamental).filter(StockFundamental.code == '2330.TW').order_by(StockFundamental.report_date.desc()).first()
    if fund:
        print(f"找到 2330.TW 基本面資料:")
        print(f"  pe_ttm: {repr(fund.pe_ttm)}")
    else:
        print("找不到 2330.TW 基本面資料")
finally:
    db.close()

# 執行分類
print("\n執行 classify_stock...")
result = classify_stock('2330.TW')
print(f"結果: {result}")