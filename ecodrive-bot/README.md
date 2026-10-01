# EcoDrive Auto — Telegram-бот обработки фото автомобилей

Корпоративный бот для сотрудников EcoDrive Auto. Сотрудник выбирает операцию,
отправляет фотографии и получает готовый файл JPEG, подготовленный для объявления.

Главный принцип — **сохранить исходный автомобиль**. Бот меняет только то, что выбрано:
табличку, фон, диски или цвет кожи салона. Форма кузова, фары, эмблемы, стекло и ракурс
не меняются.

| Операция | Как работает |
| --- | --- |
| 🔢 Замена номерной таблички | Локально, без генеративной модели: OpenCV находит номер, уточняет 4 угла и накладывает фирменную табличку по перспективе с подстройкой света, тени, бликов, цветовой температуры, размытия и шума. Рамка или бампер поверх номера остаются на месте. |
| 🏙 Замена фона | AI-провайдер (6 готовых фонов или свой референс) |
| 🛞 Замена дисков | AI-провайдер + фото диска-референса, размер: как есть / больше / меньше |
| 🎨 Цвет салона | AI-провайдер, готовый цвет или HEX, выбор элементов |

Если уверенность распознавания номера ниже порога, бот не рискует: задание получает
статус `needs_review`, а сотруднику предлагается отправить другое фото, выделить номер
вручную (кнопка-заглушка, появится в следующей версии) или передать фото оператору.

---

## Содержание

1. [Архитектура](#архитектура)
2. [Создание бота в BotFather и токен](#создание-бота-в-botfather-и-токен)
3. [Заполнение .env](#заполнение-env)
4. [Запуск через Docker Compose](#запуск-через-docker-compose)
5. [Миграции](#миграции)
6. [Администраторы и доступ](#администраторы-и-доступ)
7. [Подключение реального AI-провайдера](#подключение-реального-ai-провайдера)
8. [Фирменная табличка](#фирменная-табличка)
9. [Новые фоны](#новые-фоны)
10. [Экспорт для AutoRIA](#экспорт-для-autoria)
11. [Тесты, линтер и проверка типов](#тесты-линтер-и-проверка-типов)
12. [Развёртывание на сервере](#развёртывание-на-сервере)
13. [Безопасность](#безопасность)
14. [Локальная разработка без Docker](#локальная-разработка-без-docker)

---

## Архитектура

```
Telegram ─► bot (aiogram 3, FSM в Redis) ─► PostgreSQL (users, jobs, assets, audit_logs)
                │                         └► S3 (originals/, references/, results/)
                └► Redis (очередь ARQ) ─► worker ─► ImageEditingProvider
                                                    ├─ opencv  (номера)
                                                    ├─ openai  (фон, диски, салон)
                                                    └─ mock    (разработка и тесты)
                                          worker ─► нормализация JPEG ─► Telegram (документ)
api (FastAPI): /health, /ready, /version
```

| Сервис compose | Назначение |
| --- | --- |
| `bot` | Telegram-интерфейс: меню, пошаговые сценарии, админ-команды |
| `worker` | Очередь ARQ: обработка, экспорт, обновление статуса |
| `api` | Healthcheck и задел для будущего API (порт 8080, только localhost) |
| `postgres`, `redis`, `s3` | Хранилища (`s3` — SeaweedFS, S3-совместимый; бакет создаёт приложение) |
| `migrate` | Одноразовый: применяет миграции Alembic |

Структура кода:

```
app/
  bot/            handlers/ (start, flow, jobs, admin, common), keyboards/, middlewares/,
                  states/ (FSM и описание сценариев), notifier.py, main.py
  api/            FastAPI
  core/           настройки, перечисления, логи, ошибки
  database/       база SQLAlchemy, сессии
  models/         User, Job, Asset, AuditLog
  repositories/   доступ к данным
  services/
    image_editing/      ImageEditingProvider + mock / openai / opencv, фабрика
    plate_replacement/  детектор, геометрия, фотореалистичное наложение
    storage/            S3 и локальное хранилище
    export/             нормализация JPEG, перенос C2PA
    access.py, jobs.py, operations.py, image_validation.py, reference_check.py
  workers/        ARQ-воркер, очередь, обработчик заданий
  prompts/        серверная сборка промптов
  utils/
assets/branded_plate/   макет фирменной таблички (PNG с прозрачностью)
assets/backgrounds/     готовые фоны
alembic/                миграции
tests/                  pytest
```

Сценарии описаны декларативно в `app/bot/states/flows.py`: каждый шаг — фото, выбор,
мультивыбор, HEX или сводка. На каждом шаге есть кнопки **Подтвердить**,
**Переделать**, **Назад**, **Отмена**. Статус задания (`queued` → `processing` →
`completed` / `failed` / `needs_review`) обновляется в одном сообщении, результат
приходит **документом** без сжатия Telegram.

---

## Создание бота в BotFather и токен

1. Откройте в Telegram [@BotFather](https://t.me/BotFather) и отправьте `/newbot`.
2. Введите отображаемое имя, например `EcoDrive Auto Photo`.
3. Введите username, который заканчивается на `bot`, например `ecodrive_photo_bot`.
4. BotFather пришлёт токен вида `1234567890:AAH...` — это и есть `BOT_TOKEN`.
   Храните его как пароль: только в `.env` на сервере.
5. Рекомендуемые настройки в BotFather:
   * `/setjoingroups` → **Disable** — бот работает только в личных сообщениях;
   * `/setprivacy` → **Enable**;
   * `/setdescription` — короткое описание для сотрудников.

Если токен утёк: `/revoke` в BotFather, затем обновите `.env` и перезапустите `bot` и `worker`.

**Как узнать свой Telegram ID** (нужен для списка администраторов): напишите боту
[@userinfobot](https://t.me/userinfobot) или просто отправьте `/start` своему боту —
незнакомому пользователю бот ответит его ID.

---

## Заполнение .env

```bash
cp .env.example .env
```

Минимум для запуска:

| Переменная | Что указать |
| --- | --- |
| `BOT_TOKEN` | Токен из BotFather |
| `ADMIN_TELEGRAM_IDS` | Ваш Telegram ID (через запятую, если админов несколько) |
| `ALLOWED_TELEGRAM_IDS` | ID сотрудников (можно оставить пустым и выдавать доступ командой `/allow_user`) |
| `POSTGRES_PASSWORD` | Надёжный пароль; тот же пароль — в `DATABASE_URL` |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Ключи S3: для встроенного SeaweedFS придумайте любые (секрет — рекомендуем от 16 символов), для внешнего S3 — выданные провайдером |

Сгенерировать пароли: `openssl rand -base64 24`.

Остальное имеет рабочие значения по умолчанию:

| Переменная | По умолчанию | Смысл |
| --- | --- | --- |
| `IMAGE_PROVIDER` | `mock` | `mock` или `openai` — для фона, дисков и салона |
| `PLATE_PROVIDER` | `opencv` | `opencv` или `mock` |
| `PLATE_CONFIDENCE_THRESHOLD` | `0.55` | Ниже — задание уходит в `needs_review` |
| `PLATE_DETECTOR_MODEL_PATH` | пусто | Необязательная ONNX-модель YOLO для номеров |
| `MAX_UPLOAD_BYTES` | 20 МБ | Ботам Telegram отдаёт файлы до 20 МБ |
| `MAX_IMAGE_PIXELS` | 60 Мп | Защита от «бомб» распаковки |
| `MIN_IMAGE_SIDE` | 320 | Минимальная короткая сторона |
| `MAX_ACTIVE_JOBS_PER_USER` | 2 | Одновременных заданий на сотрудника |
| `PROVIDER_TIMEOUT_SECONDS` | 180 | Тайм-аут запроса к AI |
| `PROVIDER_MAX_RETRIES` | 3 | Повторы с экспоненциальной задержкой |
| `EXPORT_MAX_SIDE` | 2560 | Максимальная сторона результата |
| `EXPORT_JPEG_QUALITY` / `EXPORT_MIN_JPEG_QUALITY` | 92 / 90 | Качество JPEG (диапазон 90–95) |
| `EXPORT_MAX_BYTES` | 8 МБ | Ограничение размера файла |
| `VISUALIZATION_LABEL_*` | включено | Отметка «Візуалізація» для фона, дисков, салона |
| `LOG_FORMAT` | `json` | `console` — удобнее при локальной отладке |

---

## Запуск через Docker Compose

Требуется Docker 24+ с плагином compose.

```bash
cd ecodrive-bot
cp .env.example .env        # заполните BOT_TOKEN, ADMIN_TELEGRAM_IDS и пароли
docker compose up -d --build
docker compose ps           # postgres/redis/s3 — healthy, migrate — exited (0)
docker compose logs -f bot worker
```

Откройте бота в Telegram и отправьте `/start`.

Проверка API (только с самого сервера):

```bash
curl http://127.0.0.1:8080/health   # {"status":"ok"}
curl http://127.0.0.1:8080/ready    # проверка БД, Redis и хранилища
```

Остановка: `docker compose down` (данные сохраняются в томах `postgres-data`,
`redis-data`, `s3-data`). Полная очистка: `docker compose down -v`.

> Почему не MinIO: MinIO прекратил публикацию бесплатных Docker-образов (`minio/minio`
> на Docker Hub больше не скачивается), поэтому в compose используется SeaweedFS. Код работает с
> любым S3-совместимым хранилищем — MinIO, AWS S3, Cloudflare R2 и т. п.

---

## Миграции

Миграции Alembic применяются автоматически сервисом `migrate` при каждом
`docker compose up`. Вручную:

```bash
docker compose run --rm migrate                         # alembic upgrade head
docker compose run --rm migrate alembic current         # текущая версия
docker compose run --rm migrate alembic downgrade -1    # откат на одну версию
```

Новая миграция после изменения моделей (локально, с доступом к БД):

```bash
DATABASE_URL=postgresql+asyncpg://ecodrive:...@localhost:5432/ecodrive \
  .venv/bin/alembic revision --autogenerate -m "описание"
.venv/bin/alembic check     # убедиться, что модели и миграции совпадают
```

---

## Администраторы и доступ

Бот закрыт белым списком — посторонний получит отказ и свой Telegram ID.

* **Первый администратор** — ID в `ADMIN_TELEGRAM_IDS`. Такой пользователь всегда
  получает роль `admin`, его нельзя заблокировать из бота.
* **Сотрудники** — ID в `ALLOWED_TELEGRAM_IDS` (роль `employee` при первом входе)
  или команда администратора `/allow_user`.
* Блокировка через `/block_user` сильнее белого списка в `.env`.

Роли: `employee` — обработка фото; `moderator` — плюс просмотр заданий, ошибок,
статистики и перезапуск; `admin` — плюс управление пользователями.

| Команда | Роль | Что делает |
| --- | --- | --- |
| `/admin` | moderator | Список админ-команд |
| `/stats` | moderator | Количество обработок, распределение по операциям и статусам, текущая очередь |
| `/jobs` | moderator | Последние задания с автором и статусом, кнопки перезапуска |
| `/failed` | moderator | Ошибки и задания на проверке с текстом ошибки, кнопки перезапуска |
| `/users` | admin | Пользователи, роли, статус |
| `/allow_user 123456789 [employee\|moderator\|admin]` | admin | Выдать доступ / сменить роль |
| `/block_user 123456789` | admin | Заблокировать |

Жалобы сотрудников («Сообщить о проблеме») и передача фото оператору приходят всем
активным модераторам и администраторам. Все действия пишутся в `audit_logs`.

---

## Подключение реального AI-провайдера

Без ключа бот работает в **mock-режиме**: фон/диски/салон возвращают исходное фото
с пометкой `MOCK` — весь путь (очередь, статусы, экспорт, кнопки) проверяется
без затрат. Номера всегда обрабатываются локально через OpenCV.

### OpenAI (gpt-image-1) или совместимый API

```dotenv
IMAGE_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1   # или адрес совместимого шлюза
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_QUALITY=high
OPENAI_INPUT_FIDELITY=high                  # максимально сохранять детали исходника
```

```bash
docker compose up -d bot worker   # перечитать .env
```

Как это устроено (`app/services/image_editing/openai_provider.py`):

* запрос `POST /images/edits` (multipart): исходник + референсы (диск, фон);
* промпт строится **только на сервере** (`app/prompts/builder.py`) из выбранной
  операции и проверенных параметров; свободный текст сотрудника в промпт не попадает;
  в каждый промпт добавляются запреты: не менять марку/модель, форму кузова, фары,
  решётку, стекло, эмблемы, ракурс и кадрирование, не добавлять текст и детали;
* исходник дополняется полями до поддерживаемого провайдером соотношения сторон,
  а результат обрезается и возвращается к исходному разрешению — пропорции не искажаются;
* тайм-аут, повторы с экспоненциальной задержкой для 429/5xx/сетевых ошибок, понятные
  сообщения для отказа модерации и ошибок ключа; ключ не попадает в логи;
* манифест C2PA, если провайдер его добавил, сохраняется.

### Другой провайдер

1. Создайте класс-наследник `ImageEditingProvider` (`app/services/image_editing/base.py`):
   `name`, `supported_operations` и метод `_edit(request) -> EditResult`.
2. Для временных ошибок бросайте `ProviderUnavailableError`/`ProviderTimeoutError`
   (их повторяет `call_with_retry`), для отказов — `ProviderRejectedError`.
3. Подключите его в `build_default_provider()` (`factory.py`) и добавьте значение
   в `IMAGE_PROVIDER` (`app/core/config.py`). Бот и воркер менять не нужно.

### Детектор номеров на нейросети (необязательно)

Классический детектор работает без модели. Для сложных фото можно указать
ONNX-модель YOLOv8/YOLO11 (один класс «номер», выход `[1, 5, N]`):

```dotenv
PLATE_DETECTOR_MODEL_PATH=/app/models/plate.onnx
```

Смонтируйте файл в контейнер `worker` (volume). Модель ищет рамку номера, точные углы
уточняются контурным методом. Проверьте лицензию выбранной модели.

---

## Фирменная табличка

Макет: `assets/branded_plate/ecodrive_plate.png` — фирменная табличка EcoDrive Auto
(чёрная, логотип и надпись, пропорции ≈ 2.5:1).

Требования к макету:

* PNG с альфа-каналом (RGBA), **табличка от края до края** холста (скругления —
  прозрачными пикселями);
* пропорции любые. Если они близки к EU-номеру (520×112 мм), макет занимает номер
  целиком. Иначе макет сохраняет свои пропорции: ставится по центру номера, по его
  ширине (с запасом 5 %, чтобы закрыть старый номер) и по его перспективе;
* разрешение — от 700 px по ширине.

Замена:

```bash
cp new_plate.png assets/branded_plate/ecodrive_plate.png
docker compose up -d --build worker
```

Или укажите другой путь в `BRANDED_PLATE_PATH` и смонтируйте файл в контейнер.
Скрипт `python scripts/generate_assets.py` создаёт заготовки, только если файлов нет;
`--force` перезапишет и фирменный макет — не используйте его без нужды.

---

## Новые фоны

Фоны лежат в `assets/backgrounds/` (сейчас — сгенерированные заготовки; замените их
реальными фотографиями студий/площадок 1920×1280 и больше, без машин и людей).

Чтобы добавить фон:

1. Положите файл, например `assets/backgrounds/parking.jpg`.
2. Добавьте запись в `BACKGROUND_PRESETS` (`app/services/operations.py`):

   ```python
   "parking": BackgroundPreset(
       "🅿️ Парковка",                         # подпись кнопки
       "parking.jpg",                          # файл в assets/backgrounds
       "an open-air parking lot of a modern dealership, daylight",  # описание сцены для AI
   ),
   ```

3. Пересоберите: `docker compose up -d --build bot worker`.

Файл фона передаётся AI-провайдеру как референс сцены, а описание — в промпт.

---

## Экспорт для AutoRIA

Модуль `app/services/export/normalizer.py` готовит каждый результат:

* JPEG, качество 90–95 % (по умолчанию 92), прогрессивный;
* профиль sRGB: встроенный ICC конвертируется в sRGB, sRGB-профиль встраивается;
* ориентация из EXIF применяется к пикселям, тег Orientation = 1;
* ограничение стороны (`EXPORT_MAX_SIDE`) и размера файла (`EXPORT_MAX_BYTES`):
  сначала снижается качество (не ниже минимума), затем разрешение;
* EXIF собирается заново: без повреждённых и дублирующихся полей (Make/Model,
  дата съёмки, ColorSpace = sRGB, Software);
* **C2PA Content Credentials сохраняются** (переносятся из результата провайдера или
  из оригинала). Пиксели изменены, поэтому валидаторы покажут, что файл
  редактировался после подписи, — так и должно быть;
* для существенно изменённых фото (фон, диски, салон) добавляется небольшая
  отметка «Візуалізація»; оригинал всегда хранится отдельно и доступен по кнопке
  «Скачать оригинал».

В проекте **нет и не должно быть** функций обхода модерации, скрытия факта
редактирования, удаления водяных знаков или сведений о происхождении.
Изменения цвета, дисков и комплектации используйте только как визуализацию
**реально предлагаемой** конфигурации, чтобы объявление не вводило покупателя
в заблуждение.

---

## Тесты, линтер и проверка типов

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"

.venv/bin/pytest -q          # тесты (SQLite + фейковый Telegram, сеть не нужна)
.venv/bin/ruff check app tests scripts alembic
.venv/bin/ruff format --check app tests scripts alembic
.venv/bin/mypy app           # strict
# или всё сразу:
make check
```

Что покрыто тестами:

| Файл | Что проверяет |
| --- | --- |
| `test_bot_flow.py` | Реальные обработчики aiogram: меню, все 4 сценария, Назад/Переделать/Отмена, двойное подтверждение, лимит заданий, отказ постороннему |
| `test_flows.py` | Переходы FSM, условные шаги |
| `test_job_service.py` | Создание задания, идемпотентность, лимиты, машина статусов, атомарный переход |
| `test_processor.py` | Воркер: completed / failed / needs_review, защита от повторной обработки, перезапуск |
| `test_access.py` | Белый список, роли, блокировка |
| `test_image_validation.py` | MIME и реальный формат, исполняемые файлы, размеры, повреждённые файлы |
| `test_operations.py` | Параметры операций, HEX, сводка, промпты и защита от инъекций |
| `test_providers.py` | Переключение провайдеров, ошибки API, повторы с backoff, ключ не попадает в логи |
| `test_plate.py` | Углы номера, перспектива, тень/размытие, перекрытие рамкой, пиксели вне номера не меняются |
| `test_export.py` | JPEG/sRGB, ориентация, лимиты, чистый EXIF, отметка, C2PA |

---

## Развёртывание на сервере

Пример для Ubuntu 22.04/24.04 (VPS от 2 vCPU / 4 ГБ RAM).

```bash
# 1. Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 2. Код
git clone <url-репозитория> ecodrive && cd ecodrive/ecodrive-bot

# 3. Настройки
cp .env.example .env && nano .env      # BOT_TOKEN, ADMIN_TELEGRAM_IDS, пароли
chmod 600 .env

# 4. Запуск
docker compose up -d --build
docker compose ps
docker compose logs -f bot worker
```

Рекомендации:

* бот работает через long polling — открывать входящие порты не нужно; закройте всё,
  кроме SSH (`ufw allow OpenSSH && ufw enable`); API слушает только `127.0.0.1`,
  хранилище `s3` наружу не публикуется;
* обновление: `git pull && docker compose up -d --build`; миграции применятся сами;
* масштабирование обработки: `docker compose up -d --scale worker=3` — одна задача
  не будет обработана дважды (уникальный id в ARQ + атомарный переход статуса в БД);
* резервные копии:
  `docker compose exec postgres pg_dump -U ecodrive ecodrive | gzip > backup_$(date +%F).sql.gz`
  и том `s3-data` (или `aws s3 sync` с endpoint хранилища); для внешнего S3 включите
  версионирование бакета;
* вместо встроенного SeaweedFS можно использовать AWS S3, Cloudflare R2, Backblaze B2,
  MinIO и т. п.: укажите `S3_ENDPOINT_URL` (для AWS — оставьте пустым), `S3_REGION`,
  `S3_BUCKET`, ключи, затем удалите сервис `s3` из `docker-compose.yml` и из
  `depends_on` в блоке `x-app`;
* логи — JSON в stdout (ротация docker: 5 × 20 МБ); подключаются к Loki/ELK без доработок;
* мониторинг: `GET /ready` возвращает 503, если недоступны БД, Redis или хранилище.

---

## Безопасность

* Токены и ключи — только в `.env` (в git попадает лишь `.env.example`).
* Секреты маскируются в логах (structlog + фильтр стандартного logging):
  токен бота, ключи API, пароли, заголовки `Authorization`.
* Входящие файлы: проверка заявленного MIME, сигнатуры и реального формата через
  Pillow, полная декодировка, лимиты размера, пикселей и минимальной стороны;
  исполняемые файлы, архивы, PDF, SVG/HTML отклоняются.
* Уникальные имена объектов (`originals/YYYY/MM/job-N/<uuid>.jpg`), оригиналы,
  референсы и результаты — в разных префиксах.
* Тайм-ауты и повторы для внешних API; жёсткий тайм-аут задачи в воркере.
* Идемпотентность: ключ на каждый диалог + уникальный индекс в БД; атомарный
  `UPDATE ... WHERE status IN (...)` при взятии задачи.
* Лимит одновременных заданий на сотрудника (с блокировкой строки пользователя).
* Обработка идёт в памяти; временные файлы (атомарная запись локального хранилища)
  удаляются автоматически.
* Ошибки Telegram и провайдера превращаются в понятные сотруднику сообщения.

---

## Локальная разработка без Docker

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env
# в .env: DATABASE_URL=postgresql+asyncpg://...@localhost:5432/ecodrive,
#         REDIS_URL=redis://localhost:6379/0, STORAGE_BACKEND=local,
#         LOCAL_STORAGE_PATH=./var/storage, LOG_FORMAT=console
.venv/bin/alembic upgrade head
.venv/bin/python -m app.bot.main                         # бот
.venv/bin/arq app.workers.worker.WorkerSettings          # воркер (в другом терминале)
.venv/bin/uvicorn app.api.main:app --port 8080           # API (по желанию)
```

Шрифт DejaVu Sans (`assets/fonts`) распространяется по свободной лицензии,
см. `assets/fonts/DEJAVU_LICENSE.txt`.
