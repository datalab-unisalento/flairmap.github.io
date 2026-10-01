FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

RUN useradd --create-home --shell /bin/bash mcp && \
    mkdir -p /app/data/cache/disk /app/log && \
    chown -R mcp:mcp /app

USER mcp

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --chown=mcp:mcp pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

COPY --chown=mcp:mcp main.py ./
COPY --chown=mcp:mcp mcp_server/ ./mcp_server/

# Installa anche il progetto (se serve l'editable / entry points)
RUN uv sync --frozen

EXPOSE 8000
CMD ["python", "main.py"]