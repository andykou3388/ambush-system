class Rule4Valuation:
    """第4层：价格与估值规则"""

    def __init__(self, config: dict):
        self.cfg = config["price_valuation"]

    def evaluate(self, row: dict) -> bool:
        """
        评估价格与估值是否在合理范围内

        条件：
        1. 股价 < max_price（默认15元）
        2. PE < max_pe（默认10倍）
        3. 市值 < max_market_cap（默认50亿）

        Args:
            row: 包含 close, pe, market_cap 的数据行

        Returns:
            True 表示符合价格与估值条件
        """
        price_cfg = self.cfg

        # 處理 None 值：如果欄位為 None，視為不符合條件
        close = row.get("close")
        if close is None:
            cond1 = False
        else:
            cond1 = close < price_cfg["max_price"]

        pe = row.get("pe")
        if pe is None:
            cond2 = False
        else:
            cond2 = pe < price_cfg["max_pe"]

        market_cap = row.get("market_cap")
        if market_cap is None:
            cond3 = False
        else:
            cond3 = market_cap < price_cfg["max_market_cap"]

        return cond1 and cond2 and cond3
