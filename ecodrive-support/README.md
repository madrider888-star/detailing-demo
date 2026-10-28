# ECODRIVE — онлайн-консультант для сайта

Чат-виджет для ecodrive.in.ua: ИИ-консультант отвечает клиентам, находит посылки
(KeyCRM → Нова Пошта), ищет по каталогу и передаёт сложные вопросы менеджерам в Telegram.

```
сайт (widget.js) → support (FastAPI) → OpenAI Responses API + инструменты
                                      ├─ KeyCRM: заказы по телефону, заявки в воронку
                                      ├─ Нова Пошта: статус по ТТН
                                      ├─ каталог CS-Cart: API или страница поиска
                                      └─ Telegram: группа менеджеров (Reply → ответ клиенту)
```

## Подключение на сайт

Одна строка через Google Tag Manager (GTM-TTB6PFG) или HTML-блок CS-Cart:

```html
<script src="https://chat.ecodrive.in.ua/widget.js" async></script>
```

## Запуск на сервере

```bash
cd ~/detailing-demo/ecodrive-support
cp .env.example .env && nano .env        # ключи
docker compose up -d --build
curl -s localhost:8090/health            # {"status":"ok"}
```

Тестовая страница: `http://<ip>:8090/demo`. Когда DNS `chat.ecodrive.in.ua` указывает на
сервер: `CHAT_DOMAIN=chat.ecodrive.in.ua docker compose --profile https up -d` и в
`docker-compose.yml` сменить порт на `127.0.0.1:8090:8090`.

## Telegram менеджеров

1. В @BotFather создать нового бота (не фото-бота), токен → `TELEGRAM_BOT_TOKEN`.
2. Добавить бота в группу менеджеров, выключить у него Privacy mode (`/setprivacy`),
   чтобы он видел ответы. Id группы (отрицательное число) → `TELEGRAM_MANAGERS_CHAT_ID`.
3. Менеджер отвечает клиенту через Reply на сообщение бота; `/done` — вернуть диалог ИИ.

## Знания

Папка `knowledge/*.md`: условия доставки, оплаты, гарантии, частые вопросы. Пометка
`[уточнить]` означает «данных нет» — консультант не называет такие вещи, а отправляет к
менеджеру. Заполнить реальными текстами и перезапустить (`docker compose up -d --build`).

## Разработка

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check app tests && .venv/bin/ruff format --check app tests
.venv/bin/mypy app
.venv/bin/pytest -q
.venv/bin/uvicorn app.api.main:app --reload --port 8090
```
