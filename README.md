# Freelance Jobs Parser Bot

Telegram-бот для поиска заказов по ключевым словам в описании. Бот парсит площадки [Kwork](https://kwork.ru/projects) и [YouDo](https://youdo.com/tasks-all-opened-all) и присылает результаты в чат.

## Возможности

- Поиск заказов сразу на двух площадках: Kwork (через парсинг JSON-данных страницы) и YouDo (через Selenium)
- Поиск сразу по нескольким ключевым словам
- Выгрузка найденных заказов в txt файл
- Для параллельного парсинга используется несколько потоков

## Технологии

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (telebot) — Telegram Bot API
- requests — запросы к Kwork
- selenium — headless парсинг YouDo
- python-dotenv — хранение токена бота в `.env`-файле

## Требования

- Python 3.12+
- Google Chrome + подходящий ChromeDriver (для Selenium)

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

## Как пользоваться

1. Напишите боту `/start` или нажмите «Спарсить сайт»
2. Введите ключевые слова через запятую
3. Бот найдёт подходящие заказы и отправит их в чат

## Структура проекта

```
.
├── bot_telegram.py     # логика бота и обработчики команд
├── parser_kwork.py     # парсинг Kwork
├── parser_youdo.py     # парсинг YouDo
├── requirements.txt
└── .env                # токен бота (не в репозитории)
```

## Лицензия

MIT