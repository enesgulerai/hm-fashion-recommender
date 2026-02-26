import json
from unittest.mock import AsyncMock, patch

import pytest


# --- TEST 1: Basic Health Check ---
def test_home_endpoint(client):
    """
    Test: GET / (Homepage)
    Expected: The system must prove it is up and running for K8s Liveness/Readiness rehearsals.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


# --- TEST 2: Cache Miss ---
@patch("src.api.app.redis_client")
@patch("src.api.app.ml_pipeline")
def test_recommend_endpoint_cache_miss(mock_pipeline, mock_redis, client):
    """
    Test: POST /recommend (No data in Redis, go to Qdrant)
    Expected: ML pipeline should be called, result should be written to Redis and return 200.
    """
    # 1. Mock Settings
    mock_redis.get = AsyncMock(return_value=None)  # There is no data on Redis.
    mock_redis.setex = AsyncMock(return_value=True)

    expected_result = [{"product_name": "Mock Dress", "score": 0.99}]
    mock_pipeline.search_products.return_value = expected_result

    # 2. Post Request
    payload = {"text": "Red dress", "top_k": 3}
    response = client.post("/recommend", json=payload)

    # 3. Assertions
    assert response.status_code == 200
    assert response.json() == expected_result  # Is the incoming data accurate?

    # Test the system's behavior:
    mock_pipeline.search_products.assert_called_once()
    mock_redis.setex.assert_called_once()


# --- TEST 3: Cache Hit ---
@patch("src.api.app.redis_client")
@patch("src.api.app.ml_pipeline")
def test_recommend_endpoint_cache_miss(mock_pipeline, mock_redis, client):
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)

    expected_result = [{"product_name": "Mock Dress", "score": 0.99}]
    mock_pipeline.search_products.return_value = expected_result

    payload = {"text": "Red dress", "top_k": 3}
    response = client.post("/recommend", json=payload)

    assert response.status_code == 200
    assert response.json()["results"] == expected_result

    mock_pipeline.search_products.assert_called_once()
    mock_redis.setex.assert_called_once()


# --- TEST 4: Validation ---
def test_recommend_endpoint_invalid_input(client):
    """
    Test: POST /recommend (Invalid Request)
    Expected: FastAPI's Pydantic model should throw a 422 error.
    """
    payload = {"text": "a", "top_k": 5}
    response = client.post("/recommend", json=payload)
    assert response.status_code == 422


# --- TEST 5: Graceful Degradation ---
@patch("src.api.app.redis_client")
@patch("src.api.app.ml_pipeline")
def test_recommend_endpoint_backend_failure(mock_pipeline, mock_redis, client):
    mock_redis.get = AsyncMock(return_value=None)
    mock_pipeline.search_products.side_effect = Exception("Qdrant connection lost")

    payload = {"text": "Red dress", "top_k": 3}
    response = client.post("/recommend", json=payload)

    assert response.status_code == 500
    assert "detail" in response.json()
