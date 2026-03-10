# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements/backend.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r backend.txt

# --- STAGE 2: RUNTIME ---
FROM python:3.10-slim as runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r hm_app && useradd -r -g hm_app -d /home/hm_user -m hm_user

COPY --from=builder /opt/venv /opt/venv

COPY onnx_model ./onnx_model/
COPY config ./config/
COPY src ./src/

RUN chown -R hm_user:hm_app /app
USER hm_user

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/metrics || exit 1

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
