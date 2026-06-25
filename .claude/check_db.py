import sqlite3
c = sqlite3.connect('C:/Users/TK/.openclaw/state/openclaw.sqlite')
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    count = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"{t}: {count} rows")
c.close()
