import pandas as pd
import os
import sys
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Relative import to access the config reader
from ..utils.common import read_config


class IngestionPipeline:
    def __init__(self, config_path="config/config.yaml"):
        """
        Initializes the Ingestion Pipeline.
        It loads configuration, connects to Qdrant, and initializes the embedding model.
        Hybrid Config: Prioritizes Environment Variables (Docker) over config.yaml.
        """
        # 1. Load Configuration
        self.config = read_config(config_path)

        # 2. Setup Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.articles_path = os.path.join(self.base_dir, self.config['paths']['raw_data'],
                                          self.config['files']['articles'])

        # 3. Setup Qdrant Client (CRITICAL FIX 🛠️)
        self.qdrant_host = os.getenv("QDRANT_HOST", self.config['qdrant']['host'])
        self.qdrant_port = int(os.getenv("QDRANT_PORT", self.config['qdrant']['port']))

        self.collection_name = self.config['qdrant']['collection_name']
        self.vector_size = self.config['qdrant']['vector_size']

        print(f"🔌 Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}...")

        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            print("✅ Connection object created.")
        except Exception as e:
            print(f"❌ Failed to initialize Qdrant Client: {e}")
            raise e

        # 4. Load AI Model
        self.model_name = self.config['model']['name']
        print(f"🚀 Loading Embedding Model: {self.model_name}...")
        self.encoder = SentenceTransformer(self.model_name)

    def run_pipeline(self, limit=None):
        """
        Executes the ingestion process:
        1. Reads article data.
        2. Preprocesses text fields.
        3. Encodes text into vectors.
        4. Uploads vectors and payloads to Qdrant.

        Args:
            limit (int, optional): If provided, limits the number of rows processed.
        """
        try:
            print(f"📂 Reading Data from: {self.articles_path}")

            if not os.path.exists(self.articles_path):
                raise FileNotFoundError(f"Data file not found at: {self.articles_path}")

            df = pd.read_csv(self.articles_path)

            # --- PREPROCESSING ---
            # Fill missing values to prevent errors during embedding
            df['detail_desc'] = df['detail_desc'].fillna("")
            df['prod_name'] = df['prod_name'].fillna("Unknown Product")

            # If a limit is set (e.g., for testing), slice the dataframe
            if limit:
                print(f"⚠️ Limiting data to first {limit} rows.")
                df = df.head(limit)

            # Feature Engineering: Combine title and description for richer embeddings
            documents = (df['prod_name'] + ": " + df['detail_desc']).tolist()
            ids = df['article_id'].tolist()

            # Prepare Metadata (Payload) for Qdrant
            payloads = df[['prod_name', 'product_type_name', 'product_group_name',
                           'graphical_appearance_name', 'colour_group_name']].to_dict(orient='records')

            # --- QDRANT SETUP ---
            # Recreate collection to ensure a fresh start
            print(f"♻️ Recreating collection '{self.collection_name}'...")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✅ Collection '{self.collection_name}' created/reset successfully.")

            # --- BATCH UPLOAD ---
            batch_size = 250
            total_batches = len(documents) // batch_size + 1

            print("📡 Starting Vector Ingestion...")
            for i in tqdm(range(0, len(documents), batch_size), total=total_batches, desc="Uploading to Qdrant"):
                # Slice batches
                batch_docs = documents[i: i + batch_size]
                batch_ids = ids[i: i + batch_size]
                batch_payloads = payloads[i: i + batch_size]

                # Generate Embeddings
                embeddings = self.encoder.encode(batch_docs).tolist()

                # Create Points
                points = [
                    models.PointStruct(
                        id=idx,
                        vector=vector,
                        payload=payload
                    )
                    for idx, vector, payload in zip(batch_ids, embeddings, batch_payloads)
                ]

                # Upload Batch
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )

            print(
                f"\n🎉 SUCCESS! {len(documents)} items successfully uploaded to Qdrant collection '{self.collection_name}'.")

        except Exception as e:
            print(f"❌ ERROR: Pipeline failed: {e}")
            raise e


if __name__ == "__main__":
    # Test run (limiting to 5000 rows for speed)
    print("🚀 Starting Ingestion Pipeline...")
    pipeline = IngestionPipeline()
    pipeline.run_pipeline(limit=5000)  # You can remove the limit to process all data