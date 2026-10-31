import json
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from settled.models import KINDS, Answer

ROOT = Path(__file__).resolve().parent.parent
PROMPT = Path(__file__).resolve().parent / "prompt_hi.md"
KEYS = Path.home() / ".config" / "keys.env"
COST_LOG = ROOT / "bench" / "cost.log"

URL = "https://api.sarvam.ai/v1/chat/completions"
MODEL = os.environ.get("SETTLED_MODEL", "sarvam-105b-conversations")
TIMEOUT = 20
SPEAKERS = ("shopkeeper", "someone else", "unclear")

# rupees per token, before 18% GST (docs.sarvam.ai/api/getting-started/pricing, 2026-10-31)
PRICE_IN = 15 / 1_000_000
PRICE_OUT = 60 / 1_000_000
GST = 1.18

# a spend ceiling on bench/cost.log for test runs, off unless set
CAP = float(os.environ.get("SETTLED_CAP") or "inf")

SYSTEM = PROMPT.read_text(encoding="utf-8")


def _key():
    for line in KEYS.read_text(encoding="utf-8").splitlines():
        name, _, value = line.strip().removeprefix("export ").partition("=")
        if name.strip() == "SARVAM_API_KEY":
            return value.strip().strip("'\"")
    raise RuntimeError("SARVAM_API_KEY not in keys.env")


def spent():
    if not COST_LOG.exists():
        return 0.0
    return sum(json.loads(line)["rupees"] for line in COST_LOG.read_text(encoding="utf-8").splitlines() if line)


def read(text, said):
    if not text.strip():
        return Answer("no answer", text)
    try:
        return _parse(_ask(text, said), text, said)
    except Exception as e:
        _log({"error": type(e).__name__, "status": getattr(e, "code", None), "rupees": 0})
        return Answer("unsure", text)


def _ask(text, said):
    if spent() >= CAP:
        raise RuntimeError("spend cap reached")
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Agent: {said}\nHe: {text}"},
        ],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }
    if MODEL == "sarvam-105b":
        body["reasoning_effort"] = None
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-subscription-key": _key()},
    )
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        reply = json.loads(resp.read().decode("utf-8"))
    seconds = time.monotonic() - start

    usage = reply.get("usage") or {}
    tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    _log({
        "model": MODEL,
        "in": tin,
        "out": tout,
        "seconds": round(seconds, 2),
        "rupees": round((tin * PRICE_IN + tout * PRICE_OUT) * GST, 6),
    })
    return reply["choices"][0]["message"]["content"]


def _parse(content, text, said):
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").removeprefix("json").strip()
    got = json.loads(content)
    if not isinstance(got, dict) or set(got) - {"kind", "speaker", "reason", "plan"}:
        raise ValueError("unexpected reply shape")

    kind = got.get("kind")
    if kind not in KINDS:
        raise ValueError("unknown kind")
    speaker = got.get("speaker")
    if speaker not in SPEAKERS:
        raise ValueError("unknown speaker")
    reason = got.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise ValueError("reason not a string")
    if speaker != "shopkeeper":
        return Answer("unsure", text, reason=reason or f"{speaker} answered", speaker=speaker)
    return Answer(kind, text, reason=reason or None)


def _log(entry):
    entry = {"at": datetime.now().isoformat(timespec="seconds"), **entry}
    with open(COST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
