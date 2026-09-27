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

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

parsing_status = {} #хрнаит ид и статус цикла парсера

@bot.message_handler(commands=['start', 'Спарсить сайт'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_parse = types.KeyboardButton(text="Спарсить сайт")
    markup.add(button_parse)
    first_mesage = bot.send_message(message.chat.id, "Это бот для поиска вакансий по ключевым словам в описании, для поиска введите ключевые слова через запятую:", reply_markup=markup)
    print(message.text)
    bot.register_next_step_handler(first_mesage, parsing)

@bot.message_handler(func=lambda message: message.text == "Спарсить сайт")
def parse_in_button(message):
    first_mesage = bot.send_message(message.chat.id, "Для поиска введите ключевые слова через запятую:")
    print(message.text)
    bot.register_next_step_handler(first_mesage, parsing)

@bot.message_handler(func=lambda message: message.text == "Остановить поиск")
def stop_parsing(message):
    chat_id = message.chat.id
    parsing_status[chat_id] = "False"

#отдельный поток для парсинга
def parsing(message):
    threading.Thread(target=parsing_work, args=(message,), daemon=True).start()

#основная функция парсера
def parsing_work(message):
    g_word = message.text
    print(g_word)
    word_1 = g_word.split(',')
    count_of_jobs = 0
    stop_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    stop_markup.add(types.KeyboardButton(text="Остановить поиск"))
    parsing_status[message.chat.id] = "True"
    bot.send_message(message.chat.id, 'Начинаю поиск', reply_markup=stop_markup)
    
    #парсинг youdo через selenium
    result_holder = {}

    def parse_on_udo(message):
        global parsing_status
        all_parse_udo = '' 
        for words in word_1:
            if parsing_status[message.chat.id] == 'False':
                main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                main_markup.add(types.KeyboardButton(text="Спарсить сайт"))
                bot.send_message(message.chat.id, "Поиск остановлен", reply_markup=main_markup)
                break
            out_of_youdo = parse_youdo(words)
            all_parse_udo += out_of_youdo
            if len(out_of_youdo) < 4090 and len(out_of_youdo) > 100:
                bot.send_message(message.chat.id, out_of_youdo)
            else:
               chunk_size = 4000
               for i in range(0, len(out_of_youdo), chunk_size):
                   bot.send_message(message.chat.id, out_of_youdo[i:i+chunk_size])
        result_holder['udo'] = all_parse_udo

    udo_thread = threading.Thread(target=parse_on_udo, args=(message,), daemon=True)
    udo_thread.start()

    #парсинг Kwork через requests по тегам json
    all_kworks = parse_kwork(word_1)
    kwork_for_txt = ''
    for kwork in all_kworks:
        count_of_jobs += 1
        bot.send_message(message.chat.id, kwork)
        kwork_for_txt += kwork
        time.sleep(0.2)
        if parsing_status[message.chat.id] == 'False':
            main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            main_markup.add(types.KeyboardButton(text="Спарсить сайт"))
            bot.send_message(message.chat.id, "Поиск остановлен", reply_markup=main_markup)
            break

    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    main_markup.add(types.KeyboardButton(text="Спарсить сайт"))
    bot.send_message(message.chat.id, "Поиск завершён", reply_markup=main_markup)
    udo_thread.join()
    all_parse_udo = result_holder.get('udo', '')
    if count_of_jobs == 0:
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
    with open(str(chat_id) + '.txt', 'r', encoding='utf-8') as f:
        file_send = f.read()
    with open(str(chat_id) + '.txt', 'rb') as f:
        bot.send_document(chat_id, f)
    
if __name__ == '__main__':
    bot.infinity_polling()
