FROM python:3.10-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.10-slim

RUN useradd -m -u 1000 dbtmcp && \
    mkdir -p /app && \
    chown -R dbtmcp:dbtmcp /app

WORKDIR /app

COPY --from=builder /root/.local /home/dbtmcp/.local
COPY --chown=dbtmcp:dbtmcp . .

USER dbtmcp

ENV PATH=/home/dbtmcp/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV CACHE_TTL_MINUTES=60

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["python", "main.py"]