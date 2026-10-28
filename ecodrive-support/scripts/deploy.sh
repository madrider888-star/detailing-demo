#!/usr/bin/env bash
# Первый запуск / обновление консультанта на сервере. Запускать на сервере:
#   bash ~/detailing-demo/ecodrive-support/scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  # Ключ OpenAI берём из фото-бота, чтобы не вводить его второй раз
  KEY=$(grep -E '^OPENAI_API_KEY=' ../ecodrive-bot/.env | cut -d= -f2- || true)
  if [ -n "$KEY" ]; then
    sed -i '/^OPENAI_API_KEY=/d' .env
    printf 'OPENAI_API_KEY=%s\n' "$KEY" >> .env
  fi
  echo ".env создан из .env.example"
fi

docker compose up -d --build
sleep 5
docker compose ps
curl -sf http://localhost:8090/health && echo " <- health OK"
