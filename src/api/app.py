from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import uvicorn
import redis
import json
import os
import sys
import numpy as np

# --- MODULE PATH SETTING ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from src.pipelines.inference_pipeline import InferencePipeline
from src.utils.common import read_config
from src.utils.logger import logger

# --- GLOBAL VARIABLES ---
ml_pipeline = None
redis_client = None
config = read_config("config/config.yaml")

# --- JSON FIX FOR NUMPY (CRITICAL FOR STABILITY) ---
class NpEncoder(json.JSONEncoder):
    """
    The standard JSON library does not recognize Numpy numbers (float32, int64).
    This class converts them to standard Python numbers (float, int).
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The API establishes connections between Model and Redis when it starts.
    It releases resources when it closes.
    """
    global ml_pipeline, redis_client

    # 1. REDIS CONNECTION
    redis_host = os.getenv("REDIS_HOST", "localhost")
    try:
        redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        if redis_client.ping():
            logger.info(f"Redis Connection Established on {redis_host}!")
    except Exception as e:
        logger.warning(f"Redis Connection Failed: {e}. Caching disabled.")
        redis_client = None

    # 2. PIPELINE INITIATION
    logger.info("Initializing AI Pipeline...")
    ml_pipeline = InferencePipeline()
    logger.info("Model and Qdrant DB Ready!")

    yield # API works here

    # 3. CLEANING
    logger.info("API Shutting Down...")
    ml_pipeline = None
    if redis_client:
        redis_client.close()


# --- APPLICATION DESCRIPTION ---
app = FastAPI(
    title="H&M Fashion Recommender API",
    description="Production-ready API with Redis Caching & Prometheus Monitoring",
    version="2.1.0",
    lifespan=lifespan
)

# --- MONITORING ---
Instrumentator().instrument(app).expose(app)


# --- Pydantic Models ---
class SearchRequest(BaseModel):
    text: str = Field(..., min_length=2, example="Black leather jacket")
    top_k: int = Field(5, ge=1, le=20, example=5)


# --- ENDPOINTS ---

@app.get("/")
def home():
    redis_status = "active" if redis_client and redis_client.ping() else "inactive"
    return {
        "status": "alive",
        "service": "H&M AI Recommender System",
        "redis_cache": redis_status,
        "model": config['model']['name']
    }


@app.post("/recommend")
def recommend_products(request: SearchRequest):
    """
    Returns similar products using Redis Caching + Vector Search Pipeline.
    """
    try:
        # --- 1. REDIS CACHE CONTROL ---
        normalized_text = request.text.lower().strip()
        cache_key = f"search:{normalized_text}:{request.top_k}"

        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"⚡ CACHE HIT for '{normalized_text}'")
                return json.loads(cached_result)

        # --- 2. PIPELINE CALL (CACHE MISS) ---
        logger.info(f"CACHE MISS. Asking AI Model for '{normalized_text}'...")

        results = ml_pipeline.search_products(request.text, top_k=request.top_k)

        # Let's add source tags to the results.
        final_response = {
            "results": results,
            "source": "vector_db",
            "count": len(results)
        }

        # --- 3. SAVING TO REDIS ---
        if redis_client and results:
            cache_data = final_response.copy()
            cache_data["source"] = "redis_cache"

            # Keep in cache for 1 hour (3600 seconds)
            redis_client.setex(cache_key, 3600, json.dumps(cache_data, cls=NpEncoder))

        return final_response

    except Exception as e:
        logger.error(f"API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)