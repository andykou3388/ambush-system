# 單元測試 CORE-03 三區分類器
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from classifier.zone_classifier import ThreeZoneClassifier


def test_zone_buy():
    out = {
        "code": "TEST1",
        "label": "上升交易（買點）",
        "rule1": {"long": True, "strong": True},
        "rule2": True,
        "rule4": True,
    }
    c = ThreeZoneClassifier()
    res = c.classify_stock(out)
    assert res["zone"] == "買入區"
    assert res["confidence"] >= 0.8
    assert res["explanation"] == "符合超級強勢股條件，強勢上漲，可執行買入"


def test_zone_sell():
    out = {
        "code": "TEST2",
        "label": "下跌參考（警示）",
        "rule1": {"short": True},
        "rule2": False,
        "rule4": False,
    }
    c = ThreeZoneClassifier()
    res = c.classify_stock(out)
    assert res["zone"] == "賣出區"
    assert res["confidence"] == 0.0


def test_zone_hold():
    out = {
        "code": "TEST3",
        "label": "潛在實力股（觀察）",
        "rule1": {"long": True},
        "rule2": False,
        "rule4": True,
    }
    c = ThreeZoneClassifier()
    res = c.classify_stock(out)
    assert res["zone"] == "持有區"
    assert res["confidence"] >= 0.2


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
