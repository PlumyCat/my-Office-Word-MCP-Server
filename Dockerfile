# Dockerfile for Azure Container Apps deployment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for python-docx and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY word_document_server/ ./word_document_server/
COPY word_mcp_server.py .
COPY office_word_mcp_server/ ./office_word_mcp_server/
COPY __init__.py .
COPY pyproject.toml .
COPY LICENSE .
COPY README.md .

# Set environment variables for HTTP mode
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_PATH=/mcp
ENV PORT=8000
ENV FASTMCP_LOG_LEVEL=INFO

# Expose the HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/mcp')" || exit 1

# Run the MCP server in HTTP mode
CMD ["python", "word_mcp_server.py"]
