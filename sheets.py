# -*- coding: utf-8 -*-
# sheets.py
import os
import base64
import json
import gspread
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials

SHEET_1_NAME = "家庭收支表"
SHEET_2_NAME = "AI付款表單回應"
SUBSCRIPTION_DAYS = 30


def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)


def get_sheet(sheet_name):
    client = get_gspread_client()
    return client.open(sheet_name)


def is_payment_verified(user_id):
    try:
        sheet = get_sheet(SHEET_2_NAME).worksheet("付款狀態")
        records = sheet.get_all_records()
        for row in reversed(records):
            if str(row.get("用戶 Telegram ID", "")).strip() == str(user_id):
                return str(row.get("付款狀態", "")).strip() == "✅"
    except Exception as e:
        print("[付款驗證失敗]", e)
    return False


def is_subscription_valid(user_id):
    try:
        sheet = get_sheet(SHEET_1_NAME).worksheet("帳戶總覽")
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("Telegram_ID", "")).strip() == str(user_id):
                expiry_str = row.get("到期日", "")
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                return expiry_date >= datetime.now()
    except Exception as e:
        print("[檢查到期日失敗]", e)
    return False


def activate_user_subscription(user_id, username):
    try:
        client = get_gspread_client()
        sheet = client.open(SHEET_1_NAME)
        summary_ws = sheet.worksheet("帳戶總覽")
        records = summary_ws.get_all_records()
        expiry_date = (datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)).strftime("%Y-%m-%d")

        for i, row in enumerate(records, start=2):
            if str(row.get("Telegram_ID", "")) == str(user_id):
                summary_ws.update_cell(i, 2, username)
                summary_ws.update_cell(i, 3, expiry_date)
                break
        else:
            summary_ws.append_row([user_id, username, expiry_date])

        # 建立個人分頁（如未存在）
        sheet_titles = [ws.title for ws in sheet.worksheets()]
        if username not in sheet_titles:
            template = sheet.worksheet("Sheet1")
            new_ws = sheet.duplicate_sheet(template.id, new_sheet_name=username)
            print(f"[成功建立分頁] {username}")
    except Exception as e:
        print("[啟用訂閱失敗]", e)
