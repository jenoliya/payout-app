# backend/Dockerfile
FROM python:3.12-slim AS base

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install system dependencies (minimal but essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# --- Stage 1: Install Poetry & dependencies ---
FROM base AS deps

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy only pyproject.toml (no lock file)
COPY pyproject.toml ./

# Install deps from pyproject.toml (no lock)
RUN poetry install --no-root --no-interaction --no-ansi

# --- Stage 2: Copy source and run ---
FROM deps AS runtime

COPY . ${APP_HOME}
RUN chown -R appuser:appgroup ${APP_HOME}

USER appuser

EXPOSE 8000

# Environment variable for concurrency
ENV UVICORN_WORKERS=2

# Start Django app
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py shell < seed.py && gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000"]
