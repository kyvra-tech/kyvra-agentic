FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for yt-dlp and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create directory for video downloads
RUN mkdir -p /tmp/kyvra_video

EXPOSE 8000

CMD ["python", "main.py"]
