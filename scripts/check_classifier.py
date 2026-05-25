# 驗證腳本：比對分類器結果與人工判斷
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

import pandas as pd
from backend.engine.rule_engine import RuleEngine
from classifier.zone_classifier import ThreeZoneClassifier


def run_verify():
    # 測試數據（10只標的）
    data = [
        ["000001", 8.5, 8.2, 7.8, 50000, 9, 40e9, 0.5, 1, 0],
        ["000002", 12, 11.5, 13, 20000, 15, 60e9, 0.7, 0, 1],
        ["000003", 5.5, 5.7, 6.0, 15000, 8, 20e9, 0.45, 1, 0],
        ["000004", 18, 17, 16, 80000, 12, 80e9, 0.65, 0, 1],
        ["000005", 7.2, 7.1, 6.9, 45000, 7, 30e9, 0.4, 1, 0],
        ["000006", 9.5, 9.8, 10, 25000, 11, 55e9, 0.62, 0, 1],
        ["000007", 6.8, 6.7, 6.5, 60000, 8, 25e9, 0.42, 1, 0],
        ["000008", 22, 20, 19, 70000, 18, 120e9, 0.7, 0, 1],
        ["000009", 4.9, 4.8, 4.7, 38000, 6, 15e9, 0.38, 1, 0],
        ["000010", 14, 13.5, 14.2, 32000, 9, 48e9, 0.55, 1, 0],
    ]

    df = pd.DataFrame(
        data,
        columns=[
            "code",
            "close",
            "ma10",
            "ma30",
            "volume",
            "pe",
            "market_cap",
            "debt_ratio",
            "insider_buy",
            "analyst_cover",
        ],
    )

    engine = RuleEngine(os.path.join(ROOT_DIR, "backend", "engine", "config.yaml"))
    rule_result = engine.run(df)

    classifier = ThreeZoneClassifier()
    final = classifier.classify_batch(rule_result)

    print("=" * 60)
    print("CORE-03 三區分類器 驗證報告")
    print("=" * 60)
    print(final[["code", "rule_label", "zone", "confidence", "explanation"]].to_string(index=False))

    final.to_csv(
        os.path.join(ROOT_DIR, "classifier_verify_report.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    print("\n報告已輸出：classifier_verify_report.csv")


if __name__ == "__main__":
    run_verify()
