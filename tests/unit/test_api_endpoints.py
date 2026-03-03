import pytest


def test_recommend_success(client):
    """Happy Path: Standard search should return 200 and mocked results."""
    response = client.post("/recommend", json={"text": "red dress", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "vector_db"
    assert len(data["results"]) > 0
    assert data["results"][0]["product_name"] == "Test Red Dress"


def test_recommend_validation_error(client):
    """Edge Case: Input too short (min_length=2 in app.py)."""
    response = client.post("/recommend", json={"text": "a", "top_k": 3})
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation)


def test_recommend_invalid_top_k(client):
    """Edge Case: top_k out of range (ge=1, le=20)."""
    response = client.post("/recommend", json={"text": "blue jeans", "top_k": 100})
    assert response.status_code == 422


def test_home_endpoint(client):
    """Contract: Health check endpoint should always work."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
