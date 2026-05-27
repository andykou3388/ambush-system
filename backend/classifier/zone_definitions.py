# 三區分類定義與邊界條件
# CORE-03 - 買入區 / 持有區 / 賣出區


class ZoneDefinitions:
    # 分區標籤
    ZONE_BUY = "買入區"
    ZONE_HOLD = "持有區"
    ZONE_SELL = "賣出區"

    # 規則引擎對應標籤
    RULE_UP = "上升交易（買點）"
    RULE_POTENTIAL = "潛在實力股（觀察）"
    RULE_DOWN = "下跌參考（警示）"
    RULE_WAIT = "觀望"

    # 置信度區間
    CONFIDENCE_HIGH = (0.8, 1.0)
    CONFIDENCE_MID = (0.6, 0.8)
    CONFIDENCE_LOW = (0.0, 0.6)

    @staticmethod
    def get_zone_explanation(zone: str) -> str:
        """返回分區說明文字（給前端展示）"""
        mapping = {
            ZoneDefinitions.ZONE_BUY: "符合超級強勢股條件，強勢上漲，可執行買入",
            ZoneDefinitions.ZONE_HOLD: "趨勢穩健或具潛力，建議觀察或繼續持有",
            ZoneDefinitions.ZONE_SELL: "趨勢轉弱或出現風險，建議減倉或離場",
        }
        return mapping.get(zone, "無分類")
