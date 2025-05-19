
import matplotlib.pyplot as plt
import os

def generate_summary_chart(user_id: str) -> str:
    data = {
        "飲食": 1200,
        "交通": 800,
        "娛樂": 600,
        "生活用品": 500,
        "租金": 2000,
        "其他": 300
    }
    labels = list(data.keys())
    values = list(data.values())

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("📊 本月支出分佈")
    output_path = f"/mnt/data/{user_id}_summary_chart.png"
    plt.savefig(output_path)
    plt.close()
    return output_path
