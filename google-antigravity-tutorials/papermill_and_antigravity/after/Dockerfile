FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install the locked environment first so this layer caches across code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Put the project venv on PATH so `papermill` resolves inside run_pipeline.sh.
ENV PATH="/app/.venv/bin:$PATH"

COPY notebooks/ notebooks/
COPY data/ data/
COPY run_pipeline.sh ./

ENTRYPOINT ["./run_pipeline.sh"]
