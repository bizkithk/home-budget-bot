# gpt_advice.py
import os
import openai
import base64
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 初始化 OpenAI Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Sheet 認證
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)


def get_user_data(user_id):
    ss = client.open("家庭收支表")
    account_sheet = ss.worksheet("帳戶總覽")
    username = None
    for row in account_sheet.get_all_records():
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break

    if not username:
        return None

    try:
        user_sheet = ss.worksheet(username)
    except:
        return None

    data = user_sheet.get_all_records()
    income = {}
    expense = {}
    for row in data:
        cat = row.get("類別", "未分類")
        amt = float(row.get("金額", 0))
        typ = row.get("收入/支出")
        if typ == "收入":
            income[cat] = income.get(cat, 0) + amt
        elif typ == "支出":
            expense[cat] = expense.get(cat, 0) + amt
    return income, expense


def generate_financial_advice(user_id):
    result = get_user_data(user_id)
    if not result:
        return "⚠️ 暫時無法讀取你的收支資料，請確認你已成功記帳。"

    income, expense = result

    prompt = f"""
你是一個懂得理財的 AI 助手，請根據以下收支資料提供實用、親切的理財建議（中英文皆可）：

收入：{json.dumps(income, ensure_ascii=False)}
支出：{json.dumps(expense, ensure_ascii=False)}

請分析：
1. 哪些類別支出偏高？
2. 是否有儲蓄建議？
3. 怎樣提升收支平衡？

以三點方式列出建議，語氣親切簡潔，避免使用太專業術語。
"""

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message['content']
    except Exception as e:
        return f"⚠️ 無法產生建議：{str(e)}"
