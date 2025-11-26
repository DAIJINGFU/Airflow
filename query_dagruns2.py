#!/usr/bin/env python3
import sqlite3
con=sqlite3.connect('/opt/airflow/airflow.db')
cur=con.cursor()
rows=cur.execute("SELECT run_id, state, logical_date FROM dag_run WHERE dag_id='starquant_factor_pipeline' ORDER BY logical_date DESC LIMIT 10").fetchall()
print('found', len(rows))
for r in rows:
    print(r)
