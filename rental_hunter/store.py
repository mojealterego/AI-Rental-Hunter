import json, sqlite3, time
from pathlib import Path
from .models import SearchCriteria, Listing

DB_PATH=Path(__import__("os").getenv("DATABASE_PATH","data/rental_hunter.db"))

def _db():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB_PATH)
    c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS watches(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      criteria TEXT NOT NULL,
      interval_minutes INTEGER NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1,
      created_at REAL NOT NULL,
      last_run REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS listings(
      listing_id TEXT PRIMARY KEY,
      watch_id INTEGER,
      url TEXT NOT NULL,
      payload TEXT NOT NULL,
      first_seen REAL NOT NULL,
      last_seen REAL NOT NULL
    )""")
    c.commit()
    return c

def create_watch(criteria:SearchCriteria,interval_minutes:int)->int:
    c=_db()
    cur=c.execute("INSERT INTO watches(criteria,interval_minutes,created_at) VALUES(?,?,?)",(json.dumps(criteria.model_dump(),ensure_ascii=False),interval_minutes,time.time()))
    c.commit(); return int(cur.lastrowid)

def list_watches():
    c=_db()
    return [dict(r) for r in c.execute("SELECT * FROM watches WHERE enabled=1 ORDER BY id").fetchall()]

def get_new_listings(watch_id:int,items:list[Listing]):
    c=_db(); now=time.time(); fresh=[]
    for item in items:
        lid=__import__("hashlib").sha256(item.direct_url.encode()).hexdigest()[:16]
        old=c.execute("SELECT listing_id FROM listings WHERE listing_id=?",(lid,)).fetchone()
        payload=json.dumps(item.model_dump(),ensure_ascii=False)
        if old is None: fresh.append(item)
        c.execute("""INSERT INTO listings(listing_id,watch_id,url,payload,first_seen,last_seen)
                     VALUES(?,?,?,?,?,?)
                     ON CONFLICT(listing_id) DO UPDATE SET last_seen=excluded.last_seen,payload=excluded.payload""",
                  (lid,watch_id,item.direct_url,payload,now,now))
    c.execute("UPDATE watches SET last_run=? WHERE id=?",(now,watch_id)); c.commit()
    return fresh
