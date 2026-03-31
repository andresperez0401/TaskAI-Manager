FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PIP_NO_CACHE_DIR=1 \
		PORT=8010

WORKDIR /app/backend

# Install deps in a cache-friendly layer
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY app ./app
COPY core ./core
COPY modules ./modules
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini ./alembic.ini

# Run as non-root in production
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8010') + '/health').read()" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8010}"]
