<<<<<<< HEAD

=======
web: gunicorn send_daily_report:app --preload --bind 0.0.0.0:$PORT
>>>>>>> 713bdd5 (Initial commit)


web: python jravis_dashboard_v3_1.py

# Render startup configuration
web: python income_system_bundle.py

web: gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT

worker: python Mission2040_JRAVIS_VABot_Intelligence_Script.py

web: python jravis_core_debian.py
