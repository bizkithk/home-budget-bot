# -*- coding: utf-8 -*-
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from datetime import datetime

# 初始化 Google Sheet client
def get_gsheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("家庭收支表")

# 建立或讀取用戶個人工作表
def get_or_create_user_sheet(username):
    spreadsheet = get_gsheet()
    try:
        sheet = spreadsheet.worksheet(username)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=username, rows="1000", cols="10")
        sheet.append_row(["日期", "類別", "金額", "備註", "收入/支出"])
    return sheet

# 初始化用戶，並在「用戶列表」記錄資料
def init_user_sheet(user_id):
    spreadsheet = get_gsheet()
    try:
        user_sheet = spreadsheet.worksheet("用戶列表")
    except gspread.exceptions.WorksheetNotFound:
        user_sheet = spreadsheet.add_worksheet(title="用戶列表", rows="100", cols="3")
        user_sheet.append_row(["Telegram_ID", "用戶名稱", "預算"])
    
    data = user_sheet.get_all_records()
    if not any(str(row["Telegram_ID"]) == str(user_id) for row in data):
        user_sheet.append_row([user_id, "", 0])

# 記錄收支紀錄至用戶分頁
def add_record(user_id, amount, category, purpose, is_income):
    username = get_username(user_id)
    if not username:
        return
    sheet = get_or_create_user_sheet(username)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_type = "收入" if is_income else "支出"
    sheet.append_row([date, category, amount, purpose, entry_type])

# 查看用戶預算與支出總額
def check_budget_status(user_id):
    spreadsheet = get_gsheet()
    user_sheet = spreadsheet.worksheet("用戶列表")
    data = user_sheet.get_all_records()

    budget = 0
    username = ""
    for row in data:
        if str(row["Telegram_ID"]) == str(user_id):
            budget = float(row.get("預算", 0))
            username = row.get("用戶名稱", "")
            break
    
    if not username:
        return 0, 0
    
    sheet = get_or_create_user_sheet(username)
    records = sheet.get_all_records()
    used = sum(float(r["金額"]) for r in records if r.get("收入/支出") == "支出")
    return used, budget

# 設定用戶預算
def set_user_budget(user_id, amount):
    spreadsheet = get_gsheet()
    user_sheet = spreadsheet.worksheet("用戶列表")
    data = user_sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == str(user_id):
            user_sheet.update_cell(i, 3, amount)
            return
    # fallback
    user_sheet.append_row([user_id, "", amount])

# 查看收入摘要
def get_income_summary(user_id):
    username = get_username(user_id)
    if not username:
        return "❗ 未設定名稱，請先 /setusername"

    sheet = get_or_create_user_sheet(username)
    data = sheet.get_all_records()
    total_income = 0
    breakdown = {}
    for row in data:
        if row.get("收入/支出") == "收入":
            amt = float(row.get("金額", 0))
            cat = row.get("類別", "未分類")
            total_income += amt
            breakdown[cat] = breakdown.get(cat, 0) + amt
    result = f"💰 本月總收入：HK${total_income}\n"
    for cat, amt in breakdown.items():
        result += f"・{cat}: HK${amt}\n"
    return result

# 設定用戶名稱
def set_username(user_id, username):
    spreadsheet = get_gsheet()
    user_sheet = spreadsheet.worksheet("用戶列表")
    data = user_sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == str(user_id):
            user_sheet.update_cell(i, 2, username)
            return
    user_sheet.append_row([user_id, username, 0])

# 取得用戶名稱（分頁名用）
def get_username(user_id):
    spreadsheet = get_gsheet()
    user_sheet = spreadsheet.worksheet("用戶列表")
    data = user_sheet.get_all_records()
    for row in data:
        if str(row["Telegram_ID"]) == str(user_id):
            return row.get("用戶名稱", "")
    return ""

# 檢查是否已驗證付款（需配合 payment_check.py）
def is_verified_user(update):
    from modules.payment_check import is_payment_verified
    return is_payment_verified(str(update.effective_user.id))
