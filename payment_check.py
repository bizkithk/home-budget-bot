# -*- coding: utf-8 -*-
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
