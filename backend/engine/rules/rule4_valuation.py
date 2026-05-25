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

        cond1 = row.get("close", 999) < price_cfg["max_price"]
        cond2 = row.get("pe", 999) < price_cfg["max_pe"]
        cond3 = row.get("market_cap", 9e9) < price_cfg["max_market_cap"]

        return cond1 and cond2 and cond3