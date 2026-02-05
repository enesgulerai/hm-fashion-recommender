# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src/ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: RUNTIME ---
FROM python:3.10-slim as runtime
RUN groupadd -r hm_app && useradd -r -g hm_app hm_user
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv

# 1. Config
COPY config/ ./config/

# 2. UI and Utils only
COPY src/__init__.py ./src/
COPY src/ui/ ./src/ui/
COPY src/utils/ ./src/utils/

RUN chown -R hm_user:hm_app /app
USER hm_user

CMD ["streamlit", "run", "src/ui/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]