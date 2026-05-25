import talib
import numpy as np
import pandas as pd
from typing import Optional


class TALibCalculator:
    """TA-Lib 技術指標計算器"""

    def __init__(self):
        self._validate_installation()

    def _validate_installation(self):
        """驗證 TA-Lib 安裝是否正確"""
        try:
            talib.MA(np.array([1.0, 2.0, 3.0]), timeperiod=2)
            print("[OK] TA-Lib 安裝驗證通過")
        except Exception as e:
            raise RuntimeError(f"TA-Lib 安裝異常: {e}")

    def calculate_ma(
        self, close_prices: pd.Series, timeperiod: int = 10
    ) -> Optional[pd.Series]:
        """
        計算移動平均線 (MA)

        Args:
            close_prices: 收盤價序列
            timeperiod: 週期（預設 10）

        Returns:
            MA 序列，若數據不足則回傳 None
        """
        if len(close_prices) < timeperiod:
            print(
                f"[WARN] 數據不足：需要 {timeperiod} 筆，實際 {len(close_prices)} 筆"
            )
            return None

        result = talib.MA(close_prices.values, timeperiod=timeperiod)
        return pd.Series(result, index=close_prices.index)

    def calculate_ma10(
        self, close_prices: pd.Series
    ) -> Optional[pd.Series]:
        """計算 MA10"""
        return self.calculate_ma(close_prices, timeperiod=10)

    def calculate_ma30(
        self, close_prices: pd.Series
    ) -> Optional[pd.Series]:
        """計算 MA30"""
        return self.calculate_ma(close_prices, timeperiod=30)
