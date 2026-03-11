import os
import numpy as np
import onnxruntime as ort
import boto3  # YENİ: AWS SDK
from botocore.exceptions import NoCredentialsError, ClientError
from qdrant_client import QdrantClient
from transformers import AutoTokenizer

from ..utils.common import read_config
from ..utils.logger import logger


class InferencePipeline:
    def __init__(self, config_path="config/config.yaml"):
        self.config = read_config(config_path)
        self.qdrant_host = os.getenv("QDRANT_HOST", self.config["qdrant"]["host"])
        self.qdrant_port = int(os.getenv("QDRANT_PORT", self.config["qdrant"]["port"]))
        self.collection_name = self.config["qdrant"]["collection_name"]

        self.s3_bucket = os.getenv(
            "S3_BUCKET_NAME", "hm-fashion-models-production-enesguler"
        )

        logger.info(f"Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}...")
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        logger.info("Connected to Qdrant successfully!")

        self.model_path = "onnx_model"

        self._ensure_model_exists()

        logger.info(f"Loading ONNX F1 Engine from: {self.model_path}...")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.session = ort.InferenceSession(
            f"{self.model_path}/model.onnx", providers=["CPUExecutionProvider"]
        )
        logger.info("ONNX Model Loaded! Ready to fly.")

    def _ensure_model_exists(self):
        """Checks if the model exists locally. If not, downloads it from AWS S3."""
        model_file_path = os.path.join(self.model_path, "model.onnx")

        if os.path.exists(model_file_path):
            logger.info("Model found locally. Skipping S3 download.")
            return

        logger.info(
            f"Model not found at {model_file_path}. Downloading from S3 bucket: {self.s3_bucket}..."
        )
        os.makedirs(self.model_path, exist_ok=True)

        s3_client = boto3.client("s3")

        try:
            s3_client.download_file(self.s3_bucket, "model.onnx", model_file_path)
            logger.info("Model successfully downloaded from S3!")
        except NoCredentialsError:
            logger.error("AWS Credentials not found. Please configure them.")
            raise
        except ClientError as e:
            logger.error(f"Failed to download model from S3: {e}")
            raise

    def encode_text(self, text: str) -> list[float]:
        """Converts text to vector using pure NumPy and ONNX. (Mean Pooling)."""
        encoded_input = self.tokenizer(
            text, padding=True, truncation=True, return_tensors="np"
        )

        model_inputs = [i.name for i in self.session.get_inputs()]

        ort_inputs = {
            k: v.astype(np.int64) for k, v in encoded_input.items() if k in model_inputs
        }

        ort_outputs = self.session.run(None, ort_inputs)
        token_embeddings = ort_outputs[0]
        attention_mask = encoded_input["attention_mask"]

        # Mean Pooling
        mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        # L2 Normalization
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.maximum(norms, 1e-9)

        return embeddings[0].tolist()

    def search_products(self, query_text: str, top_k: int = 3):
        logger.info(f"SEARCHING: '{query_text}'")
        try:
            query_vector = self.encode_text(query_text)
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
            )
            results = []
            for hit in search_result:
                results.append(
                    {
                        "score": hit.score,
                        "product_name": hit.payload.get("prod_name", "Unknown"),
                        "description": hit.payload.get("detail_desc", ""),
                        "category": hit.payload.get("product_group_name", "Unknown"),
                        "details": hit.payload,
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
