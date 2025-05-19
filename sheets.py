# -*- coding: utf-8 -*-
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from datetime import datetime

def get_gsheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv("GOOGLE_SERVICE_JSON_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("家庭收支表").sheet1

def init_user_sheet(user_id):
    # This function is a placeholder in case you need user-specific setup
    pass

def add_record(user_id, amount, category, purpose, is_income):
    sheet = get_gsheet()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([user_id, date, amount, category, purpose, is_income])

def check_budget_status(user_id):
    sheet = get_gsheet()
    data = sheet.get_all_records()
    used = 0
    budget = 0
    for row in data:
        if str(row.get("user_id", "")).strip() == str(user_id):
            if str(row.get("is_income", "")).strip().lower() == "false":
                used += float(row.get("amount", 0))
            budget = float(row.get("budget", budget))
    return used, budget

def set_user_budget(user_id, amount):
    sheet = get_gsheet()
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("user_id", "")).strip() == str(user_id):
            sheet.update_cell(i, 7, amount)  # Assume column 7 = budget
            return
    # If user not found, append new row
    sheet.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, "", "", False, amount])

def get_income_summary(user_id):
    sheet = get_gsheet()
    data = sheet.get_all_records()
    total_income = 0
    breakdown = {}
    for row in data:
        if str(row.get("user_id", "")).strip() == str(user_id) and str(row.get("is_income", "")).lower() == "true":
            amt = float(row.get("amount", 0))
            cat = row.get("category", "未分類")
            total_income += amt
            breakdown[cat] = breakdown.get(cat, 0) + amt
    result = f"💰 本月總收入：HK${total_income}\n"
    for cat, amt in breakdown.items():
        result += f"・{cat}: HK${amt}\n"
    return result

def set_username(user_id, username):
    sheet = get_gsheet()
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if str(row.get("user_id", "")).strip() == str(user_id):
            sheet.update_cell(i, 8, username)  # Assume column 8 = username
            return
    sheet.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, "", "", False, 0, username])

def is_verified_user(update):
    from payment_check import is_payment_verified
    return is_payment_verified(str(update.effective_user.id))
