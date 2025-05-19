
import openai
import os

def classify_entry(purpose: str, is_income: bool) -> str:
    if is_income:
        return "收入"
    keywords = {
        "飲食": ["餐", "飯", "食", "飲", "外賣"],
        "交通": ["巴士", "地鐵", "的士", "油", "車", "車費"],
        "娛樂": ["電影", "遊戲", "唱K", "Netflix", "音樂"],
        "生活用品": ["洗衣", "牙膏", "紙巾", "廁紙", "清潔"],
        "租金": ["租", "房", "按金"]
    }
    for category, keys in keywords.items():
        if any(k in purpose for k in keys):
            return category
    return "其他"

def generate_financial_advice(user_data: list) -> str:
    if not user_data:
        return "💡 目前資料不足，無法提供理財建議。"
    total = sum([float(x['Amount']) for x in user_data if x['Type'] == '支出'])
    if total > 5000:
        return "⚠️ 本月支出偏高，建議減少娛樂與外食開支。"
    elif total < 2000:
        return "✅ 支出控制良好，請保持良好理財習慣！"
    return "📊 支出尚算合理，如能記錄更詳細分類將更有幫助。"
