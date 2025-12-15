FROM python:3.9-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim
RUN useradd --create-home --shell /bin/bash appuser && mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY --chown=appuser:appuser app.py .
USER appuser

ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app FLASK_APP=app.py PROMETHEUS_MULTIPROC_DIR=/tmp
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--worker-class", "gthread", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "30", "--keepalive", "5", "--max-requests", "1000", "--max-requests-jitter", "50", "app:app"]
