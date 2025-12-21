import pytest
from unittest.mock import patch


def test_home_endpoint(client):
    """
    Test: GET / (Ana Sayfa)
    Beklenen: 200 OK ve "alive" mesajı.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_recommend_endpoint_success(client):
    """
    Test: POST /recommend (Başarılı Arama)
    Senaryo: Kullanıcı geçerli bir metin yollar.
    Beklenen: 200 OK ve sonuç listesi.
    """
    # Pipeline'ı ve Redis'i mockluyoruz (Gerçek bağlantı yapmasın)
    with patch("src.api.app.ml_pipeline") as mock_pipeline:
        # Pipeline'ın ne döndüreceğini ayarlıyoruz
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
    Test: POST /recommend (Hatalı Giriş)
    Senaryo: Kullanıcı çok kısa bir metin yollar.
    Beklenen: 422 Unprocessable Entity (Validation Error).
    """
    # 2 karakterden kısa metin yasak
    payload = {"text": "a", "top_k": 5}
    response = client.post("/recommend", json=payload)

    assert response.status_code == 422