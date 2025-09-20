import pdfkit
import os
import pandas as pd
from datetime import datetime

# wkhtmltopdf path
wk_path = '/nix/store/hxiay4lkq4389vxnhnb3d0pbaw6siwkw-wkhtmltopdf/bin/wkhtmltopdf'
config = pdfkit.configuration(wkhtmltopdf=wk_path)

# Load invoice template
with open("invoice_template.html", "r") as f:
    template_html = f.read()

# Load CSV data
df = pd.read_csv("invoices.csv")

# Group by invoice_no to combine items
for invoice_no, group in df.groupby("invoice_no"):
    invoice_data = {
        "date": datetime.today().strftime("%d-%m-%Y"),
        "invoice_no": invoice_no,
        "client_name": group.iloc[0]["client_name"],
        "items": "",
        "grand_total": 0
    }

    # Build items table
    items_html = ""
    grand_total = 0
    for idx, row in group.iterrows():
        total = row["qty"] * row["unit_price"]
        items_html += f"<tr><td>{idx+1}</td><td>{row['item_desc']}</td><td>{row['qty']}</td><td>{row['unit_price']}</td><td>{total}</td></tr>"
        grand_total += total

    invoice_data["items"] = items_html
    invoice_data["grand_total"] = grand_total

    # Replace placeholders
    filled_html = template_html
    for key, value in invoice_data.items():
        filled_html = filled_html.replace(f"{{{{{key}}}}}", str(value))

    # Output PDF
    output_pdf = f"Invoice_{invoice_no}.pdf"
    pdfkit.from_string(filled_html, output_pdf, configuration=config)
    print(f"Generated: {output_pdf}")

print("All invoices generated successfully!")
