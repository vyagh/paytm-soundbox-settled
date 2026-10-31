import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from settled import records
from voice import calls, script

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "board" / "index.html"
FONTS = ROOT / "board" / "fonts"
DB = Path(os.environ.get("SETTLED_DB") or ROOT / "settled.db").resolve()
PORT = int(os.environ.get("BOARD_PORT") or 8080)
MAX_REPLY = 5_000_000

LANGUAGES = [{"code": code, "name": l["name"], "own": l["own"]} for code, l in script.LANGUAGES.items()]

COLUMNS = ("id", "at", "shop", "step", "said", "heard", "read_as", "reason", "rule", "outcome", "action")


def shops():
    out = []
    for shop_id in records.shop_ids():
        shop = records.load(shop_id)
        call = calls.get(shop_id)
        code = call.language if call else shop.language
        language = script.LANGUAGES[code]
        out.append({
            "id": shop_id,
            "name": shop.name,
            "owner": shop.owner,
            "language": {"code": code, "name": language["name"], "own": language["own"]},
            "default": shop.language,
            "languages": LANGUAGES,
            "lines": {said: language[said] for said in (script.ASK, script.READ_BACK, script.NA_FOLLOW_UP)},
            "call": call.state() if call else None,
        })
    return out


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
        elif url.path.startswith("/fonts/") and (font := FONTS / url.path.removeprefix("/fonts/")).parent == FONTS \
                and font.suffix == ".woff2" and font.is_file():
            self.send(200, "font/woff2", font.read_bytes())
        elif url.path == "/api/log":
            try:
                after = int(parse_qs(url.query).get("after", ["0"])[0])
            except ValueError:
                after = 0
            self.json(200, rows_after(after))
        elif url.path == "/api/shops":
            self.json(200, shops())
        elif len(parts := url.path.split("/")) == 6 and parts[1:3] == ["api", "call"] and parts[4] == "audio":
            call = calls.get(parts[3])
            if call and call.audio and str(call.seq) == parts[5]:
                self.send(200, "audio/wav", call.audio)
            else:
                self.send(404, "text/plain; charset=utf-8", b"no audio")
        else:
            self.send(404, "text/plain; charset=utf-8", b"not found")

    def do_POST(self):
        url = urlparse(self.path)
        parts = url.path.split("/")
        if len(parts) != 5 or parts[1:3] != ["api", "call"] or parts[3] not in records.shop_ids():
            return self.send(404, "text/plain; charset=utf-8", b"not found")
        shop_id, what = parts[3], parts[4]
        try:
            if what == "start":
                length = int(self.headers.get("Content-Length") or 0)
                if length > MAX_REPLY:
                    return self.json(413, {"error": "too long"})
                calls.start(shop_id, json.loads(self.rfile.read(length) or b"{}").get("language"))
                return self.json(200, {"started": shop_id})
            if what == "reply":
                return self.reply(shop_id, url)
        except calls.Busy as e:
            return self.json(409, {"error": str(e)})
        except ValueError as e:
            return self.json(422, {"error": str(e)})
        except Exception as e:
            return self.json(502, {"error": f"{type(e).__name__}: {e}"})
        self.send(404, "text/plain; charset=utf-8", b"not found")

    def reply(self, shop_id, url):
        call = calls.get(shop_id)
        if call is None:
            raise calls.Busy("no call on")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_REPLY:
            return self.json(413, {"error": "reply too long"})
        body = self.rfile.read(length)
        seq = int(parse_qs(url.query).get("seq", ["0"])[0])
        ctype = self.headers.get("Content-Type") or ""
        if ctype.startswith("audio/"):
            seconds = float(self.headers.get("X-Seconds") or 0)
            got = call.reply(seq, audio=body, ctype=ctype, seconds=seconds)
        else:
            got = call.reply(seq, text=json.loads(body or b"{}").get("text", ""))
        self.json(200, got)

    def json(self, status, data):
        self.send(status, "application/json; charset=utf-8", json.dumps(data, ensure_ascii=False).encode("utf-8"))

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
