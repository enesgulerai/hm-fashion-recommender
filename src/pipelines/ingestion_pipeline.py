import os
import gdown
import pandas as pd
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from tqdm import tqdm

# Bizim yeni F1 motorumuzu içeri alıyoruz
from .inference_pipeline import InferencePipeline
from ..utils.common import read_config


class IngestionPipeline:
    def __init__(self, config_path="config/config.yaml"):
        """
        Initializes the Ingestion Pipeline.
        Uses our custom InferencePipeline (ONNX) for generating embeddings.
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

        # 1. Initialize ONNX Engine (Self-contained)
        print("🚀 Initializing ONNX Embedding Engine...")
        self.inference_engine = InferencePipeline(config_path=config_path)

        # Share the Qdrant client from the engine
        self.client = self.inference_engine.client
        self.collection_name = self.config["qdrant"]["collection_name"]
        self.vector_size = self.config["qdrant"]["vector_size"]

    def _download_data_if_needed(self):
        """Checks if the CSV exists locally. If not, downloads it from Google Drive."""
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
            print(f"❌ Download failed. Error: {e}")
            raise e

    def run_pipeline(self, limit=None):
        try:
            self._download_data_if_needed()

            print(f"📖 Reading CSV data from: {self.articles_path}")
            try:
                df = pd.read_csv(self.articles_path)
            except UnicodeDecodeError:
                df = pd.read_csv(self.articles_path, encoding="latin1")

            # --- PREPROCESSING ---
            df["detail_desc"] = df["detail_desc"].fillna("")
            df["prod_name"] = df["prod_name"].fillna("Unknown Product")

            if limit:
                print(f"⚠️ Limiting data to first {limit} rows for testing.")
                df = df.head(limit)

            # Bizim modelimize uygun format (Name + Description)
            documents = (df["prod_name"] + ": " + df["detail_desc"]).tolist()
            ids = df["article_id"].tolist()
            payloads = df[
                [
                    "prod_name",
                    "product_type_name",
                    "product_group_name",
                    "colour_group_name",
                ]
            ].to_dict(orient="records")

            # --- QDRANT SETUP ---
            if self.client.collection_exists(self.collection_name):
                self.client.delete_collection(self.collection_name)
                print(f"🗑️ Deleted existing collection '{self.collection_name}'")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size, distance=models.Distance.COSINE
                ),
            )

            # --- BATCH UPLOAD WITH ONNX ---
            batch_size = 64  # ONNX için ideal batch size
            print("📡 Starting Vector Ingestion with ONNX Engine...")

            for i in tqdm(
                range(0, len(documents), batch_size), desc="Ingesting to Qdrant"
            ):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_payloads = payloads[i : i + batch_size]

                # ONNX kullanarak vektörleri üretiyoruz
                # NOT: encode_text fonksiyonu tekil string aldığı için list comprehension ile geçiyoruz
                embeddings = [
                    self.inference_engine.encode_text(doc) for doc in batch_docs
                ]

                points = [
                    models.PointStruct(id=idx, vector=vector, payload=payload)
                    for idx, vector, payload in zip(
                        batch_ids, embeddings, batch_payloads
                    )
                ]

                self.client.upsert(collection_name=self.collection_name, points=points)

            print(
                f"\n🎉 SUCCESS! {len(documents)} items successfully uploaded with ONNX embeddings."
            )

        except Exception as e:
            print(f"❌ ERROR: Pipeline failed: {e}")
            raise e


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.run_pipeline(limit=5000)
