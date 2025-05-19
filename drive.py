
from fpdf import FPDF
import os

def export_pdf_report(user_id: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="📄 月報表", ln=True, align='C')
    pdf.cell(200, 10, txt=f"用戶 ID: {user_id}", ln=True, align='L')
    pdf.cell(200, 10, txt="支出總結、圖表與 GPT 理財建議（示意）", ln=True)
    filepath = f"/mnt/data/{user_id}_monthly_report.pdf"
    pdf.output(filepath)
    return filepath
