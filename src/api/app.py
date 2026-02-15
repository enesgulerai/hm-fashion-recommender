import json
import os
import sys
import time  # <--- EKLENDI: Süre ölçümü için
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd  # <--- EKLENDI: Veri analizi için
import redis
import uvicorn
from evidently.metric_preset import DataDriftPreset

# --- EVIDENTLY IMPORTS (YENİ) ---
from evidently.report import Report
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse  # <--- EKLENDI: Dashboard HTML'i için
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
# Modelin "Sağlıklı" olduğu zamanları temsil eden Referans Veri.
# Gerçek hayatta burası eğitim veri setin (training data) olurdu.
reference_data = pd.DataFrame(
    {
        "text_len": np.random.normal(15, 5, 100).astype(int),  # Ort. 15 harf uzunluk
        "response_time": np.random.normal(0.05, 0.01, 100),  # Ort. 50ms cevap süresi
    }
)
# Negatif değerleri temizleyelim
reference_data = reference_data[reference_data["text_len"] > 0]

# Canlı verileri burada biriktireceğiz
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
        logger.error(f"Model yüklenirken hata oluştu: {e}")
        # Hata olsa bile API çökmesin, drift dashboard çalışsın diye pass geçiyoruz
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
    description="Production-ready API with Redis, Prometheus & Evidently Drift Detection 🚀",
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
        "drift_monitoring": "active",  # Yeni özellik
    }


@app.post("/recommend")
def recommend_products(request: SearchRequest):
    """
    Returns similar products using Redis Caching + Vector Search Pipeline.
    Now logs data for Drift Detection.
    """
    start_time = time.time()  # <--- Kronometre Başladı

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

            # Eğer Pipeline yüklüyse gerçek tahmin yap, değilse boş dön (Hata vermesin)
            if ml_pipeline:
                results = ml_pipeline.search_products(request.text, top_k=request.top_k)
            else:
                results = [{"error": "Model henüz yüklenmedi veya pipeline hatası."}]

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

        # --- 4. EVIDENTLY LOGGING (YENİ KISIM) ---
        # İşlem bitti, drift için veriyi kaydedelim
        process_time = time.time() - start_time

        current_data_buffer.append(
            {
                "text_len": len(request.text),  # Girdi özelliği (Drift olabilir)
                "response_time": process_time,  # Çıktı performansı (Model yavaşladı mı?)
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
    # Veri yoksa boş sayfa gösterme
    if not current_data_buffer:
        return """
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>Henüz Veri Yok! 📉</h1>
                <p>Sistem drift analizi yapmak için veri bekliyor.</p>
                <p>Lütfen <b>/recommend</b> endpointine birkaç istek atın.</p>
            </body>
        </html>
        """

    # 1. Tampon belleği DataFrame'e çevir
    current_data = pd.DataFrame(current_data_buffer)

    # 2. Raporu oluştur
    drift_report = Report(metrics=[DataDriftPreset()])

    # 3. Referans vs Güncel veriyi karşılaştır
    drift_report.run(reference_data=reference_data, current_data=current_data)

    # 4. HTML çıktısını dön
    return drift_report.get_html()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
