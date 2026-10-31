"""Run the simulated shopkeepers through the call flow and score the outcomes.

    python bench/run.py --reader typed
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CASES = Path(__file__).resolve().parent / "cases.json"


def typed_reader(case):
    labelled = {turn["text"]: turn for turn in case["turns"]}

    def read(text, said):
        from settled.models import Answer
        turn = labelled[text]
        return Answer(turn["kind"], text, reason=turn.get("reason"), plan=turn.get("plan"))

    return read


def make_reader(name, case):
    if name == "typed":
        return typed_reader(case)
    if name == "ai":
        from ai.reader import read
        return read
    raise SystemExit(f"no reader {name!r}")


def play(case, read):
    from settled import flow
    from settled.models import Answer

    lines = iter(turn["text"] for turn in case["turns"])
    heard = []

    def listener(shop, said):
        text = next(lines, None)
        answer = Answer("no answer") if text is None else read(text, said)
        heard.append(answer)
        return answer

    return flow.run(case["shop"], listener), heard


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

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.cases:
        wanted = args.cases.split(",")
        cases = [c for c in cases if c["id"] in wanted]
    if args.reader == "ai":
        from ai import reader as ai
        log_start = len(ai.COST_LOG.read_text(encoding="utf-8").splitlines()) if ai.COST_LOG.exists() else 0
    misread = []
    bad = honest = honest_charged = matched = 0

    print(f"{'case':<22}{'shop':<8}{'expected':<16}{'got':<16}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for n, case in enumerate(cases):
            if args.reader == "ai" and ai.spent() >= args.cap:
                print(f"stopped: ₹{ai.spent():.4f} spent, cap ₹{args.cap}")
                break
            os.environ["SETTLED_DB"] = str(Path(tmp) / f"{n}.db")
            decision, heard = play(case, make_reader(args.reader, case))
            got = label(decision)
            want = expected_label(case["expect"])
            ok = got == want
            matched += ok
            signed_plan = decision.outcome == "charged" and not any(a.plan for a in heard)
            if signed_plan and any(a.kind in ("na", "unsure") for a in heard):
                bad += 1
            if case.get("honest"):
                honest += 1
                honest_charged += got.startswith("charged")
            labelled = {t["text"]: t for t in case["turns"]}
            for a in heard:
                t = labelled.get(a.words)
                if t and (t["kind"] != a.kind or t.get("plan") != a.plan):
                    misread.append(f"{case['id']}: {a.words!r} labelled {t['kind']}{'/' + t['plan'] if t.get('plan') else ''}, read {a.kind}{'/' + a.plan if a.plan else ''}")
            print(f"{case['id']:<22}{case['shop']:<8}{want:<16}{got:<16}{'' if ok else 'MISMATCH'}")

    print()
    print(f"charged after na or unsure: {bad}")
    print(f"honest yeses charged: {honest_charged}/{honest}")
    print(f"cases matching expected outcome: {matched}/{len(cases)}")
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
