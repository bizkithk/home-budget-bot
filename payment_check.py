import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import base64
import json

SCOPE = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
PAYMENT_SHEET_ID = os.getenv("PAYMENT_SHEET_ID", "")

def _auth():
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    return gspread.authorize(creds)

def is_user_paid(user_id):
    if not PAYMENT_SHEET_ID:
        return True  # If not set, assume free mode
    gc = _auth()
    sheet = gc.open_by_key(PAYMENT_SHEET_ID)
    ws = sheet.sheet1
    records = ws.get_all_records()
    for r in records:
        if str(r.get("Telegram_ID")) == str(user_id) and str(r.get("已付款", "")).strip() == "是":
            return True
    return False
