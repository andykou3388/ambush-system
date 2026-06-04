#!/usr/bin/env python3
"""
刪除 stock_fundamental 表格中的所有資料
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.stock_fundamental import StockFundamental
from app.database import SessionLocal

def delete_all_stock_fundamental_data():
    """刪除 stock_fundamental 表格中的所有資料"""
    
    # 建立資料庫連接
    engine = create_engine(os.getenv('DATABASE_URL'))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 先查詢總數量
        count = db.query(StockFundamental).count()
        print(f"找到 {count} 條 stock_fundamental 記錄")
        
        if count == 0:
            print("沒有資料需要刪除")
            return
            
        # 問題使用者是否確定要刪除
        response = input(f"確定要刪除這 {count} 條記錄嗎？(y/N): ")
        if response.lower() != 'y':
            print("取消刪除操作")
            return
            
        # 執行刪除操作
        deleted_count = db.query(StockFundamental).delete(synchronize_session=False)
        db.commit()
        
        print(f"成功刪除 {deleted_count} 條記錄")
        
    except Exception as e:
        db.rollback()
        print(f"刪除失敗: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_stock_fundamental_data()