FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --pre \
    "agent-framework-core>=1.14" \
    "agent-framework-ag-ui>=1.1" \
    "agent-framework-github-copilot>=1.0" \
    "mcp>=1.0,<2" \
    "fastapi>=0.121" \
    "uvicorn[standard]>=0.29" \
    "httpx>=0.27"

COPY app ./app

EXPOSE 8002

CMD ["python", "-m", "app.server"]
