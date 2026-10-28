from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import random
import html

def parse_youdo(word, parse_only_new: bool = False):
    driver = None
    db = None

    print(f'Парсинг YouDo по ключевым словам: {word}')
    try:
        #создание таблицы которая будет хранить id заказов 
        db = sqlite3.connect('ww.db')
        c = db.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS youdo_jobs
                     (id TEXT UNIQUE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS youdo_word_baseline
             (word TEXT PRIMARY KEY)''')

        count_of_jobs = 0
        #создание и запуск драйвера
        url = "https://youdo.com/tasks-all-opened-all"
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()

        driver.get(url)
        time.sleep(2)
           
        if parse_only_new == True:
            all_out_of_udo = {}
        else:
            all_out_of_udo = ''
        
        #сам парминг
        if isinstance(word, str):
            word_parts = word.split(',')
        else:
            word_parts = word

        search_words = []
        for part in word_parts:
            keyword = str(part).strip()
            if keyword:
                search_words.append(keyword)

        titles_list = []
        price_list = []
        list_url_udo = []
        list_id_url = []
        db_id_list = []
        db_id = c.execute("SELECT id FROM youdo_jobs").fetchall()
        for row in db_id:
            db_id_list.append(row[0])
        
        baseline_words = []
        baseline_rows = c.execute("SELECT word FROM youdo_word_baseline").fetchall()
        for row in baseline_rows:
            baseline_words.append(row[0])

        for keyword in search_words:
            kw = keyword.casefold()
            first_time = kw not in baseline_words

            button_find = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]'))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();",
                button_find
            )
            button_find.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
            button_find.send_keys(keyword)

            button_search = driver.find_element(By.CSS_SELECTOR, 'button[data-sentry-source-file="KeywordsFilter.tsx"]')
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button_search)
            time.sleep(1)

            try:
                title_elements = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-sentry-source-file="TaskItem.tsx"]'))
                )
            except:
                title_elements = []
                continue

            for title_element in title_elements:
                title_text = title_element.text.strip()
                if len(title_text) <= 2:
                    continue
            
                task_url = title_element.get_attribute('href')
            
                try:
                    task_price = title_element.find_element(
                        By.XPATH, 'ancestor::li[1]//span[@data-sentry-component="Money"]'
                    ).get_attribute('textContent').strip().replace('\xa0', ' ')
                except NoSuchElementException:
                    task_price = ''

                if parse_only_new == False:                    
                    price_list.append(task_price)
                    list_url_udo.append(task_url)
                titles_list.append(title_text)
                id_url = task_url.split('?')[0].rstrip('/').rsplit('/', 1)[-1]
                list_id_url.append(id_url)

                if parse_only_new == True:
                    if id_url not in db_id_list:
                        if not first_time:
                            job_text = (
                                f'📌 <b>Новый заказ</b>\n\n'
                                f'<i>{html.escape(title_text)}</i>\n\n'
                                f'💰 Цена: <b>{html.escape(task_price)}</b>\n'
                                f'🔗 <a href="{task_url}">Открыть на YouDo</a>\n\n'
                            )
                            all_out_of_udo.setdefault(kw, []).append(job_text)
                        c.execute("INSERT OR IGNORE INTO youdo_jobs VALUES (?)", (id_url,))
                        db_id_list.append(id_url)
                        
            if parse_only_new == True and first_time:
                c.execute("INSERT OR IGNORE INTO youdo_word_baseline VALUES (?)", (kw,))
                baseline_words.append(kw)

            time.sleep(random.uniform(3, 8))

        db.commit()

        count_of_jobs = len(titles_list)
        
        #формируем ответ
        if parse_only_new == False:
            out_of_youdo = '🔶 <b>YouDo</b> — https://youdo.com/tasks-all-opened-all\n\n'
            for i in range(len(titles_list)):
                out_of_youdo += (
                    f'📌 Новый заказ (YouDo)\n'
                    f'📝 {html.escape(titles_list[i])}\n'
                    f'💰 Цена: {html.escape(price_list[i])}\n'
                    f'🔗 {list_url_udo[i]}\n\n'
                )
            out_of_youdo += 'Количество найденных заданий: ' + str(count_of_jobs)
            all_out_of_udo = out_of_youdo
        return all_out_of_udo
    finally:
        if driver is not None:
            try: driver.quit()
            except Exception: pass
        if db is not None:
            try: db.close()
            except Exception: pass

if __name__ == "__main__":
    task = input("Введите ключевые слова через запятую: ")
    result = parse_youdo(task)
    print(result)
