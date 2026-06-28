FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for building Python packages and Rust toolchain
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl git ca-certificates gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain (non-interactive) for building pydantic-core if needed
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Install Python dependencies first (copy only requirements to leverage Docker cache)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip setuptools wheel && pip install --prefer-binary -r requirements.txt

# Copy application code
COPY backend /app

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
