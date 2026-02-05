# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder

WORKDIR /app

# Gereksiz dosyaları temizleyerek başla
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

# ADIM 1: Önce Sadece CPU Torch'u kur (En Temizi)
# --no-cache-dir ile cache şişkinliğini önle
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ADIM 2: Sentence-Transformers'ı Torch OLMADAN Kur
# --no-deps: "Bağımlılıkları indirme, ben hallettim" demektir.
# Böylece gidip GPU Torch indirmesini %100 engelleriz.
# Ancak HuggingFace gibi diğer bağımlılıkları manuel eklememiz gerekebilir,
# o yüzden önce normal deniyoruz ama torch kurulu olduğu için atlamasını umuyoruz.
# Eğer yine şişerse --no-deps kullanacağız.
RUN pip install --no-cache-dir sentence-transformers

# ADIM 3: Geriye kalanları kur
COPY src/api/requirements.txt .
# Dosyadan torch ve sentence-transformers satırlarını silmiş olman lazım!
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: RUNTIME ---
FROM python:3.10-slim as runtime

# ... (Kullanıcı ve env ayarları aynı)
RUN groupadd -r hm_app && useradd -r -g hm_app -d /home/hm_user -m hm_user
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Runtime paketleri
RUN apt-get update && apt-get install -y libgomp1 curl && rm -rf /var/lib/apt/lists/*

# Sadece venv'i kopyala (En büyük tasarruf)
COPY --from=builder /opt/venv /opt/venv

# Kodları kopyala
COPY config ./config/
COPY src/__init__.py ./src/
COPY src/api ./src/api/
COPY src/components ./src/components/
COPY src/pipelines ./src/pipelines/
COPY src/utils ./src/utils/

RUN mkdir -p /app/models && chown -R hm_user:hm_app /app /home/hm_user
USER hm_user

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]