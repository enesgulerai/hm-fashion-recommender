from unittest.mock import MagicMock, patch

import pytest

from src.pipelines.inference_pipeline import InferencePipeline


# --- TEST 1: Initialization Verification ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_pipeline_initialization(mock_encoder, mock_qdrant):
    """
    Test: Pipeline Initialization
    Expected: The Model and Qdrant Client should load and be assigned to the instance without errors.
    """
    pipeline = InferencePipeline()

    # We guarantee not just that it was called, but that it was called only once (there should be no performance leakage).
    mock_qdrant.assert_called_once()
    mock_encoder.assert_called_once()

    # Prove that the class variables are assigned correctly.
    assert pipeline.client == mock_qdrant.return_value
    assert pipeline.encoder == mock_encoder.return_value


# --- TEST 2: Behavioral & Data Verification ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_search_logic_success(mock_encoder, mock_qdrant):
    """
    Test: Lookup Function (Successful Scenario)
    Expected: Text should be converted to vector, queried from Qdrant with the CORRECT parameters, and returned in formatted form.
    """
    pipeline = InferencePipeline()

    # 1. Model Mock: Generate a fake vector.
    mock_vector = [0.1, 0.2, 0.3]
    mock_encode_result = MagicMock()
    mock_encode_result.tolist.return_value = mock_vector
    pipeline.encoder.encode.return_value = mock_encode_result

    # 2. Qdrant Mock: Returns a fake result.
    mock_hit = MagicMock()
    mock_hit.score = 0.95
    mock_hit.payload = {
        "prod_name": "Premium Dress",
        "detail_desc": "Summer collection",
    }
    pipeline.client.search.return_value = [mock_hit]

    # Action
    results = pipeline.search_products("summer dress", top_k=2)

    # 3. Data Verification
    assert len(results) == 1
    assert results[0]["product_name"] == "Premium Dress"
    assert results[0]["score"] == 0.95

    # 4. Behavioral Proof
    pipeline.client.search.assert_called_once()
    called_kwargs = pipeline.client.search.call_args.kwargs
    assert called_kwargs["query_vector"] == mock_vector
    assert called_kwargs["limit"] == 2


# --- TEST 3: Edge Case / Zero State ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_search_logic_empty_results(mock_encoder, mock_qdrant):
    """
    Test: If Qdrant finds no matches
    Expected: The code should safely return an empty list instead of crashing.
    """
    pipeline = InferencePipeline()
    pipeline.client.search.return_value = []  # Qdrant returned empty.

    results = pipeline.search_products("asdfghjkl", top_k=5)

    assert results == []


# --- TEST 4: Resilience ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_search_logic_qdrant_failure(mock_encoder, mock_qdrant):
    """
    Test: If Qdrant returns a timeout or connection error.
    Expected: The code doesn't crash (the exception is swallowed) and safely returns an empty list.
    """
    pipeline = InferencePipeline()
    pipeline.client.search.side_effect = Exception("Qdrant Connection Timeout")

    results = pipeline.search_products("shoes", top_k=2)

    assert results == []
