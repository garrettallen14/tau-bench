# syntax=docker/dockerfile:1
FROM python:3.10-slim

WORKDIR /app

# Install system deps if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Entrypoint runs the API server
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
