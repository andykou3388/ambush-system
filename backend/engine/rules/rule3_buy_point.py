class Rule3BuyPoint:
    """第3层：低风险买点规则（回踩10周均线）"""

    def __init__(self, config: dict):
        self.cfg = config["buy_point"]

    def evaluate(self, row: dict) -> bool:
        """
        评估是否为低风险买点

        条件：
        1. 收盘价在 MA10 附近（允许 tolerance 误差）
        2. 成交量缩量至 50% 以下
        3. 周波幅 <= 4%（窄幅整理）

        Args:
            row: 包含 close, ma10, volume, vol_ma5, week_high, week_low 的数据行

        Returns:
            True 表示符合低风险买点条件
        """
        close = float(row.get("close", 0))
        ma10 = float(row.get("ma10", 0))

        if ma10 <= 0:
            return False

        # 条件1：收盘价在 MA10 附近（允许 tolerance 误差）
        tol = float(self.cfg["touch_ma10_tolerance"])
        touch_ma10 = (close >= ma10 * (1 - tol)) and (close <= ma10 * (1 + tol))

        # 条件2：成交量缩量至 50% 以下
        volume = float(row.get("volume", 0))
        vol_ma5 = row.get("vol_ma5", 0)
        # 確保型別為 float（避免 Decimal * float 錯誤）
        vol_ma5 = float(vol_ma5) if vol_ma5 else 0.0
        volume_shrink = True
        if vol_ma5 > 0:
            min_vol_ratio = float(self.cfg["min_volume_ratio"])
            volume_shrink = volume <= vol_ma5 * min_vol_ratio

        # 条件3：周波幅 <= 4%（窄幅整理）
        week_high = float(row.get("week_high", close))
        week_low = float(row.get("week_low", close))
        week_range = (week_high - week_low) / (week_low if week_low > 0 else 1)
        narrow_range = week_range <= float(self.cfg["narrow_range_ratio"])

        return touch_ma10 and volume_shrink and narrow_range
