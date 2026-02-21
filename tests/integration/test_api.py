from unittest.mock import patch
from unittest.mock import patch, AsyncMock

import pytest


def test_home_endpoint(client):
    """
    Test: GET / (Homepage)
    Expected: 200 OK and "alive" message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_recommend_endpoint_success(client):
    """
    Test: POST /recommend (Successful Search)
    """
    with patch("src.api.app.ml_pipeline") as mock_pipeline:
        mock_pipeline.search_products.return_value = [
            {"product_name": "Mock Dress", "score": 0.99}
        ]

        with patch("src.api.app.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock(return_value=True)

            payload = {"text": "Red dress", "top_k": 3}
            response = client.post("/recommend", json=payload)

            assert response.status_code == 200


def test_recommend_endpoint_invalid_input(client):
    """
    Test: POST /recommend (Invalid Input)
    Scenario: User sends a very short text.
    Expected: 422 Unprocessable Entity (Validation Error).
    """
    payload = {"text": "a", "top_k": 5}
    response = client.post("/recommend", json=payload)

    assert response.status_code == 422
