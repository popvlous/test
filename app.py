import requests as requests
from flask import Flask, current_app
from bs4 import BeautifulSoup
import time
from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
app = Flask(__name__)

LINE_TOKEN = 'qUYZTP3u08ugL8mCGJNSKJis45VlHO3RnjWdCuWUcoZ'


@app.route('/')
def hello_world():
    lineNotifyMessage(LINE_TOKEN, '歡迎登入系統')
    sendActionRecordJob()
    url = "http://www.google.com"
    options = create_options()
    driver = webdriver.Chrome()
    driver.get(url)
    # 定位搜尋框
    element = driver.find_element(By.ID, "APjFqb")
    # 傳入字串
    element.send_keys("未平倉")
    button = driver.find_element(By.CLASS_NAME, "gNO89b")
    button.click()
    # 回傳最先找到的元素，若沒有找到則會跳 error
    data = driver.find_element(By.PARTIAL_LINK_TEXT, "交易資訊-三大法人-查詢-區分各期貨契約-依日期").text
    print(data)
    lineNotifyMessage(LINE_TOKEN, f' data: {data} ')

    # 會尋找目前葉面當中所有符合條件的元素，並回傳一個 list，若沒找到會回傳一個空 list
    datas = driver.find_elements(By.PARTIAL_LINK_TEXT, "交易資訊-三大法人-查詢-區分各期貨契約-依日期")
    [lineNotifyMessage(LINE_TOKEN, f' tmp: {tmp} ') for tmp in datas]
    return data


def create_options() -> Options:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")

    return options


def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,  # 權杖，Bearer 的空格不要刪掉呦
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}

    # Post 封包出去給 Line Notify
    r = requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        params=payload)
    return r.status_code


def sendActionRecordJob():
    lineNotifyMessage(LINE_TOKEN, f' 溫馨提醒: 開始抓取網站資料 ')
    url = 'https://www.taifex.com.tw/cht/3/futContractsDate'  # 台積電 Yahoo 股市網址
    web = requests.get(url)  # 取得網頁內容
    soup = BeautifulSoup(web.text, "html.parser")  # 轉換內容
    try:
        result = ''
        tdlist = []
        result_list = []
        tr = soup.find_all(class_="table_f", limit=3)
        for trr in tr:
            tdlist = trr.find_all('td')
        for i in range(len(tdlist)):
            result += str(tdlist[i].text).strip() + ';'
        result_list = result.split(';')
        lineNotifyMessage(LINE_TOKEN, f' 新聞標題: {result_list} ')
        lineNotifyMessage(LINE_TOKEN, f' 溫馨提醒: https://www.taifex.com.tw/cht/3/futContractsDate，抓取資料完畢 ')
    except Exception as err:
        current_app.logger.error(f'sendActionRecord 發生錯誤: {err}')
        lineNotifyMessage(LINE_TOKEN, f'溫馨提醒: https://www.taifex.com.tw/cht/3/futContractsDate 發生錯誤: {err}')


if __name__ == '__main__':
    app.run()
