import os
import yaml
import pandas as pd
from typing import Optional

from .rules import (
    Rule1Trend,
    Rule2Volume,
    Rule3BuyPoint,
    Rule4Valuation,
    Rule5Fundamental,
)


class RuleEngine:
    """规则引擎 V1 - 5层规则筛选"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config.yaml"
            )
        with open(config_path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

        # 初始化5层规则
        self.rule1 = Rule1Trend(self.cfg)
        self.rule2 = Rule2Volume(self.cfg)
        self.rule3 = Rule3BuyPoint(self.cfg)
        self.rule4 = Rule4Valuation(self.cfg)
        self.rule5 = Rule5Fundamental(self.cfg)

    # ------------------------------
    # 第1层：趋势规则
    # ------------------------------
    def evaluate_rule1(self, row: dict) -> dict:
        """评估趋势状态"""
        return self.rule1.evaluate(row)

    # ------------------------------
    # 第2层：成交量放量突破
    # ------------------------------
    def evaluate_rule2(self, row: dict, vol_ma5: float = None) -> bool:
        """评估成交量是否异常放量"""
        return self.rule2.evaluate(row, vol_ma5)

    # ------------------------------
    # 第3层：低风险买点（回踩MA10）
    # ------------------------------
    def evaluate_rule3(self, row: dict) -> bool:
        """评估是否为低风险买点"""
        return self.rule3.evaluate(row)

    # ------------------------------
    # 第4层：价格+估值
    # ------------------------------
    def evaluate_rule4(self, row: dict) -> bool:
        """评估价格与估值"""
        return self.rule4.evaluate(row)

    # ------------------------------
    # 第5层：基本面
    # ------------------------------
    def evaluate_rule5(self, row: dict) -> bool:
        """评估基本面条件"""
        return self.rule5.evaluate(row)

    # ------------------------------
    # 三分类输出
    # ------------------------------
    @staticmethod
    def classify(r1: dict, r2: bool, r3: bool, r4: bool, r5: bool) -> str:
        """
        根据5层规则结果输出三分类信号

        分类逻辑：
        - 上升交易（买点）：多头 + 强势 + 放量 + 回踩 + 低估值 + 好基本面
        - 潜在实力股（观察）：多头 + 低估值 + 好基本面（但未放量或未回踩）
        - 下跌参考（警示）：空头或弱势
        - 观望：其他情况
        """
        is_long = r1.get("long", False)
        is_strong = r1.get("strong", False)
        is_short = r1.get("short", False)
        is_weak = r1.get("weak", False)

        # 上升交易（买点）：所有条件都满足
        if is_long and is_strong and r2 and r3 and r4 and r5:
            return "上升交易（买点）"

        # 潜在实力股（观察）：多头 + 低估值 + 好基本面
        if is_long and r4 and r5:
            return "潜在实力股（观察）"

        # 下跌参考（警示）：空头（close < ma10）
        if is_short:
            return "下跌参考（警示）"

        return "观望"

    # ------------------------------
    # 从 ORM 对象执行规则引擎
    # ------------------------------
    def run_from_db(self, bar: 'StockBar', fund: 'StockFundamental' = None) -> dict:
        """
        從 ORM 物件執行規則引擎

        Args:
            bar: StockBar ORM 物件（需包含 code, trade_date, close, ma10_w, ma30_w, volume）
            fund: StockFundamental ORM 物件（可選，需包含 pe_ttm, eps_ttm, float_shares, debt_ratio, insider_net_buy_3m）

        Returns:
            規則引擎結果（含各層規則狀態）
        """
        row = {
            "code": bar.code,
            "datetime": bar.trade_date.isoformat() if hasattr(bar.trade_date, 'isoformat') else str(bar.trade_date),
            "close": float(bar.close) if bar.close else 0,
            "ma10": float(bar.ma10_w) if bar.ma10_w else 0,
            "ma30": float(bar.ma30_w) if bar.ma30_w else 0,
            "volume": float(bar.volume) if bar.volume else 0,
            "vol_ma5": float(bar.volume_ma5_w) if bar.volume_ma5_w else 0,
            "pe": float(fund.pe_ttm) if fund and fund.pe_ttm else None,
            "market_cap": (float(fund.float_shares) * float(bar.close)) if fund and fund.float_shares and bar.close else None,
            "debt_ratio": float(fund.debt_ratio) if fund and fund.debt_ratio else None,
            "insider_buy": float(fund.insider_net_buy_3m) if fund and fund.insider_net_buy_3m else 0,
        }

        # 執行 5 層規則
        r1 = self.evaluate_rule1(row)
        r2 = self.evaluate_rule2(row, float(bar.volume_ma5_w) if bar.volume_ma5_w else 0)
        r3 = self.evaluate_rule3(row)
        r4 = self.evaluate_rule4(row)
        r5 = self.evaluate_rule5(row)

        # 分類
        label = self.classify(r1, r2, r3, r4, r5)

        return {
            "code": bar.code,
            "datetime": row["datetime"],
            "label": label,
            "rule1_trend": r1,
            "rule2_volume_break": r2,
            "rule3_buy_point": r3,
            "rule4_valuation": r4,
            "rule5_fundamental": r5,
        }

    # ------------------------------
    # 总引擎：按优先级执行全部5层
    # ------------------------------
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对输入的DataFrame执行全部5层规则

        Args:
            df: 包含以下字段的DataFrame
                - code, datetime, close, ma10, ma30, volume
                - pe, market_cap, debt_ratio, insider_buy, analyst_cover
                - 可选: week_high, week_low

        Returns:
            包含每层规则结果和最终分类标签的DataFrame
        """
        results = []

        # 计算5日均量
        if "volume" in df.columns:
            vol_ma5_series = df["volume"].rolling(5).mean().fillna(0)
        else:
            vol_ma5_series = pd.Series([0] * len(df))

        for idx, row in df.iterrows():
            row_dict = row.to_dict()

            # 执行5层规则
            r1 = self.evaluate_rule1(row_dict)
            r2 = self.evaluate_rule2(row_dict, vol_ma5_series.iloc[idx])
            r3 = self.evaluate_rule3(row_dict)
            r4 = self.evaluate_rule4(row_dict)
            r5 = self.evaluate_rule5(row_dict)

            # 分类
            label = self.classify(r1, r2, r3, r4, r5)

            results.append(
                {
                    "code": row_dict.get("code", ""),
                    "datetime": row_dict.get("datetime", ""),
                    "close": row_dict.get("close", 0),
                    "ma10": row_dict.get("ma10", 0),
                    "ma30": row_dict.get("ma30", 0),
                    "volume": row_dict.get("volume", 0),
                    "rule1_trend": r1,
                    "rule2_volume_break": r2,
                    "rule3_buy_point": r3,
                    "rule4_valuation": r4,
                    "rule5_fundamental": r5,
                    "label": label,
                }
            )

        return pd.DataFrame(results)