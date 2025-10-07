# Dockerfile for agrr CLI
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py pyproject.toml README.md ./

# Install the package
RUN pip install -e .

# Set the entrypoint to agrr command
ENTRYPOINT ["agrr"]
CMD ["--help"]

