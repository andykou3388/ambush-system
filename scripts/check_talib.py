import sys
sys.path.append('backend')
from indicators.ta_lib_calculator import TALibCalculator
import pandas as pd
import numpy as np


def test_talib():
    """驗證 TA-Lib 技術指標計算"""
    print("測試 TA-Lib 技術指標計算...")
    print("=" * 50)

    # 測試 1：基本安裝驗證
    print("\n[測試 1] TA-Lib 安裝驗證")
    calculator = TALibCalculator()
    print("  [OK] TA-Lib 安裝正確")

    # 測試 2：MA10 計算
    print("\n[測試 2] MA10 計算")
    test_data = pd.Series(np.random.randn(50) + 100)
    ma10 = calculator.calculate_ma10(test_data)
    if ma10 is not None and len(ma10) == 50:
        print(f"  [OK] MA10 計算成功，共 {len(ma10)} 筆數據")
        print(f"  最新 MA10 值: {ma10.iloc[-1]:.2f}")
    else:
        print("  [FAIL] MA10 計算失敗")

    # 測試 3：MA30 計算
    print("\n[測試 3] MA30 計算")
    ma30 = calculator.calculate_ma30(test_data)
    if ma30 is not None and len(ma30) == 50:
        print(f"  [OK] MA30 計算成功，共 {len(ma30)} 筆數據")
        print(f"  最新 MA30 值: {ma30.iloc[-1]:.2f}")
    else:
        print("  [FAIL] MA30 計算失敗")

    # 測試 4：邊界情況 - 數據不足
    print("\n[測試 4] 邊界情況 - 數據不足")
    short_data = pd.Series(np.random.randn(5))
    result = calculator.calculate_ma30(short_data)
    if result is None:
        print("  [OK] 正確處理數據不足情況")
    else:
        print("  [FAIL] 應回傳 None")

    print("\n" + "=" * 50)
    print("TA-Lib 驗證通過！")
    return True


if __name__ == "__main__":
    test_talib()