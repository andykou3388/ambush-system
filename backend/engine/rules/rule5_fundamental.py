class Rule5Fundamental:
    """第5层：基本面辅助规则"""

    def __init__(self, config: dict):
        self.cfg = config["fundamental"]

    def evaluate(self, row: dict) -> bool:
        """
        评估基本面条件

        条件：
        1. 负债比 < low_debt_ratio（默认60%）
        2. 内部人买入 = 1（有内部人买入）
        3. 无分析师覆盖

        Args:
            row: 包含 debt_ratio, insider_buy, analyst_cover 的数据行

        Returns:
            True 表示符合基本面条件
        """
        fund_cfg = self.cfg

        # 處理 debt_ratio 為 None 的情況
        debt_ratio = row.get("debt_ratio")
        if debt_ratio is None:
            cond1 = True  # 如果沒有負債比數據，視為符合條件
        else:
            cond1 = debt_ratio < fund_cfg["low_debt_ratio"]
            
        cond2 = row.get("insider_buy", 0) == 1
        cond3 = row.get("analyst_cover", 1) == 0

        return cond1 and cond2 and cond3
