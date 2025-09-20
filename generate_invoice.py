import pdfkit
import os
from datetime import datetime

# wkhtmltopdf path on Replit
wk_path = '/nix/store/hxiay4lkq4389vxnhnb3d0pbaw6siwkw-wkhtmltopdf/bin/wkhtmltopdf'
config = pdfkit.configuration(wkhtmltopdf=wk_path)

# Example dynamic data
invoice_data = {
    "date":
    datetime.today().strftime("%d-%m-%Y"),
    "invoice_no":
    "INV-1001",
    "client_name":
    "Elina Pvt Ltd",
    "items": [{
        "no": 1,
        "desc": "Design Service",
        "qty": 2,
        "unit_price": 500,
        "total": 1000
    }, {
        "no": 2,
        "desc": "Printing Service",
        "qty": 1,
        "unit_price": 750,
        "total": 750
    }]
}

# Generate items rows HTML
items_html = ""
grand_total = 0
for item in invoice_data["items"]:
    items_html += f"<tr><td>{item['no']}</td><td>{item['desc']}</td><td>{item['qty']}</td><td>{item['unit_price']}</td><td>{item['total']}</td></tr>"
    grand_total += item["total"]

invoice_data["items"] = items_html
invoice_data["grand_total"] = grand_total

# Read template
with open("invoice_template.html", "r") as f:
    template = f.read()

# Replace placeholders
for key, value in invoice_data.items():
    template = template.replace(f"{{{{{key}}}}}", str(value))

# Output PDF
output_pdf = f"Invoice_{invoice_data['invoice_no']}.pdf"
pdfkit.from_string(template, output_pdf, configuration=config)

print(f"Invoice PDF generated: {output_pdf}")
