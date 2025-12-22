import pytest
from unittest.mock import patch


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
    Scenario: User sends valid text.
    Expected: 200 OKs and a list of results.
    """
    # We're mocking Pipeline and Redis (so it doesn't make a real connection).
    with patch("src.api.app.ml_pipeline") as mock_pipeline:
        # We are setting what the pipeline will return.
        mock_pipeline.search_products.return_value = [
            {"product_name": "Mock Dress", "score": 0.99}
        ]

        payload = {"text": "Red dress", "top_k": 3}
        response = client.post("/recommend", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert data["results"][0]["product_name"] == "Mock Dress"


def test_recommend_endpoint_invalid_input(client):
    """
    Test: POST /recommend (Invalid Input)
    Scenario: User sends a very short text.
    Expected: 422 Unprocessable Entity (Validation Error).
    """
    payload = {"text": "a", "top_k": 5}
    response = client.post("/recommend", json=payload)

    assert response.status_code == 422