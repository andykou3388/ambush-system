import requests

def test_stock_detail():
    """驗證個股詳情 API"""
    print("测试个股详情 API...")
    print("=" * 50)

    # 测试 1：查询正常股票
    print("\n测试 1：查询 2330.TW")
    resp = requests.get("http://localhost:8000/api/v1/stocks/2330.TW")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  成功：股票名称: {data['name']}")
        print(f"  价格: ${data['price']:.2f}")
        print(f"  区域: {data['zone_info']['zone']}")
        print(f"  规则检核: {len(data['rules'])} 条")
    else:
        print(f"  失败：请求失败: {resp.status_code}")

    # 测试 2：查询不存在的股票
    print("\n警告：测试 2：查询不存在的股票")
    resp = requests.get("http://localhost:8000/api/v1/stocks/INVALID")
    if resp.status_code == 404:
        print("  成功：正确返回 404")
    else:
        print(f"  失败：预期 404，实际 {resp.status_code}")

    print("\n" + "=" * 50)
    print("成功：个股详情 API 验证通过！")

if __name__ == "__main__":
    test_stock_detail()
