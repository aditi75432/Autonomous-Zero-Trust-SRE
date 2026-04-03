FROM python:3.10-slim

WORKDIR /app

# Install uv directly
RUN pip install uv

# Copy your dependency files first to cache the layer
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync (this respects the lockfile)
RUN uv sync --no-dev

# Copy the rest of your environment code
COPY . .

EXPOSE 7860

# Run the app using the uv environment
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]