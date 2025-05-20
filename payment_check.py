import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json

def get_payment_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds_dict)
    sheet_id = os.getenv("PAYMENT_SHEET_ID")  # 你付款記錄表嘅 Spreadsheet ID
    return client.open_by_key(sheet_id).sheet1

def is_payment_verified(user_id: str) -> bool:
    sheet = get_payment_sheet()
    records = sheet.get_all_records()
    for row in records:
        if str(row.get("Telegram ID", "")).strip() == str(user_id):
            return str(row.get("狀態", "")).strip() == "已付款"
    return False

def is_subscription_active(user_id: str) -> bool:
    sheet = get_payment_sheet()
    records = sheet.get_all_records()
    for row in records:
        if str(row.get("Telegram ID", "")).strip() == str(user_id):
            expiry_str = row.get("到期日", "")
            if not expiry_str:
                return False
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                today = datetime.today().date()
                return expiry_date >= today
            except ValueError:
                return False
    return False
