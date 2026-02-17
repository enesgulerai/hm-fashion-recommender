import json
import os
import sys
import time
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
import redis
import uvicorn
from evidently.metric_preset import DataDriftPreset

# --- EVIDENTLY IMPORTS ---
from evidently.report import Report
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

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

# --- EVIDENTLY CONFIGURATION (SIMULATION) ---
reference_data = pd.DataFrame(
    {
        "text_len": np.random.normal(15, 5, 100).astype(int),
        "response_time": np.random.normal(0.05, 0.01, 100),
    }
)
reference_data = reference_data[reference_data["text_len"] > 0]

current_data_buffer = []


# --- JSON FIX FOR NUMPY ---
class NpEncoder(json.JSONEncoder):
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
    global ml_pipeline, redis_client

    # 1. REDIS CONNECTION
    redis_host = os.getenv("REDIS_HOST", "localhost")
    try:
        redis_client = redis.Redis(
            host=redis_host, port=6379, db=0, decode_responses=True
        )
        if redis_client.ping():
            logger.info(f"Redis Connection Established on {redis_host}!")
    except Exception as e:
        logger.warning(f"Redis Connection Failed: {e}. Caching disabled.")
        redis_client = None

    # 2. PIPELINE INITIATION
    logger.info("Initializing AI Pipeline...")
    try:
        ml_pipeline = InferencePipeline()
        logger.info("Model and Qdrant DB Ready!")
    except Exception as e:
        logger.error(f"An error occurred while loading the model: {e}")
        pass

    yield

    # 3. CLEANING
    logger.info("API Shutting Down...")
    ml_pipeline = None
    if redis_client:
        redis_client.close()


# --- APP DEFINITION ---
app = FastAPI(
    title="H&M Fashion Recommender API",
    description="Production-ready API with Redis, Prometheus & Evidently Drift Detection",
    version="2.2.0",
    lifespan=lifespan,
)

# --- MONITORING ---
Instrumentator().instrument(app).expose(app)


# --- MODELS ---
class SearchRequest(BaseModel):
    text: str = Field(
        ..., min_length=2, json_schema_extra={"example": "Black leather jacket"}
    )
    top_k: int = Field(5, ge=1, le=20, json_schema_extra={"example": 5})


# --- ENDPOINTS ---
@app.get("/")
def home():
    redis_status = "active" if redis_client and redis_client.ping() else "inactive"
    return {
        "status": "alive",
        "service": "H&M AI Recommender System",
        "redis_cache": redis_status,
        "model": config["model"]["name"],
        "drift_monitoring": "active",
    }


@app.post("/recommend")
def recommend_products(request: SearchRequest):
    """
    Returns similar products using Redis Caching + Vector Search Pipeline.
    Now logs data for Drift Detection.
    """
    start_time = time.time()

    try:
        # --- 1. REDIS CACHE CONTROL ---
        normalized_text = request.text.lower().strip()
        cache_key = f"search:{normalized_text}:{request.top_k}"

        final_response_data = None

        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"CACHE HIT for '{normalized_text}'")
                final_response_data = json.loads(cached_result)

        # --- 2. PIPELINE CALL (CACHE MISS) ---
        if not final_response_data:
            logger.info(f"CACHE MISS. Asking AI Model for '{normalized_text}'...")

            if ml_pipeline:
                results = ml_pipeline.search_products(request.text, top_k=request.top_k)
            else:
                results = [
                    {
                        "error": "The model hasn't been uploaded yet, or there's a pipeline error."
                    }
                ]

            final_response_data = {
                "results": results,
                "source": "vector_db",
                "count": len(results),
            }

            # --- 3. SAVING TO REDIS ---
            if redis_client and results and ml_pipeline:
                cache_data = final_response_data.copy()
                cache_data["source"] = "redis_cache"
                redis_client.setex(
                    cache_key, 3600, json.dumps(cache_data, cls=NpEncoder)
                )

        # --- 4. EVIDENTLY LOGGING ---
        process_time = time.time() - start_time

        current_data_buffer.append(
            {
                "text_len": len(request.text),
                "response_time": process_time,
            }
        )

        return final_response_data

    except Exception as e:
        logger.error(f"API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """
    DRIFT REPORT GENERATOR
    """
    if not current_data_buffer:
        return """
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>No Data Yet!</h1>
                <p>The system is waiting for data to perform drift analysis.</p>
                <p>Please <b>/recommend</b> Send a few requests to the endpoint.</p>
            </body>
        </html>
        """

    # 1. Convert buffer memory to DataFrame
    current_data = pd.DataFrame(current_data_buffer)

    # 2. Generate report
    drift_report = Report(metrics=[DataDriftPreset()])

    # 3. Compare reference data vs. current data.
    drift_report.run(reference_data=reference_data, current_data=current_data)

    # 4. Return HTML output
    return drift_report.get_html()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
