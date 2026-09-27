import time
import requests
import json
import re
import html


def parse_kwork(word_parse):
    url = "https://kwork.ru/projects"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    page_number = 0
    list_kwork = []
    run = True
    while run and page_number != 27:
        #if parsing_status[message.chat.id] == 'False':
        #    run = False
        #    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        #    main_markup.add(types.KeyboardButton(text="Спарсить сайт"))
        #    bot.send_message(message.chat.id, "Поиск остановлен", reply_markup=main_markup)
        #    return
        try:
            page_number += 1
            params = {'page': page_number}
            responce = requests.get(url, headers=headers, params=params)
            responce_text = responce.text  
            #оставляем только чистый json
            i = responce_text.find("window.stateData=")
            json_text, _ = json.JSONDecoder().raw_decode(responce_text[i + len("window.stateData="):])

            def clean(text: str) -> str:
                text = re.sub(r"<[^>]+>", " ", text or "")
                text = html.unescape(text)
                return re.sub(r"\s+", " ", text).strip()
            
            items = json_text["wantsListData"]["pagination"]["data"]
            out = []
            for item in items:
                    out.append({
                    "url": f"https://kwork.ru/projects/{item['id']}/view",
                    "decription": clean(item.get("description", "")), 
                    "price": item.get("priceLimit"),
                    "data": item.get("max_days"),
                })
            out_sort = ''
            for i in out:
                for word in word_parse:
                    if word.lower() in i["decription"].lower():
                        out_sort = 'Биржа: Kwork' + '\n'
                        out_sort += ("URL:" + i["url"] + '\n')
                        out_sort += ("Description:" + i["decription"] + '\n')
                        out_sort += ("Price:" + str(i["price"]) + '\n')
                        if len(out_sort) < 4095:
                            list_kwork.append(out_sort)
                        else:
                            list_kwork.append("URL:" + i["url"] + "описание проекта слишком длинное")
            time.sleep(0.2)

        except Exception as e:
            print("Произошла ошибка:", str(e))
            run = False
            break
    return list_kwork


if __name__ == "__main__":
    task = input('Введите ключевые слова для поиска через запятую:')
    task = task.split(',')
    task = parse_kwork(task)
    out_kwork = ''
    for kwork in task:
        out_kwork += kwork 
    print(out_kwork)

