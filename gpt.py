import openai
import os

def classify_entry(text, is_income):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if is_income:
        return "收入"
    prompt = f"請將以下支出分類為一個詞：飲食、交通、娛樂、生活用品、租金、其他。

用途：{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.3,
        )
        category = response.choices[0].message.content.strip()
        return category if category in ["飲食", "交通", "娛樂", "生活用品", "租金", "其他"] else "其他"
    except Exception:
        return "其他"

def generate_financial_advice(summary):
    prompt = f"以下係一個人呢個月嘅支出分類總結：\n{summary}\n請用繁體中文提供3項簡單理財建議。"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "⚠️ 無法生成建議。"
