"""Run the simulated shopkeepers through the call flow and score the outcomes.

    python bench/run.py --reader typed

Each case lists his replies in order, from the recording ask on. The code line
gets the bench's fixed app code, 3456. A case with "tap" then taps that choice in
his WhatsApp through POST /api/consent, on a board started in this process.
"""
import argparse
import json
import os
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CASES = Path(__file__).resolve().parent / "cases.json"
APP_CODE = "3456"


def typed_reader(case):
    labelled = {turn["text"]: turn for turn in case["turns"] if "kind" in turn}

    def read(text, said):
        from settled.models import Answer
        turn = labelled[text]
        return Answer(turn["kind"], text, reason=turn.get("reason"), speaker=turn.get("speaker", "shopkeeper"))

    return read


def make_reader(name, case):
    if name == "typed":
        return typed_reader(case)
    if name == "ai":
        from ai.reader import read
        return read
    raise SystemExit(f"no reader {name!r}")


def play(case, read):
    """The call as calls.py runs it: blanks are no answer, and the code line never reaches the reader."""
    from settled import flow
    from settled.models import Answer, CallState
    from voice import script

    state = CallState(code=APP_CODE)
    turns = iter(case["turns"])
    heard = []

    def listener(shop, said, wait=True):
        if not wait:
            return None
        turn = next(turns, None)
        text = "" if turn is None else turn["text"]
        if not text.strip():
            answer = Answer("no answer", "")
        elif said == script.CODE:
            answer = Answer("unsure", text)
        else:
            answer = read(text, script.english(said, shop))
        heard.append((said, answer))
        return answer

    decision = flow.run(case["shop"], listener, state)
    return decision, heard, state, list(turns)


def tap(board, shop):
    """His tap on the choices in his WhatsApp, through the board's endpoint. Also checks a second tap is refused."""
    from settled import log
    with sqlite3.connect(log.path()) as db:
        found = db.execute("SELECT id FROM messages WHERE shop = ? AND choices IS NOT NULL ORDER BY id DESC", (shop,)).fetchone()
    if not found:
        return None, "no choices sent"

    def post(choice):
        req = urllib.request.Request(f"{board}/api/consent/{found[0]}/{choice}", data=b"", method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    return post, found[0]


def start_board():
    import server
    board = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=board.serve_forever, daemon=True).start()
    return board, f"http://127.0.0.1:{board.server_address[1]}"


def label(decision):
    if decision.outcome == "charged":
        return f"charged:{decision.plan.id}"
    return decision.outcome


def expected_label(expect):
    return "charged:plan-a" if expect == "charged" else expect


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", default="typed")
    parser.add_argument("--cases", help="comma-separated case ids, default all")
    parser.add_argument("--cap", type=float, default=1.0, help="stop the ai reader at this many rupees spent")
    args = parser.parse_args(argv)

    from settled import log, paytm_mock
    from voice import script

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.cases:
        wanted = args.cases.split(",")
        cases = [c for c in cases if c["id"] in wanted]
    if args.reader == "ai":
        from ai import reader as ai
        log_start = len(ai.COST_LOG.read_text(encoding="utf-8").splitlines()) if ai.COST_LOG.exists() else 0
    misread, problems = [], []
    bad = unverified = negative = honest = honest_charged = matched = taps = 0

    board, url = start_board()
    print(f"{'case':<26}{'shop':<8}{'expected':<16}{'got':<16}{'identity':<24}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for n, case in enumerate(cases):
            if args.reader == "ai" and ai.spent() >= args.cap:
                print(f"stopped: ₹{ai.spent():.4f} spent, cap ₹{args.cap}")
                break
            os.environ["SETTLED_DB"] = str(Path(tmp) / f"{n}.db")
            decision, heard, state, unread = play(case, make_reader(args.reader, case))
            rows = log.rows(case["shop"])
            identity = next((r["rule"] for r in reversed(rows) if r["step"] == "identity"), None)
            got = label(decision)
            wrong = []

            if decision.outcome == "charged":
                asked = [a for said, a in heard if said in (script.ASK, script.READ_BACK)]
                bad += any(a.kind in ("na", "unsure") for a in asked)
                unverified += identity != "verified"
            negative += sum(1 for r in rows if r["action"] and r["action"].removesuffix(" (mock)") in paytm_mock.NEGATIVE)

            if case.get("tap"):
                post, msg = tap(url, case["shop"])
                if post is None:
                    wrong.append(msg)
                else:
                    status, reply = post(case["tap"])
                    again, _ = post(case["tap"])
                    taps += 1
                    if status != 200:
                        wrong.append(f"tap answered {status}")
                    else:
                        got = reply["outcome"] if reply["outcome"] != "charged" else f"charged:{reply['plan']}"
                    if again != 409:
                        wrong.append(f"second tap answered {again}")
                    after = log.rows(case["shop"])[len(rows):]
                    pickups = sum(1 for r in after if r["action"] == "book pickup (mock)")
                    if pickups != (case["tap"] == "cancel"):
                        wrong.append(f"{pickups} pickups after a {case['tap']} tap")

            want = expected_label(case["expect"])
            if got != want:
                wrong.append("outcome")
            if "identity" in case and identity != case["identity"]:
                wrong.append(f"identity {identity}")
            if "recording" in case and state.recording != case["recording"]:
                wrong.append(f"recording {state.recording}")
            if unread:
                wrong.append(f"{len(unread)} turns never read")
            matched += not wrong
            if case.get("honest"):
                honest += 1
                honest_charged += got.startswith("charged")
            if wrong:
                problems.append(f"{case['id']}: {', '.join(wrong)}")

            labelled = {t["text"]: t for t in case["turns"] if "kind" in t}
            for said, a in heard:
                t = labelled.get(a.words)
                if t and said != script.CODE and (t["kind"] != a.kind or t.get("speaker", "shopkeeper") != a.speaker):
                    misread.append(f"{case['id']}: {a.words!r} labelled {t['kind']}/{t.get('speaker', 'shopkeeper')}, read {a.kind}/{a.speaker}")
            print(f"{case['id']:<26}{case['shop']:<8}{want:<16}{got:<16}{identity or '-':<24}{'' if not wrong else 'MISMATCH'}")
    board.shutdown()

    print()
    print(f"charged after na or unsure: {bad}")
    print(f"charged without verified identity: {unverified}")
    print(f"negative actions from the AI: {negative}")
    print(f"honest yeses charged: {honest_charged}/{honest}")
    print(f"consent taps through the endpoint: {taps}")
    print(f"cases matching expected outcome: {matched}/{len(cases)}")
    for line in problems:
        print(f"  {line}")
    print(f"lines read differently from their label: {len(misread)}")
    for line in misread:
        print(f"  {line}")
    if args.reader == "ai":
        entries = [json.loads(l) for l in ai.COST_LOG.read_text(encoding="utf-8").splitlines()[log_start:] if l]
        calls = [e for e in entries if "seconds" in e]
        errors = [e for e in entries if "error" in e]
        avg = sum(e["seconds"] for e in calls) / len(calls) if calls else 0
        print(f"ai calls: {len(calls)}, errors: {len(errors)}, average {avg:.2f}s per reply")
        print(f"cost this run: ₹{sum(e['rupees'] for e in entries):.4f} (incl. GST), all runs: ₹{ai.spent():.4f}")


if __name__ == "__main__":
    main(sys.argv[1:])
