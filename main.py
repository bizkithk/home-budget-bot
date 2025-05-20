# -*- coding: utf-8 -*-
import os
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          filters, ContextTypes, ConversationHandler)
from sheets import (is_verified_user, set_username, add_record, get_summary_chart,
                    get_income_summary, set_user_budget, export_pdf_report)
from payment_check import is_payment_verified

# --- 狀態代碼 ---
AWAITING_USERNAME, AWAITING_EXPORT_PASSWORD = range(2)

# --- 指令 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        await update.message.reply_text(
            "👋 歡迎使用《AI 家居記帳助手》！\n\n"
            "請先輸入：\n"
            "/verify 密碼 解鎖功能 🔐\n\n"
            "未驗證前無法使用記帳與查表功能～"
        )
        return

    await update.message.reply_text(
        "🎉 驗證成功！\n\n"
        "👋 歡迎使用《AI 家居記帳助手》！\n\n"
        "📌 請先設定你嘅用戶名稱：\n"
        "`/setusername 你的名稱`\n（建議用你嘅 Telegram 名稱，例如：`/setusername 阿強`）\n\n"
        "💡 完成後你就可以直接輸入金額＋備註嚟記帳，例如：\n"
        "`50 晚餐` 👉 支出\n"
        "`+1000 freelance` 👉 收入\n\n"
        "📘 常用指令：\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出 PDF 月報\n"
        "/help - 查看所有功能"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ 請加上密碼，例如：`/verify your_password`")
        return

    password = context.args[0]
    if is_payment_verified(user_id, password):
        await update.message.reply_text("✅ 驗證成功，請輸入 `/start` 開始使用！")
    else:
        await update.message.reply_text("❌ 密碼錯誤或未付款。請先完成付款。")

async def setusername(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        await update.message.reply_text("⚠️ 請先完成驗證。輸入 `/verify 密碼`")
        return

    if not context.args:
        await update.message.reply_text("❌ 請輸入名稱，例如：`/setusername 阿媽`")
        return

    username = " ".join(context.args)
    set_username(user_id, username)
    await update.message.reply_text(f"✅ 已設定名稱為「{username}」！你可開始記帳啦～")

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        await update.message.reply_text("⚠️ 請先完成驗證。輸入 `/verify 密碼`")
        return

    if not context.args:
        await update.message.reply_text("請輸入預算金額，例如：/setbudget 5000")
        return

    try:
        amount = float(context.args[0])
        set_user_budget(user_id, amount)
        await update.message.reply_text(f"✅ 已設定每月預算為 HK${amount}")
    except ValueError:
        await update.message.reply_text("❌ 請輸入有效的數字金額。")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        await update.message.reply_text("⚠️ 請先完成驗證。輸入 `/verify 密碼`")
        return
    image = get_summary_chart(user_id)
    await update.message.reply_photo(photo=image)

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        await update.message.reply_text("⚠️ 請先完成驗證。輸入 `/verify 密碼`")
        return
    msg = get_income_summary(user_id)
    await update.message.reply_text(msg)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("請輸入密碼，例如：/export your_password")
        return

    password = context.args[0]
    if not is_payment_verified(user_id, password):
        await update.message.reply_text("❌ 未能驗證付款或密碼錯誤。請確認是否完成付款。")
        return

    file_path = export_pdf_report(user_id)
    await update.message.reply_document(document=open(file_path, "rb"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 指令一覽：\n\n"
        "/start - 開始使用\n"
        "/verify 密碼 - 解鎖功能\n"
        "/setusername 名稱 - 設定使用者名稱\n"
        "/setbudget 金額 - 設定預算\n"
        "/summary - 查看支出圖表\n"
        "/income - 查看收入總結\n"
        "/export 密碼 - 匯出 PDF 月報\n"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_verified_user(update):
        return await update.message.reply_text("⚠️ 請先輸入 /verify 密碼 完成驗證。")

    text = update.message.text.strip()
    if text.startswith("+"):
        try:
            parts = text[1:].split(" ", 1)
            amount = float(parts[0])
            purpose = parts[1] if len(parts) > 1 else "未分類"
            add_record(user_id, amount, "收入", purpose, True)
            await update.message.reply_text("✅ 收入已記錄！")
        except:
            await update.message.reply_text("❌ 輸入格式錯誤，例子：+1000 freelance")
    else:
        try:
            parts = text.split(" ", 1)
            amount = float(parts[0])
            purpose = parts[1] if len(parts) > 1 else "未分類"
            add_record(user_id, amount, "支出", purpose, False)
            await update.message.reply_text("✅ 支出已記錄！")
        except:
            await update.message.reply_text("❌ 輸入格式錯誤，例子：52 晚餐")

# --- 主程序 ---
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("setusername", setusername))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()
