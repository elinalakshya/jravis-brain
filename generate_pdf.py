import pdfkit

# Correct path from your Replit
config = pdfkit.configuration(
    wkhtmltopdf=
    '/nix/store/hxiay4lkq4389vxnhnb3d0pbaw6siwkw-wkhtmltopdf/bin/wkhtmltopdf')

# Example: convert HTML string to PDF
html_string = '<h1>Hello, Boss!</h1><p>This PDF now works!</p>'
pdfkit.from_string(html_string, 'output.pdf', configuration=config)

print("PDF generated successfully! Check 'output.pdf'.")
