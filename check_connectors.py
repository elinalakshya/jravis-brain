#!/usr/bin/env python3
# check_connectors.py
# Prints which connectors will be created successfully and which are failing (no jobs executed).

import json
import sys
import os

# ensure current dir on path
sys.path.insert(0, os.getcwd())

try:
    import phase1_runner as runner
except Exception as e:
    print("❌ Failed to import phase1_runner.py:", e)
    sys.exit(2)


def main():
    try:
        conns, errors = runner.create_all()
    except Exception as e:
        print("❌ create_all() crashed:", e)
        raise

    print("\n=== CONNECTORS READY ===")
    if conns:
        for name in sorted(conns.keys()):
            print(f"✅ {name}")
    else:
        print("— none ready")

    print("\n=== CONNECTORS WITH ERRORS ===")
    if errors:
        for name, err in errors.items():
            # print only first line of error for brevity
            first_line = err.splitlines()[0] if isinstance(err,
                                                           str) else str(err)
            print(f"❌ {name} -> {first_line}")
    else:
        print("— none")

    # quick summary as JSON for tools
    summary = {"ready": list(conns.keys()), "errors": errors}
    print("\n=== SUMMARY JSON ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
