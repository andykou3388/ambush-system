import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append("backend")

from engine.rule_engine import RuleEngine
from engine.rules.rule1_trend import Rule1Trend
from engine.rules.rule2_volume import Rule2Volume
from engine.rules.rule3_buy_point import Rule3BuyPoint
from engine.rules.rule4_valuation import Rule4Valuation
from engine.rules.rule5_fundamental import Rule5Fundamental


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def config():
    """加载配置文件"""
    import yaml
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "backend", "engine", "config.yaml"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def engine():
    """创建规则引擎实例"""
    return RuleEngine()


@pytest.fixture
def mock_data():
    """创建模拟测试数据"""
    data = [
        # code, close, ma10, ma30, volume, pe, market_cap, debt_ratio, insider_buy, analyst_cover
        ["000001", 8.5, 8.2, 7.8, 50000, 9, 4e9, 0.5, 1, 0],
        ["000002", 12, 11.5, 13, 20000, 15, 60e9, 0.7, 0, 1],
        ["000003", 5.5, 5.7, 6.0, 15000, 8, 20e9, 0.45, 1, 0],
        ["000004", 18, 17, 16, 80000, 12, 80e9, 0.65, 0, 1],
        ["000005", 7.2, 7.1, 6.9, 45000, 7, 30e9, 0.4, 1, 0],
        ["000006", 9.5, 9.8, 10, 25000, 11, 55e9, 0.62, 0, 1],
        ["000007", 6.8, 6.7, 6.5, 60000, 8, 25e9, 0.42, 1, 0],
        ["000008", 22, 20, 19, 70000, 18, 120e9, 0.7, 0, 1],
        ["000009", 4.9, 4.8, 4.7, 38000, 6, 15e9, 0.38, 1, 0],
        ["000010", 14, 13.5, 14.2, 32000, 9, 48e9, 0.55, 1, 0],
    ]

    return pd.DataFrame(
        data,
        columns=[
            "code", "close", "ma10", "ma30", "volume",
            "pe", "market_cap", "debt_ratio", "insider_buy", "analyst_cover",
        ],
    )


# ============================================================
# 第1层：趋势规则测试
# ============================================================

class TestRule1Trend:
    def test_long_trend(self, config):
        """测试多头趋势：close > ma10"""
        rule = Rule1Trend(config)
        result = rule.evaluate({"close": 10, "ma10": 9, "ma30": 8})
        assert result["long"] is True
        assert result["strong"] is True
        assert result["short"] is False
        assert result["weak"] is False

    def test_short_trend(self, config):
        """测试空头趋势：close < ma10"""
        rule = Rule1Trend(config)
        result = rule.evaluate({"close": 8, "ma10": 9, "ma30": 10})
        assert result["long"] is False
        assert result["strong"] is False
        assert result["short"] is True
        assert result["weak"] is True

    def test_mixed_trend(self, config):
        """测试混合趋势：close > ma10 但 close < ma30"""
        rule = Rule1Trend(config)
        result = rule.evaluate({"close": 9.5, "ma10": 9, "ma30": 10})
        assert result["long"] is True
        assert result["strong"] is False
        assert result["short"] is False
        assert result["weak"] is True


# ============================================================
# 第2层：成交量规则测试
# ============================================================

class TestRule2Volume:
    def test_volume_breakout(self, config):
        """测试成交量放量突破"""
        rule = Rule2Volume(config)
        result = rule.evaluate({"volume": 100000}, vol_ma5=10000)
        assert result is True

    def test_no_breakout(self, config):
        """测试未放量"""
        rule = Rule2Volume(config)
        result = rule.evaluate({"volume": 10000}, vol_ma5=10000)
        assert result is False

    def test_zero_volume_ma(self, config):
        """测试均量为0的情况"""
        rule = Rule2Volume(config)
        result = rule.evaluate({"volume": 10000}, vol_ma5=0)
        assert result is False


# ============================================================
# 第3层：低风险买点测试
# ============================================================

class TestRule3BuyPoint:
    def test_buy_point(self, config):
        """测试符合低风险买点条件"""
        rule = Rule3BuyPoint(config)
        result = rule.evaluate({
            "close": 10,
            "ma10": 10,
            "volume": 1000,
            "vol_ma5": 10000,
            "week_high": 10.2,
            "week_low": 9.9,
        })
        assert result is True

    def test_not_touching_ma10(self, config):
        """测试未回踩MA10"""
        rule = Rule3BuyPoint(config)
        result = rule.evaluate({
            "close": 15,
            "ma10": 10,
            "volume": 1000,
            "vol_ma5": 10000,
            "week_high": 15,
            "week_low": 10,
        })
        assert result is False


# ============================================================
# 第4层：价格估值测试
# ============================================================

class TestRule4Valuation:
    def test_valuation_pass(self, config):
        """测试价格估值条件通过"""
        rule = Rule4Valuation(config)
        result = rule.evaluate({
            "close": 8,
            "pe": 8,
            "market_cap": 3e9,  # 30亿 < 50亿
        })
        assert result is True

    def test_price_too_high(self, config):
        """测试股价过高"""
        rule = Rule4Valuation(config)
        result = rule.evaluate({
            "close": 20,
            "pe": 8,
            "market_cap": 30e9,
        })
        assert result is False

    def test_pe_too_high(self, config):
        """测试PE过高"""
        rule = Rule4Valuation(config)
        result = rule.evaluate({
            "close": 8,
            "pe": 20,
            "market_cap": 30e9,
        })
        assert result is False

    def test_market_cap_too_high(self, config):
        """测试市值过高"""
        rule = Rule4Valuation(config)
        result = rule.evaluate({
            "close": 8,
            "pe": 8,
            "market_cap": 100e9,
        })
        assert result is False


# ============================================================
# 第5层：基本面测试
# ============================================================

class TestRule5Fundamental:
    def test_fundamental_pass(self, config):
        """测试基本面条件通过"""
        rule = Rule5Fundamental(config)
        result = rule.evaluate({
            "debt_ratio": 0.4,
            "insider_buy": 1,
            "analyst_cover": 0,
        })
        assert result is True

    def test_high_debt(self, config):
        """测试负债过高"""
        rule = Rule5Fundamental(config)
        result = rule.evaluate({
            "debt_ratio": 0.8,
            "insider_buy": 1,
            "analyst_cover": 0,
        })
        assert result is False

    def test_no_insider_buy(self, config):
        """测试无内部人买入"""
        rule = Rule5Fundamental(config)
        result = rule.evaluate({
            "debt_ratio": 0.4,
            "insider_buy": 0,
            "analyst_cover": 0,
        })
        assert result is False


# ============================================================
# 规则引擎集成测试
# ============================================================

class TestRuleEngine:
    def test_engine_initialization(self, engine):
        """测试规则引擎初始化"""
        assert engine.rule1 is not None
        assert engine.rule2 is not None
        assert engine.rule3 is not None
        assert engine.rule4 is not None
        assert engine.rule5 is not None

    def test_run_with_mock_data(self, engine, mock_data):
        """测试使用模拟数据运行规则引擎"""
        results = engine.run(mock_data)
        assert len(results) == 10
        assert "label" in results.columns
        assert "rule1_trend" in results.columns
        assert "rule2_volume_break" in results.columns
        assert "rule3_buy_point" in results.columns
        assert "rule4_valuation" in results.columns
        assert "rule5_fundamental" in results.columns

    def test_classify_buy_signal(self):
        """测试分类：上升交易（买点）"""
        r1 = {"long": True, "strong": True, "short": False, "weak": False}
        label = RuleEngine.classify(r1, True, True, True, True)
        assert label == "上升交易（买点）"

    def test_classify_watch_signal(self):
        """测试分类：潜在实力股（观察）"""
        r1 = {"long": True, "strong": True, "short": False, "weak": False}
        label = RuleEngine.classify(r1, False, False, True, True)
        assert label == "潜在实力股（观察）"

    def test_classify_avoid_signal(self):
        """测试分类：下跌参考（警示）"""
        r1 = {"long": False, "strong": False, "short": True, "weak": True}
        label = RuleEngine.classify(r1, False, False, False, False)
        assert label == "下跌参考（警示）"

    def test_classify_wait_signal(self):
        """测试分类：观望"""
        r1 = {"long": True, "strong": False, "short": False, "weak": True}
        label = RuleEngine.classify(r1, False, False, False, False)
        assert label == "观望"

    def test_mock_data_potential_signals(self, engine, mock_data):
        """测试模拟数据中是否有潜在实力股信号"""
        results = engine.run(mock_data)
        watch_signals = results[results["label"] == "潜在实力股（观察）"]
        # 000001 应该产生潜在实力股信号（多头+低估值+好基本面）
        assert len(watch_signals) > 0

    def test_mock_data_avoid_signals(self, engine, mock_data):
        """测试模拟数据中是否有警示信号"""
        results = engine.run(mock_data)
        avoid_signals = results[results["label"] == "下跌参考（警示）"]
        # 000002 应该产生警示信号
        assert len(avoid_signals) > 0