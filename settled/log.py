import json
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
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  shop TEXT NOT NULL,
  to_whom TEXT NOT NULL CHECK (to_whom IN ('shopkeeper', 'manager', 'support')),
  channel TEXT NOT NULL CHECK (channel IN ('SMS', 'WhatsApp', 'ticket')),
  text TEXT NOT NULL,
  link TEXT,
  choices TEXT,
  call INTEGER
);
CREATE TRIGGER IF NOT EXISTS messages_no_update BEFORE UPDATE ON messages
BEGIN SELECT RAISE(ABORT, 'messages are only added, never changed'); END;
CREATE TRIGGER IF NOT EXISTS messages_no_delete BEFORE DELETE ON messages
BEGIN SELECT RAISE(ABORT, 'messages are only added, never deleted'); END;
CREATE TABLE IF NOT EXISTS taps (
  message INTEGER PRIMARY KEY REFERENCES messages (id),
  at TEXT NOT NULL,
  choice TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS taps_no_update BEFORE UPDATE ON taps
BEGIN SELECT RAISE(ABORT, 'taps are only added, never changed'); END;
CREATE TRIGGER IF NOT EXISTS taps_no_delete BEFORE DELETE ON taps
BEGIN SELECT RAISE(ABORT, 'taps are only added, never deleted'); END;
"""

FIELDS = ("said", "heard", "read_as", "reason", "rule", "outcome", "action")

CLIP_TYPES = {"wav": "audio/wav", "webm": "audio/webm", "ogg": "audio/ogg", "mp3": "audio/mpeg", "m4a": "audio/mp4"}
CLIP_EXTS = {**{t: ext for ext, t in CLIP_TYPES.items()}, "audio/x-wav": "wav", "audio/wave": "wav"}


def path():
    env = os.environ.get("SETTLED_DB")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "settled.db"


def clips():
    return path().resolve().parent / "clips"


class Tapped(Exception):
    pass


class AlreadySettled(Exception):
    pass


# The actions that settle a shop's rent. Settled covers the first rent, so each shop
# gets at most one of these, and add_settle is the only way one is written.
SETTLES = ("charge rent (mock)", "cancel plan (mock)")


def _connect():
    db = sqlite3.connect(path(), timeout=5)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    have = {r[1] for r in db.execute("PRAGMA table_info(messages)")}
    for column, kind in (("link", "TEXT"), ("choices", "TEXT"), ("call", "INTEGER")):
        if column not in have:
            db.execute(f"ALTER TABLE messages ADD COLUMN {column} {kind}")
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


def add_settle(shop, step, **fields):
    """Add the row that settles the shop's rent, in the same transaction as the check
    that none is there yet. Raises AlreadySettled if one is."""
    if fields.get("action") not in SETTLES:
        raise ValueError(f"not a settling action: {fields.get('action')!r}")
    at = datetime.now().isoformat(timespec="seconds")
    cols = ["at", "shop", "step", *fields]
    db = _connect()
    try:
        db.isolation_level = None
        db.execute("BEGIN IMMEDIATE")
        if _settled(db, shop):
            raise AlreadySettled("this shop's rent is already settled")
        cur = db.execute(
            f"INSERT INTO log ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [at, shop, step, *fields.values()],
        )
        db.execute("COMMIT")
        return cur.lastrowid
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()


def _settled(db, shop):
    row = db.execute(
        f"SELECT * FROM log WHERE shop = ? AND action IN ({', '.join('?' * len(SETTLES))}) ORDER BY id LIMIT 1",
        [shop, *SETTLES],
    ).fetchone()
    return dict(row) if row else None


def settled(shop):
    """The row that settled this shop's rent (its charge or cancel), or None."""
    with closing(_connect()) as db:
        return _settled(db, shop)


def last_step(shop, step):
    with closing(_connect()) as db:
        row = db.execute("SELECT * FROM log WHERE shop = ? AND step = ? ORDER BY id DESC LIMIT 1", (shop, step)).fetchone()
        return dict(row) if row else None


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


def last_answer(shop, read_as=None):
    sql = "SELECT * FROM log WHERE shop = ? AND step = 'answered'"
    args = [shop]
    if read_as:
        sql += " AND read_as = ?"
        args.append(read_as)
    with closing(_connect()) as db:
        row = db.execute(sql + " ORDER BY id DESC LIMIT 1", args).fetchone()
        return dict(row) if row else None


def clip_name(row_id, at):
    """A clip's file stem: the row id and its time, so a reset log never picks up an old clip."""
    return f"{int(row_id)}-{''.join(c for c in at if c.isdigit())}"


def _row_at(row_id):
    with closing(_connect()) as db:
        row = db.execute("SELECT at FROM log WHERE id = ?", (int(row_id),)).fetchone()
        return row[0] if row else None


def save_clip(row_id, audio, ctype):
    ext = CLIP_EXTS.get(ctype.split(";")[0].strip().lower(), "audio")
    folder = clips()
    folder.mkdir(exist_ok=True)
    name = clip_name(row_id, _row_at(row_id))
    tmp = folder / f"{name}.{ext}.part"
    tmp.write_bytes(audio)
    os.replace(tmp, folder / f"{name}.{ext}")


def clip(row_id):
    """The saved clip for an answered row, as (path, content type), or None."""
    at = _row_at(row_id)
    if not at:
        return None
    for found in clips().glob(f"{clip_name(row_id, at)}.*"):
        ext = found.suffix[1:]
        if ext != "part":
            return found, CLIP_TYPES.get(ext, "application/octet-stream")
    return None


def message(shop, to_whom, channel, text, choices=None, call=None):
    """Add a message. {ticket} in text becomes this message's ticket id, SET-<4 digits>.
    With choices, the message gets a mock consent link, and {link} in text becomes it.
    call is the id of the "due" row of the call that sent it."""
    at = datetime.now().isoformat(timespec="seconds")
    db = _connect()
    try:
        db.isolation_level = None
        db.execute("BEGIN IMMEDIATE")
        msg_id = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM messages").fetchone()[0]
        link = consent_link(msg_id) if choices else None
        db.execute(
            "INSERT INTO messages (id, at, shop, to_whom, channel, text, link, choices, call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (msg_id, at, shop, to_whom, channel, text.replace("{ticket}", ticket_id(msg_id)).replace("{link}", link or ""),
             link, json.dumps(choices, ensure_ascii=False) if choices else None, call),
        )
        db.execute("COMMIT")
        return msg_id
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()


def ticket_id(msg_id):
    return f"SET-{msg_id:04d}"


def consent_link(msg_id):
    return f"https://paytm.example/settled/{ticket_id(msg_id).lower()}"


def get_message(msg_id):
    with closing(_connect()) as db:
        row = db.execute("SELECT * FROM messages WHERE id = ?", (int(msg_id),)).fetchone()
        return dict(row) if row else None


def last_choices(shop):
    """The latest message to this shop that carries choices, or None."""
    with closing(_connect()) as db:
        row = db.execute("SELECT * FROM messages WHERE shop = ? AND choices IS NOT NULL ORDER BY id DESC LIMIT 1",
                         (shop,)).fetchone()
        return dict(row) if row else None


def tap(msg_id, choice):
    """Record his tap on a message's choice. Each message takes one tap."""
    at = datetime.now().isoformat(timespec="seconds")
    try:
        with closing(_connect()) as db, db:
            db.execute("INSERT INTO taps (message, at, choice) VALUES (?, ?, ?)", (int(msg_id), at, choice))
    except sqlite3.IntegrityError:
        raise Tapped("he already chose on this message") from None


def taps():
    with closing(_connect()) as db:
        return {r["message"]: r["choice"] for r in db.execute("SELECT message, choice FROM taps")}
