"""Drive one call on a running board the way the page does, no mic needed.

    python bench/voice_run.py <shop> <reply>...

Each reply answers the next line Settled says: a .wav path is sent as his voice,
text:<words> is typed, wait sends nothing and lets the call time out.
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


def main(shop, replies):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    start = max([r["id"] for r in call("/api/log")[1]] or [0])
    print("start", call(f"/api/call/{shop}/start", b"")[0])
    seq = 0
    for reply in replies:
        prompt = next_prompt(shop, seq)
        if prompt is None:
            break
        seq = prompt["seq"]
        status, audio = call(f"/api/call/{shop}/audio/{seq}")
        print(f"line {seq}: {prompt['said']}  (voice {status}, {len(audio) if status == 200 else 0} bytes)")
        if reply == "wait":
            print("  waiting it out")
            continue
        if reply.startswith("text:"):
            got = call(f"/api/call/{shop}/reply?seq={seq}", json.dumps({"text": reply[5:]}).encode("utf-8"), "application/json")
        else:
            clip = Path(reply).read_bytes()
            with wave.open(reply) as w:
                seconds = w.getnframes() / w.getframerate()
            got = call(f"/api/call/{shop}/reply?seq={seq}", clip, "audio/wav", {"X-Seconds": str(seconds)})
        print("  reply", *got)

    while shop_state(shop)["call"]["active"]:
        time.sleep(0.3)
    for row in call(f"/api/log?after={start}")[1]:
        if row["shop"] == shop:
            print(" ", " | ".join(str(row[k]) for k in ("step", "heard", "read_as", "reason", "rule", "outcome", "action") if row[k]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
