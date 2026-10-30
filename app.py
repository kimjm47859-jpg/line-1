from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta

app = Flask(__name__)

# 발급받으신 토큰과 시크릿 입력
line_bot_api = LineBotApi('yUtAB4CZAJkzOhjku7/nbWrdx2u4TJNwcfDbgIfQEHBLNxazsOEG67Nr0M917Or6cqAA4Bik6XGJluDdKxqoK8W5+VwuJ6W4JG0yLdKnjksrTfA3OjCcIvrl0hFkTGWPTRolt1e2Vb+G6hpjM73t3wdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('2b4ca1bdd850e26f1da6e85a847b3034')

# 유저별 상태와 시작 시간을 기억할 공간
# 예: { "user_id": { "group": "group1", "start_time": datetime객체 } }
user_data = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ==========================================
# 📌 함수 1: 첫 번째 그룹 (초기 단계)
# ==========================================
def process_group_1(user_name, elapsed_time):
    # 3일(timedelta)이 지났는지 확인
    # 테스트를 원하시면 timedelta(days=3) 대신 timedelta(minutes=1) 등으로 변경 가능합니다.
    limit_time = timedelta(days=3)
    
    if elapsed_time >= limit_time:
        return "SHIFT_TO_GROUP2" # 그룹 2로 넘어가라는 신호
    else:
        remaining = limit_time - elapsed_time
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"👋 [함수 1 / 1번조] {user_name}님 환영합니다!\n⏳ 2번조로 이동까지 남은 시간: {days}일 {hours}시간 {minutes}분"

# ==========================================
# 📌 함수 2: 두 번째 그룹 (시간 경과 후 단계)
# ==========================================
def process_group_2(user_name):
    return f"🎉 [함수 2 / 2번조] {user_name}님은 지정된 시간이 지나 2번조(함수 2)로 이동되었습니다!"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "알 수 없음"

    current_time = datetime.now()

    # 1. 처음 온 유저라면 '함수 1'과 현재 시간 기록
    if user_id not in user_data:
        user_data[user_id] = {
            "group": "group1",
            "start_time": current_time
        }

    # 2. 유저의 현재 그룹과 시작 시간 가져오기
    user_group = user_data[user_id]["group"]
    start_time = user_data[user_id]["start_time"]
    elapsed_time = current_time - start_time

    # 3. 그룹별 함수 실행 및 시간 체크
    if user_group == "group1":
        result = process_group_1(user_name, elapsed_time)
        
        # 시간이 다 되어 그룹 2로 이동 신호가 온 경우
        if result == "SHIFT_TO_GROUP2":
            user_data[user_id]["group"] = "group2" # 상태를 그룹 2로 변경
            reply_text = process_group_2(user_name)
        else:
            reply_text = result
            
    elif user_group == "group2":
        reply_text = process_group_2(user_name)
    else:
        reply_text = "상태를 확인할 수 없습니다."

    # 답변 전송
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
