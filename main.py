# -*- coding: utf-8 -*-
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sheets import (
    is_verified_user,
    init_user_sheet,
    set_user_budget,
    add_record,
    get_income_summary,
    get_summary_chart,
    export_pdf_report
)
from payment_check import is_payment_verified
from gpt import generate_financial_advice

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot welcome message
WELCOME_MESSAGE = (
    "✅ 驗證成功！\n\n"
    "👋 歡迎使用《AI 家居記帳助手》！\n\n"
    "📌 你已自動建立個人專屬分頁，可即時開始記帳！\n\n"
    "💡 記帳方法：\n"
    "`52 晚餐` 👉 支出\n"
    "`+1000 freelance` 👉 收入\n\n"
    "📘 指令教學：\n"
    "/setbudget 金額 - 設定預算\n"
    "/summary - 查看支出圖表\n"
    "/income - 查看收入總結\n"
    "/export 密碼 - 匯出 PDF 月報\n"
    "/advice - GPT 理財建議\n"
    "/help - 查看所有指令"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_verified_user(update):
        await update.message.reply_text(
            "👋 歡迎使用《AI 家居記帳助手》！\n\n"
            "請先輸入：\n"
            "/verify 密碼 解鎖功能 🔐\n\n"
            "未驗證前無法使用記帳與查表功能～"
        )
        return

    username = update.effective_user.first_name
    init_user_sheet(user_id, username)
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("請用法：/verify [密碼]")
        return
    password = context.args[0]
    user_id = update.effective_user.id
    if is_payment_verified(user_id, password):
        username = update.effective_user.first_name
        init_user_sheet(user_id, username)
        await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ 驗證失敗，請檢查密碼或付款狀態。")

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified_user(update):
        await update.message.reply_text("請先輸入 /verify 密碼 解鎖功能 🔐")
        return

    text = update.message.text.strip()
    is_income = text.startswith("+")
    if is_income:
        text = text[1:].strip()

    try:
        amount_str, *category_parts = text.split()
        amount = float(amount_str)
        category = " ".join(category_parts)
        add_record(user_id, amount, category, "", is_income)
        await update.message.reply_text("✅ 已記錄成功！")
    except Exception as e:
        await update.message.reply_text("⚠️ 格式錯誤，請用：\n`52 晚餐` 或 `+1000 freelance`", parse_mode="Markdown")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_verified_user(update):
        await update.message.reply_text("請先輸入 /verify 密碼 解鎖功能 🔐")
        return

    chart_path = get_summary_chart(update.effective_user.id)
    if chart_path:
        await update.message.reply_photo(photo=open(chart_path, "rb"))
    else:
        await update.message.reply_text("目前尚未有支出紀錄。")

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_verified_user(update):
        await update.message.reply_text("請先輸入 /verify 密碼 解鎖功能 🔐")
        return

    summary = get_income_summary(update.effective_user.id)
    await update.message.reply_text(summary)

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("請輸入數字，例如：/setbudget 5000")
        return
    try:
        amount = float(context.args[0])
        set_user_budget(update.effective_user.id, amount)
        await update.message.reply_text("📌 預算設定成功！")
    except:
        await update.message.reply_text("⚠️ 無效的數字。")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("請用法：/export [密碼]")
        return

    password = context.args[0]
    user_id = update.effective_user.id
    if not is_payment_verified(user_id, password):
        await update.message.reply_text("❌ 密碼錯誤，無法匯出報告。")
        return

    file_path = export_pdf_report(user_id)
    await update.message.reply_document(document=open(file_path, "rb"), filename="月報表.pdf")

async def advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified_user(update):
        await update.message.reply_text("請先驗證 /verify 密碼 才可使用 GPT 理財分析 ✨")
        return
    await update.message.reply_text("🤖 正在分析中...請稍候...")
    result = generate_financial_advice(user_id)
    await update.message.reply_text(result)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("advice", advice))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record))

    app.run_polling()
