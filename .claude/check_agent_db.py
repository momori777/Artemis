import sqlite3, json

# Check agent main DB for conversation storage
db = 'C:/Users/TK/.openclaw/agents/main/agent/openclaw-agent.sqlite'
c = sqlite3.connect(db)
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    count = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"{t}: {count} rows")
    if count > 0 and count < 10:
        rows = c.execute(f"SELECT * FROM [{t}] LIMIT 3").fetchall()
        for r in rows:
            print(f"  {r[:2]}...")
c.close()
