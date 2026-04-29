# backend/Dockerfile
FROM python:3.12-slim AS base

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

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

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml ./
RUN poetry install --no-root --no-interaction --no-ansi

# --- Stage 2: Copy source and run ---
FROM deps AS runtime

COPY . ${APP_HOME}
RUN mkdir -p /app/db

EXPOSE 8000

ENV UVICORN_WORKERS=2

CMD ["sh", "-c", "mkdir -p /app/db && python manage.py migrate && python manage.py collectstatic --noinput && python manage.py shell < seed.py && gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000"]