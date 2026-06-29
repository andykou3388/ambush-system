#!/usr/bin/env python3
"""
種子數據腳本：生成 ram_stop_loss 表的測試數據
用於測試實時動態止損追蹤功能
"""
import sys
import os
from datetime import date, datetime
from decimal import Decimal

# 添加專案根目錄和 backend 目錄到 Python 路徑
project_root = '/app'
backend_path = os.path.join(project_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss


def seed_ram_stop_loss_data():
    """向 ram_stop_loss 表插入測試數據（先清空舊數據）"""
    
    db = SessionLocal()
    
    try:
        # 先清空現有數據
        print("正在清空現有數據...")
        db.query(RamStopLoss).delete()
        db.commit()
        
        # 重新初始化會話以獲取最新數據
        db.close()
        db = SessionLocal()
        
        print("✅ ram_stop_loss 表已清空，準備插入測試數據...")
        print("-" * 60)
        
        # 測試數據 - 台積電 (正常監控中)
        position1 = RamStopLoss(
            code="2330.TW",
            market="TW",
            buy_date=date(2025, 6, 1),
            buy_price=Decimal("550.0000"),
            current_price=Decimal("565.5000"),
            highest_price=Decimal("570.0000"),
            stop_loss_price=Decimal("524.7000"),  # 570 * (1 - 0.08)
            drawdown_pct=Decimal("0.0086"),  # (570 - 565.5) / 570
            is_triggered=False,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 測試數據 - 創意 (盈利狀態)
        position2 = RamStopLoss(
            code="2454.TW",
            market="TW",
            buy_date=date(2025, 5, 15),
            buy_price=Decimal("890.0000"),
            current_price=Decimal("920.0000"),
            highest_price=Decimal("950.0000"),
            stop_loss_price=Decimal("874.0000"),
            drawdown_pct=Decimal("0.0316"),
            is_triggered=False,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 測試數據 - 鴻海 (接近止損閾值)
        position3 = RamStopLoss(
            code="2303.TW",
            market="TW",
            buy_date=date(2025, 6, 10),
            buy_price=Decimal("180.0000"),
            current_price=Decimal("165.2000"),
            highest_price=Decimal("185.0000"),
            stop_loss_price=Decimal("170.2000"),
            drawdown_pct=Decimal("0.0800"),  # 剛好達到 8%
            is_triggered=False,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 測試數據 - 創意 (已觸發止損，使用不同代碼)
        position4 = RamStopLoss(
            code="3008.TW",
            market="TW",
            buy_date=date(2025, 4, 1),
            buy_price=Decimal("1200.0000"),
            current_price=Decimal("1050.0000"),
            highest_price=Decimal("1250.0000"),
            stop_loss_price=Decimal("1150.0000"),
            drawdown_pct=Decimal("0.1600"),
            is_triggered=True,
            is_active=False,
            triggered_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 測試數據 - 友達光電 (小幅度回撤)
        position5 = RamStopLoss(
            code="2409.TW",
            market="TW",
            buy_date=date(2025, 6, 15),
            buy_price=Decimal("45.0000"),
            current_price=Decimal("44.5000"),
            highest_price=Decimal("45.5000"),
            stop_loss_price=Decimal("41.8600"),
            drawdown_pct=Decimal("0.0220"),
            is_triggered=False,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 插入所有數據
        for position in [position1, position2, position3, position4, position5]:
            db.add(position)
        
        db.commit()
        
        print("=" * 60)
        print("✅ ram_stop_loss 測試數據已產生")
        print("=" * 60)
        print("\n測試數據列表：")
        print(f"{'代碼':<10} {'買入價':<10} {'當前價':<10} {'最高價':<10} {'回撤 %':<10} {'狀態'}")
        print("-" * 60)
        
        positions = db.query(RamStopLoss).all()
        for p in positions:
            status = "已觸發 ✗" if p.is_triggered else "监控中 ✓"
            print(f"{p.code:<10} {float(p.buy_price):<10.2f} {float(p.current_price):<10.2f} "
                  f"{float(p.highest_price):<10.2f} {p.drawdown_pct:<10.2%} {status}")
        
        print("\n" + "=" * 60)
        print("📊 統計：")
        print(f"   總數：{len(positions)}")
        print(f"   活跃：{db.query(RamStopLoss).filter(RamStopLoss.is_active == True).count()}")
        print(f"   已觸發：{db.query(RamStopLoss).filter(RamStopLoss.is_triggered == True).count()}")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 產生數據失敗：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_ram_stop_loss_data()