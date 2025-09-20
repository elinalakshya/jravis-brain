#!/usr/bin/env python3
"""
generate_api_keys.py
- Imports phase1_runner.create_all() but does NOT trigger connector jobs.
- For each connector created, if connector.impl has method `create_api_key()`
  it will call it and save returned keys to generated_api_keys.json.
- Prints a clear report of successes and platforms that need manual action.
"""
import json, os, sys, traceback

sys.path.insert(0, os.getcwd())
try:
    import phase1_runner as runner
except Exception as e:
    print("❌ Failed to import phase1_runner.py:", e)
    raise


def main():
    conns, errors = runner.create_all()
    report = {"generated": {}, "needs_manual": {}, "errors": {}}

    # try to call create_api_key() on any connector.impl that exposes it
    for name, conn in conns.items():
        impl = getattr(conn, "impl", None)
        if impl and hasattr(impl, "create_api_key"):
            try:
                print(f"Attempting API key creation for {name} ...")
                key_info = impl.create_api_key()
                report["generated"][name] = key_info
                print(f"✅ {name}: created key -> {key_info}")
            except Exception as e:
                report["errors"][name] = str(e)
                print(f"❌ {name}: create_api_key failed -> {e}")
                print(traceback.format_exc())
        else:
            # no programmatic API key creation available from connector implementation
            report["needs_manual"][name] = "no create_api_key() method exposed"
            print(
                f"⚠️ {name}: requires manual API key creation (no create_api_key() method)"
            )

    # save results
    out = "generated_api_keys.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to {out}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
