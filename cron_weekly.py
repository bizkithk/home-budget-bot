from telegram import Bot
from modules.plot import generate_weekly_charts
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

def weekly_chart():
    # Normally would list from sheet
    users = os.getenv("WEEKLY_USER_IDS", "").split(",")
    for user_id in users:
        if not user_id.strip().isdigit():
            continue
        try:
            chart = generate_weekly_charts(user_id)
            bot.send_photo(chat_id=int(user_id), photo=open(chart, 'rb'), caption="📈 每週支出圖表")
        except:
            continue

if __name__ == "__main__":
    weekly_chart()
