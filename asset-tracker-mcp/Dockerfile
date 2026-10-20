FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml server.py ./
RUN pip install --no-cache-dir -e .

# API_BASE_URL is provided at runtime, e.g.:
#   docker run -e API_BASE_URL=http://host.docker.internal:8000 asset-tracker-mcp
ENV API_BASE_URL=http://127.0.0.1:8000

# The server speaks MCP over stdio.
CMD ["python", "server.py"]
