# -*- coding: utf-8 -*-
# main.py
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sheets import (
    init_user_sheet,
    add_record,
    get_summary_chart,
    get_income_summary,
    set_user_budget,
    export_pdf_report,
    get_financial_advice,
    check_expiry,
    auto_register_user
)
from payment_check import is_verified_user

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name or "用戶"
    auto_register_user(user_id, username)

    if not is_verified_user(user_id):
        await update.message.reply_text(
            "🔒 功能尚未解鎖：請先完成付款並驗證 🔐\n\n"
            "請至付款表單上傳付款截圖，付款成功後會自動開通功能。"
        )
        return

    await update.message.reply_text(
        "🎉 你已成功啟用《AI 家庭記帳助手》！\n\n"
        "💡 記帳方法：\n"
        "`52 晚餐` 👉 支出\n"
        "`+1000 freelance` 👉 收入\n\n"
        "📘 指令教學：\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出 PDF 月報\n"
        "/gpt - GPT 理財建議\n"
        "/help - 查看所有指令"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 可用指令：\n\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出 PDF 月報\n"
        "/gpt - GPT 理財建議"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款與驗證。")
        return

    if text.startswith("+"):
        parts = text[1:].split(" ", 1)
        if len(parts) == 2:
            amount, category = parts
            add_record(user_id, amount, category, is_income=True)
            await update.message.reply_text("✅ 收入已記錄！")
        else:
            await update.message.reply_text("請用格式：`+金額 分類`")
    else:
        parts = text.split(" ", 1)
        if len(parts) == 2:
            amount, category = parts
            add_record(user_id, amount, category, is_income=False)
            await update.message.reply_text("✅ 支出已記錄！")
        else:
            await update.message.reply_text("請用格式：`金額 分類`")

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款。")
        return
    if len(context.args) == 0:
        await update.message.reply_text("請輸入預算金額，如：`/setbudget 5000`")
        return
    set_user_budget(user_id, context.args[0])
    await update.message.reply_text("🎯 預算已更新！")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款。")
        return
    image_path = get_summary_chart(user_id)
    if image_path:
        await update.message.reply_photo(photo=open(image_path, 'rb'))

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款。")
        return
    msg = get_income_summary(user_id)
    await update.message.reply_text(msg)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款。")
        return
    if len(context.args) == 0:
        await update.message.reply_text("請輸入密碼，如：`/export 密碼`")
        return
    pdf_path = export_pdf_report(user_id)
    if pdf_path:
        await update.message.reply_document(document=open(pdf_path, 'rb'))

async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(user_id):
        await update.message.reply_text("🔒 功能未解鎖，請先完成付款。")
        return
    suggestion = get_financial_advice(user_id)
    await update.message.reply_text(suggestion)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("gpt", gpt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
