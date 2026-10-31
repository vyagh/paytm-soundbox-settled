"""Drive one call on a running board the way the page does, no mic needed.

    python bench/voice_run.py <shop> <reply>...

Each reply answers the next line Settled says: a .wav path is sent as his voice,
text:<words> is typed ({code} in it becomes the code in his mock Paytm app), wait
sends nothing and lets the call time out. A last tap:<choice> taps that choice in
his WhatsApp once the call is over.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

BOARD = f"http://127.0.0.1:{os.environ.get('BOARD_PORT') or 8080}"


def call(path, body=None, ctype=None, headers=None):
    req = urllib.request.Request(BOARD + path, data=body, headers={**({"Content-Type": ctype} if ctype else {}), **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if resp.headers.get_content_type() == "application/json" else data
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def shop_state(shop):
    return next(s for s in call("/api/shops")[1] if s["id"] == shop)


def next_prompt(shop, after):
    while True:
        state = shop_state(shop)["call"]
        if state["waiting"] and state["seq"] > after:
            return state
        if not state["active"]:
            return None
        time.sleep(0.3)


def rows_after(after, what="log"):
    """Every row after an id. /api/log and /api/messages give 500 rows a page."""
    rows = []
    while page := call(f"/api/{what}?after={after}")[1]:
        rows += page
        after = page[-1]["id"]
    return rows


def main(shop, replies):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tap = replies.pop()[4:] if replies and replies[-1].startswith("tap:") else None
    start = max([r["id"] for r in rows_after(0)] or [0])
    print("start", call(f"/api/call/{shop}/start", b"")[0])
    seq = 0
    for reply in replies:
        prompt = next_prompt(shop, seq)
        if prompt is None:
            break
        seq = prompt["seq"]
        status, audio = call(f"/api/call/{shop}/audio/{seq}")
        print(f"line {seq} [{prompt['step']}]: {prompt['said']}  "
              f"(voice {status}, {len(audio) if status == 200 else 0} bytes)")
        if reply == "wait":
            print("  waiting it out")
            continue
        if reply.startswith("text:"):
            text = reply[5:].replace("{code}", prompt["app_code"] or "")
            got = call(f"/api/call/{shop}/reply?seq={seq}", json.dumps({"text": text}).encode("utf-8"), "application/json")
        else:
            clip = Path(reply).read_bytes()
            with wave.open(reply) as w:
                seconds = w.getnframes() / w.getframerate()
            got = call(f"/api/call/{shop}/reply?seq={seq}", clip, "audio/wav", {"X-Seconds": str(seconds)})
        print("  reply", *got)

    while shop_state(shop)["call"]["active"]:
        time.sleep(0.3)
    if tap:
        asked = [m for m in rows_after(0, "messages") if m["shop"] == shop and m["choices"]]
        status, got = call(f"/api/consent/{asked[-1]['id']}/{tap}", b"") if asked else (None, "no choices sent")
        print("tap", tap, status, got)
    for row in rows_after(start):
        if row["shop"] == shop:
            print(" ", " | ".join(str(row[k]) for k in ("step", "heard", "read_as", "reason", "rule", "outcome", "action") if row[k]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
