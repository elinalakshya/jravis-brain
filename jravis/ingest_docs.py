# ingest_docs.py
import os, glob, uuid
import fitz  # pymupdf
from memory_store import embed_and_store, save_report

DOC_FOLDER = os.getenv("DOC_FOLDER", "./Report")


def text_from_pdf(path):
    doc = fitz.open(path)
    txt = []
    for p in doc:
        txt.append(p.get_text())
    return "\n".join(txt)


def ingest_all():
    files = glob.glob(os.path.join(DOC_FOLDER, "**", "*.pdf"), recursive=True)
    for f in files:
        txt = text_from_pdf(f)[:15000]  # limit size
        rid = str(uuid.uuid4())
        meta = {"source": f, "type": "pdf"}
        embed_and_store(rid, txt, meta)
        save_report(rid, "unknown", "pdf_ingest", f, txt[:400])


if __name__ == "__main__":
    ingest_all()
