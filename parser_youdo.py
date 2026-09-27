from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def parse_youdo(word):
    try:
        count_of_jobs = 0
        url = "https://youdo.com/tasks-all-opened-all"
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()

        response = driver.get(url)
        time.sleep(2)
           
        all_out_of_udo = ''
        
        button_find = driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
        button_find.send_keys(word)
        button_search = driver.find_element(By.CSS_SELECTOR, 'button[data-sentry-source-file="KeywordsFilter.tsx"]')
        time.sleep(1)
        driver.execute_script("arguments[0].click();", button_search)
        time.sleep(1)
        titles = driver.find_elements(By.CSS_SELECTOR, 'a[data-sentry-source-file="TaskItem.tsx"]')
        time.sleep(1)
        titles_list = []
        for title in titles:
            if len(title.text) > 2:
                titles_list.append(title.text)
                count_of_jobs += 1
        
        price = driver.find_elements(By.CSS_SELECTOR, 'span[data-sentry-source-file="Money.tsx"]')
        time.sleep(1)
        price_list = []
        for prise in price:
            if len(prise.text) > 2:
                price_list.append(prise.text)

        list_url_udo = []
        for i in range(len(titles_list)):
            url_udo = titles[i].get_attribute('href')
            list_url_udo.append(url_udo)

        #формируем ответ
        out_of_youdo = 'Биржа: YouDo https://youdo.com/tasks-all-opened-all' + '\n' + 'поиск по слову: ' + word + '\n'
        for i in range(len(titles_list)):
            out_of_youdo += titles_list[i] + '\n' + price_list[i] + '\n' + list_url_udo[i] + '\n'
        out_of_youdo += 'Количество найденных заданий: ' + str(count_of_jobs)
        return out_of_youdo
    finally:
        driver.quit()

if __name__ == "__main__":
    task = input("Введите ключевое слово для поиска на YouDo: ")
    print(parse_youdo(task))
