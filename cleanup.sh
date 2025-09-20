#!/bin/bash
echo "🧹 Starting cleanup..."

# Delete logs
rm -f *.log *.log.* va_activation_*.log

# Delete test and backup scripts
rm -f test*.py *.bak app_root_unused.py main_elina.py

# Delete unused HTML / reports / icons
rm -f report*.html generated-icon.png invoices.csv

# Delete old configs not needed
rm -f vault.js package.json pyproject.toml render.yaml Dockerfile Procfile.bak

# Delete old JSON state/backups
rm -f daily_inputs.json payments.json logins.json tasks.json state.json approval_state.json *.json.bak

# Keep main essentials
echo "✅ Cleanup complete. Kept: main.py, .replit, Procfile, requirements.txt, DailyReport/, connectors in use."

cat > cleanup.sh <<'EOF'
#!/bin/bash
echo "🧹 Starting cleanup..."

# Delete logs
rm -f *.log *.log.* va_activation_*.log

# Delete test and backup scripts
rm -f test*.py *.bak app_root_unused.py main_elina.py

# Delete unused HTML / reports / icons
rm -f report*.html generated-icon.png invoices.csv

# Delete old configs not needed
rm -f vault.js package.json pyproject.toml render.yaml Dockerfile Procfile.bak

# Delete old JSON state/backups
rm -f daily_inputs.json payments.json logins.json tasks.json state.json approval_state.json *.json.bak

# Keep main essentials
echo "✅ Cleanup complete. Kept: main.py, .replit, Procfile, requirements.txt, DailyReport/, connectors in use."
EOF
