import json
import string
from urllib import request
import uuid

import google
import proto
import requests as requests
from flask import Flask, request, current_app, Response, render_template, redirect, jsonify, url_for
from bs4 import BeautifulSoup
import time

from google.oauth2 import service_account
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

import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.language_models import ChatModel, InputOutputTextPair, ChatMessage
from vertexai import generative_models
from google.cloud import language_v1
from google.cloud import aiplatform
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# coding: utf-8
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from random import choice
from firebase import firebase

# line token 星雲說
channel_access_token = 'u2lKAnt/xacOJW9IUTrrC77YP0YsrqICiocYE0TzwWr6zsPJLd7+/j/0kyH4LcfWf4IVr0QuFz9Txe60RsEKPsmDXbkDKygFLrN5riFmK83f/YhpO9opziz/PWs5AE1kFHxgt0Yku3HY34I8JvIFIQdB04t89/1O/w1cDnyilFU='
channel_secret = '63cab70334966c3908e47bf86edcfbe7'
ngrok_url = 'https://oasis.pyrarc.com'

firebase_url = 'https://pyrarc-official-default-rtdb.firebaseio.com/'

# line token 星雲大師說
# channel_access_token = 'yH/ouqK0h5Ikcg9Gvm8Z1DiY1nU8Jp1KFdudeDvHlE6YehLf8+S26CfKHkVWkMuwGNSY1LMW+cirlNRVukNFwRqezD1cNyYj8P9iuRnKo8JFFbxKFiFkAQ0YleSKF5w7ZNnn44vR+lDygFaamT9kcAdB04t89/1O/w1cDnyilFU='
# channel_secret = 'e619c7032c0b819501f24680c34e5761'
# ngrok_url = 'https://87bc-211-72-15-211.ngrok-free.app'
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(__name__, static_folder='image/static', template_folder='templates', static_url_path='/static')

genai.configure(api_key='AIzaSyA89Mv9_J_ZWuqry0L6vRaoRUBouq1NYDA')

LINE_TOKEN = 'qUYZTP3u08ugL8mCGJNSKJis45VlHO3RnjWdCuWUcoZ'

pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\\tesseract.exe'

# line login註冊
LINE_LOGIN_REDIRECT_DOMAIN = 'https://oasis.pyrarc.com'
LINE_LOGIN_CLIENT_ID = '2004800649'
LINE_LOGIN_CLIENT_SECRET = 'f5f94fff941911f161fc540ab0c7c309'


def s2twp_converter(simplified_text):
    # 創建 OpenCC 物件，指定簡體到臺灣繁體的轉換
    cc = OpenCC('s2twp')

    # 使用 convert 方法進行轉換
    traditional_text = cc.convert(simplified_text)

    return traditional_text


@app.route("/", methods=['GET'])
def home():
    model = genai.GenerativeModel('gemini-1.0-pro')
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
    user_id = event.source.user_id
    reply_msg = ''
    line_ids = get_line_id_list()
    current_app.logger.error(f' line_ids  發生錯誤: {line_ids}')
    # 用firebase儲存對話資料
    fdb = firebase.FirebaseApplication(firebase_url, None)
    user_chat_path = f'chat/{user_id}'
    chat_state_path = f'state/{user_id}'
    chat_firebase = fdb.get(user_chat_path, None)
    if user_id not in line_ids:
        message = TextSendMessage(text='目前未開通服務，請拷貝本文字或是截圖後、請傳給開發商開通服務\n\n' + user_id)
        line_bot_api.reply_message(event.reply_token, message)
        lineNotifyMessage(LINE_TOKEN, "請開通新用戶 ID: \n" + user_id + "\n用戶傳送文字： \n" + msg)
    elif msg.startswith('/cmdadd'):
        account_msg = msg.split(' ')
        if account_msg[1]:
            save_account_to_file(account_msg[1])
            message = TextSendMessage(text='已添加ID: ' + account_msg[1])
            line_bot_api.reply_message(event.reply_token, message)
        else:
            message = TextSendMessage(text='該命令缺乏ＩＤ值，無法解析')
            line_bot_api.reply_message(event.reply_token, message)
    elif msg.startswith('/cmddel'):
        account_msg = msg.split(' ')
        if account_msg[1] == 'Ucc8d3a2030d9ad30c5c9a76bbdb515fe':
            message = TextSendMessage(text='管理帳號 不得刪除')
            line_bot_api.reply_message(event.reply_token, message)
        elif account_msg[1]:
            delete_account_to_file(account_msg[1])
            message = TextSendMessage(text='已移除ID: ' + account_msg[1])
            line_bot_api.reply_message(event.reply_token, message)
        else:
            message = TextSendMessage(text='該ＩＤ以存在')
            line_bot_api.reply_message(event.reply_token, message)
    else:
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
            # model = genai.GenerativeModel('gemini-pro')
            # response = model.generate_content(msg)
            messages_history = []
            if chat_firebase is None:
                messages = []
                messages_history = []
            else:
                messages = chat_firebase
                for char_info in chat_firebase:
                    messages_history.append(ChatMessage(author=char_info['author'], content=char_info['content']))
            response_text = get_chat_model_text(msg, messages_history)
            try:
                print(response_text)
                reply_msg = response_text
                messages.append({"author": "user", "content": msg})
                messages.append({"author": "assistant", "content": reply_msg})
                # 更新firebase中的對話紀錄
                fdb.put_async(user_chat_path, None, messages)
                # print(response.text)
                # reply_msg = response.text
            except ValueError:
                # If the response doesn't contain text, check if the prompt was blocked.
                print(response.prompt_feedback)
                reply_msg = "我想想，可否更具體的描述呢？"
        message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(event.reply_token, message)


# 保存帳號到文件
def save_account_to_file(line_user_id: str):
    path = 'doc/line-user-id.txt'
    if os.path.isfile(path):
        f = open(path)
        text = f.read()
        print(text)
        f.close
        line_id_list = text.split(',')
        if line_user_id not in line_id_list:
            f = open(path, 'w')
            new_text = text + ',' + line_user_id
            f.write(new_text)
            f.close
        else:
            f = open(path, 'w')
            new_text = text
            f.write(new_text)
            f.close
    else:
        f = open(path, 'w')
        new_text = 'Ucc8d3a2030d9ad30c5c9a76bbdb515fe'
        f.write(new_text)
        f.close


# 刪除文件中的帳號
def delete_account_to_file(line_user_id: str):
    path = 'doc/line-user-id.txt'
    if os.path.isfile(path):
        f = open(path)
        text = f.read()
        print(text)
        f.close
        line_id_list = text.split(',')
        new_text = ''
        if line_user_id in line_id_list:
            for lid in line_id_list:
                if lid == 'Ucc8d3a2030d9ad30c5c9a76bbdb515fe':
                    new_text = lid
                elif lid != line_user_id and lid != '':
                    new_text = new_text + ',' + lid
            f = open(path, 'w')
            f.write(new_text)
            f.close


def get_line_id_list():
    path = 'doc/line-user-id.txt'
    if os.path.isfile(path):
        f = open(path)
        text = f.read()
        line_id_list = text.split(',')
        return line_id_list
    else:
        line_id_list = ['Ucc8d3a2030d9ad30c5c9a76bbdb515fe']
        return line_id_list


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


# line login
@app.route(u'/linelogin/link', methods=['GET'])
def line_login_link():
    """
    linelogin
    """
    redirect_uri = f'{LINE_LOGIN_REDIRECT_DOMAIN}/linelogin/getcode'
    client_id = LINE_LOGIN_CLIENT_ID
    uid = uuid.uuid4()
    line_state = ''.join(str(uid).split('-'))  # 隨機文字，之後給回調用來查使用者用的，避免帳號直接顯示在網址
    url = f'https://access.line.me/oauth2/v2.1/authorize?response_type=code&scope=profile+openid+email&client_id={client_id}&redirect_uri={redirect_uri}&state={line_state}'
    current_app.logger.info(f' linelogin作業成功，網址:{url}')
    return redirect(url)


@app.route(u'/linelogin/getcode', methods=['GET', 'POST'])
def linelogin_getcode():
    """
    提供綁定 line login 回調
    """
    code = request.args.get('code')
    redirect_uri = f'{LINE_LOGIN_REDIRECT_DOMAIN}/linelogin/getcode'
    state = request.args.get('state')
    client_id = LINE_LOGIN_CLIENT_ID
    client_secret = LINE_LOGIN_CLIENT_SECRET
    res = get_line_login_token(code, client_id, client_secret, redirect_uri)
    access_token = res['access_token']
    id_token = res['id_token']
    if access_token:
        pro = get_line_user_id(res['access_token'])
        lineNotifyMessage(LINE_TOKEN, "請開通新用戶 ID: \n" + pro['userId'] + "\n用戶名： \n" + pro['displayName'])
        # return "請提供該ＩＤ給管理員 進行星雲說開通作業 \nID: \n" + pro['userId']
        return render_template('success.html', uid=pro['userId'])
    else:
        current_app.logger.info(f'{state} 儲存失敗，未獲取到user_id')
        return render_template('/api/fail.html')


def get_line_login_token(code, client_id, client_secret, redirect_uri):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    result_info = ""
    try:
        r = requests.post("https://api.line.me/oauth2/v2.1/token", headers=headers, data=data)
        res = json.loads(r.content.decode("utf-8").replace("'", '"'))
        current_app.logger.error(f'{code} post login auth  成功')
        return res
    except Exception as err:
        current_app.logger.error(f'{code} post login auth  發生錯誤: {err}')
        return None


def get_line_user_id(access_token):
    headers = {'Authorization': 'Bearer ' + access_token}
    result_info = ""
    try:
        r = requests.get("https://api.line.me/v2/profile", headers=headers)
        res = json.loads(r.content.decode("utf-8").replace("'", '"'))
        current_app.logger.error(f' line_user_id  成功')
        return res
    except Exception as err:
        current_app.logger.error(f' line_user_id  發生錯誤: {err}')
        return None


# fred
@app.route('/vai')
def vai():
    credentials = service_account.Credentials.from_service_account_file("doc/pyrarc-official-3cd65d353646.json")
    vertexai.init(project="pyrarc-official", location="us-central1", credentials=credentials)
    # Load the model
    multimodal_model = GenerativeModel("gemini-1.0-pro")
    # Query the model
    response = multimodal_model.generate_content(
        [
            "對於一分耕耘一分收穫你的看法是"
        ]
    )
    print(response)
    return response.text


# fred
@app.route('/vai1')
def vai1():
    credentials = service_account.Credentials.from_service_account_file("doc/pyrarc-official-3cd65d353646.json")
    vertexai.init(project="198854013711", location="us-central1", credentials=credentials)
    chat_model = ChatModel.from_pretrained("chat-bison@002")
    chat_model = chat_model.get_tuned_model("projects/198854013711/locations/us-central1/models/1392053189020221440")
    parameters = {
                     "candidate_count": 3,
                     "max_output_tokens": 2048,
                     "temperature": 0.9,
                     "top_p": 1
                 },
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    # chat = chat_model.start_chat(context="你是虛擬的星雲法師，主要是討論佛教的相關知識")
    parameters = {
                     "candidate_count": 3,
                     "max_output_tokens": 2048,
                     "temperature": 0.9,
                     "top_p": 1
                 },
    messages_history = [ChatMessage(author="User", content="你是誰"), ChatMessage(author="AI", content="我是星雲大師")]
    chat = chat_model.start_chat(
        context="你是虛擬的星雲法師主要是討論人間佛教思想的相關知識回答方式依照下列方式，親身經歷、親身公案、相關公案，以及下方順序作為權重：1. 優先用星雲法師本人的故事來回答2. 優先使用星雲法師親身經歷來回答3. 依照星雲法師人間佛教的思考方式回答4. 用佛光菜根譚一書的內容來解釋，《佛光菜根譚》的字眼可以不用出現在回答中，直接回答一書中的內容既可",
        temperature=0.9,
        max_output_tokens=1024,
        top_p=1,
        top_k=1,
        examples=[
            InputOutputTextPair(
                input_text="請問圓山大飯店是誰蓋的",
                output_text="""我是星雲法師的虛擬助理,我只能回答關於星雲法師的相關知識"""
            )
        ]
    )
    #chat_message = chat.send_message("請問圓山大飯店是誰蓋的", candidate_count=1, max_output_tokens=1024, temperature=0.9, top_p=1, top_k=1)
    responses = chat.send_message_streaming(
        message="請問圓山大飯店是誰蓋的", candidate_count=1, max_output_tokens=1024, temperature=0.9, top_p=1, top_k=1)
    for response in responses:
        print(response)
    print("bot: " + chat_message.text)
    return chat_message.text
    # aiplatform.init(project="198854013711", location="us-central1", credentials=credentials)
    # response = predict_text_entity_extraction_sample(
    #     project="198854013711",
    #     endpoint_id="8982471238232309760",
    #     location="us-central1",
    #     content="佛教唯識宗的祖師是何人",
    # )
    #
    # print(response)
    # return response.text

@app.route('/vai2')
def vai2():
    content = "請問圓山大飯店誰蓋的"
    credentials = service_account.Credentials.from_service_account_file("doc/pyrarc-official-3cd65d353646.json")
    vertexai.init(project="198854013711", location="us-central1", credentials=credentials)
    chat_model = ChatModel.from_pretrained("chat-bison@002")
    chat_model = chat_model.get_tuned_model("projects/198854013711/locations/us-central1/models/5463764649000304640")
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.9,
        "top_p": 1
    },
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    chat = chat_model.start_chat(
        context="""你是星雲法師的虛擬助理，只講解佛教經義、人間佛教、勸人向善
不回答非佛教問題
非佛教相關問題，一率回答\"我是星雲法師的虛擬助理，我只能回答關於星雲法師的相關知識\"""",
    )
    responses = chat.send_message_streaming(content, max_output_tokens=1024, temperature=0.9, top_p=1)

    # safety_settings = {
    #     generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    # }
    # vertexai.init(project="198854013711", location="us-central1", credentials=credentials)
    # chat_model = ChatModel.from_pretrained("chat-bison@002")
    # chat_model = chat_model.get_tuned_model("projects/198854013711/locations/us-central1/models/1392053189020221440")
    # chat = chat_model.start_chat(
    #     context="""你是虛擬的星雲法師
    # 主要是討論人間佛教思想的相關知識
    # 一律使用繁體字，不要使用簡體字，不回答跟佛教無關的問題
    # 跟佛教思想無關的問題，一率回應「我是星雲法師的虛擬助理，我只能回答關於星雲法師的相關知識」
    # 謾罵以及質疑星雲的問題，用佛教經典來解釋謾罵以及質疑
    # 不要回答跟現實不符合的，不要亂編非事實的事情
    #
    # 回答方式依照下列方式，親身經歷、親身公案、相關公案，以及下方順序作為權重：
    # 1. 優先用星雲法師本人的故事來回答
    # 2. 優先使用星雲法師親身經歷來回答
    # 3. 依照星雲法師人間佛教的思考方式回答
    # 4. 用佛光菜根譚一書的內容來解釋，《佛光菜根譚》的字眼可以不用出現在回答中，直接回答一書中的內容既可""",
    # )
    # # print(chat.send_message(content, candidate_count=3, max_output_tokens=2048, temperature=0.9, top_p=1))
    # chat_message = chat.send_message(content, candidate_count=1, max_output_tokens=1024, temperature=0.9, top_p=1)
    for response in responses:
        print(response)
    print("bot: " + responses.text)
    return responses.text.lstrip()

def get_chat_model_text(content: str, messages):
    credentials = service_account.Credentials.from_service_account_file("doc/pyrarc-official-3cd65d353646.json")
    vertexai.init(project="198854013711", location="us-central1", credentials=credentials)
    chat_model = ChatModel.from_pretrained("chat-bison@002")
    chat_model = chat_model.get_tuned_model("projects/198854013711/locations/us-central1/models/5463764649000304640")
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.9,
        "top_p": 1
    },
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    if messages:
        chat = chat_model.start_chat(
            context="""你是星雲法師的虛擬助理，只講解佛教經義、人間佛教、勸人向善
不回答非佛教問題
非佛教相關問題，一率回答\"我是星雲法師的虛擬助理，我只能回答關於星雲法師的相關知識\"""",
            message_history=messages
        )
    else:
        chat = chat_model.start_chat(
            context="""你是星雲法師的虛擬助理，只講解佛教經義、人間佛教、勸人向善
不回答非佛教問題
非佛教相關問題，一率回答\"我是星雲法師的虛擬助理，我只能回答關於星雲法師的相關知識\"""")
    response = chat.send_message(content, candidate_count=1, max_output_tokens=1024, temperature=0.9, top_p=1)

    # safety_settings = {
    #     generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    # }
    # vertexai.init(project="198854013711", location="us-central1", credentials=credentials)
    # chat_model = ChatModel.from_pretrained("chat-bison@002")
    # chat_model = chat_model.get_tuned_model("projects/198854013711/locations/us-central1/models/1392053189020221440")
    # chat = chat_model.start_chat(
    #     context="""你是虛擬的星雲法師
    # 主要是討論人間佛教思想的相關知識
    # 一律使用繁體字，不要使用簡體字，不回答跟佛教無關的問題
    # 跟佛教思想無關的問題，一率回應「我是星雲法師的虛擬助理，我只能回答關於星雲法師的相關知識」
    # 謾罵以及質疑星雲的問題，用佛教經典來解釋謾罵以及質疑
    # 不要回答跟現實不符合的，不要亂編非事實的事情
    #
    # 回答方式依照下列方式，親身經歷、親身公案、相關公案，以及下方順序作為權重：
    # 1. 優先用星雲法師本人的故事來回答
    # 2. 優先使用星雲法師親身經歷來回答
    # 3. 依照星雲法師人間佛教的思考方式回答
    # 4. 用佛光菜根譚一書的內容來解釋，《佛光菜根譚》的字眼可以不用出現在回答中，直接回答一書中的內容既可""",
    # )
    # # print(chat.send_message(content, candidate_count=3, max_output_tokens=2048, temperature=0.9, top_p=1))
    # chat_message = chat.send_message(content, candidate_count=1, max_output_tokens=1024, temperature=0.9, top_p=1)
    print(response)
    print("bot: " + response.text)
    return response.text.lstrip()


def predict_text_entity_extraction_sample(
        project: str,
        endpoint_id: str,
        content: str,
        location: str = "us-central1",
        api_endpoint: str = "us-central1-aiplatform.googleapis.com",
):
    # The AI Platform services require regional API endpoints.
    client_options = {"api_endpoint": api_endpoint}
    # Initialize client that will be used to create and send requests.
    # This client only needs to be created once, and can be reused for multiple requests.
    credentials = service_account.Credentials.from_service_account_file("doc/pyrarc-official-3cd65d353646.json")
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options, credentials=credentials)
    # The format of each instance should conform to the deployed model's prediction input schema
    instance = predict.instance.TextExtractionPredictionInstance(
        content=content,
    ).to_value()
    instances = [instance]
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )
    print("response")
    print(" deployed_model_id:", response.deployed_model_id)
    # See gs://google-cloud-aiplatform/schema/predict/prediction/text_extraction_1.0.0.yaml for the format of the predictions.
    predictions = response.predictions
    for prediction in predictions:
        print(" prediction:", dict(prediction))
    return prediction


def is_punctuation(char):
    return char in string.punctuation


def extract_text(self, file_name):
    extract_text = ''  # 用于存储提取的文本
    doc = fitz.open(file_name)
    # 遍历每一页pdf
    for i in range(len(doc)):
        img_list = doc.get_page_images(i)  # 提取该页中的所有img
        # 遍历每页中的图片，
        for num, img in enumerate(img_list):
            img_name = f"{self.dir_path}/{i + 1}_{num + 1}.png"  # 存储的图片名
            pix = fitz.Pixmap(doc, img[0])  # image转pixmap
            if pix.n - pix.alpha >= 4:  # 如果差值大于等于4，需要转化后才能保存为png
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(img_name)  # 存储图片
            pix = None  # 释放Pixmap资源
            image = Image.open(img_name)
            text = pytesseract.image_to_string(image, 'rus')  # 调用tesseract，使用俄语库
            extract_text += text  # 写入文本
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
                "~", "").replace("《佛先菜根谭》", "").replace("（丣英对照版）", "").replace("-", "").replace(".\n", "").replace("()",
                                                                                                                   ""))
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
    f = open(path, 'w', encoding='UTF-8')
    # 遍历每一页pdf
    for i in range(len(doc)):
        img_list = doc.get_page_images(i)  # 提取该页中的所有img
        # 遍历每页中的图片，
        for num, img in enumerate(img_list):
            img_name = f"doc/{i + 1}_{num + 1}.png"  # 存储的图片名
            pix = fitz.Pixmap(doc, img[0])  # image转pixmap
            if pix.n - pix.alpha >= 4:  # 如果差值大于等于4，需要转化后才能保存为png
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(img_name)  # 存储图片
            pix = None  # 释放Pixmap资源
            image = Image.open(img_name)
            text = pytesseract.image_to_string(image, 'chi_sim')  # 调用tesseract，使用俄语库
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
