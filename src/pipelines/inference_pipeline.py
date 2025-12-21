import sys
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Relative import to access the config reader
from ..utils.common import read_config
# 👇 YENİ: Logger modülünü import ediyoruz
from ..utils.logger import logger


class InferencePipeline:
    def __init__(self, config_path="config/config.yaml"):
        """
        Initializes the Inference Pipeline.
        Optimization: Loads the heavy AI model ONLY ONCE during startup.
        Hybrid Config: Prioritizes Environment Variables (Docker) over config.yaml.
        """
        # 1. Load Configuration
        self.config = read_config(config_path)

        # 2. Setup Qdrant Connection Settings
        # Docker Env önceliği (Localhost sorununu çözen kısım)
        self.qdrant_host = os.getenv("QDRANT_HOST", self.config['qdrant']['host'])
        self.qdrant_port = int(os.getenv("QDRANT_PORT", self.config['qdrant']['port']))
        self.collection_name = self.config['qdrant']['collection_name']

        # LOG: Bağlantı deneniyor
        logger.info(f"🔌 Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}...")

        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            # Bağlantı başarılı logu
            logger.info("✅ Connected to Qdrant successfully!")
        except Exception as e:
            # Kritik olmayan hata (Warning) - Belki o an Qdrant kapalıdır ama kod çalışmaya devam etsin
            logger.warning(
                f"⚠️ WARNING: Could not connect to Qdrant at {self.qdrant_host}:{self.qdrant_port}. Error: {e}")

        # 3. Load AI Model
        self.model_name = self.config['model']['name']
        logger.info(f"🚀 Loading AI Model: {self.model_name}...")

        self.encoder = SentenceTransformer(self.model_name)
        logger.info("✅ AI Model Loaded!")

    def search_products(self, query_text, top_k=5):
        """
        Performs semantic search for the given query.
        Returns a list of dictionaries (compatible with API response).
        """
        # Her aramayı bilgi olarak logluyoruz
        logger.info(f"🔎 SEARCHING: '{query_text}'")

        try:
            # 1. TRANSLATION: Text -> Vector
            query_vector = self.encoder.encode(query_text).tolist()

            # 2. SEARCH: Query Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k
            )

            # 3. FORMAT RESULTS
            results = []
            for hit in search_result:
                product_data = {
                    "score": hit.score,
                    "product_name": hit.payload.get('prod_name', 'Unknown'),
                    "description": hit.payload.get('detail_desc', ''),
                    "category": hit.payload.get('product_group_name', 'Unknown'),
                    "details": hit.payload  # Frontend detayları buradan çekiyor
                }
                results.append(product_data)

            return results

        except Exception as e:
            # Kritik hata logu (Dosyaya ve konsola kırmızı olarak düşer)
            logger.error(f"❌ Error during search: {e}")
            return []


if __name__ == "__main__":
    # --- SMOKE TEST (Manuel Çalıştırma) ---
    print("running smoke test...")
    pipeline = InferencePipeline()

    test_queries = [
        "I want to go to the beach",
        "Something for running and gym",
    ]

    for query in test_queries:
        # Sonuçları ekrana basıyoruz ama arka planda log dosyasına da yazılıyor
        results = pipeline.search_products(query)
        print("-" * 50)
        print(f"Query: {query}")
        for i, item in enumerate(results):
            print(f"{i + 1}. {item['product_name']} (Score: {item['score']:.4f})")
    print("-" * 50)