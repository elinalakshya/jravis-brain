#!/usr/bin/env python3
"""
phase1_runner.py (Auto API-key generation integrated)

Behavior:
- Creates connectors for 10 streams (all use MASTER_USER / MASTER_PASS for login).
- Runs connector jobs (--run-once or daemon).
- AFTER jobs complete, if SKIP_API_GEN is not set, attempts to call impl.create_api_key()
  for any connector.impl that exposes it; results are saved to generated_api_keys.json.

Env required:
  MASTER_USER
  MASTER_PASS
Optional:
  PRINTIFY_KEY

Usage:
  ./activate_all.sh
  python3 phase1_runner.py --run-once --parallel
  python3 phase1_runner.py --start-daemon --parallel --interval 600
"""
import os
import sys
import time
import json
import argparse
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------- Connector ----------------
class Connector:

    def __init__(self, name, config, impl=None):
        self.name = name
        self.config = config
        self.impl = impl

    def run_job_once(self):
        try:
            if self.impl and hasattr(self.impl, "run_job_once"):
                return {"status": "ok", "detail": self.impl.run_job_once()}
            # default stubbed work
            time.sleep(0.3)
            return {"status": "ok", "detail": f"{self.name} job executed"}
        except Exception as e:
            return {
                "status": "error",
                "detail": str(e),
                "trace": traceback.format_exc()
            }


# ---------------- Helpers ----------------
def _check_master():
    user = os.getenv("MASTER_USER")
    pw = os.getenv("MASTER_PASS")
    if not user or not pw:
        raise EnvironmentError("Missing MASTER_USER/MASTER_PASS")
    return user, pw


# ---------------- Factories ----------------
def create_elina_instagram():
    u, p = _check_master()
    return Connector("ElinaInstagram", {"user": u, "pass": p})


def create_printify():
    u, p = _check_master()
    key = os.getenv("PRINTIFY_KEY")
    # For Printify we support both login-mode and API-key mode.
    # If a future impl supports create_api_key() it will be used by the auto-gen step.
    return Connector("PrintifyPOD", {"user": u, "pass": p, "api_key": key})


def create_meshy():
    u, p = _check_master()

    # Example impl with optional create_api_key; real impl should replace this stub.
    class MeshyImpl:

        def run_job_once(self):
            return "Meshy AI store sync success"

        # optional create_api_key method (stubbed to simulate behavior)
        def create_api_key(self):
            # In a real implementation this would interact with Meshy UI/API
            return {"api_key": f"msy-simulated-{int(time.time())}"}

    return Connector("MeshyAIStore", {"user": u, "pass": p}, MeshyImpl())


def create_cadcrowd():
    u, p = _check_master()

    class CadImpl:

        def run_job_once(self):
            return "CadCrowd job executed"

    return Connector("CadCrowdAuto", {"user": u, "pass": p}, CadImpl())


def create_fiverr():
    u, p = _check_master()

    class FiverrImpl:

        def run_job_once(self):
            return "Fiverr job executed"

    return Connector("FiverrAIAuto", {"user": u, "pass": p}, FiverrImpl())


def create_youtube():
    u, p = _check_master()

    # YouTube usually requires Google Cloud Console manual steps for OAuth/API keys;
    # we provide a stub that does NOT implement create_api_key (so it will be flagged manual).
    class YouTubeImpl:

        def run_job_once(self):
            return "YouTube automation executed"

    return Connector("YouTubeAutomation", {
        "user": u,
        "pass": p
    }, YouTubeImpl())


def create_stockimg():
    u, p = _check_master()

    class StockImpl:

        def run_job_once(self):
            return "Stock image/video sync executed"

    return Connector("StockImageVideo", {"user": u, "pass": p}, StockImpl())


def create_kdp():
    u, p = _check_master()

    class KdpImpl:

        def run_job_once(self):
            return "KDP job executed"

    return Connector("AI_Book_KDP", {"user": u, "pass": p}, KdpImpl())


def create_shopify():
    u, p = _check_master()

    class ShopifyImpl:

        def run_job_once(self):
            return "Shopify digital products sync executed"

    return Connector("ShopifyDigital", {"user": u, "pass": p}, ShopifyImpl())


def create_stationery():
    u, p = _check_master()

    class StationeryImpl:

        def run_job_once(self):
            return "Stationery export automation executed"

    return Connector("StationeryExport", {
        "user": u,
        "pass": p
    }, StationeryImpl())


# ---------------- Registry ----------------
FACTORIES = {
    "ElinaInstagram": create_elina_instagram,
    "PrintifyPOD": create_printify,
    "MeshyAIStore": create_meshy,
    "CadCrowdAuto": create_cadcrowd,
    "FiverrAIAuto": create_fiverr,
    "YouTubeAutomation": create_youtube,
    "StockImageVideo": create_stockimg,
    "AI_Book_KDP": create_kdp,
    "ShopifyDigital": create_shopify,
    "StationeryExport": create_stationery,
}


# ---------------- Core runner ----------------
def create_all():
    conns, errors = {}, {}
    for name, factory in FACTORIES.items():
        try:
            conns[name] = factory()
            print(f"[OK] {name} ready")
        except Exception as e:
            errors[name] = str(e)
            print(f"[ERR] {name} -> {e}")
    return conns, errors


def run_all(conns, parallel=True, max_workers=6):
    results = {}
    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(c.run_job_once): n for n, c in conns.items()}
            for f in as_completed(futs):
                n = futs[f]
                try:
                    results[n] = f.result()
                except Exception as e:
                    results[n] = {"status": "error", "detail": str(e)}
    else:
        for n, c in conns.items():
            results[n] = c.run_job_once()
    return results


# ---------------- API key auto-generator ----------------
def auto_generate_api_keys(conns):
    """
    For each connector that has impl.create_api_key(), call it and save results.
    Returns a dict with keys: generated, needs_manual, errors.
    """
    report = {"generated": {}, "needs_manual": {}, "errors": {}}
    for name, conn in conns.items():
        impl = getattr(conn, "impl", None)
        if impl and hasattr(impl, "create_api_key"):
            try:
                print(f"[API-GEN] Attempting create_api_key() for {name} ...")
                key_info = impl.create_api_key()
                # accept any serializable object returned by create_api_key()
                report["generated"][name] = key_info
                print(f"[API-GEN] ✅ {name} created key -> {key_info}")
            except Exception as e:
                report["errors"][name] = str(e)
                print(f"[API-GEN] ❌ {name} failed to create API key -> {e}")
                print(traceback.format_exc())
        else:
            report["needs_manual"][name] = "no create_api_key() method exposed"
            print(
                f"[API-GEN] ⚠️ {name} requires manual API key creation (no create_api_key())"
            )
    # persist to file
    out = "generated_api_keys.json"
    try:
        with open(out, "w") as f:
            json.dump(report, f, indent=2)
        print(f"[API-GEN] Report written to {out}")
    except Exception as e:
        print(f"[API-GEN] Failed to write {out}: {e}")
    return report


# ---------------- CLI / orchestration ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-once",
                    action="store_true",
                    help="Create connectors and run each once, then exit")
    ap.add_argument(
        "--start-daemon",
        action="store_true",
        help="Start a simple daemon loop that runs connectors periodically")
    ap.add_argument("--interval",
                    type=int,
                    default=300,
                    help="Daemon interval seconds")
    ap.add_argument("--parallel",
                    action="store_true",
                    help="Run connector jobs in parallel")
    ap.add_argument("--max-workers",
                    type=int,
                    default=6,
                    help="Max workers for parallel runs")
    args = ap.parse_args()

    if args.run_once:
        conns, errs = create_all()
        # if any creation errors show up, they are in errs
        results = run_all(conns,
                          parallel=args.parallel,
                          max_workers=args.max_workers)
        print(json.dumps({"results": results, "errors": errs}, indent=2))
        # Auto-generate API keys unless explicitly skipped
        if os.getenv("SKIP_API_GEN") == "1":
            print("[API-GEN] SKIP_API_GEN=1 set — skipping API key generation")
        else:
            print("[API-GEN] Starting automatic API key generation...")
            auto_generate_api_keys(conns)
        return

    if args.start_daemon:
        print("Starting daemon loop. Press Ctrl+C to stop.")
        try:
            while True:
                conns, errs = create_all()
                results = run_all(conns,
                                  parallel=args.parallel,
                                  max_workers=args.max_workers)
                print(
                    json.dumps({
                        "results": results,
                        "errors": errs
                    }, indent=2))
                if os.getenv("SKIP_API_GEN") == "1":
                    print(
                        "[API-GEN] SKIP_API_GEN=1 set — skipping API key generation"
                    )
                else:
                    print(
                        "[API-GEN] Starting automatic API key generation (daemon iteration)..."
                    )
                    auto_generate_api_keys(conns)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Daemon stopped by user.")
            return

    ap.print_help()


if __name__ == "__main__":
    main()
