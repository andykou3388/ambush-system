class Rule2Volume:
    """第2层：成交量异常规则（成交量突增判断）"""

    def __init__(self, config: dict):
        self.cfg = config["volume"]

    def evaluate(self, row: dict, vol_ma5: float = None) -> bool:
        """
        评估成交量是否异常放量

        Args:
            row: 包含 volume 的数据行
            vol_ma5: 5日均量（由外部计算传入）

        Returns:
            True 表示成交量异常放量（>= 5倍均量）
        """
        vol_current = row.get("volume", 0)

        # 如果没有传入 vol_ma5，尝试从 row 中获取
        if vol_ma5 is None:
            vol_ma5 = row.get("vol_ma5", 0)

        if vol_ma5 <= 0:
            return False

        ratio = self.cfg["volume_boost_ratio"]
        return vol_current >= vol_ma5 * ratio