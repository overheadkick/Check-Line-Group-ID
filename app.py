# โหลดไลบรารีที่จำเป็น (Necessary libraries)
import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# -----------------
# 1. ตั้งค่า API Keys (ดึงค่าจาก Environment Variables ของ Render)
#    (Configure API Keys - pulling values from Render Environment Variables)
# -----------------
# Render จะใส่ค่าเหล่านี้ให้เองจาก Environment Variables ที่คุณตั้งค่าไว้
# (Render will automatically inject these values from the Environment Variables you set)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") 
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    logging.error("Environment variables for Line API are not set.")
    pass

# -----------------
# 2. ตั้งค่า Flask App และ Line Bot
#    (Configure Flask App and Line Bot)
# -----------------
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ตั้งค่า Logging เพื่อให้แสดง Group ID ใน console
# (Configure Logging to show Group ID in the console)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route("/callback", methods=['POST'])
def callback():
    """
    Webhook endpoint ที่ Line จะส่งกิจกรรมต่างๆ เข้ามา
    (Webhook endpoint where Line sends various events)
    """
    # รับ X-Line-Signature header
    signature = request.headers['X-Line-Signature']

    # รับ body ของ request ในรูปแบบ text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # จัดการ Webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # พิมพ์ข้อความเตือนหากลายเซ็นไม่ถูกต้อง
        logging.error("Invalid signature. โปรดตรวจสอบ Channel Secret และ Access Token ของคุณ")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    จัดการเมื่อมีข้อความถูกส่งเข้ามาในแชท (Group หรือ User)
    (Handles incoming text messages in chat (Group or User))
    """
    source_type = event.source.type
    
    # 3. ตรวจสอบว่ากิจกรรมมาจาก "group" หรือไม่
    if source_type == 'group':
        # ดึง Group ID
        group_id = event.source.group_id
        
        # Log group ID (จะไปปรากฏใน console ที่รันโปรแกรม)
        logging.info(f"Line Group ID ถูกดึงออกมาแล้ว: {group_id}")
        
        # ตอบกลับ Group ID ไปยังแชท (Bot จะต้องถูกเชิญเข้ากลุ่มก่อน)
        try:
            reply_text = f"✅ Group ID ของกลุ่มนี้คือ:\n{group_id}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
        except Exception as e:
            logging.error(f"ไม่สามารถตอบกลับได้: {e}")
            
    # เพิ่มการจัดการสำหรับห้องแชท (Room ID) ด้วย
    elif source_type == 'room':
        room_id = event.source.room_id
        logging.info(f"Line Room ID ถูกดึงออกมาแล้ว: {room_id}")
        try:
            reply_text = f"✅ Room ID ของห้องแชทนี้คือ:\n{room_id}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
        except Exception as e:
            logging.error(f"ไม่สามารถตอบกลับได้: {e}")
            
    else:
        # ถ้ามาจาก user ส่วนตัว (user) 
        pass 

# -----------------
# 4. รัน Flask Server
#    (Run Flask Server)
# -----------------
if __name__ == "__main__":
    # Render จะรันด้วย Gunicorn (ผ่าน Procfile)
    port = int(os.environ.get("PORT", 5000))
    if os.environ.get('RENDER', False):
        pass
    else:
        app.run(debug=True, port=port)
