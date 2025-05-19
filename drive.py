from fpdf import FPDF
from modules.sheets import _get_user_ws
from modules.gpt import generate_financial_advice

def export_pdf_report(user_id):
    ws = _get_user_ws(user_id)
    data = ws.get_all_records()
    cat_sum = {}
    total = 0
    for d in data:
        if d["收入"] == "否":
            cat_sum[d["類別"]] = cat_sum.get(d["類別"], 0) + float(d["金額"])
            total += float(d["金額"])
    summary = "\n".join([f"{k}: ${v}" for k, v in cat_sum.items()])
    advice = generate_financial_advice(summary)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"📊 月報 - 用戶 {user_id}", ln=True)
    pdf.cell(200, 10, txt=f"總支出：${total}", ln=True)
    pdf.multi_cell(200, 10, txt="支出分類：\n" + summary)
    pdf.multi_cell(200, 10, txt="GPT 理財建議：\n" + advice)

    path = f"/mnt/data/{user_id}_report.pdf"
    pdf.output(path)
    return path
