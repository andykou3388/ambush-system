class Rule1Trend:
    """第1层：趋势判断规则（MA10 与 MA30 位置关系）"""

    def __init__(self, config: dict):
        self.cfg = config["trend"]

    def evaluate(self, row: dict) -> dict:
        """
        评估趋势状态

        Args:
            row: 包含 close, ma10, ma30 的数据行

        Returns:
            {
                "long": bool,    # 多头：close > ma10
                "strong": bool,  # 强势：close > ma30
                "short": bool,   # 空头：close < ma10
                "weak": bool     # 弱势：close < ma30
            }
        """
        close = row.get("close", 0)
        ma10 = row.get("ma10", 0)
        ma30 = row.get("ma30", 0)
        
        # 處理 None 值和非數值類型
        if close is None:
            close = 0
        else:
            close = float(close)
            
        if ma10 is None:
            ma10 = 0
        else:
            ma10 = float(ma10)
            
        if ma30 is None:
            ma30 = 0
        else:
            ma30 = float(ma30)

        return {
            "long": close > ma10,
            "strong": close > ma30,
            "short": close < ma10,
            "weak": close < ma30,
        }
