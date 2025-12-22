import pytest
from unittest.mock import patch, MagicMock
from src.pipelines.inference_pipeline import InferencePipeline


@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_pipeline_initialization(mock_sentence_transformer, mock_qdrant_client):
    """
    Test: Pipeline Initialization Objective: Are there any errors while loading Qdrant and Model?
    """
    # Set mock objects
    mock_qdrant_instance = MagicMock()
    mock_qdrant_client.return_value = mock_qdrant_instance

    # Start the pipeline
    pipeline = InferencePipeline()

    # Check if Model and Client were called.
    mock_qdrant_client.assert_called()
    mock_sentence_transformer.assert_called()
    assert pipeline.client == mock_qdrant_instance


@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_search_logic(mock_sentence_transformer, mock_qdrant_client):
    """
    Test: Lookup Function
    Purpose: Is the given text converted to a vector and queried in Qdrant?
    """
    # 1. Setup Mocks
    pipeline = InferencePipeline()

    mock_vector = MagicMock()
    mock_vector.tolist.return_value = [0.1, 0.2, 0.3]
    pipeline.encoder.encode.return_value = mock_vector

    # Qdrant mock: Return a fake search result.
    mock_hit = MagicMock()
    mock_hit.score = 0.88
    mock_hit.payload = {"prod_name": "Test Item", "detail_desc": "Desc"}
    pipeline.client.search.return_value = [mock_hit]

    # 2. Action
    results = pipeline.search_products("running shoes", top_k=2)

    # 3. Assertions
    assert len(results) == 1
    assert results[0]["product_name"] == "Test Item"
    assert results[0]["score"] == 0.88