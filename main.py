# -*- coding: utf-8 -*-
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gpt import classify_entry, generate_financial_advice
from sheets import add_record, check_budget_status, get_income_summary, set_user_budget, init_user_sheet, set_username, is_verified_user
from plot import generate_summary_chart
from drive import  export_pdf_report
from datetime import datetime

JOIN_PASSWORD = os.getenv("JOIN_PASSWORD")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not await is_verified_user(update):
        await update.message.reply_text("👋 歡迎使用《AI 家居記帳助手》！\n\n請先輸入：\n/veri...
        return
    await update.message.reply_text("✅ 歡迎你再次使用《AI 家居記帳助手》！\n\n📌 記帳方式：\n1. 52 晚餐（支出）\n2. +1000 freelance（收入）")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0 or context.args[0] != JOIN_PASSWORD:
        await update.message.reply_text("❌ 密碼錯誤，請再試一次。")
        return
    user_id = str(update.effective_user.id)
    init_user_sheet(user_id)
    await update.message.reply_text("✅ 驗證成功，請輸入 /setusername [你的名稱] 完成設定！\n例如：/setusername Nic")

async def setusername(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("請輸入名稱，例如 /setusername Nic")
        return
    username = context.args[0]
    user_id = str(update.effective_user.id)
    set_username(user_id, username)
    await update.message.reply_text(f"✅ 名稱已設定為 {username}")

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    if len(context.args) == 0:
        await update.message.reply_text("請輸入預算金額，例如 /setbudget 5000")
        return
    user_id = str(update.effective_user.id)
    amount = float(context.args[0])
    set_user_budget(user_id, amount)
    await update.message.reply_text(f"💰 本月預算已設定為 HK${amount}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    user_id = str(update.effective_user.id)
    chart_path = generate_summary_chart(user_id)
    await update.message.reply_photo(photo=open(chart_path, 'rb'), caption="📊 本月支出總結")

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    user_id = str(update.effective_user.id)
    summary_text = get_income_summary(user_id)
    await update.message.reply_text(summary_text)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    if len(context.args) == 0 or context.args[0] != JOIN_PASSWORD:
        await update.message.reply_text("❌ 密碼錯誤，請再試一次。")
        return
    user_id = str(update.effective_user.id)
    pdf_path = export_pdf_report(user_id)
    await update.message.reply_document(document=open(pdf_path, 'rb'), filename="月報表.pdf")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    is_income = text.startswith('+')
    try:
        amount_str, purpose = text[1:].split(' ', 1) if is_income else text.split(' ', 1)
        amount = float(amount_str)
    except:
        await update.message.reply_text("⚠️ 格式錯誤：請輸入 52 晚餐 或 +1000 freelance")
        return
    category = classify_entry(purpose, is_income)
    add_record(user_id, amount, category, purpose, is_income)
    used, budget = check_budget_status(user_id)
    msg = f"✅ 已記錄：{category} - ${amount}（{purpose}）\n📊 本月已用：${used} / ${budget}"
    if used > budget:
        msg += "\n⚠️ 已超出預算！"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""📘 指令列表：
/start - 使用教學
/verify [密碼] - 驗證使用權限
/setusername [名稱] - 設定用戶名稱
/setbudget [金額] - 設定預算
/summary - 查看支出圖表總結
/income - 查看收入統計
/export [密碼] - 匯出月報 PDF
/help - 查看所有指令
直接輸入「金額 用途」記帳，如：52 晚餐 或 +1000 freelance
""")

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("verify", verify))
app.add_handler(CommandHandler("setusername", setusername))
app.add_handler(CommandHandler("setbudget", setbudget))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("income", income))
app.add_handler(CommandHandler("export", export))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
