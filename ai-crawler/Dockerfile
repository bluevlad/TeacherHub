FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default: run scheduler
# Override with: docker run ... python -m src.cli crawl
CMD ["python", "-m", "src.scheduler"]
