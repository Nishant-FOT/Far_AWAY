import sqlite3, json, sys
p='/app/backend/replay_store.db'
try:
    conn=sqlite3.connect(p)
    cur=conn.cursor()
    cur.execute('SELECT incident_id FROM replays')
    rows=cur.fetchall()
    print('rows:', rows)
    for r in rows:
        cur.execute('SELECT stages FROM replays WHERE incident_id=?',(r[0],))
        data=cur.fetchone()[0]
        print(r[0], len(json.loads(data)))
    conn.close()
except Exception as e:
    print('ERR', e)
    sys.exit(1)
