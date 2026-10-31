"""Stand in for the AI: type the shopkeeper's answers.

    python try.py <shop> [answers...]
    python try.py reset

Answers: haan, na, unsure, question, silent, for the plan question and the
read-back. A quoted text right after na or unsure is his reason. He allows the
recording, says he is the owner and reads the right code first.
"""
import shutil
import sys

from settled import flow, log, records
from settled.models import Answer, CallState
from voice import script

HEARD = {
    "haan": ["Haan, liya tha.", "Haan, pakka."],
    "na": ["Na bhaiya, usne ₹1 bola tha."],
    "unsure": ["Haan, par ₹1 bola tha."],
    "question": ["Yeh plan kya hai?"],
}
TOKENS = {"haan", "na", "unsure", "question", "silent"}


def parse(args):
    answers = []
    seen = {}
    i = 0
    while i < len(args):
        token = args[i]
        i += 1
        if token not in TOKENS:
            sys.exit(f"unknown answer {token!r}, use haan, na, unsure, question or silent")
        if token == "silent":
            answers.append(Answer("no answer"))
            continue
        lines = HEARD[token]
        words = lines[min(seen.get(token, 0), len(lines) - 1)]
        seen[token] = seen.get(token, 0) + 1
        reason = None
        if token in ("na", "unsure") and i < len(args) and args[i] not in TOKENS:
            reason = args[i]
            i += 1
        answers.append(Answer(token, words, reason=reason))
    return answers


def show(row):
    parts = [f"{row['shop']:<7}", f"{row['step']:<16}"]
    if row["said"]:
        parts.append(f"said: {row['said']}")
    if row["read_as"]:
        heard = row["heard"] or "(silence)"
        parts.append(f"heard: {heard} -> {row['read_as']}")
    if row["reason"]:
        parts.append(f"reason: {row['reason']}")
    for key in ("action", "rule", "outcome"):
        if row[key]:
            parts.append(f"{key}: {row[key]}")
    print("  ".join(parts))


def main(args):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not args:
        sys.exit(__doc__)
    if args[0] == "reset":
        log.path().unlink(missing_ok=True)
        print(f"deleted {log.path()}")
        if log.clips().is_dir():
            shutil.rmtree(log.clips())
            print(f"deleted {log.clips()}")
        return

    shop_id, answers = args[0], parse(args[1:])
    if shop_id not in records.shop_ids():
        sys.exit(f"no shop {shop_id!r}, known shops: {', '.join(records.shop_ids())}")

    state = CallState()
    queue = iter([Answer("haan", "Haan, theek hai."), Answer("haan", "Haan ji, main hi bol raha hoon."), None, *answers])

    def listener(shop, said, wait=True):
        if not wait:
            return None
        answer = next(queue, Answer("no answer"))
        return Answer("unsure", state.code) if said in script.CODE_LINES else answer

    start = log.last_id()
    decision = flow.run(shop_id, listener, state)
    for row in log.rows(after=start):
        show(row)

    outcome = decision.outcome.capitalize()
    if decision.outcome == "charged":
        outcome += f" at ₹{decision.plan.price} ({decision.plan.name})"
    print(f"\nOutcome: {outcome}.")


if __name__ == "__main__":
    main(sys.argv[1:])
