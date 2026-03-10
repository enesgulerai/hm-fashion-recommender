from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.pipelines.inference_pipeline import InferencePipeline


# --- TEST 1: Initialization Verification ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.ort.InferenceSession")
@patch("src.pipelines.inference_pipeline.AutoTokenizer.from_pretrained")
def test_pipeline_initialization(mock_tokenizer, mock_onnx_session, mock_qdrant):
    """
    Test: Pipeline Initialization (ONNX Version)
    Expected: Qdrant, Tokenizer and ONNX Session should be initialized correctly.
    """
    pipeline = InferencePipeline()

    mock_qdrant.assert_called_once()
    mock_onnx_session.assert_called_once()
    mock_tokenizer.assert_called_once()

    assert pipeline.client == mock_qdrant.return_value
    assert pipeline.session == mock_onnx_session.return_value
    assert pipeline.tokenizer == mock_tokenizer.return_value


# --- TEST 2: Behavioral & Data Verification ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.ort.InferenceSession")
@patch("src.pipelines.inference_pipeline.AutoTokenizer.from_pretrained")
def test_search_logic_success(mock_tokenizer, mock_onnx_session, mock_qdrant):
    """
    Test: Lookup Function (Successful Scenario with ONNX)
    """
    # 1. Setup Mocks
    pipeline = InferencePipeline()

    # Mock Tokenizer Output
    mock_tokenizer_instance = mock_tokenizer.return_value
    mock_tokenizer_instance.return_value = {
        "input_ids": np.array([[1, 2, 3]]),
        "attention_mask": np.array([[1, 1, 1]]),
    }

    fake_embeddings = np.random.rand(1, 3, 384).astype(np.float32)
    mock_onnx_session.return_value.run.return_value = [fake_embeddings]
    mock_input = MagicMock()
    mock_input.name = "input_ids"
    mock_onnx_session.return_value.get_inputs.return_value = [mock_input]

    # 2. Qdrant Mock: Fake result
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
    pipeline.client.search.assert_called_once()


# --- TEST 3: Edge Case / Zero State ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.ort.InferenceSession")
@patch("src.pipelines.inference_pipeline.AutoTokenizer.from_pretrained")
def test_search_logic_empty_results(mock_tokenizer, mock_onnx, mock_qdrant):
    """Test: Qdrant empty results handling."""
    pipeline = InferencePipeline()
    # Mocking encode_text to avoid complex internal mocking
    pipeline.encode_text = MagicMock(return_value=[0.1] * 384)
    pipeline.client.search.return_value = []

    results = pipeline.search_products("asdfghjkl", top_k=5)
    assert results == []


# --- TEST 4: Resilience ---
@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.ort.InferenceSession")
@patch("src.pipelines.inference_pipeline.AutoTokenizer.from_pretrained")
def test_search_logic_qdrant_failure(mock_tokenizer, mock_onnx, mock_qdrant):
    """Test: Qdrant exception handling."""
    pipeline = InferencePipeline()
    pipeline.encode_text = MagicMock(return_value=[0.1] * 384)
    pipeline.client.search.side_effect = Exception("Qdrant Connection Timeout")

    results = pipeline.search_products("shoes", top_k=2)
    assert results == []
