import pytest
from unittest.mock import patch, MagicMock
from src.pipelines.inference_pipeline import InferencePipeline


@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_pipeline_initialization(mock_sentence_transformer, mock_qdrant_client):
    """
    Test: Pipeline Başlatma
    Amacı: Qdrant ve Model yüklenirken hata çıkıyor mu?
    """
    # Mock nesneleri ayarla
    mock_qdrant_instance = MagicMock()
    mock_qdrant_client.return_value = mock_qdrant_instance

    # Pipeline'ı başlat
    pipeline = InferencePipeline()

    # Model ve Client çağrıldı mı kontrol et
    mock_qdrant_client.assert_called()
    mock_sentence_transformer.assert_called()
    assert pipeline.client == mock_qdrant_instance


@patch("src.pipelines.inference_pipeline.QdrantClient")
@patch("src.pipelines.inference_pipeline.SentenceTransformer")
def test_search_logic(mock_sentence_transformer, mock_qdrant_client):
    """
    Test: Arama Fonksiyonu
    Amacı: Verilen metin vektöre çevrilip Qdrant'a soruluyor mu?
    """
    # 1. Setup Mocks
    pipeline = InferencePipeline()

    # DÜZELTME BURADA:
    # Kodun içinde .tolist() çağrıldığı için, mock nesnesinin tolist()
    # metodunun bir liste döndürmesini sağlıyoruz.
    mock_vector = MagicMock()
    mock_vector.tolist.return_value = [0.1, 0.2, 0.3]
    pipeline.encoder.encode.return_value = mock_vector  # tolist() metodu olan bir nesne döndür

    # Qdrant mock: Sahte arama sonucu dönsün
    mock_hit = MagicMock()
    mock_hit.score = 0.88
    mock_hit.payload = {"prod_name": "Test Item", "detail_desc": "Desc"}
    pipeline.client.search.return_value = [mock_hit]

    # 2. Action
    results = pipeline.search_products("running shoes", top_k=2)

    # 3. Assertions
    # Sonuçların boş gelmediğini ve doğru datayı içerdiğini doğrula
    assert len(results) == 1
    assert results[0]["product_name"] == "Test Item"
    assert results[0]["score"] == 0.88