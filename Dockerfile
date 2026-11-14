FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY prompts ./prompts
RUN pip install --upgrade pip && pip install gunicorn . boto3 opensearch-py

EXPOSE 8000
# Un worker per processo, come oggi: le cache (catalogo, dati TM/SP) sono per processo.
CMD ["gunicorn", "cycle_validation.api.entry:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000", "--timeout", "600", "--graceful-timeout", "120", "--keep-alive", "75"]
