# Personal Agent Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Create data directory
RUN mkdir -p /app/data

# Set default command
CMD ["python", "-m", "src.cli"]
