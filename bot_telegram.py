import telebot
import time
from dotenv import load_dotenv
import os
from telebot import types
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from parser_youdo import parse_youdo
from parser_kwork import parse_kwork
from datetime import datetime
import sqlite3
from contextlib import closing
import queue
import html as html_lib

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'), parse_mode='HTML')

with closing(sqlite3.connect('id.db', timeout=30)) as conn:
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS id "
            "(id_user TEXT UNIQUE, word_parse TEXT)"
        )

parsing_status = {} #хрнаит ид и статус цикла парсера

#очередь для задач парсинга чтобы не было блокировок от сайтов
parse_queue = queue.Queue()

def parse_worker():
    while True:
        task = parse_queue.get()
        try:
            task["func"](*task["args"], **task["kwargs"])
        except Exception as e:
            print("Worker error:", e)
        finally:
            parse_queue.task_done()
        time.sleep(10)  

bot.set_my_commands([
    types.BotCommand("start", "🏠 Главное меню"),
    types.BotCommand("help", "❓ Помощь"),
])

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "<b>❓ Помощь</b>\n\n"
        "<b>🔍 Ручной поиск</b>\n"
        "Нажмите «Найти сейчас» → введите слова через запятую → "
        "получите результаты и файл.\n\n"
        "<b>🔔 Подписка</b>\n"
        "Нажмите «Подписка» → введите слова. Бот будет присылать "
        "только новые заказы раз в иногда.\n\n"
        "<b>⚙️ Управление подпиской</b>\n"
        "Через «Подписка» → «Информация о рассылке».\n\n"
        "<b>💡 Примеры слов</b>\n"
        "<code>python, парсинг, телеграм</code>\n"
        "<code>дизайн, логотип, figma</code>\n"
        "<code>копирайтинг, статья</code>",
        parse_mode="HTML"
    )

#основная клавиатура
def defoolt_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_parse = types.KeyboardButton(text="🔍 Найти сейчас")
    button_news = types.KeyboardButton(text="🔔 Подписка")
    button_menu = types.KeyboardButton(text="🏠 Меню")
    markup.add(button_parse, button_menu)
    markup.add(button_news)
    return markup

#Меню бота
def main_menu(message):
    markup = defoolt_markup()
    preview_options = types.LinkPreviewOptions(is_disabled=True)
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton(
        text="⚙️ Управление подпиской",
        callback_data="settings"
    ))
    inline_markup.add(types.InlineKeyboardButton(
        text="📖 О проекте",
        url="https://github.com/MistorX/Freelance-Jobs-Parser-Bot"
    ))
    bot.send_message(
        message.chat.id,
        "👋 <b>Добро пожаловать в Freelance Jobs Parser Bot!</b>\n\n"
        "🔎 Помогаю находить заказы на биржах:\n"
        "• <b>Kwork</b> — kwork.ru\n"
        "• <b>YouDo</b> — youdo.com\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Искать заказы по вашим словам прямо сейчас\n"
        "• Присылать только новые заказы по подписке\n"
        "• Выгружать результаты в файл\n\n"
        "👇 Выберите действие на клавиатуре ниже",
        reply_markup=inline_markup,
        link_preview_options=preview_options
    )
    bot.send_message(message.chat.id, "Чтоб автоматически получать уведомления о новых заказах, нажмите «🔔 Подписка»", reply_markup=markup)

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == '🏠 Меню')
@bot.message_handler(func=lambda message: message.text == 'Назад')
def start(message):
    main_menu(message)

#выводит информаци. о пользователе из бд
@bot.callback_query_handler(func=lambda call: call.data == "settings")
def settings_info(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    with closing(sqlite3.connect('id.db', timeout=30)) as conn:
        with conn:
            result = conn.execute(
                "SELECT word_parse FROM id WHERE id_user = ?",
                (str(chat_id),)
            ).fetchone()
    if result:
        markups = types.InlineKeyboardMarkup()
        button_cancellation = types.InlineKeyboardButton(text="Отключить уведомления", callback_data="cancel_notifications")
        button_changes = types.InlineKeyboardButton(text="Изменить ключевые слова", callback_data="change_keywords")
        markups.add(button_changes)
        markups.add(button_cancellation)
        bot.send_message(
            call.message.chat.id,
            f"⚙️ <b>Ваша подписка</b>\n\n"
            f"🔑 Ключевые слова:\n<code>{html_lib.escape(result[0])}</code>",
            reply_markup=markups
        )
    else:
        markup = types.InlineKeyboardMarkup()
        button_changes = types.InlineKeyboardButton(text="Установить ключевые слова", callback_data="change_keywords")
        markup.add(button_changes)
        bot.send_message(
            call.message.chat.id,
            "⚙️ <b>Подписка не оформлена</b>\n\n"
            "Нажмите кнопку ниже, чтобы установить ключевые слова.",
            reply_markup=markup
        )
        

@bot.message_handler(func=lambda message: message.text == "🔍 Найти сейчас")
def parse_in_button(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(text="Назад"))
    first_mesage = bot.send_message(message.chat.id, "Для поиска введите ключевые слова через запятую:", reply_markup=markup)
    bot.register_next_step_handler(first_mesage, parsing)

@bot.message_handler(func=lambda message: message.text == "Остановить поиск")
def stop_parsing(message):
    chat_id = message.chat.id
    parsing_status[chat_id] = "False"

#отдельный поток для парсинга
def parsing(message):
    if message.text == "Назад":
        main_menu(message)
        return
    parse_queue.put({
        "func": parsing_work,
        "args": (message,),
        "kwargs": {}
    })
    bot.send_message(message.chat.id, f"Вы в очереди. Позиция: {parse_queue.qsize()}")

#основная функция парсера
def parsing_work(message):
    g_word = message.text
    print(g_word)
    #приводим слова в приемлемый вид
    word_2 = g_word.split(',')
    word_1 = []
    for w in word_2:
        if w.strip():
            word_1.append(w.strip())
    if not word_1:
        first_mesage = bot.send_message(message.chat.id, "Введите хотя бы одно ключевое слово для поиска")
        bot.register_next_step_handler(first_mesage, parsing)
        return
    print("Ключевые слова для поиска:", word_1)
    count_of_jobs = 0
    stop_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    stop_markup.add(types.KeyboardButton(text="Остановить поиск"))
    parsing_status[message.chat.id] = "True"
    bot.send_message(message.chat.id, 'Начинаю поиск', reply_markup=stop_markup)
    
    #парсинг youdo через selenium
    result_holder = {}

    def parse_on_udo(message):
        all_parse_udo = ''
        try:
            try:
                out_of_youdo = parse_youdo(word_1)
            except Exception as e:
                import traceback; traceback.print_exc()
                bot.send_message(message.chat.id, f"Ошибка парсинга YouDo: {e}")
                out_of_youdo = ''
            all_parse_udo += out_of_youdo
            if 100 < len(out_of_youdo) < 4090:
                bot.send_message(message.chat.id, out_of_youdo)
            else:
                for i in range(0, len(out_of_youdo), 4000):
                    if out_of_youdo[i:i+4000]:
                        bot.send_message(message.chat.id, out_of_youdo[i:i+4000])
        finally:
            result_holder['udo'] = all_parse_udo

    udo_thread = threading.Thread(target=parse_on_udo, args=(message,), daemon=True)
    udo_thread.start()

    #парсинг Kwork через requests по тегам json
    all_kworks = parse_kwork(word_1)
    kwork_1_message = '🔷 <b>Kwork</b>\n\n'
    kwork_for_txt = ''
    for kwork in all_kworks:
        count_of_jobs += 1
        if len(kwork_1_message + kwork) < 4000:
            kwork_1_message += kwork
        else:
            bot.send_message(message.chat.id, kwork_1_message)
            kwork_1_message = '🔷 <b>Kwork</b>\n\n' + kwork
        kwork_for_txt += kwork
        time.sleep(0.2)
        if parsing_status[message.chat.id] == 'False':
            main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            main_markup.add(types.KeyboardButton(text="Спарсить сайт"))
            bot.send_message(message.chat.id, "Поиск остановлен", reply_markup=main_markup)
            break
    if kwork_1_message != '🔷 <b>Kwork</b>\n\n':
        bot.send_message(message.chat.id, kwork_1_message)

    main_markup = defoolt_markup()
    udo_thread.join()
    bot.send_message(message.chat.id, "Поиск завершён", reply_markup=main_markup)
    all_parse_udo = result_holder.get('udo', '')
    if count_of_jobs == 0 and not all_parse_udo.strip():
        bot.send_message(message.chat.id, "По вашему запросу ничего не найдено")
    else:
        markup1 = types.InlineKeyboardMarkup()
        btn_txt = types.InlineKeyboardButton(text='Скачать результат', callback_data='download_txt')
        markup1.add(btn_txt)
        with open(str(message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
            f.write(kwork_for_txt + '\n' + all_parse_udo)
        print("Проектов найдено:", count_of_jobs)
        bot.send_message(message.chat.id, "Найдено проектов на kwork:" + str(count_of_jobs), reply_markup=markup1)


@bot.callback_query_handler(func=lambda call: call.data == "download_txt")
def download_data(call):
    chat_id = call.message.chat.id
    with open(str(chat_id) + '.txt', 'rb') as f:
        bot.send_document(chat_id, f)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == "🔔 Подписка")
def send_notifications(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup_close = types.KeyboardButton(text="Назад")
    markup.add(markup_close)
    bot.send_message(message.chat.id, "Введите ключевые слова для поиска", reply_markup=markup)
    bot.register_next_step_handler(message, parse_new)

@bot.callback_query_handler(func=lambda call: call.data == "change_keywords")
def change_keywords(call):
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup_close = types.KeyboardButton(text="Назад")
    markup.add(markup_close)
    bot.send_message(call.message.chat.id, "Введите новые ключевые слова для поиска", reply_markup=markup)
    bot.register_next_step_handler(call.message, parse_new)

def parse_new(message): #записывает ключевые слова в бд для рассылки уведомлений
    g_word = message.text
    if g_word == "Назад":
        main_menu(message)
        return
    x_word = g_word.split(',')
    g_word = [el.strip() for el in x_word if el.strip()]
    if not g_word:
        first_mesage = bot.send_message(message.chat.id, "Введите хотя бы одно ключевое слово для поиска")
        bot.register_next_step_handler(first_mesage, parse_new)
        return

    with closing(sqlite3.connect('id.db', timeout=30)) as conn:
        with conn:
            conn.execute(
                "INSERT INTO id (id_user, word_parse) VALUES (?, ?) "
                "ON CONFLICT(id_user) DO UPDATE SET word_parse = excluded.word_parse",
                (str(message.chat.id), ",".join(g_word).casefold())
            )

    markups = defoolt_markup()
    bot.send_message(message.chat.id, "✅ <b>Ключевые слова сохранены</b>\n\nСкоро здесь появятся новые заказы", reply_markup=markups)

@bot.message_handler(func=lambda message: message.text == "Отключить уведомления")
def disable_notifications(message):
    with closing(sqlite3.connect('id.db', timeout=30)) as conn:
        with conn:
            conn.execute(
                "DELETE FROM id WHERE id_user = ?",
                (str(message.chat.id),)
            )
    markup = defoolt_markup()
    bot.send_message(message.chat.id, "Уведомления отключены", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_notifications")
def disable_notifications_callback(call):
    with closing(sqlite3.connect('id.db', timeout=30)) as conn:
        with conn:
            conn.execute(
                "DELETE FROM id WHERE id_user = ?",
                (str(call.message.chat.id),)
            )
    bot.answer_callback_query(call.id)
    markup = defoolt_markup()
    bot.send_message(call.message.chat.id, "Уведомления отключены", reply_markup=markup)

def send_new_orders(stop_event, interval=300):
    while not stop_event.wait(interval):
        try:
            with sqlite3.connect("id.db", timeout=30) as conn:
                users = conn.execute(
                    "SELECT id_user, word_parse FROM id"
                ).fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка чтения подписок: {e}")
            continue

        subscriptions = {}
        all_words = []
        seen_words = set()

        # Собираем подписки пользователей и общий список уникальных слов.
        for chat_id, raw_words in users:
            word_list = []
            user_words = set()

            for part in (raw_words or "").split(","):
                keyword = part.strip()
                normalized_keyword = keyword.casefold()

                if keyword and normalized_keyword not in user_words:
                    word_list.append(keyword)
                    user_words.add(normalized_keyword)

                if keyword and normalized_keyword not in seen_words:
                    all_words.append(keyword)
                    seen_words.add(normalized_keyword)

            if word_list:
                subscriptions[chat_id] = word_list

        # Для каждого уникального слова парсим сайты 
        try:
            kworks_by_word = parse_kwork(all_words, parse_only_new=True)
        except Exception as e:
            print("Kwork parse error:", e)
            kworks_by_word = {}
        
        try:
            youdo_by_word = parse_youdo(all_words, parse_only_new=True)
        except Exception as e:
            print("YouDo parse error:", e)
            youdo_by_word = {}

        for chat_id, word_list in subscriptions.items():
            try:
                kworks = []
                seen_kworks = set()
                youdo_results = []
                seen_youdo = set()

                for keyword in word_list:
                    for item in kworks_by_word.get(keyword, []):
                        if item not in seen_kworks:
                            kworks.append(item)
                            seen_kworks.add(item)

                    for item in youdo_by_word.get(keyword, []):
                        if item not in seen_youdo:
                            youdo_results.append(item)
                            seen_youdo.add(item)

                if not kworks and not youdo_results:
                    continue

                bot.send_message(chat_id, "🔔 <b>Новые заказы</b>\n\n")

                messages = []
                if kworks:
                    messages.append("Kwork:\n" + "\n".join(kworks))
                messages.extend(youdo_results)

                for text in messages:
                    for start in range(0, len(text), 4000):
                        if text[start:start + 4000]:
                            bot.send_message(chat_id, text[start:start + 4000])

            except Exception as e:
                print(f"Ошибка отправки пользователю {chat_id}: {e}")


if __name__ == '__main__':
    stop_event = threading.Event()
    threading.Thread(
        target=send_new_orders,
        args=(stop_event,),
        kwargs={"interval": 300},
        daemon=True
    ).start()
    threading.Thread(target=parse_worker, daemon=True).start()
    bot.infinity_polling()
