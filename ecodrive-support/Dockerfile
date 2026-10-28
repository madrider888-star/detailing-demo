FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install .

COPY widget ./widget
COPY knowledge ./knowledge
RUN mkdir -p /app/var

EXPOSE 8090
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8090"]
