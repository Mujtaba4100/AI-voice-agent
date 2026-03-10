# Use Python 3.11 slim image (better wheel support than 3.10)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (runtime only - no build tools to prevent source compilation)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Download and install Piper TTS (Linux version)
RUN wget -q https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz \
    && tar -xzf piper_amd64.tar.gz -C /app \
    && rm piper_amd64.tar.gz \
    && chmod +x /app/piper/piper

# Download Piper voice model (en_US-lessac-medium - natural voice, ~100MB)
RUN mkdir -p /app/piper/models \
    && wget -q -O /app/piper/models/en_US-lessac-medium.onnx \
       https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx \
    && wget -q -O /app/piper/models/en_US-lessac-medium.onnx.json \
       https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Copy requirements (using client requirements)
COPY requirements_client.txt requirements.txt

# Install Python dependencies (--only-binary prevents any source compilation)
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

# Copy project files
COPY . .

# Create models directory for Whisper cache
RUN mkdir -p /app/models

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_LOGGER_LEVEL=info

# Expose port 7860 (HF Spaces default for Docker SDK)
EXPOSE 7860

# Simple direct startup - backend on 8000, streamlit on 7860 (HF default)
CMD ["/bin/sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port 8000 & sleep 10 && streamlit run ui.py --server.port=7860 --server.address=0.0.0.0"]
