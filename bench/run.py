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

    def read(text):
        from settled.models import Answer
        turn = labelled[text]
        return Answer(turn["kind"], text, reason=turn.get("reason"), plan=turn.get("plan"))

    return read


def make_reader(name, case):
    if name == "typed":
        return typed_reader(case)
    raise SystemExit(f"no reader {name!r}")


def play(case, read):
    from settled import flow
    from settled.models import Answer

    lines = iter(turn["text"] for turn in case["turns"])
    heard = []

    def listener(shop, said):
        text = next(lines, None)
        answer = Answer("no answer") if text is None else read(text)
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
    args = parser.parse_args(argv)

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    bad = honest = honest_charged = matched = 0

    print(f"{'case':<22}{'shop':<8}{'expected':<16}{'got':<16}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for n, case in enumerate(cases):
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
            print(f"{case['id']:<22}{case['shop']:<8}{want:<16}{got:<16}{'' if ok else 'MISMATCH'}")

    print()
    print(f"charged after na or unsure: {bad}")
    print(f"honest yeses charged: {honest_charged}/{honest}")
    print(f"cases matching expected outcome: {matched}/{len(cases)}")


if __name__ == "__main__":
    main(sys.argv[1:])
