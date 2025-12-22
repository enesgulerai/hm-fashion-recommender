import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.app import app

# 2. Test Client Fixture
@pytest.fixture
def client():
    """
    Creates a Test Client for the FastAPI application.
    """
    return TestClient(app)

# 3. Mock Pipeline Fixture
@pytest.fixture
def mock_pipeline():
    """
    Instead of loading the real Qdrant and AI model, it returns a mock pipeline.
    This allows tests to run faster.
    """
    mock = MagicMock()
    # a fake answer that will be returned when the search_products function is called
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