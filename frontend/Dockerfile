# frontend/Dockerfile
FROM node:22-slim AS base

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# --- Stage 1: Install dependencies ---
FROM base AS deps

COPY package.json ./
RUN npm install

# --- Stage 2: Build ---
FROM deps AS builder

COPY . ${APP_HOME}
RUN npm run build

# --- Stage 3: Serve with vite preview ---
FROM builder AS runtime

RUN chown -R appuser:appgroup ${APP_HOME}
USER appuser

EXPOSE 4173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
