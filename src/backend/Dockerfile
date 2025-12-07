# Python AG-UI Server
FROM python:3.12-slim

# Ensure Python output is not buffered (important for Docker logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Azure CLI for DefaultAzureCredential
RUN apt-get update && apt-get install -y curl && \
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY config.py ./
COPY server.py ./
COPY auth/ ./auth/
COPY tools/ ./tools/
COPY agents/ ./agents/
COPY api/ ./api/
COPY utils/ ./utils/

# Expose port
EXPOSE 8888

# Run the server
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8888"]
