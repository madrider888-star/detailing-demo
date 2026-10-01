# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные пакеты не нужны: opencv-python-headless самодостаточен,
# шрифт с кириллицей для отметки «Візуалізація» лежит в assets/fonts.
WORKDIR /app

# Сначала только зависимости из pyproject.toml — слой кешируется. Сам код не
# устанавливается в site-packages: приложение работает из /app (рядом с assets/).
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" > /tmp/requirements.txt \
    && pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY . .
RUN useradd --create-home --uid 10001 ecodrive \
    && mkdir -p /data/storage \
    && chown -R ecodrive:ecodrive /app /data

USER ecodrive

EXPOSE 8080
CMD ["python", "-m", "app.bot.main"]
