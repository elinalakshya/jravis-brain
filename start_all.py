import subprocess
import threading
import time

# Define services and their ports
services = [("mission_bridge.py", 6000), ("jravis_core_v1.py", 7000),
            ("vabot_core_v1.py", 8000), ("jravis_dashboard_v5.py", 10000)]


def run_service(file, port):
    print(f"🚀 Starting {file} on port {port} ...")
    subprocess.run(["python3", file])


threads = []
for file, port in services:
    t = threading.Thread(target=run_service, args=(file, port))
    t.start()
    threads.append(t)
    time.sleep(2)  # give each service time to boot

for t in threads:
    t.join()
