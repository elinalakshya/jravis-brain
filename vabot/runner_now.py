import os, sys, importlib, datetime, traceback

# Ensure project root on sys.path (so "DailyReport" is importable)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def log(msg): print(msg, flush=True)

def main():
    log("VA Bot Runner @ " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " IST")
    try:
        m = importlib.import_module("DailyReport.phase1")
    except Exception as e:
        log("❌ Could not import DailyReport.phase1: " + repr(e))
        traceback.print_exc()
        sys.exit(2)
    if not hasattr(m, "run_all"):
        log("❌ phase1.run_all() not found"); sys.exit(3)
    try:
        results = m.run_all()
        for r in (results or []):
            try:
                log(f"- {r.get('task')}: {r.get('status')} — {r.get('details')} {'(' + r.get('at','') + ')' if r.get('at') else ''}")
            except Exception:
                log(f"- {r}")
        log("✅ Phase 1 batch completed.")
        sys.exit(0)
    except Exception as e:
        log("❌ Phase 1 batch failed: " + repr(e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
