from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from sheets import add_record, set_username, check_budget_status, set_user_budget, get_income_summary, get_user_sheet
from payment_check import is_payment_verified
import logging

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VERIFICATION_CODE = os.getenv("BOT_VERIFY_CODE")

user_verified = set()
user_states = {}
user_temp_data = {}

logging.basicConfig(level=logging.INFO)

def is_verified(user_id):
    from payment_check import is_payment_verified, is_subscription_active
    return is_payment_verified(user_id) and is_subscription_active(user_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text(
            "👋 歡迎使用《AI 家居記帳助手》！

"
            "🔐 請先輸入：
"
            "/verify 密碼 解鎖功能

"
            "⚠️ 未驗證前無法使用記帳與查表功能～"
        )
        return
    await update.message.reply_text(
        "🎉 你已成功啟用 AI 家居記帳助手！

"
        "📝 記帳方法：
"
        "➡️ `52 晚餐` 👉 支出
"
        "➡️ `+1000 freelance` 👉 收入

"
        "📘 指令教學：
"
        "🔤 /setusername 名稱 - 設定名稱
"
        "💰 /setbudget 金額 - 設定預算
"
        "📊 /summary - 查看支出圖表
"
        "📈 /income - 查看收入總結
"
        "📄 /export 密碼 - 匯出 PDF 月報
"
        "❓ /help - 查看所有指令"
    )
    user_states[user_id] = "amount"

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) > 0 and context.args[0] == VERIFICATION_CODE:
        user_verified.add(user_id)
        await update.message.reply_text(
            "✅ 驗證成功，AI 家居記帳助手已為你啟動！

"
            "👇 請先完成以下設定步驟：
"
            "1️⃣ 輸入 `/setusername`，系統會自動幫你使用 Telegram 名稱作為用戶名

"
            "2️⃣ 設定本月支出預算（可選）：
"
            "   `/setbudget 金額`
"
            "   例如：`/setbudget 5000`

"
            "✅ 完成後你可以直接輸入金額開始記帳，或使用以下指令：

"
            "📘 指令一覽：
"
            "📝 `52 晚餐` 👉 支出
"
            "💵 `+1000 freelance` 👉 收入
"
            "📊 /summary - 查看支出圖表
"
            "📈 /income - 查看收入總結
"
            "📄 /export 密碼 - 匯出 PDF 月報
"
            "🆘 /help - 查看所有指令"
        )
    else:
        await update.message.reply_text("❌ 驗證失敗，請檢查驗證碼是否正確。")
    else:
        await update.message.reply_text("驗證失敗，請檢查驗證碼是否正確。")
    else:
        await update.message.reply_text("驗證失敗，請檢查驗證碼是否正確。")

async def setusername(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return
    # 自動設定 Telegram 名稱為用戶名稱
    tg_name = update.effective_user.first_name or update.effective_user.username or str(user_id)
    set_username(user_id, tg_name)
    await update.message.reply_text(f"✅ 使用者名稱已自動設定為：{tg_name}")
    await update.message.reply_text(f"✅ 使用者名稱已設定為：{name}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return

    text = update.message.text.strip()
    state = user_states.get(user_id)

    if state == "amount":
        if text.replace('.', '', 1).isdigit():
            user_temp_data[user_id] = {"amount": float(text)}
            user_states[user_id] = "category"
            await update.message.reply_text("請輸入類別，例如：食品、交通、娛樂")
        else:
            await update.message.reply_text("請輸入有效金額！")

    elif state == "category":
        user_temp_data[user_id]["category"] = text
        user_states[user_id] = "note"
        await update.message.reply_text("可選填寫備註（如無可輸入 -）")

    elif state == "note":
        user_temp_data[user_id]["note"] = text if text != "-" else ""
        user_states[user_id] = "type"
        keyboard = [
            [InlineKeyboardButton("收入", callback_data="income"),
             InlineKeyboardButton("支出", callback_data="expense")]
        ]
        await update.message.reply_text("請選擇類型：", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selection = query.data

    if user_id in user_temp_data:
        data = user_temp_data[user_id]
        is_income = (selection == "income")
        add_record(user_id, data["amount"], data["category"], data["note"], is_income)
        await query.edit_message_text("✅ 記帳成功！如要再新增請輸入金額。")
        user_states[user_id] = "amount"
        user_temp_data.pop(user_id)

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return
    used, budget = check_budget_status(user_id)
    await update.message.reply_text(f"📊 本月已用：HK${used} / 預算：HK${budget}")

async def setbudget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return
    if context.args and context.args[0].isdigit():
        set_user_budget(user_id, float(context.args[0]))
        await update.message.reply_text(f"✅ 預算已設定為 HK${context.args[0]}")
    else:
        await update.message.reply_text("請輸入有效預算，例如： /setbudget 5000")

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return
    summary = get_income_summary(user_id)
    await update.message.reply_text(summary)

async def advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("請先輸入驗證碼 /verify")
        return
    advice_text = generate_financial_advice(user_id)
    await update.message.reply_text(f"💡 AI 理財建議：
{advice_text}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("setusername", setusername))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("budget", budget))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("advice", advice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
