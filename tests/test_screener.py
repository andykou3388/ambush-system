import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_screen_stocks_basic():
    """測試基本篩選功能"""
    response = client.get("/api/v1/screener/stocks")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "items" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["page_size"], int)
    assert isinstance(data["items"], list)

def test_screen_stocks_zone_filter():
    """測試區域過濾功能"""
    response = client.get("/api/v1/screener/stocks", params={"zone": "buy"})
    assert response.status_code == 200
    data = response.json()
    # 確保返回的都是買入區股票
    for item in data["items"]:
        assert item["zone"] == "buy"

def test_screen_stocks_price_filter():
    """測試價格過濾功能"""
    response = client.get("/api/v1/screener/stocks", params={"min_price": 100, "max_price": 500})
    assert response.status_code == 200
    data = response.json()
    # 確保返回的股票價格都在範圍內
    for item in data["items"]:
        assert 100 <= item["price"] <= 500

def test_screen_stocks_pagination():
    """測試分頁功能"""
    response = client.get("/api/v1/screener/stocks", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5

def test_screen_stocks_invalid_page():
    """測試無效頁碼"""
    response = client.get("/api/v1/screener/stocks", params={"page": 0})
    assert response.status_code == 422  # 驗證錯誤

if __name__ == "__main__":
    pytest.main([__file__])
