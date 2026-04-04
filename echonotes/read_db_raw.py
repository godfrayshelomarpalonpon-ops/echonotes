import sqlite3
conn = sqlite3.connect('db.sqlite3', timeout=1)
try:
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM auth_user WHERE username IN ('Godfray', 'tester')")
    print(cur.fetchall())
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
