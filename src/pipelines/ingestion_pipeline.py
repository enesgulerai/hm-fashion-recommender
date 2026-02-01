import os
import sys

import gdown
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Relative import to access the config reader
# NOTE: Run this script as a module: python -m src.pipelines.ingestion_pipeline
from ..utils.common import read_config


class IngestionPipeline:
    def __init__(self, config_path="config/config.yaml"):
        """
        Initializes the Ingestion Pipeline.
        Loads configuration, sets up paths, connects to Qdrant, and initializes the embedding model.
        """
        self.config = read_config(config_path)

        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.raw_data_dir = os.path.join(
            self.base_dir, self.config["paths"]["raw_data"]
        )

        self.articles_path = os.path.join(
            self.raw_data_dir,
            self.config["files"]["articles"],
        )

        # Docker environment variable priority
        self.qdrant_host = os.getenv("QDRANT_HOST", self.config["qdrant"]["host"])
        self.qdrant_port = int(os.getenv("QDRANT_PORT", self.config["qdrant"]["port"]))
        self.collection_name = self.config["qdrant"]["collection_name"]
        self.vector_size = self.config["qdrant"]["vector_size"]

        print(f"🔌 Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}...")

        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            # Check connection by listing collections
            self.client.get_collections()
            print("✅ Connection established successfully.")
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant. Is Docker running? Error: {e}")
            raise e

        self.model_name = self.config["model"]["name"]
        print(f"🚀 Loading Embedding Model: {self.model_name}...")
        self.encoder = SentenceTransformer(self.model_name)

    def _download_data_if_needed(self):
        """
        Checks if the CSV exists locally. If not, downloads it from Google Drive.
        """
        if os.path.exists(self.articles_path):
            print(f"✅ CSV Data found at: {self.articles_path}")
            return

        print(
            f"⚠️ Data NOT found at {self.articles_path}. Starting automatic download..."
        )
        os.makedirs(self.raw_data_dir, exist_ok=True)

        file_id = "1w52TQfKYfdDuASM1qMoIJHhxbHogvJKJ"
        url = f"https://drive.google.com/uc?id={file_id}"

        try:
            print("⏳ Downloading CSV from Google Drive...")
            gdown.download(url, self.articles_path, quiet=False)
            print(f"🎉 Download complete! Saved to {self.articles_path}")
        except Exception as e:
            print(f"❌ Download failed. Check internet/Drive ID. Error: {e}")
            if os.path.exists(self.articles_path):
                os.remove(self.articles_path)
            raise e

    def run_pipeline(self, limit=None):
        try:
            self._download_data_if_needed()

            print(f"📖 Reading CSV data from: {self.articles_path}")

            try:
                df = pd.read_csv(self.articles_path)
            except UnicodeDecodeError:
                print("⚠️ UTF-8 failed. Trying 'latin1' encoding...")
                df = pd.read_csv(self.articles_path, encoding="latin1")

            # --- PREPROCESSING ---
            df["detail_desc"] = df["detail_desc"].fillna("")
            df["prod_name"] = df["prod_name"].fillna("Unknown Product")

            if limit:
                print(f"⚠️ Limiting data to first {limit} rows for testing.")
                df = df.head(limit)

            documents = (df["prod_name"] + ": " + df["detail_desc"]).tolist()
            ids = df["article_id"].tolist()

            payloads = df[
                [
                    "prod_name",
                    "product_type_name",
                    "product_group_name",
                    "graphical_appearance_name",
                    "colour_group_name",
                ]
            ].to_dict(orient="records")

            # --- QDRANT SETUP (MODERN METHOD) ---
            print(f"♻️ Checking collection '{self.collection_name}'...")

            if self.client.collection_exists(self.collection_name):
                self.client.delete_collection(self.collection_name)
                print(f"🗑️ Deleted existing collection '{self.collection_name}'")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size, distance=models.Distance.COSINE
                ),
            )
            print(f"✅ Collection '{self.collection_name}' created successfully.")

            # --- BATCH UPLOAD ---
            batch_size = 250
            total_batches = len(documents) // batch_size + 1

            print("📡 Starting Vector Ingestion...")
            for i in tqdm(
                range(0, len(documents), batch_size),
                total=total_batches,
                desc="Uploading to Qdrant",
            ):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_payloads = payloads[i : i + batch_size]

                embeddings = self.encoder.encode(batch_docs).tolist()

                points = [
                    models.PointStruct(id=idx, vector=vector, payload=payload)
                    for idx, vector, payload in zip(
                        batch_ids, embeddings, batch_payloads
                    )
                ]

                self.client.upsert(collection_name=self.collection_name, points=points)

            print(
                f"\n🎉 SUCCESS! {len(documents)} items successfully uploaded to Qdrant collection '{self.collection_name}'."
            )

        except Exception as e:
            print(f"❌ ERROR: Pipeline failed: {e}")
            raise e


if __name__ == "__main__":
    print("🚀 Starting Ingestion Pipeline...")
    pipeline = IngestionPipeline()
    pipeline.run_pipeline()
