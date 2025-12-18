# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the project files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen ensures that the lockfile is respected
# --no-cache avoids storing the cache in the layer
RUN uv sync --frozen --no-cache

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
# Ensure we use the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Command to run the application
CMD ["python", "main.py"]
