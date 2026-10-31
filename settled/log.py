import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  shop TEXT NOT NULL,
  step TEXT NOT NULL,
  said TEXT,
  heard TEXT,
  read_as TEXT,
  reason TEXT,
  rule TEXT,
  outcome TEXT,
  action TEXT
);
CREATE TRIGGER IF NOT EXISTS log_no_update BEFORE UPDATE ON log
BEGIN SELECT RAISE(ABORT, 'log rows are only added, never changed'); END;
CREATE TRIGGER IF NOT EXISTS log_no_delete BEFORE DELETE ON log
BEGIN SELECT RAISE(ABORT, 'log rows are only added, never deleted'); END;
"""

FIELDS = ("said", "heard", "read_as", "reason", "rule", "outcome", "action")


def path():
    env = os.environ.get("SETTLED_DB")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "settled.db"


def _connect():
    db = sqlite3.connect(path(), timeout=5)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def add(shop, step, **fields):
    unknown = set(fields) - set(FIELDS)
    if unknown:
        raise TypeError(f"unknown log fields: {', '.join(sorted(unknown))}")
    at = datetime.now().isoformat(timespec="seconds")
    cols = ["at", "shop", "step", *fields]
    with closing(_connect()) as db, db:
        cur = db.execute(
            f"INSERT INTO log ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [at, shop, step, *fields.values()],
        )
        return cur.lastrowid


def rows(shop=None, after=0):
    sql = "SELECT * FROM log WHERE id > ?"
    args = [after]
    if shop:
        sql += " AND shop = ?"
        args.append(shop)
    with closing(_connect()) as db:
        return [dict(r) for r in db.execute(sql + " ORDER BY id", args)]


def last_id():
    with closing(_connect()) as db:
        return db.execute("SELECT COALESCE(MAX(id), 0) FROM log").fetchone()[0]
