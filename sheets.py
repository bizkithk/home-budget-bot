# -*- coding: utf-8 -*-
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from datetime import datetime

# ========== Google Sheet 認證 ==========
def get_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("家庭收支表").worksheet(sheet_name)
    return sheet

# ========== 使用者初始化 ==========
def init_user_account(user_id, username):
    sheet = get_sheet("帳戶總覽")
    data = sheet.get_all_records()
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            return  # 已存在
    sheet.append_row([str(user_id), username, 0])
    try:
        client = get_sheet("帳戶總覽").spreadsheet
        new_sheet = client.add_worksheet(title=username, rows="100", cols="5")
        new_sheet.append_row(["日期", "類別", "金額", "備註", "收入/支出"])
    except Exception as e:
        print("創建分頁失敗：", e)

# ========== 記帳 ==========
def add_record(user_id, amount, category, note, is_income):
    sheet = get_sheet("帳戶總覽")
    users = sheet.get_all_records()
    username = None
    for row in users:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return
    user_sheet = get_sheet(username)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    user_sheet.append_row([now, category, amount, note, "收入" if is_income else "支出"])

# ========== 預算設定 ==========
def set_user_budget(user_id, amount):
    sheet = get_sheet("帳戶總覽")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("Telegram_ID")) == str(user_id):
            sheet.update_cell(i, 3, amount)
            break

# ========== 總結圖表 ==========
def get_summary_chart(user_id):
    sheet = get_sheet("帳戶總覽")
    data = sheet.get_all_records()
    username = None
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return "❌ 用戶未註冊"

    user_sheet = get_sheet(username)
    rows = user_sheet.get_all_values()[1:]  # skip headers
    category_sum = {}
    for row in rows:
        if len(row) < 5 or row[4] != "支出":
            continue
        cat = row[1]
        amt = float(row[2])
        category_sum[cat] = category_sum.get(cat, 0) + amt
    if not category_sum:
        return "📊 暫時未有支出記錄"

    result = "📊 支出分類總結：\n"
    for cat, amt in category_sum.items():
        result += f"・{cat}: HK${amt}\n"
    return result

# ========== 收入總結 ==========
def get_income_summary(user_id):
    sheet = get_sheet("帳戶總覽")
    data = sheet.get_all_records()
    username = None
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return "❌ 用戶未註冊"

    user_sheet = get_sheet(username)
    rows = user_sheet.get_all_values()[1:]  # skip headers
    income_sum = 0
    breakdown = {}
    for row in rows:
        if len(row) < 5 or row[4] != "收入":
            continue
        cat = row[1]
        amt = float(row[2])
        income_sum += amt
        breakdown[cat] = breakdown.get(cat, 0) + amt

    if not breakdown:
        return "💰 暫時未有收入記錄"

    result = f"💰 總收入：HK${income_sum}\n"
    for cat, amt in breakdown.items():
        result += f"・{cat}: HK${amt}\n"
    return result

# ========== 使用者名稱設定 ==========
def set_username(user_id, username):
    sheet = get_sheet("帳戶總覽")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("Telegram_ID")) == str(user_id):
            sheet.update_cell(i, 2, username)
            return
    sheet.append_row([str(user_id), username, 0])
