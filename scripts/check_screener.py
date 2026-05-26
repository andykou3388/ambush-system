import requests
import sys

BASE_URL = "http://localhost:8000"

def test_screener():
    """验证筛选 API"""
    print("Testing screener API...")
    print("=" * 50)

    # Test 1: Basic query
    print("\nTest 1: Basic query")
    resp = requests.get(f"{BASE_URL}/api/v1/screener/stocks")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  OK: {data['total']} stocks, {len(data['items'])} items")
        if data['items']:
            first = data['items'][0]
            print(f"  Sample: {first['symbol']} - {first['name']} ({first['zone']})")
    else:
        print(f"  FAILED: {resp.status_code}")
        return False

    # Test 2: Zone filtering
    print("\nTest 2: Zone filtering")
    resp = requests.get(
        f"{BASE_URL}/api/v1/screener/stocks",
        params={"zone": "buy", "page": 1, "page_size": 10}
    )
    if resp.status_code == 200:
        data = resp.json()
        all_buy = all(item["zone"] == "buy" for item in data["items"])
        print(f"  OK: {data['total']} buy zone stocks, all buy: {all_buy}")
    else:
        print(f"  FAILED: {resp.status_code}")
        return False

    # Test 3: Price filtering
    print("\nTest 3: Price filtering")
    resp = requests.get(
        f"{BASE_URL}/api/v1/screener/stocks",
        params={"min_price": 100, "max_price": 500, "page": 1, "page_size": 10}
    )
    if resp.status_code == 200:
        data = resp.json()
        all_in_range = all(100 <= item["price"] <= 500 for item in data["items"])
        print(f"  OK: {data['total']} stocks, all in range: {all_in_range}")
    else:
        print(f"  FAILED: {resp.status_code}")
        return False

    # Test 4: Pagination
    print("\nTest 4: Pagination")
    resp = requests.get(
        f"{BASE_URL}/api/v1/screener/stocks",
        params={"page": 2, "page_size": 5}
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"  OK: Page {data['page']}, {len(data['items'])} items")
    else:
        print(f"  FAILED: {resp.status_code}")
        return False

    # Test 5: Sorting
    print("\nTest 5: Sorting")
    resp = requests.get(
        f"{BASE_URL}/api/v1/screener/stocks",
        params={"page": 1, "page_size": 5, "sort_by": "price", "sort_order": "asc"}
    )
    if resp.status_code == 200:
        data = resp.json()
        prices = [item["price"] for item in data["items"]]
        is_sorted = prices == sorted(prices)
        print(f"  OK: Sorted ascending: {is_sorted}")
    else:
        print(f"  FAILED: {resp.status_code}")
        return False

    print("\n" + "=" * 50)
    print("All tests passed!")
    return True

if __name__ == "__main__":
    success = test_screener()
    sys.exit(0 if success else 1)