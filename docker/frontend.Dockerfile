# syntax=docker/dockerfile:1
# InfraDesk web image: build the React app, then serve it with unprivileged nginx.
#   docker build -f docker/frontend.Dockerfile -t infradesk-frontend:latest .
# Build context: the repository root.

# ---- Stage 1: build the static files (Vite writes frontend/dist) ----
FROM node:22-alpine AS build
WORKDIR /build
COPY frontend/package*.json ./
# `npm ci` is reproducible when a lock file exists; fall back to `npm install` otherwise.
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: tiny runtime image, no Node, runs as a non-root user on port 8080 ----
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html

USER root

RUN chmod 0644 /etc/nginx/conf.d/default.conf \
 && find /usr/share/nginx/html -type d -exec chmod 0755 {} \; \
 && find /usr/share/nginx/html -type f -exec chmod 0644 {} \;

USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/nginx-health"]
