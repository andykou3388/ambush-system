import pandas as pd

from classifier.zone_definitions import ZoneDefinitions


class ThreeZoneClassifier:
    def __init__(self):
        self.defs = ZoneDefinitions()

    def classify_stock(self, rule_output: dict) -> dict:
        """
        單隻股票分類：買入區 / 持有區 / 賣出區
        :param rule_output: CORE-02 規則引擎輸出
        :return: 分類結果 + 置信度 + 說明
        """
        label = rule_output.get("label", "")
        rule1 = rule_output.get("rule1", {})
        rule2 = rule_output.get("rule2", False)
        rule4 = rule_output.get("rule4", False)

        # ====================== 三區分類邏輯 ======================
        if label == self.defs.RULE_UP:
            zone = self.defs.ZONE_BUY
        elif label == self.defs.RULE_DOWN:
            zone = self.defs.ZONE_SELL
        elif label in [self.defs.RULE_POTENTIAL, self.defs.RULE_WAIT]:
            zone = self.defs.ZONE_HOLD
        else:
            zone = self.defs.ZONE_HOLD

        # ====================== 置信度計算 ======================
        confidence = self._calc_confidence(label, rule1, rule2, rule4)

        # ====================== 說明文字 ======================
        explanation = self.defs.get_zone_explanation(zone)

        return {
            "code": rule_output.get("code", ""),
            "datetime": rule_output.get("datetime", ""),
            "rule_label": label,
            "zone": zone,
            "confidence": round(confidence, 2),
            "explanation": explanation,
        }

    def _calc_confidence(self, label, rule1, rule2, rule4) -> float:
        """
        置信度公式：
        置信度 = (符合條件數 / 總條數) * 0.8 + (信號強度) * 0.2
        """
        score = 0.0
        total = 4

        if isinstance(rule1, dict):
            if rule1.get("long", False):
                score += 1
            if rule1.get("strong", False):
                score += 1
        if rule2:
            score += 1
        if rule4:
            score += 1

        rule_strength = 1.0 if label == self.defs.RULE_UP else \
                        0.7 if label == self.defs.RULE_POTENTIAL else \
                        0.3 if label == self.defs.RULE_WAIT else 0.0

        confidence = (score / total) * 0.8 + rule_strength * 0.2
        return round(min(confidence, 1.0), 2)

    def classify_batch(self, df_rules: pd.DataFrame) -> pd.DataFrame:
        """
        批量分類（整個股票列表）
        """
        results = []
        for _, row in df_rules.iterrows():
            rule_out = row.to_dict()
            classified = self.classify_stock(rule_out)
            results.append(classified)
        return pd.DataFrame(results)
