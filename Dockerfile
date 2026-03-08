# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    ffmpeg \
    libffmpeg-ocaml-dev \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    libsndfile1 \
    libsndfile1-dev \
    curl \
    portaudio19-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (using client requirements)
COPY requirements_client.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create models directory for Whisper cache
RUN mkdir -p /app/models

# Create startup script that runs both FastAPI and Streamlit with error handling
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting FastAPI backend..."\n\
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --workers=1 &\n\
BACKEND_PID=$!\n\
sleep 3\n\
if ! kill -0 $BACKEND_PID 2>/dev/null; then\n\
    echo "ERROR: Backend failed to start"\n\
    exit 1\n\
fi\n\
echo "Backend started successfully (PID: $BACKEND_PID)"\n\
echo "Starting Streamlit frontend..."\n\
streamlit run ui.py --server.port=8501 --server.address=0.0.0.0 --logger.level=info\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_LOGGER_LEVEL=info

# Expose Streamlit port (HF will route to this)
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run startup script
CMD ["/bin/bash", "/app/start.sh"]
