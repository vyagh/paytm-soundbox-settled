"""One AI call per reply: what he meant, and what Settled could say back.

Code checks both before anything is said or done: flow.py keeps the steps and
rules.py the money. The year of birth, his payments and his number never reach
the model.
"""
import json
from pathlib import Path

from settled import log
from settled.models import KINDS, Answer
from voice import script

from . import reader

SYSTEM = (Path(__file__).resolve().parent / "prompt_agent_hi.md").read_text(encoding="utf-8")
# the call so far, as much as the model needs
HISTORY = 8


def read(text, said, shop, turn, call=None):
    """His reply as an Answer carrying the AI's say and next. turn is CallState.turn;
    call is the id of this call's "due" row, for the call so far."""
    if not text.strip():
        return Answer("no answer", text)
    year_step = turn["step"] == "year"
    try:
        content = reader._ask(text, said, SYSTEM, max_tokens=320, user=_message(text, said, shop, turn, call))
        return _parse(content, text, turn["step"])
    except Exception as e:
        reader._log({"error": type(e).__name__, "status": getattr(e, "code", None), "rupees": 0})
        return Answer("unsure", text, intent="other" if year_step else None)


def record(shop):
    """What the model may know: names, plans and prices, dates. Not his year of birth, payments or number."""
    f = script.fields("hi", shop)
    signed = shop.plan((shop.signup or {}).get("plan"))
    lines = [f"Shop: {shop.name}, owner {f['owner']} ({shop.owner})"]
    if signed:
        lines.append(f"Signed up {f['signed']} with salesman {f['salesman']}, {signed.name} at ₹{signed.price} a month, "
                     f"rent from {f['starts']}. Soundbox put in on {f['delivered']}.")
    others = [p for p in shop.plans if p != signed]
    if others:
        lines.append("Other plans: " + ", ".join(f"{p.name} ₹{p.price} a month" for p in others))
    return "\n".join(lines)


def _message(text, said, shop, turn, call):
    so_far = []
    if call:
        for r in log.rows(shop.id):
            if r["id"] < call or not r["said"]:
                continue
            so_far.append(f"Settled: {r['said']}")
            if r["step"] != "said":
                so_far.append(f"He: {r['heard'] or '(silence)'}")
    return (f"Record:\n{record(shop)}\n\nCall so far:\n" + "\n".join(so_far[-HISTORY:] or ["(just started)"]) +
            f"\n\nStep: {turn['step']}\nSettled just said: {said}\nallowed: {json.dumps(turn['allowed'])}\n"
            f"His reply: {text}")


def _parse(content, text, step):
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").removeprefix("json").strip()
    got = json.loads(content)
    if not isinstance(got, dict):
        raise ValueError("unexpected reply shape")
    say, nxt = got.get("say"), got.get("next")
    say = say.strip() if isinstance(say, str) else None
    nxt = nxt if isinstance(nxt, str) else None
    kind = got.get("kind")
    if step == "year":
        return Answer("unsure", text, intent=kind if kind in reader.INTENTS else "other", say=say, next=nxt)
    if kind not in KINDS:
        raise ValueError("unknown kind")
    speaker = got.get("speaker")
    if speaker not in reader.SPEAKERS:
        raise ValueError("unknown speaker")
    if step == "name" and kind == "question" and speaker == "someone else":
        # asking who's calling doesn't say he isn't the owner: he gets asked once more
        speaker = "unclear"
    reason = got.get("reason") if isinstance(got.get("reason"), str) else None
    if speaker != "shopkeeper":
        return Answer("unsure", text, reason=reason or f"{speaker} answered", speaker=speaker, say=say, next=nxt)
    topic = (got.get("topic") if got.get("topic") in reader.TOPICS else "other") if kind == "question" else None
    promise = got.get("promise") if kind in ("na", "unsure") and got.get("promise") in reader.PROMISES else None
    return Answer(kind, text, reason=reason or None, topic=topic, promise=promise, upset=got.get("upset") is True,
                  say=say, next=nxt)
