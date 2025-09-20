#!/usr/bin/env bash
# activate_all.sh — Phase 1 VA Bot activation (finalized)

set -e

echo "========================================"
echo "🚀 Starting VA Bot Phase 1 Activation"
echo "Date: $(date -u)"
echo "========================================"

# Required env vars
REQUIRED_VARS=("MASTER_USER" "MASTER_PASS")

missing=false
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing: $var"
    missing=true
  else
    echo "✅ $var found"
  fi
done

# Optional env var for Printify API
if [ -z "${PRINTIFY_KEY}" ]; then
  echo "⚠️  PRINTIFY_KEY not set (Printify will run in login mode only)"
else
  echo "✅ PRINTIFY_KEY found"
fi

if [ "$missing" = true ]; then
  echo "========================================"
  echo "❌ MASTER_USER/MASTER_PASS missing. Please add them in Replit."
  echo "========================================"
  exit 1
fi

echo "========================================"
echo "✅ All required secrets present. Running VA Bot..."
echo "========================================"

# Run once with parallel execution
python3 phase1_runner.py --run-once --parallel 2>&1 | tee "va_activation_$(date +%s).log"

echo "========================================"
echo "✅ Activation complete. Log saved."
echo "========================================"
