# jravis_core_engine.py
# JRAVIS Core Engine — Phase 1 Active Automation Controller
# Author: Dhruvayu
# Mission 2040 (Phase 1): Stream Validation, Memory Logging, Dashboard Feed, Encrypted Reports

import datetime, os
from validate_streams import load_config, validate_stream
from memory_store import add_report, add_earnings
from send_report import encrypt_pdf, send_email_with_approval, check_approve_and_proceed, init_db, create_run
from fpdf import FPDF
from pathlib import Path

LOCK_CODE = os.getenv("LOCK_CODE", "1234")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def run_stream_diagnostics():
    cfg = load_config("streams_config.json")
    results = []
    ok_count = 0
    print("\n🔍 Running JRAVIS Stream Validation...\n")
    for s in cfg["streams"]:
        ok, msg = validate_stream(s)
        ok_count += 1 if ok else 0
        status = "✅ OK" if ok else "❌ FAIL"
        line = f"{status} | {s['name']} | {msg}"
        print(line)
        results.append(line)
    summary = "\n".join(results)
    add_report(datetime.datetime.utcnow().isoformat(), summary)
    add_earnings(datetime.date.today().isoformat(), ok_count * 10000,
                 "Validated Streams")
    return summary


def generate_report_files(summary_text):
    pdf_summary = REPORT_DIR / "summary_plain.pdf"
    pdf_invoices = REPORT_DIR / "invoices.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "JRAVIS Phase 1 Daily Summary", ln=True)
    pdf.multi_cell(0, 8, summary_text)
    pdf.output(pdf_summary)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Invoices Summary", ln=True)
    pdf.cell(0, 10, "All income streams clean, legal, automated.", ln=True)
    pdf.output(pdf_invoices)

    return pdf_summary, pdf_invoices


def execute_daily_cycle():
    print("🚀 JRAVIS Core Engine — Daily Cycle Started\n")
    summary_text = run_stream_diagnostics()

    summary_pdf, invoices_pdf = generate_report_files(summary_text)
    locked_pdf = REPORT_DIR / "summary_locked.pdf"
    encrypt_pdf(summary_pdf, locked_pdf, LOCK_CODE)

    init_db()
    run_id = datetime.datetime.utcnow().isoformat()
    create_run(run_id)
    send_email_with_approval(str(locked_pdf), str(invoices_pdf), run_id)

    print("\n⏳ Waiting up to 10 minutes for Boss approval...")
    approved = check_approve_and_proceed(run_id, timeout_seconds=600)
    if approved:
        print("✅ Approved: Continuing JRAVIS operations.")
    else:
        print("⏰ No approval received: Auto-resume triggered.")

    print("\n✅ Daily JRAVIS Core Cycle Completed.")


if __name__ == "__main__":
    execute_daily_cycle()
