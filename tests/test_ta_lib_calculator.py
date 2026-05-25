import pytest
import pandas as pd
import numpy as np
import sys
sys.path.append('backend')
from indicators.ta_lib_calculator import TALibCalculator


class TestTALibCalculator:
    def setup_method(self):
        self.calculator = TALibCalculator()
        # 建立測試數據（50筆隨機數據）
        np.random.seed(42)
        self.test_data = pd.Series(np.random.randn(50) + 100)

    def test_calculate_ma10_success(self):
        """測試 MA10 計算成功"""
        result = self.calculator.calculate_ma10(self.test_data)
        assert result is not None
        assert len(result) == 50

    def test_calculate_ma30_success(self):
        """測試 MA30 計算成功"""
        result = self.calculator.calculate_ma30(self.test_data)
        assert result is not None
        assert len(result) == 50

    def test_insufficient_data(self):
        """測試數據不足情況"""
        short_data = pd.Series(np.random.randn(5))
        assert self.calculator.calculate_ma30(short_data) is None

    def test_ma10_value_range(self):
        """測試 MA10 值在合理範圍內"""
        result = self.calculator.calculate_ma10(self.test_data)
        valid_values = result.dropna()
        assert all(valid_values.between(95, 105))
