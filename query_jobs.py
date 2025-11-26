#!/usr/bin/env python3
import sqlite3, time, json, os

REGISTRY_DB = '/opt/airflow/metadata/factor_platform.db'
TIMEOUT = 60*30
INTERVAL = 10

def print_jobs():
    if not os.path.exists(REGISTRY_DB):
        print('Registry DB not found:', REGISTRY_DB)
        return
    con = sqlite3.connect(REGISTRY_DB)
    cur = con.cursor()
    rows = cur.execute('SELECT id, factor_code, status, result_path, metrics_json, error_message, created_at, updated_at FROM factor_jobs ORDER BY created_at DESC').fetchall()
    print(f'Found {len(rows)} jobs')
    for r in rows:
        id, code, status, result_path, metrics_json, error_message, created_at, updated_at = r
        print(f'job_id={id} code={code} status={status} result_path={result_path} created_at={created_at}')
        if metrics_json:
            try:
                print('  metrics:', json.loads(metrics_json))
            except Exception:
                print('  metrics (raw):', metrics_json)
        if error_message:
            print('  error:', error_message[:500])

if __name__ == '__main__':
    start = time.time()
    while True:
        print('\n--- polling registry ---')
        print_jobs()
        # check if any job is still PENDING or RUNNING
        con = sqlite3.connect(REGISTRY_DB)
        cur = con.cursor()
        rows = cur.execute("SELECT COUNT(*) FROM factor_jobs WHERE status IN ('PENDING','RUNNING')").fetchone()
        pending_running = rows[0] if rows else 0
        print(f'pending_or_running={pending_running}')
        if pending_running == 0:
            print('No PENDING/RUNNING jobs. Exiting.')
            break
        if time.time() - start > TIMEOUT:
            print('Timeout reached. Exiting.')
            break
        time.sleep(INTERVAL)
