import time
import requests
import json
import re
import html
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_kwork(word_parse, parse_only_new: bool = False):
    url = "https://kwork.ru/projects"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    page_number = 0
    MOSCOW_TZ = ZoneInfo("Europe/Moscow")
    dict_sort = {}
    list_kwork = []
    print(f'парсинг Kwork по ключевым словам: {word_parse}')

    def clean(text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text or "")
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    run = True
    while run and page_number != 10:
        try:
            page_number += 1
            params = {'page': page_number}
            responce = requests.get(url, headers=headers, params=params)
            responce_text = responce.text  
            #оставляем только чистый json
            i = responce_text.find("window.stateData=")
            json_text, _ = json.JSONDecoder().raw_decode(responce_text[i + len("window.stateData="):])           
            
            items = json_text["wantsListData"]["pagination"]["data"]
            out = []
            time_now = datetime.now(MOSCOW_TZ)
            if parse_only_new == True: #если парсинг только новых проектов то останавливаем цикл на проектах старше 5 минут 
                for item in items:
                    time_work = datetime.strptime(item.get("date_active"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=MOSCOW_TZ)
                    left = int((time_now - time_work).total_seconds() // 60)
                    print(time_work, left)
                    if 0 <= left <= 5: 
                            out.append({
                            "url": f"https://kwork.ru/projects/{item['id']}/view",
                            "decription": clean(item.get("description", "")), 
                            "price": item.get("priceLimit"),
                            "data": item.get("date_active"),
                        })
                    else:
                        run = False
                        break
            else:
                for item in items:
                    out.append({
                            "url": f"https://kwork.ru/projects/{item['id']}/view",
                            "decription": clean(item.get("description", "")), 
                            "price": item.get("priceLimit"),
                            "data": item.get("date_active"),
                        })
            out_sort = ''
            for i in out:
                for word in word_parse:
                    if word.lower() in i["decription"].lower():
                        out_sort = ''
                        description = html.escape(i["decription"])
                        price = html.escape(str(i["price"]))
                        if len(description) > 300:
                            description_short = description[:300] + '...'
                        else:
                            description_short = description
                        out_sort = (
                            f'📌 Новый заказ (Kwork)\n'
                            f'📝 {description_short}\n'
                            f'💰 Цена: {price}\n'
                            f'🔗 {i["url"]}\n\n'
                        )
                        if parse_only_new == True:
                            if len(out_sort) < 4095:
                                dict_sort.setdefault(word.lower(), []).append(out_sort)
                            else:
                                dict_sort.setdefault(word.lower(), []).append(
                                    "Ссылка: " + i["url"] + "описание проекта слишком длинное"
                                )
                        else:
                            if len(out_sort) < 4095:
                                list_kwork.append(out_sort)
                            else:
                                list_kwork.append("Ссылка: " + i["url"] + "описание проекта слишком длинное")
                            break
            time.sleep(0.2)

        except Exception as e:
            print("Произошла ошибка:", str(e))
            run = False
            break
    if parse_only_new == True:
        return dict_sort
    else:
        return list_kwork



if __name__ == "__main__":
    task = input('Введите ключевые слова для поиска через запятую:')
    task = task.split(',')
    task = parse_kwork(task)
    out_kwork = ''
    for kwork in task:
        out_kwork += kwork 
    print(out_kwork)
    input()
