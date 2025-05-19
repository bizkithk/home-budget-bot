import matplotlib.pyplot as plt
from modules.sheets import _get_user_ws
import os

def generate_summary_chart(user_id):
    ws = _get_user_ws(user_id)
    data = ws.get_all_records()
    cat_sum = {}
    for d in data:
        if d["收入"] == "否":
            cat_sum[d["類別"]] = cat_sum.get(d["類別"], 0) + float(d["金額"])
    labels = list(cat_sum.keys())
    sizes = list(cat_sum.values())
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    path = f"/mnt/data/{user_id}_summary.png"
    plt.savefig(path)
    plt.close()
    return path

def generate_weekly_charts(user_id):
    # Placeholder: can be extended for trend lines and bar charts
    return generate_summary_chart(user_id)
