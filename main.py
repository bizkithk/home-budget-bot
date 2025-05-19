# -*- coding: utf-8 -*-
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gpt import classify_entry, generate_financial_advice
from sheets import add_record, check_budget_status, get_income_summary, set_user_budget, init_user_sheet, set_username, is_verified_user
from plot import generate_summary_chart
from drive import export_pdf_report
from datetime import datetime

# 環境變數
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JOIN_PASSWORD = os.getenv("JOIN_PASSWORD")

# 機器人指令：start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not await is_verified_user(update):
        await update.message.reply_text(
            "👋 歡迎使用《AI 家居記帳助手》！\n\n"
            "請先輸入：\n"
            "/verify 密碼 解鎖功能 🔐\n\n"
            "未驗證前暫時無法使用任何記帳與圖表功能。"
        )
        return
    await update.message.reply_text(
        "🎉 你已成功啟用 AI 家居記帳助手！\n\n"
        "💡 記帳方式：\n"
        "➡️ `52 晚餐` 👉 支出\n"
        "➡️ `+1000 freelance` 👉 收入\n\n"
        "📌 指令教學：\n"
        "/setusername 名稱 - 設定名稱\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出月報 PDF\n"
        "/help - 查看所有指令\n"
    )

# 驗證指令
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0 or context.args[0] != JOIN_PASSWORD:
        await update.message.reply_text("❌ 密碼錯誤，請再試一次。")
        return
    user_id = str(update.effective_user.id)
    init_user_sheet(user_id)
    await update.message.reply_text("✅ 驗證成功，請輸入 /setusername [你的名稱] 以完成設定。")

# 設定用戶名稱
async def setusername(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("請輸入名稱，例如 /setusername Nic")
        return
    user_id = str(update.effective_user.id)
    username = context.args[0]
    set_username(user_id, username)
    await update.message.reply_text(f"✅ 名稱已設定為 {username}")

# 設定預算
async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    if len(context.args) == 0:
        await update.message.reply_text("請輸入預算金額，例如 /setbudget 5000")
        return
    user_id = str(update.effective_user.id)
    try:
        amount = float(context.args[0])
        set_user_budget(user_id, amount)
        await update.message.reply_text(f"✅ 本月預算已設定為 HK${amount}")
    except:
        await update.message.reply_text("⚠️ 輸入格式錯誤，請輸入數字，例如 /setbudget 5000")

# 顯示支出圖表
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    user_id = str(update.effective_user.id)
    chart_path = generate_summary_chart(user_id)
    await update.message.reply_photo(photo=open(chart_path, 'rb'), caption="📊 本月支出總結")

# 顯示收入總結
async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    user_id = str(update.effective_user.id)
    summary = get_income_summary(user_id)
    await update.message.reply_text(summary)

# 匯出 PDF 報告
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        return
    if len(context.args) == 0 or context.args[0] != JOIN_PASSWORD:
        await update.message.reply_text("❌ 密碼錯誤，請再試一次。")
        return
    user_id = str(update.effective_user.id)
    pdf_path = export_pdf_report(user_id)
    await update.message.reply_document(document=open(pdf_path, 'rb'), filename="月報表.pdf")

# 處理日常記帳輸入
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
        await update.message.reply_text("❗ 輸入格式錯誤，請試例如：52 晚餐 或 +1000 freelance")
        return
    category = classify_entry(purpose, is_income)
    add_record(user_id, amount, category, purpose, is_income)
    used, budget = check_budget_status(user_id)
    msg = f"✅ 已記錄：{category} - ${amount}（{purpose}）\n📊 本月已用：${used} / ${budget}"
    if used > budget:
        msg += "\n⚠️ 已超出本月預算！"
    await update.message.reply_text(msg)

# 指令教學
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
📥 記帳方式：
例如：52 晚餐 或 +1000 freelance
""")

# App 初始化
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 指令處理器
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
