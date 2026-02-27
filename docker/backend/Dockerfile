# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder

WORKDIR /app

# Sadece temel derleme araçlarını bırakıyoruz
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

# --- KRİTİK DEĞİŞİKLİK ---
# Ağır PyTorch kütüphanelerini sildik, sadece hafif bağımlılıkları kuruyoruz.
COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: RUNTIME ---
FROM python:3.10-slim as runtime

# Güvenlik ve performans için non-root user yapısını koruyoruz
RUN groupadd -r hm_app && useradd -r -g hm_app -d /home/hm_user -m hm_user
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# ONNX Runtime'ın Linux'ta düzgün çalışması için libgomp1 ŞART, bunu bırakman çok iyi olmuş.
RUN apt-get update && apt-get install -y libgomp1 curl && rm -rf /var/lib/apt/lists/*

# Builder'dan gelen tertemiz venv'i kopyala
COPY --from=builder /opt/venv /opt/venv

# --- MODEL ENTEGRASYONU ---
# Yereldeki ONNX modelini konteyner içine alıyoruz
COPY onnx_model ./onnx_model/

# Proje dosyalarını kopyala
COPY config ./config/
COPY src/__init__.py ./src/
COPY src/api ./src/api/
COPY src/components ./src/components/
COPY src/pipelines ./src/pipelines/
COPY src/utils ./src/utils/

# Yetkilendirmeyi yap
RUN chown -R hm_user:hm_app /app /home/hm_user
USER hm_user

# 4 worker ile yüksek RPS karşılamaya hazırız!
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
