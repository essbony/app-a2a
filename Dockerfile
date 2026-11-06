# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1 : builder - resolve and install locked dependencies
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first: this layer is rebuilt only when pyproject/uv.lock change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Then the application code (see .dockerignore for what is excluded).
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


# ============================================================
# Stage 2 : runtime - slim image, no uv, no build tooling, non-root
# ============================================================
FROM python:3.13-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

# Unprivileged user: a compromised process cannot write to the system.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home \
       --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

USER app
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/_stcore/health' % os.getenv('STREAMLIT_SERVER_PORT', '8501'), timeout=4)"

# Streamlit : expose l'UI. Les variables HOST/PORT restent pour l'agent distant (outline_agent).
CMD ["sh", "-c", "exec streamlit run ui.py --server.port ${STREAMLIT_SERVER_PORT:-8501} --server.address 0.0.0.0 --server.headless true"]
