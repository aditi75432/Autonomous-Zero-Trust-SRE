FROM python:3.10-slim

WORKDIR /app

# Install uv directly
RUN pip install uv

# COPY README.md HERE to satisfy hatchling during the uv sync
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv sync
RUN uv sync --no-dev

# Copy the rest of your environment code
COPY . .

EXPOSE 7860

# Run the app using the uv environment
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]