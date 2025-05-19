# -*- coding: utf-8 -*-
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from modules.gpt import classify_entry, generate_financial_advice
from modules.sheets import add_record, check_budget_status, get_summary, set_user_budget, init_user_sheet, is_verified_user, set_username, get_income_summary
from modules.plot import generate_weekly_charts, generate_summary_chart
from modules.drive import export_pdf_report
from datetime import datetime

JOIN_PASSWORD = os.getenv("JOIN_PASSWORD")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not await is_verified_user(update):
        await update.message.reply_text("""👋 歡迎使用《AI 家居記帳助手》！

請先輸入：/verify [密碼] 解鎖功能 🔐

未驗證前暫時無法使用任何記帳與查閱功能。
""")
        return
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""✅ 驗證成功！

🎉 你已成功啟用 AI 家居記帳助手！

📚 記帳教學：

🧾 支出 ➜ 輸入「金額＋用途」
　例：52 晚餐、25 交通、198 書本

💵 收入 ➜ 輸入「+金額＋來源」
　例：+8000 薪金、+5000 freelance、+200 投資回報

🗂️ 系統會自動分類為：
🍔 飲食、🚇 交通、🎮 娛樂、🧻 生活用品、💡 水電煤、🏠 租金、📈 投資、💵 收入、🧩 其他

📊 每次記帳後會顯示：
✅ 分類結果＋📊 本月預算進度
⚠️ 超出預算即時提示！

🔁 每日自動摘要，📅 每週圖表推送
📄 可用 /export 匯出 PDF 報表

🆘 輸入 /help 查看所有功能列表 ✨
""")

🎉 你已成功啟用 AI 家居記帳助手！

📌 記帳方式：
52 晚餐 ➜ 支出
+1000 freelance ➜ 收入

🆘 輸入 /help 查看所有功能列表 ✨
""")

async def setusername(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("請輸入名稱，例如 /setusername Nic")
        return
    username = context.args[0]
    user_id = str(update.effective_user.id)
    set_username(user_id, username)
    await update.message.reply_text(f"👤 名稱已設定為 {username}")

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
    await update.message.reply_document(document=open(pdf_path, 'rb'), filename="📄 月報表.pdf")

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
        msg += "\n⚠️ 已超出本月預算！💸"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_verified_user(update):
        await update.message.reply_text("❌ 請先輸入 /verify [密碼] 解鎖所有功能 🔐")
        return
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
