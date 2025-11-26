import sqlite3
import json

db_path = "/opt/airflow/metadata/factor_platform.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, factor_code, status, metrics_json FROM factor_jobs WHERE status='SUCCESS' LIMIT 2;")
rows = cursor.fetchall()

for row in rows:
    job_id, factor_code, status, metrics = row
    print(f"\n{'='*60}")
    print(f"Job ID: {job_id}")
    print(f"Factor Code: {factor_code}")
    print(f"Status: {status}")
    print(f"Metrics (raw): {metrics}")
    print(f"Metrics type: {type(metrics)}")
    if metrics:
        try:
            m = json.loads(metrics)
            print(f"Metrics (parsed): {json.dumps(m, indent=2)}")
        except:
            print("Failed to parse metrics as JSON")

conn.close()
