# Передача проекта — онлайн-консультант ECODRIVE

Прочитай целиком перед работой. Владелец — не программист: объясняй простыми шагами.

## Что это

ИИ-консультант «Олена» для сайта ecodrive.in.ua (CS-Cart, за Cloudflare): чат-виджет,
поиск заказов в KeyCRM, статус посылок Новой Почты, поиск по каталогу, передача
менеджеру в Telegram. Устройство и запуск — в `README.md`.

## Где что работает (на 2026-10-28)

- Сервер: DigitalOcean `157.245.68.131`, папка `/root/detailing-demo/ecodrive-support`,
  docker compose проект `ecodrive-support`, порт 8090. Рядом — фото-бот `ecodrive-bot`.
- Тестовая страница: http://157.245.68.131:8090/demo
- Модель: `gpt-5.4` (ключ OpenAI взят из `.env` фото-бота). `gpt-5.4-mini` быстрее, но
  слишком рано передаёт менеджеру — не переключать без проверки.
- Telegram: бот менеджеров @ecodrive_support_bot («ECODRIVE Менеджери»), группа
  «ECODRIVE · Обращения с сайта» (id -5594203080). Проверено: обращение → группа,
  Reply менеджера → чат на сайте.
- Секреты (токены, ключи) — **только** в `/root/detailing-demo/ecodrive-support/.env`
  на сервере. В git и в чат не попадают.
- Презентация для руководства: https://claude.ai/artifact/Tqxo3YkamJwTmxxEStuC3h
  (10 слайдов, последний — план встречи с программистом сайта).

## Что осталось (ждём от владельца и программиста сайта)

1. Cloudflare → Security → WAF → Tools: Allow для IP `157.245.68.131`. Сейчас Cloudflare
   отдаёт серверу 403, поэтому `search_catalog` не работает (с обычного ПК работает).
2. Cloudflare → DNS: A-запись `chat` → `157.245.68.131`, DNS only. Потом на сервере:
   `CHAT_DOMAIN=chat.ecodrive.in.ua docker compose --profile https up -d` и в
   `docker-compose.yml` порт support → `127.0.0.1:8090:8090`.
3. KeyCRM: API-ключ → `KEYCRM_API_KEY`, воронка → `KEYCRM_PIPELINE_ID` в `.env`.
4. Тексты в `knowledge/*.md` вместо пометок `[уточнить]`: доставка, оплата, гарантия
   (на сайте конфликт: «3 месяца» и «30 дней» на самокаты), адреса, режим работы.
5. Запуск: строка `<script src="https://chat.ecodrive.in.ua/widget.js" async></script>`
   через Google Tag Manager (GTM-TTB6PFG) или HTML-блок CS-Cart.
6. Потом: тот же агент в Telegram для клиентов, затем Instagram (нужно одобрение Meta).

## Как обновлять сервер

С сервера нет доступа к GitHub (репо приватный). Копировать папку:
```
tar czf /tmp/s.tgz --exclude=.venv --exclude=var ecodrive-support
scp /tmp/s.tgz root@157.245.68.131:/tmp/
# на сервере: сохранить .env, распаковать, вернуть .env, docker compose up -d --build
```
SSH-ключи: `zinchenko-windows` и `zinchenko-mac` (оба добавлены на сервер).

## Правила работы

- После нетривиальных правок — проверки (`ruff`, `mypy`, `pytest`) и ревью Codex.
- Визуальные действия на ПК владельца (браузер, Telegram) — на втором мониторе.
- Перед отправкой сообщений от имени владельца — проверить получателя на экране.
- Не выдумывать данные магазина в промпте/знаниях: что неизвестно — `[уточнить]`.
