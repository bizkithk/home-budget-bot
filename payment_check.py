# Let's generate the updated payment_check.py that uses "AI付款表單回應" for payment verification

payment_check_path = "/mnt/data/payment_check.py"

updated_payment_check_code = """# -*- coding: utf-8 -*-
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json

def get_payment_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Get the payment sheet specifically from AI付款表單回應
    sheet = client.open("AI付款表單回應").sheet1
    return sheet

def is_payment_verified(user_id):
    sheet = get_payment_sheet()
    data = sheet.get_all_records()
    for row in data:
        if str(row.get("Telegram_ID", "")).strip() == str(user_id):
            status = str(row.get("付款狀態", "")).strip()
            if status == "已付款":
                return True
    return False
"""

with open(payment_check_path, "w", encoding="utf-8") as f:
    f.write(updated_payment_check_code)

payment_check_path
