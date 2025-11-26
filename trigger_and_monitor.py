#!/usr/bin/env python3
import subprocess, sqlite3, time, os, glob, json

AIRFLOW_DB = '/opt/airflow/airflow.db'
REGISTRY_DB = '/opt/airflow/metadata/factor_platform.db'
SUMMARY_DIR = '/opt/airflow/.airflow_factor_pipeline'
DAG_ID = 'starquant_factor_pipeline'


def trigger_dag():
    print('Triggering DAG...')
    p = subprocess.run(['airflow', 'dags', 'trigger', DAG_ID], capture_output=True, text=True)
    print('airflow trigger stdout:')
    print(p.stdout)
    if p.returncode != 0:
        print('airflow trigger stderr:')
        print(p.stderr)
    return


def poll_dag_run(timeout=60*30, interval=10):
    """Poll airflow.airflow.db dag_run for this DAG. Returns (run_id, state) or (None,None) on timeout."""
    start = time.time()
    con = sqlite3.connect(AIRFLOW_DB)
    cur = con.cursor()
    while True:
        row = cur.execute("SELECT run_id, state, logical_date FROM dag_run WHERE dag_id=? ORDER BY logical_date DESC LIMIT 1", (DAG_ID,)).fetchone()
        if row:
            run_id, state, exec_date = row
            print(f'Latest dag_run: run_id={run_id}, state={state}, logical_date={exec_date}')
            if state and state.upper() in ('SUCCESS','FAILED'):
                return run_id, state.upper()
        else:
            print('No dag_run found yet.')
        if time.time() - start > timeout:
            print('Timeout waiting for dag_run')
            return None, None
        time.sleep(interval)


def collect_summary():
    print('\nLooking for summary CSVs in', SUMMARY_DIR)
    if not os.path.isdir(SUMMARY_DIR):
        print('Summary dir does not exist')
        return []
    files = sorted(glob.glob(os.path.join(SUMMARY_DIR, 'qlib_factor_summary_*.csv')))
    for f in files:
        print('  ', f)
    return files


def query_registry():
    print('\nQuerying registry for jobs...')
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
    trigger_dag()
    run_id, state = poll_dag_run()
    print('\nDAG finished:', run_id, state)
    files = collect_summary()
    query_registry()
    if files:
        print('\nNewest summary file:', files[-1])
    else:
        print('\nNo summary files found yet.')
