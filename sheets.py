# -*- coding: utf-8 -*-
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from datetime import datetime, timedelta
import io
from fpdf import FPDF

# 建立 Google Sheet 認證與連線
def get_gsheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# 取得帳戶總覽 Sheet
def get_account_sheet():
    return get_gsheet().open("家庭收支表").worksheet("帳戶總覽")

# 初始化用戶分頁
def init_user_sheet(user_id, username):
    client = get_gsheet()
    file = client.open("家庭收支表")
    sheet_titles = [ws.title for ws in file.worksheets()]
    if username not in sheet_titles:
        user_sheet = file.add_worksheet(title=username, rows="1000", cols="10")
        user_sheet.append_row(["日期", "類別", "金額", "備註", "收入/支出"])
    summary_sheet = file.worksheet("帳戶總覽")
    users = summary_sheet.col_values(1)
    if str(user_id) not in users:
        summary_sheet.append_row([str(user_id), username, 0])

# 新增收支紀錄

def add_record(user_id, amount, category, purpose, is_income):
    summary_sheet = get_account_sheet()
    records = summary_sheet.get_all_records()
    username = None
    for row in records:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return False

    sheet = get_gsheet().open("家庭收支表").worksheet(username)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    income_or_expense = "收入" if is_income else "支出"
    sheet.append_row([date, category, amount, purpose, income_or_expense])
    return True

# 設定用戶名稱

def set_username(user_id, username):
    summary_sheet = get_account_sheet()
    data = summary_sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("Telegram_ID")) == str(user_id):
            summary_sheet.update_cell(i, 2, username)
            return
    summary_sheet.append_row([str(user_id), username, 0])

# 設定預算

def set_user_budget(user_id, budget):
    summary_sheet = get_account_sheet()
    data = summary_sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("Telegram_ID")) == str(user_id):
            summary_sheet.update_cell(i, 3, budget)
            return

# 收入總結

def get_income_summary(user_id):
    summary_sheet = get_account_sheet()
    data = summary_sheet.get_all_records()
    username = None
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return "找不到對應的分頁。請先設定名稱。"

    sheet = get_gsheet().open("家庭收支表").worksheet(username)
    rows = sheet.get_all_records()
    total_income = 0
    breakdown = {}
    for row in rows:
        if row.get("收入/支出") == "收入":
            amt = float(row.get("金額", 0))
            cat = row.get("類別", "未分類")
            total_income += amt
            breakdown[cat] = breakdown.get(cat, 0) + amt
    result = f"💰 本月總收入：HK${total_income}\n"
    for cat, amt in breakdown.items():
        result += f"・{cat}: HK${amt}\n"
    return result

# 支出圖表

def get_summary_chart(user_id):
    summary_sheet = get_account_sheet()
    data = summary_sheet.get_all_records()
    username = None
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return {}

    sheet = get_gsheet().open("家庭收支表").worksheet(username)
    rows = sheet.get_all_records()
    chart_data = {}
    for row in rows:
        if row.get("收入/支出") == "支出":
            cat = row.get("類別", "未分類")
            chart_data[cat] = chart_data.get(cat, 0) + float(row.get("金額", 0))
    return chart_data

# 用戶是否已驗證

def is_verified_user(user_id):
    from payment_check import is_payment_verified
    return is_payment_verified(user_id)

# 匯出 PDF

def export_pdf_report(user_id):
    summary_sheet = get_account_sheet()
    data = summary_sheet.get_all_records()
    username = None
    for row in data:
        if str(row.get("Telegram_ID")) == str(user_id):
            username = row.get("用戶名稱")
            break
    if not username:
        return None

    sheet = get_gsheet().open("家庭收支表").worksheet(username)
    rows = sheet.get_all_values()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="📘 收支報告 PDF", ln=True, align="C")
    pdf.ln()

    for row in rows:
        line = " | ".join(row)
        pdf.cell(200, 10, txt=line, ln=True)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output
