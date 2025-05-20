# -*- coding: utf-8 -*-
# main.py
import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sheets import is_verified_user, set_username, add_record, get_summary_chart, get_income_summary, set_user_budget, export_pdf_report
from payment_check import is_payment_verified
from gpt_advice import generate_financial_advice
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_payment_verified(user_id):
        await update.message.reply_text(
            "👋 歡迎使用《AI 家居記帳助手》！\n\n"
            "請先輸入：\n"
            "/verify 密碼 解鎖功能 🔐\n\n"
            "未驗證前無法使用記帳與查表功能～"
        )
        return

    username = update.effective_user.full_name
    set_username(user_id, username)

    await update.message.reply_text(
        "✅ 驗證成功！\n\n"
        f"Hello {username}～歡迎加入《AI 家庭記帳助手》大家庭！\n\n"
        "你已自動建立個人專屬分頁，可即時開始記帳。\n\n"
        "💡 記帳方法：\n"
        "`52 晚餐` 👉 支出\n"
        "`+1000 freelance` 👉 收入\n\n"
        "📘 指令教學：\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出 PDF 月報\n"
        "/advice - 查看 GPT 理財建議\n"
        "/help - 查看所有指令"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = os.getenv("BOT_ACCESS_PASSWORD")
    if len(context.args) == 0 or context.args[0] != password:
        await update.message.reply_text("密碼錯誤，請再試一次。")
        return

    user_id = str(update.effective_user.id)
    context.user_data["verified"] = True
    await start(update, context)

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("請輸入你的每月預算，例如 `/setbudget 1000`。")
        return
    try:
        budget = float(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入正確數字。")
        return
    user_id = str(update.effective_user.id)
    set_user_budget(user_id, budget)
    await update.message.reply_text(f"🎯 每月預算已設定為 HK${budget}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chart_url = get_summary_chart(str(update.effective_user.id))
    await update.message.reply_photo(chart_url)

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_income_summary(str(update.effective_user.id))
    await update.message.reply_text(result)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0 or context.args[0] != os.getenv("BOT_ACCESS_PASSWORD"):
        await update.message.reply_text("密碼錯誤，無法匯出報告。")
        return
    pdf = export_pdf_report(str(update.effective_user.id))
    await update.message.reply_document(pdf)

async def advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    advice_text = generate_financial_advice(user_id)
    await update.message.reply_text(advice_text)

async def handle_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_verified_user(update):
        await update.message.reply_text("請先輸入 /verify 密碼 解鎖功能。")
        return

    text = update.message.text
    user_id = str(update.effective_user.id)

    try:
        if text.startswith("+"):
            amount, purpose = text[1:].split(" ", 1)
            add_record(user_id, amount, "收入", purpose, True)
        else:
            amount, purpose = text.split(" ", 1)
            add_record(user_id, amount, "支出", purpose, False)
        await update.message.reply_text("✅ 記錄成功！")
    except:
        await update.message.reply_text("⚠️ 請用正確格式輸入，如：`+1000 freelance` 或 `52 晚餐`")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("advice", advice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_entry))

    app.run_polling()
