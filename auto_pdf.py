import pdfkit
import os
import sys

# Auto-detect wkhtmltopdf path on Replit
wk_path = '/nix/store/hxiay4lkq4389vxnhnb3d0pbaw6siwkw-wkhtmltopdf/bin/wkhtmltopdf'
if not os.path.exists(wk_path):
    raise FileNotFoundError(f"wkhtmltopdf not found at {wk_path}")

config = pdfkit.configuration(wkhtmltopdf=wk_path)


def generate_pdf_from_html_string(html_string, output_file='output.pdf'):
    pdfkit.from_string(html_string, output_file, configuration=config)
    print(f"PDF generated successfully: {output_file}")


def generate_pdf_from_file(html_file, output_file='output.pdf'):
    if not os.path.exists(html_file):
        raise FileNotFoundError(f"HTML file not found: {html_file}")
    pdfkit.from_file(html_file, output_file, configuration=config)
    print(f"PDF generated successfully: {output_file}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 0:
        # No arguments → use default HTML string
        html_content = """
        <h1>Hello, Boss!</h1>
        <p>This PDF is generated automatically from HTML string.</p>
        """
        generate_pdf_from_html_string(html_content, output_file='output.pdf')

    elif len(args) == 1:
        # One argument → HTML file, default output name
        html_file = args[0]
        output_name = os.path.splitext(os.path.basename(html_file))[0] + '.pdf'
        generate_pdf_from_file(html_file, output_file=output_name)

    else:
        # Multiple arguments → treat as pairs: html_file output_name
        if len(args) % 2 != 0:
            print(
                "Error: For multiple PDFs, provide pairs of [html_file output_pdf_name]"
            )
            sys.exit(1)
        for i in range(0, len(args), 2):
            html_file = args[i]
            output_name = args[i + 1]
            generate_pdf_from_file(html_file, output_file=output_name)
