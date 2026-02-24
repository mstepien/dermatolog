FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to bake it into the image
# This prevents downloading 4GB+ on every container start
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

RUN python -c "from transformers import AutoProcessor, AutoModel; \
    import os; \
    token = os.environ.get('HF_TOKEN'); \
    print(f'Downloading MedSigLIP model with token present: {bool(token)}...'); \
    AutoProcessor.from_pretrained('google/medsiglip-448', token=token); \
    AutoModel.from_pretrained('google/medsiglip-448', token=token)"

# Pre-download YOLO model
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy application code
COPY . .

# Expose port (Cloud Run defaults to 8080, providing a fallback)
ENV PORT=8080
EXPOSE $PORT

# Command to run (Using Shell form so it evaluates $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
