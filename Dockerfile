FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Default port (Railway provides PORT env var)
ENV PORT=8000

# Expose the port
EXPOSE ${PORT}

# Run the server
CMD ["python", "-m", "okta_mcp_server.server"]
