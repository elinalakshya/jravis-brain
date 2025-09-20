#!/usr/bin/env python3
"""
Generate two PDFs from DailyReport/out/connector_results.json:
  1) DD-MM-YYYY summary report.pdf    (encrypted with passcode 'MY OG')
  2) DD-MM-YYYY invoices.pdf          (not encrypted)

Requirements:
  pip install reportlab PyPDF2

Usage:
  python3 scripts/generate_reports.py
Return codes:
  0 = success (both PDFs created, summary encrypted)
  1 = connector_results.json missing / parse error
  2 = PDF generation error
"""

import json, os, sys, time
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DailyReport" / "out"
OUT.mkdir(parents=True, exist_ok=True)

PASSCODE = "MY OG"  # per your saved memory


def load_results():
    p = OUT / "connector_results.json"
    if not p.exists():
        print("Missing connector_results.json at", p)
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        print("Error reading connector_results.json:", e)
        return None


def make_summary_pdf(summary_path, results):
    """
    Creates a neat summary PDF listing each connector, status, and earnings.
    """
    try:
        c = canvas.Canvas(str(summary_path), pagesize=A4)
        width, height = A4
        margin = 15 * mm
        x = margin
        y = height - margin

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, "VA Bot — Daily Summary Report")
        y -= 10 * mm
        c.setFont("Helvetica", 10)
        ts = results.get("generated_at") or time.strftime("%d-%m-%Y %H:%M:%S")
        c.drawString(x, y, f"Generated: {ts}")
        y -= 8 * mm

        # Table header
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Connector")
        c.drawString(x + 70 * mm, y, "Status")
        c.drawString(x + 110 * mm, y, "Earnings (INR)")
        y -= 6 * mm
        c.setFont("Helvetica", 10)

        total = 0
        results_map = results.get("results", {})
        for name, info in results_map.items():
            if y < 30 * mm:
                c.showPage()
                y = height - margin
            earnings = info.get("earnings") or info.get("amount") or 0
            if isinstance(earnings, (int, float)):
                display_earn = f"{int(earnings)}"
                total += earnings
            else:
                display_earn = str(earnings)
            status = info.get("status", "")
            note = info.get("note", "")
            c.drawString(x, y, name)
            c.drawString(x + 70 * mm, y, f"{status} {note}")
            c.drawRightString(x + 150 * mm, y, display_earn)
            y -= 6 * mm

        # Total
        if y < 30 * mm:
            c.showPage()
            y = height - margin
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y - 4 * mm, "TOTAL")
        c.drawRightString(x + 150 * mm, y - 4 * mm, str(int(total)))
        c.showPage()
        c.save()
        return True
    except Exception as e:
        print("Error generating summary PDF:", e)
        return False


def make_invoices_pdf(invoices_path, results):
    """
    Simple invoices PDF: one line per connector with a small invoice-like layout.
    """
    try:
        c = canvas.Canvas(str(invoices_path), pagesize=A4)
        width, height = A4
        margin = 15 * mm
        x = margin
        y = height - margin

        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, "VA Bot — Invoices")
        y -= 10 * mm
        c.setFont("Helvetica", 10)
        c.drawString(
            x, y,
            f"Date: {results.get('generated_at') or time.strftime('%d-%m-%Y %H:%M:%S')}"
        )
        y -= 8 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Connector")
        c.drawString(x + 70 * mm, y, "Amount (INR)")
        y -= 6 * mm
        c.setFont("Helvetica", 10)

        results_map = results.get("results", {})
        for name, info in results_map.items():
            if y < 30 * mm:
                c.showPage()
                y = height - margin
            earnings = info.get("earnings") or 0
            c.drawString(x, y, f"Invoice: {name}")
            c.drawRightString(x + 150 * mm, y, str(int(earnings)))
            y -= 8 * mm
            # invoice small details (dummy invoice number)
            c.setFont("Helvetica", 8)
            c.drawString(
                x + 5 * mm, y,
                f"Invoice ID: {name[:3].upper()}-{int(time.time())%100000}")
            y -= 8 * mm
            c.setFont("Helvetica", 10)
        c.showPage()
        c.save()
        return True
    except Exception as e:
        print("Error generating invoices PDF:", e)
        return False


def encrypt_pdf(in_path, out_path, password):
    try:
        reader = PdfReader(str(in_path))
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        writer.encrypt(user_pwd=password, owner_pwd=None, use_128bit=True)
        with open(out_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print("Error encrypting PDF:", e)
        return False


def main():
    results = load_results()
    if results is None:
        return 1

    date_str = time.strftime("%d-%m-%Y")
    summary_name = f"{date_str} summary report.pdf"
    invoices_name = f"{date_str} invoices.pdf"
    summary_tmp = OUT / ("tmp_" + summary_name)
    summary_final = OUT / summary_name
    invoices_final = OUT / invoices_name

    ok1 = make_summary_pdf(summary_tmp, results)
    if not ok1:
        print("Failed to create summary PDF")
        return 2

    ok2 = make_invoices_pdf(invoices_final, results)
    if not ok2:
        print("Failed to create invoices PDF")
        return 2

    # Encrypt the summary (write to final)
    enc_ok = encrypt_pdf(summary_tmp, summary_final, PASSCODE)
    # cleanup tmp
    try:
        if summary_tmp.exists():
            summary_tmp.unlink()
    except Exception:
        pass

    if not enc_ok:
        print("Failed to encrypt summary PDF")
        return 2

    print("Generated files:")
    print(" -", summary_final)
    print(" -", invoices_final)
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
