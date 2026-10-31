import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "board" / "index.html"
DB = Path(os.environ.get("SETTLED_DB") or ROOT / "settled.db").resolve()
PORT = int(os.environ.get("BOARD_PORT") or 8080)

COLUMNS = ("id", "at", "shop", "step", "said", "heard", "read_as", "reason", "rule", "outcome", "action")


def rows_after(after):
    if not DB.exists():
        return []
    try:
        con = sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True, timeout=2)
    except sqlite3.Error:
        return []
    try:
        cur = con.execute(
            f"SELECT {', '.join(COLUMNS)} FROM log WHERE id > ? ORDER BY id LIMIT 500",
            (after,),
        )
        return [dict(zip(COLUMNS, r)) for r in cur]
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self.send(200, "text/html; charset=utf-8", PAGE.read_bytes())
        elif url.path == "/api/log":
            try:
                after = int(parse_qs(url.query).get("after", ["0"])[0])
            except ValueError:
                after = 0
            body = json.dumps(rows_after(after), ensure_ascii=False).encode("utf-8")
            self.send(200, "application/json; charset=utf-8", body)
        else:
            self.send(404, "text/plain; charset=utf-8", b"not found")

    def send(self, status, ctype, body):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"board on http://127.0.0.1:{PORT}  reading {DB}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
