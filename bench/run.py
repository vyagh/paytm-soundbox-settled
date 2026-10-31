"""Run the simulated shopkeepers through the call flow and score the outcomes.

    python bench/run.py --reader typed

Each case lists his replies in order, from the name question on. His reply to the
year question is checked against his year of birth on record. A case with "tap" then taps that choice in
his WhatsApp through POST /api/consent, on a board started in this process. A case
with "again" calls the shop a second time in the same log, with its own turns and
expect ("refused" when Settled won't call), and "old_tap" then taps the first
call's WhatsApp, which should answer 409 unless it gives another "status".
A turn at the year question may carry the "intent" the AI would read in it.
"year_asks" checks how many times the year was asked, "year_wrong" how many of those
said the year didn't match, and "unread" how many of his
turns the call never got to. A turn {"hangup": true} is him hanging up there, and
"ends" names the script line said just before the goodbye, "answered" the answer
lines that should be said, and "manager" whether his manager got a WhatsApp.
"retry" says a retry call should be booked, as after a cut line or silence, and
"call_me" whether an SMS with a Call me now button went out. "callback" on "again"
makes the second call one he started. "new_round" starts a demo round through
POST /api/round/new between the first call and the rest.
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


def typed_reader(case):
    labelled = {turn["text"]: turn for turn in case["turns"] if "kind" in turn}

    def read(text, said):
        from settled.models import Answer
        turn = labelled[text]
        return Answer(turn["kind"], text, reason=turn.get("reason"), speaker=turn.get("speaker", "shopkeeper"),
                      topic=turn.get("topic"), promise=turn.get("promise"), upset=turn.get("upset", False))

    return read


def make_reader(name, case):
    if name == "typed":
        return typed_reader(case)
    if name == "ai":
        from ai.reader import read
        return read
    raise SystemExit(f"no reader {name!r}")


def play(case, read):
    """The call as calls.py runs it: blanks are no answer, and the year question never reaches the reader."""
    from settled import flow, log
    from settled.models import Answer, CallState
    from voice import script

    state = CallState()
    turns = iter(case["turns"])
    heard, told = [], []

    def listener(shop, said, wait=True):
        if not wait:
            told.append(said)
            return None
        turn = next(turns, None)
        if turn is not None and turn.get("hangup"):
            raise flow.HungUp()
        text = "" if turn is None else turn["text"]
        if not text.strip():
            answer = Answer("no answer", "")
        elif said in script.YEAR_LINES:
            answer = Answer("unsure", text, intent=turn.get("intent"))
        else:
            answer = read(text, script.english(said, shop))
        heard.append((said, answer))
        return answer

    try:
        decision = flow.run(case["shop"], listener, state, callback=case.get("callback", False))
    except log.AlreadySettled:
        decision = None
    return decision, heard, state, list(turns), told


def tap(board, shop):
    """His tap on the choices in his latest WhatsApp, through the board's endpoint. Also checks a second tap is refused."""
    from settled import log
    with sqlite3.connect(log.path()) as db:
        found = db.execute("SELECT id FROM messages WHERE shop = ? AND channel = 'WhatsApp' AND choices IS NOT NULL ORDER BY id DESC", (shop,)).fetchone()
    if not found:
        return None, "no choices sent"
    return poster(board, found[0]), found[0]


def post_json(url):
    req = urllib.request.Request(url, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def doubled(rows, shop):
    """True when a round has more than one charge or cancel for the shop."""
    from settled import log
    settles = [0]
    for r in rows:
        if r["shop"] == log.ROUNDS and r["step"] == "round":
            settles.append(0)
        elif r["shop"] == shop and r["action"] in log.SETTLES:
            settles[-1] += 1
    return max(settles) > 1


def poster(board, msg):
    return lambda choice: post_json(f"{board}/api/consent/{msg}/{choice}")


def start_board():
    import server
    board = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=board.serve_forever, daemon=True).start()
    return board, f"http://127.0.0.1:{board.server_address[1]}"


def score(decision, heard, rows):
    """(identity rule, charged after na or unsure, charged unverified, negative actions) for one call's rows."""
    from settled import paytm_mock
    from voice import script
    identity = next((r["rule"] for r in reversed(rows) if r["step"] == "identity"), None)
    bad = unverified = 0
    if decision is not None and decision.outcome == "charged":
        # a na or doubt about the plan that was charged; one about Plan A before a Plan B charge is not
        lines = {script.ASK, script.ASK_AGAIN, script.READ_BACK} if decision.plan.id == "plan-a" else \
            {script.OFFER_B, script.OFFER_AGAIN, script.PROMISE_ONE, script.PROMISE_FREE, script.PROMISE_LOWER, script.READ_BACK_B}
        asked = [a for said, a in heard if said in lines]
        bad = any(a.kind in ("na", "unsure") for a in asked)
        unverified = not (identity or "").startswith("verified")
    negative = sum(1 for r in rows if r["action"] and r["action"].removesuffix(" (mock)") in paytm_mock.NEGATIVE)
    return identity, bad, unverified, negative


def label(decision):
    if decision is None:
        return "refused"
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
    bad = unverified = negative = honest = honest_charged = matched = taps = double = 0

    board, url = start_board()
    print(f"{'case':<26}{'shop':<8}{'expected':<16}{'got':<16}{'identity':<24}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for n, case in enumerate(cases):
            if args.reader == "ai" and ai.spent() >= args.cap:
                print(f"stopped: ₹{ai.spent():.4f} spent, cap ₹{args.cap}")
                break
            os.environ["SETTLED_DB"] = str(Path(tmp) / f"{n}.db")
            decision, heard, state, unread, spoken = play(case, make_reader(args.reader, case))
            rows = log.rows(case["shop"])
            identity, b, u, neg = score(decision, heard, rows)
            bad, unverified, negative = bad + b, unverified + u, negative + neg
            got = label(decision)
            wrong = []

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

            first = log.last_choices(case["shop"])
            if case.get("new_round"):
                status, reply = post_json(f"{url}/api/round/new")
                if status != 200 or reply.get("round") != 2:
                    wrong.append(f"new round answered {status} {reply}")
            if case.get("again"):
                later = case["again"]
                before = len(log.rows(case["shop"]))
                decision2, heard2, _, unread2, _ = play({**case, "turns": later["turns"], "callback": later.get("callback", False)},
                                                     make_reader(args.reader, later))
                _, b, u, neg = score(decision2, heard2, log.rows(case["shop"])[before:])
                bad, unverified, negative = bad + b, unverified + u, negative + neg
                heard += heard2
                if label(decision2) != expected_label(later["expect"]):
                    wrong.append(f"second call {label(decision2)}")
                if unread2 and decision2 is not None:
                    wrong.append(f"{len(unread2)} turns never read on the second call")
            if case.get("old_tap"):
                old = case["old_tap"] if isinstance(case["old_tap"], dict) else {"choice": case["old_tap"], "status": 409}
                if not first:
                    wrong.append("no first-call choices to tap")
                else:
                    status, reply = poster(url, first["id"])(old["choice"])
                    taps += 1
                    if status != old["status"] or (status == 409 and not reply.get("expired")):
                        wrong.append(f"old tap answered {status}")
            double += doubled(log.rows(), case["shop"])

            want = expected_label(case["expect"])
            if got != want:
                wrong.append("outcome")
            if "identity" in case and identity != case["identity"]:
                wrong.append(f"identity {identity}")
            if len(unread) != case.get("unread", 0):
                wrong.append(f"{len(unread)} turns never read")
            with sqlite3.connect(log.path()) as db:
                sms = db.execute("SELECT id FROM messages WHERE shop = ? AND channel = 'SMS' AND choices LIKE '%call_me%'",
                                 (case["shop"],)).fetchall()
            if bool(sms) != case.get("call_me", bool(sms)):
                wrong.append("call me SMS sent" if sms else "no call me SMS")
            if case.get("again", {}).get("callback") and not any(
                    r["step"] == "calling" and (r["rule"] or "").startswith("callback") for r in log.rows(case["shop"])):
                wrong.append("callback not logged")
            retried = any(r["action"] == "book retry call (mock)" for r in log.rows(case["shop"]))
            if retried != case.get("retry", False):
                wrong.append("retry call booked" if retried else "no retry call booked")
            asked = sum(1 for said, _ in heard if said in script.YEAR_LINES)
            if "year_asks" in case and asked != case["year_asks"]:
                wrong.append(f"year asked {asked} times")
            told = sum(1 for said, _ in heard if said == script.YEAR_WRONG)
            if "year_wrong" in case and told != case["year_wrong"]:
                wrong.append(f"year didn't match said {told} times")
            if "ends" in case:
                ending = spoken[-2] if len(spoken) > 1 else None
                if ending != getattr(script, case["ends"]):
                    wrong.append(f"ended on {next((k for k in dir(script) if getattr(script, k) == ending), ending)}")
            for line in case.get("answered", []):
                if getattr(script, line) not in spoken:
                    wrong.append(f"{line} not said")
            with sqlite3.connect(log.path()) as db:
                manager = bool(db.execute("SELECT id FROM messages WHERE shop = ? AND to_whom = 'manager'", (case["shop"],)).fetchall())
            if manager != case.get("manager", manager):
                wrong.append("manager told" if manager else "manager not told")
            matched += not wrong
            if case.get("honest"):
                honest += 1
                honest_charged += got.startswith("charged")
            if wrong:
                problems.append(f"{case['id']}: {', '.join(wrong)}")

            labelled = {t["text"]: t for t in case["turns"] + case.get("again", {}).get("turns", []) if "kind" in t}
            for said, a in heard:
                t = labelled.get(a.words)
                if t and said not in script.YEAR_LINES and (t["kind"] != a.kind or t.get("speaker", "shopkeeper") != a.speaker):
                    misread.append(f"{case['id']}: {a.words!r} labelled {t['kind']}/{t.get('speaker', 'shopkeeper')}, read {a.kind}/{a.speaker}")
            print(f"{case['id']:<26}{case['shop']:<8}{want:<16}{got:<16}{identity or '-':<24}{'' if not wrong else 'MISMATCH'}")
    board.shutdown()

    print()
    print(f"charged after na or unsure: {bad}")
    print(f"charged without verified identity: {unverified}")
    print(f"negative actions from the AI: {negative}")
    print(f"double charges (more than one charge or cancel per shop in a round): {double}")
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
