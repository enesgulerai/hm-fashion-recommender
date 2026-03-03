# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

COPY requirements/backend.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: RUNTIME ---
FROM python:3.10-slim as runtime

RUN groupadd -r hm_app && useradd -r -g hm_app -d /home/hm_user -m hm_user
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

RUN apt-get update && apt-get install -y libgomp1 curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# --- MODEL INTEGRATION ---
COPY onnx_model ./onnx_model/

COPY config ./config/
COPY src/__init__.py ./src/
COPY src/api ./src/api/
COPY src/components ./src/components/
COPY src/pipelines ./src/pipelines/
COPY src/utils ./src/utils/

RUN chown -R hm_user:hm_app /app /home/hm_user
USER hm_user

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
