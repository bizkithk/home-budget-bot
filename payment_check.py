import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from datetime import datetime, timedelta


def get_payment_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("AI付款表單回應").sheet1


def is_payment_verified(telegram_id):
    sheet = get_payment_sheet()
    data = sheet.get_all_records()

    for row in data:
        if str(row.get("用戶 Telegram ID", "")).strip() == str(telegram_id):
            status = row.get("付款狀態", "")
            if status and "已確認付款" in status:
                return True
    return False


def get_password_by_user(telegram_id):
    sheet = get_payment_sheet()
    data = sheet.get_all_records()

    for row in data:
        if str(row.get("用戶 Telegram ID", "")).strip() == str(telegram_id):
            return row.get("付款密碼", "")
    return ""


def is_subscription_expired(telegram_id):
    sheet = get_payment_sheet()
    data = sheet.get_all_records()

    for row in data:
        if str(row.get("用戶 Telegram ID", "")) == str(telegram_id):
            ts = row.get("Timestamp", "")
            if ts:
                try:
                    timestamp = datetime.strptime(ts, "%Y/%m/%d %H:%M:%S")
                    if datetime.now() - timestamp > timedelta(days=30):
                        return True
                except:
                    pass
    return False
