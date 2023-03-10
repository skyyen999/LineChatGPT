# 引入所需的套件
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

ImageSendMessage
from api.chatgpt import ChatGPT
import os

# 建立 LineBotApi 和 WebhookHandler 物件
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 定義一個工作狀態變數，用於判斷程式是否在運行中
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

# 建立 Flask 物件，指定為主程式
app = Flask(__name__)
chatgpt = ChatGPT()

# 設定根網域的路由
@app.route('/')
def home():
    return 'Hello, World!'


# 設定 /webhook 路由，用於接收 linebot 的 callback 請求
@app.route("/webhook", methods=['POST'])
def callback():
    # 取得 X-Line-Signature header 的值
    signature = request.headers['X-Line-Signature']
    # 取得 request body 的文字內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # 處理 webhook 的 body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 設定處理訊息的函數
@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    mtext = event.message.text

    # 判斷是不是繪圖API
    is_draw = False;

    # 判斷訊息類型是否為文字
    if event.message.type == "text":
        is_text = False   

    if event.source.type == 'user':
        is_text = True       

    # 判斷訊息類型是否個人聊天，不是個人聊天檢查是不是"YY "開頭
    if event.source.type != 'user':
        if mtext.lower().startswith(('yy ','bot ','gpt ')):
            is_text = True       
        if mtext.lower().startswith(('yydraw ','botdraw ','gptdraw ', 'draw ')):
            is_text = False       
            is_draw = True   

    mtext = mtext.split(" ", 1)[1]


    if is_text:
        # 加入使用者的訊息到 chatgpt 物件中
        chatgpt.add_msg(f"Human:{mtext}?\n")
        # 取得 chatgpt 回答的訊息
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))

    if is_draw:
        tlen = len(mtext)
        if(tlen < 10):
            print(f"len:{tlen}")
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我不想畫，這描述太少了，認真一點，好嗎"))
            return
        

        # 加入使用者的訊息到 chatgpt 物件中
        chatgpt.add_msg(f"Human:{mtext}?\n")
        # 取得 chatgpt 回答的訊息
        image_url = chatgpt.get_image_response()

        image_message = ImageSendMessage(
            original_content_url= image_url
        )
        line_bot_api.reply_message(event.reply_token, image_message)

if __name__ == "__main__":
    app.run()