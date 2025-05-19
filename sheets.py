import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

SCOPE = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
SHEET_ID = "1EbGOIeQzgrLd2d8s60wifELwboDHv5EFA8zMzavTCLU"

def _auth():
    import base64, json
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    return gspread.authorize(creds)

def _get_user_ws(user_id):
    gc = _auth()
    sheet = gc.open_by_key(SHEET_ID)
    try:
        return sheet.worksheet(user_id)
    except:
        sheet.add_worksheet(title=user_id, rows="1000", cols="5")
        ws = sheet.worksheet(user_id)
        ws.append_row(["時間", "類別", "金額", "用途", "收入"])
        return ws

def init_user_sheet(user_id):
    _get_user_ws(user_id)

def add_record(user_id, amount, category, purpose, is_income):
    ws = _get_user_ws(user_id)
    ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), category, amount, purpose, "是" if is_income else "否"])

def check_budget_status(user_id):
    ws = _get_user_ws(user_id)
    data = ws.get_all_records()
    budget = float(os.getenv(f"BUDGET_{user_id}", "5000"))
    spent = sum(float(d["金額"]) for d in data if d["收入"] == "否")
    return spent, budget

def set_user_budget(user_id, amount):
    os.environ[f"BUDGET_{user_id}"] = str(amount)

def set_username(user_id, name):
    os.environ[f"USERNAME_{user_id}"] = name

async def is_verified_user(update):
    user_id = str(update.effective_user.id)
    if f"USERNAME_{user_id}" not in os.environ:
        await update.message.reply_text("⚠️ 請先輸入 /verify 密碼，再用 /setusername [名稱] 設定帳戶。")
        return False
    return True

def get_income_summary(user_id):
    ws = _get_user_ws(user_id)
    data = ws.get_all_records()
    income_data = [d for d in data if d["收入"] == "是"]
    total = sum(float(d["金額"]) for d in income_data)
    by_type = {}
    for d in income_data:
        key = d["類別"]
        by_type[key] = by_type.get(key, 0) + float(d["金額"])
    summary = f"💰 本月總收入：HK${total}\n\n分類統計：\n" + "\n".join([f"- {k}: ${v}" for k, v in by_type.items()])
    return summary
