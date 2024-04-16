import json
import string
from urllib import request

import proto
import requests as requests
from flask import Flask, current_app
from bs4 import BeautifulSoup
import time
from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai
import os
import fitz
import re
from opencc import OpenCC
from pypdf import PdfReader
import PyPDF2
import time
import fitz
import pytesseract
from PIL import Image

# coding: utf-8
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from random import choice

# line token
channel_access_token = 'u2lKAnt/xacOJW9IUTrrC77YP0YsrqICiocYE0TzwWr6zsPJLd7+/j/0kyH4LcfWf4IVr0QuFz9Txe60RsEKPsmDXbkDKygFLrN5riFmK83f/YhpO9opziz/PWs5AE1kFHxgt0Yku3HY34I8JvIFIQdB04t89/1O/w1cDnyilFU='
channel_secret = '63cab70334966c3908e47bf86edcfbe7'
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(__name__, static_folder='image/static', static_url_path='/static')

genai.configure(api_key='AIzaSyA89Mv9_J_ZWuqry0L6vRaoRUBouq1NYDA')

LINE_TOKEN = 'qUYZTP3u08ugL8mCGJNSKJis45VlHO3RnjWdCuWUcoZ'

ngrok_url = 'https://f81a-211-72-15-212.ngrok-free.app/'

pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\\tesseract.exe'



def s2twp_converter(simplified_text):
    # 創建 OpenCC 物件，指定簡體到臺灣繁體的轉換
    cc = OpenCC('s2twp')

    # 使用 convert 方法進行轉換
    traditional_text = cc.convert(simplified_text)

    return traditional_text


@app.route("/", methods=['GET'])
def home():
    pdfimage()
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content('Please summarise this document: ...')
    return response.text


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # echo
    msg = event.message.text
    reply_msg = ''
    if msg.startswith('/美股'):
        reply_msg = us()
    elif msg.startswith('/長輩圖'):
        files_lists = os.listdir('image/static/')
        if files_lists:
            files_lists_count = len(files_lists)
        pic_name = choice(files_lists)
        image = ImageSendMessage(original_content_url=ngrok_url + "/static/" + pic_name,
                                 preview_image_url=ngrok_url + "/static/" + pic_name)
        line_bot_api.reply_message(event.reply_token, image)
        reply_msg = "今日長輩圖"
    else:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(msg)
        try:
            print(response.text)
            reply_msg = response.text
        except ValueError:
            # If the response doesn't contain text, check if the prompt was blocked.
            print(response.prompt_feedback)
            reply_msg = "我想想，可否更具體的描述呢？"
    message = TextSendMessage(text=reply_msg)
    line_bot_api.reply_message(event.reply_token, message)


# fred
@app.route('/us')
def us():
    lineNotifyMessage(LINE_TOKEN, '獲取美國股市指數')
    url = "https://tw.stock.yahoo.com/markets"
    web = requests.get(url)  # 取得網頁內容
    soup = BeautifulSoup(web.text, "html.parser")  # 轉換內容
    try:
        result = ''
        tdlist = []
        result_list = []
        tr = soup.find_all(class_="D(f) Fxw(w) Fw(600) Mb(8px) Lh(n)", limit=6)
        for trr in tr:
            tdlist.append(trr.text)
        for i in range(len(tdlist)):
            result += str(tdlist[i]).strip() + ';'
        result_list = result.split(';')
        lineNotifyMessage(LINE_TOKEN,
                          f' 國際指數: \n\n道瓊工業指數: {result_list[0]}, \n\nSP 500指數: {result_list[1]}, \n\nNASDAQ指數: {result_list[2]}, \n\n費城半導體指數: {result_list[3]}, \n\n日經225指數: {result_list[4]}, \n\n香港恒生指數: {result_list[5]}')
        lineNotifyMessage(LINE_TOKEN, f' 溫馨提醒: 國際指數，抓取資料完畢 ')
        return f' 國際指數: \n\n道瓊工業指數: {result_list[0]}, \n\nSP 500指數: {result_list[1]}, \n\nNASDAQ指數: {result_list[2]}, \n\n費城半導體指數: {result_list[3]}, \n\n日經225指數: {result_list[4]}, \n\n香港恒生指數: {result_list[5]}'
    except Exception as err:
        current_app.logger.error(f'sendActionRecord 發生錯誤: {err}')
        lineNotifyMessage(LINE_TOKEN, f'溫馨提醒: https://www.taifex.com.tw/cht/3/futContractsDate 發生錯誤: {err}')
        return err


def is_punctuation(char):
    return char in string.punctuation


def extract_text(self,file_name):
    extract_text = '' # 用于存储提取的文本
    doc = fitz.open(file_name)
    # 遍历每一页pdf
    for i in range(len(doc)):
        img_list = doc.get_page_images(i) # 提取该页中的所有img
        # 遍历每页中的图片，
        for num, img in enumerate(img_list):
            img_name = f"{self.dir_path}/{i + 1}_{num + 1}.png" # 存储的图片名
            pix = fitz.Pixmap(doc, img[0])  # image转pixmap
            if pix.n - pix.alpha >= 4:  # 如果差值大于等于4，需要转化后才能保存为png
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(img_name) # 存储图片
            pix = None  # 释放Pixmap资源
            image = Image.open(img_name)
            text = pytesseract.image_to_string(image,'rus') # 调用tesseract，使用俄语库
            extract_text += text # 写入文本
            os.remove(img_name)
    return extract_text


@app.route('/pdf')
def pdf():
    doc = fitz.open('doc/change.pdf')
    path = 'doc/output.txt'
    f = open(path, 'w')
    text = ""
    for page in doc:
        text += page.get_text()
        temp = re.sub('[a-zA-Z0-9]', '', page.get_text())
        str1 = re.sub('[\n]+', '\n', temp)
        str1 = str1.strip()
        new_text = s2twp_converter(
            str1.replace(",", "").replace(".", "").replace(";", "").replace("?", "").replace(":", "").replace("'",
                                                                                                              "").replace(
                "~", "").replace("《佛先菜根谭》", "").replace("（丣英对照版）", "").replace("-", "").replace(".\n",
                                                                                                          "").replace(
                "()", ""))
        f.write(new_text)
    print(text)
    f.close()

    # coding:utf-8

    file1 = open(path, 'r', encoding='utf-8')  # 打开要去掉空行的文件
    file2 = open('doc/new_output.txt', 'w', encoding='utf-8')  # 生成没有空行的文件

    for text in file1.readlines():
        if text.split():
            file2.write(text)

    file1.close()
    file2.close()

    return "finish"


@app.route('/pdfimage')
def pdfimage():
    doc = fitz.open('doc/change.pdf')
    path = 'doc/output.txt'
    f = open(path, 'w' ,encoding='UTF-8')
    # 遍历每一页pdf
    for i in range(len(doc)):
        img_list = doc.get_page_images(i) # 提取该页中的所有img
        # 遍历每页中的图片，
        for num, img in enumerate(img_list):
            img_name = f"doc/{i + 1}_{num + 1}.png" # 存储的图片名
            pix = fitz.Pixmap(doc, img[0])  # image转pixmap
            if pix.n - pix.alpha >= 4:  # 如果差值大于等于4，需要转化后才能保存为png
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(img_name) # 存储图片
            pix = None  # 释放Pixmap资源
            image = Image.open(img_name)
            text = pytesseract.image_to_string(image,'chi_sim') # 调用tesseract，使用俄语库
            f.write(text)
            os.remove(img_name)
    f.close()
    return "finish"


# fred
@app.route('/test')
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
