from telegram import Bot
from modules.sheets import _auth
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

def daily_summary():
    gc = _auth()
    sheet = gc.open_by_key("1EbGOIeQzgrLd2d8s60wifELwboDHv5EFA8zMzavTCLU")
    for ws in sheet.worksheets():
        user_id = ws.title
        if not user_id.isdigit():
            continue
        data = ws.get_all_records()
        today_data = [d for d in data if "今日" in d["時間"]]
        total = sum(float(d["金額"]) for d in today_data if d["收入"] == "否")
        if total > 0:
            msg = f"📅 今日支出總結：HK${total}"
            try:
                bot.send_message(chat_id=int(user_id), text=msg)
            except:
                pass

if __name__ == "__main__":
    daily_summary()
