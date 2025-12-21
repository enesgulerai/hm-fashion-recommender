import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# 1. Proje ana dizinini Python yoluna ekle (Import hatası almamak için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.app import app

# 2. Test Client Fixture
@pytest.fixture
def client():
    """
    FastAPI uygulaması için bir Test Client oluşturur.
    """
    return TestClient(app)

# 3. Mock Pipeline Fixture (Yapay Zeka'yı Taklit Etme)
@pytest.fixture
def mock_pipeline():
    """
    Gerçek Qdrant ve AI modelini yüklemek yerine,
    sahte (mock) bir pipeline döndürür. Böylece testler hızlı çalışır.
    """
    mock = MagicMock()
    # search_products fonksiyonu çağrıldığında dönecek sahte cevap
    mock.search_products.return_value = [
        {
            "score": 0.95,
            "product_name": "Test Red Dress",
            "description": "A beautiful red dress",
            "category": "Dresses",
            "details": {"product_type_name": "Dress"}
        }
    ]
    return mock