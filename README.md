# Freelance Jobs Parser Bot

Telegram-бот для поиска заказов по ключевым словам в описании. Бот парсит площадки [Kwork](https://kwork.ru/projects) и [YouDo](https://youdo.com/tasks-all-opened-all) и присылает результаты в чат. Воспользоваться ботом можно тут -> https://t.me/find_nice_work_bot

## Возможности

- Поиск заказов сразу на двух площадках: Kwork (через парсинг JSON-данных страницы) и YouDo (через Selenium)
- Поиск сразу по нескольким ключевым словам
- Выгрузка найденных заказов в txt файл
- автоматическая рассылка новых заказов

## Технологии

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (telebot) — Telegram Bot API
- requests — запросы к Kwork
- selenium — headless парсинг YouDo
- python-dotenv — хранение токена бота в `.env`-файле
- SQLite — хранение подписок и уже отправленных заказов

## Требования

- Python 3.12+
- Google Chrome + подходящий ChromeDriver (для Selenium)

## Как это работает

- Ручной поиск. Задача попадает в глобальную очередь — одновременно парсит только один пользователь, остальные ждут (защита от блокировок). Kwork парсится через requests (JSON внутри HTML), YouDo — через Selenium в отдельном потоке. Результаты обоих источников складываются в .txt файл.

- Подписка. Фоновый поток раз в 5 минут собирает уникальные слова всех пользователей из бд, парсит каждый источник отдельно и раздаёт результаты каждому по его словам.

- Новые заказы. Kwork — по времени публикации (последние ~5 минут). YouDo — по id в таблице youdo_jobs. При первом парсинге нового слова заказы запоминаются в youdo_jobs без отправки (таблица youdo_word_baseline), чтобы не прилетели сразу все старые.

- Данные. id.db — подписки, ww.db — id заказов YouDo и baseline-слова, <chat_id>.txt — временные результаты ручного поиска.

## Установка

```bash
git clone https://github.com/MistorX/Freelance-Jobs-Parser-Bot.git
cd Freelance-Jobs-Parser-Bot
pip install -r requirements.txt
```

## Настройка

В корне проекта создайте или найдите файл `.env` и укажите в нём токен, полученный у [@BotFather](https://t.me/BotFather):

```
TOKEN=your_telegram_bot_token
```

## Запуск

Для запуска бота выполните:

```bash
python bot_telegram.py
```

Также можно запустить скрипты парсинга Kwork и YouDo отдельно:

Для Kwork:
```bash
python parser_kwork.py
```

Для YouDo:
```bash
python parser_youdo.py
```

## Структура проекта

```
.
├── bot_telegram.py     # логика бота и обработчики команд
├── parser_kwork.py     # парсинг Kwork
├── parser_youdo.py     # парсинг YouDo
├── requirements.txt
├── id.db               # подписки пользователей (создаётся автоматически)
├── ww.db               # уже отправленные заказы YouDo (создаётся автоматически)
└── .env                # токен бота (не коммитить)
```

