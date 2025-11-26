#!/usr/bin/env python3
import sqlite3
con=sqlite3.connect('/opt/airflow/airflow.db')
cur=con.cursor()
rows=cur.execute("PRAGMA table_info(dag_run)").fetchall()
print('dag_run schema:')
for r in rows:
    print(r)
