import os
import sys
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.app import app


# 1. Mock Pipeline Fixture
@pytest.fixture
def mock_pipeline_instance():
    """
    Bu, Pipeline SINIFININ üreteceği sahte NESNE (Instance).
    """
    mock_instance = MagicMock()
    mock_instance.search_products.return_value = [
        {
            "score": 0.95,
            "product_name": "Test Red Dress",
            "description": "A beautiful red dress",
            "category": "Dresses",
            "details": {"product_type_name": "Dress"},
            "image_url": "http://example.com/image.jpg"
        }
    ]
    return mock_instance


# 2. Test Client Fixture
@pytest.fixture
def client(mock_pipeline_instance):
    with patch("src.api.app.InferencePipeline") as MockPipelineClass:
        MockPipelineClass.return_value = mock_pipeline_instance

        with patch("src.api.app.redis.Redis"):
            with TestClient(app) as c:
                yield c