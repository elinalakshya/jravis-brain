from fpdf import FPDF
from datetime import datetime
import os


def create_dummy_pdf(path, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=content, ln=True)
    pdf.output(path)


def main():
    from datetime import datetime
    today_str = datetime.now().strftime("%d-%m-%Y")
    folder = "reports/daily"
    os.makedirs(folder, exist_ok=True)
    summary_path = f"{folder}/{today_str}-summary.pdf"
    invoices_path = f"{folder}/{today_str}-invoices.pdf"

    create_dummy_pdf(summary_path, f"Summary Report for {today_str}")
    create_dummy_pdf(invoices_path, f"Invoices Report for {today_str}")

    print(f"Created dummy PDFs:\n- {summary_path}\n- {invoices_path}")


if __name__ == "__main__":
    main()
