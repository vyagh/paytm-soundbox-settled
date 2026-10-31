"""Hindi replies in real voices, clean, in crowd noise and over a phone line,
sent through a running board the way the page sends them.

    python bench/hindi_voice.py build
    BOARD_PORT=8131 python bench/hindi_voice.py run --tag before [--cond clean,phone] [--ids a,b]
    python bench/hindi_voice.py report before [after]

The clips are in bench/audio/hindi-real/manifest.json. The clip is his reply to
the line named in "at"; the other line gets a typed reply (ask: "हाँ जी, लिया था",
read-back: "हाँ, पक्का"), and after a na the call is left to time out.
"""
import argparse
import array
import hashlib
import json
import math
import statistics
import subprocess
import sys
import threading
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bench"))

import voice_run  # noqa: E402
from ai import reader  # noqa: E402
from voice import sarvam, script  # noqa: E402

HERE = ROOT / "bench" / "audio" / "hindi-real"
MANIFEST = HERE / "manifest.json"
RUNS = HERE / "runs"
RATE = 16000
SNRS = (20, 10, 5)
CONDITIONS = ("clean", "n20", "n10", "n5", "phone")
SHOPS = ("gupta", "sharma")
TYPED = {script.ASK: "हाँ जी, लिया था", script.READ_BACK: "हाँ, पक्का"}


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def samples(path):
    with wave.open(str(path)) as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1
        return array.array("h", w.readframes(w.getnframes()))


def write(path, data, rate=RATE):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())


def rms(data):
    return math.sqrt(sum(x * x for x in data) / max(1, len(data))) or 1.0


def crowd():
    """A shop-floor bed: other people's speech, reversed and overlapped, in a hall, with hiss."""
    out = HERE / "crowd.wav"
    if out.exists():
        return samples(out)
    lines = sorted(p for p in sarvam.CACHE.glob("*.wav") if not p.name.startswith("hi-"))[:6]
    inputs = [a for p in lines for a in ("-stream_loop", "-1", "-t", "32", "-i", str(p))]
    chains = [f"[{i}]aresample={RATE},areverse,atrim=start={i * 1.3}[s{i}]" for i in range(len(lines))]
    mix = "".join(f"[s{i}]" for i in range(len(lines)))
    graph = ";".join(chains) + (f";{mix}amix=inputs={len(lines)}:normalize=0,aecho=0.8:0.6:60|130:0.35|0.25[talk];"
                                f"anoisesrc=d=30:c=pink:r={RATE}:a=0.03[hiss];[talk][hiss]amix=inputs=2:normalize=0,atrim=0:30")
    ffmpeg(*inputs, "-filter_complex", graph, "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(out))
    return samples(out)


def build():
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bed = crowd()
    for case in cases:
        clean = HERE / f"{case['id']}.clean.wav"
        if not case["text"]:
            write(clean, bed[RATE * 3:RATE * 5])
            for snr in SNRS:
                write(HERE / f"{case['id']}.n{snr}.wav", bed[RATE * 3:RATE * 5])
        else:
            raw = HERE / f"{case['id']}.raw.wav"
            if not raw.exists():
                raw.write_bytes(sarvam.speak(case["text"], "hi-IN", case["voice"]))
            ffmpeg("-i", str(raw), "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(clean))
        speech = samples(clean)
        start = int(hashlib.sha1(case["id"].encode()).hexdigest(), 16) % (len(bed) - len(speech))
        noise = bed[start:start + len(speech)]
        for snr in SNRS if case["text"] else ():
            gain = rms(speech) / rms(noise) / 10 ** (snr / 20)
            mixed = array.array("h", (max(-32768, min(32767, int(s + n * gain))) for s, n in zip(speech, noise)))
            write(HERE / f"{case['id']}.n{snr}.wav", mixed)
        ffmpeg("-i", str(clean), "-af", "highpass=f=300,lowpass=f=3400,aresample=8000",
               "-ar", "8000", "-c:a", "pcm_mulaw", "-f", "wav", str(HERE / f"{case['id']}.mulaw.wav"))
        ffmpeg("-i", str(HERE / f"{case['id']}.mulaw.wav"), "-ac", "1", "-ar", "8000", "-c:a", "pcm_s16le",
               str(HERE / f"{case['id']}.phone.wav"))
        (HERE / f"{case['id']}.mulaw.wav").unlink()
    print(f"{len(cases)} clips, {len(CONDITIONS)} versions each, in {HERE}")


def last_id():
    after = 0
    while rows := voice_run.call(f"/api/log?after={after}")[1]:
        after = rows[-1]["id"]
    return after


def outcome(rows):
    decided = [r for r in rows if r["step"] == "decided" and r["outcome"] not in ("call", "ask again")]
    if not decided:
        return "none", ""
    last = decided[-1]
    return ("charged" if last["outcome"] == "charged" else last["outcome"]), last["rule"]


def play(shop, case, cond):
    clip = HERE / f"{case['id']}.{cond}.wav"
    tested = script.ASK if case["at"] == "ask" else script.READ_BACK
    first = last_id()
    status, _ = voice_run.call(f"/api/call/{shop}/start", b"")
    if status != 200:
        raise RuntimeError(f"start {shop}: {status}")
    row = {"id": case["id"], "group": case["group"], "cond": cond, "expect": case["expect"], "kind": case["kind"]}
    seq = 0
    while True:
        prompt = voice_run.next_prompt(shop, seq)
        if prompt is None:
            break
        seq = prompt["seq"]
        said = prompt["said"]
        if said == tested:
            with wave.open(str(clip)) as w:
                seconds = w.getnframes() / w.getframerate()
            t = time.monotonic()
            status, got = voice_run.call(f"/api/call/{shop}/reply?seq={seq}", clip.read_bytes(), "audio/wav",
                                         {"X-Seconds": str(seconds)})
            ms = round((time.monotonic() - t) * 1000)
            heard = got.get("heard", "") if status == 200 else ""
            read_as = got.get("read_as") if status == 200 else f"{status} {got.get('error')}"
            if "heard" in row:
                row.setdefault("again", []).append({"heard": heard, "read_as": read_as, "ms": ms})
            else:
                row.update(heard=heard, read_as=read_as, ms=ms)
        elif said in TYPED:
            voice_run.call(f"/api/call/{shop}/reply?seq={seq}", json.dumps({"text": TYPED[said]}).encode("utf-8"),
                           "application/json")
    while voice_run.shop_state(shop)["call"]["active"]:
        time.sleep(0.2)
    rows = [r for r in voice_run.call(f"/api/log?after={first}")[1] if r["shop"] == shop]
    row["got"], row["rule"] = outcome(rows)
    row["asks"] = sum(1 for r in rows if r["step"] == "answered")
    return row


def run(tag, conds, ids, cap):
    cases = [c for c in json.loads(MANIFEST.read_text(encoding="utf-8")) if not ids or c["id"] in ids]
    jobs = [(c, cond) for cond in conds for c in cases]
    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"{tag}.jsonl"
    lock = threading.Lock()
    spent_at_start = reader.spent()

    def worker(shop):
        while True:
            with lock:
                if not jobs or reader.spent() >= cap:
                    return
                case, cond = jobs.pop(0)
            row = play(shop, case, cond)
            with lock:
                with open(out, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                mark = "ok" if row["got"] == row["expect"] else "MISS"
                print(f"{mark:4} {cond:5} {case['id']:15} heard {row.get('heard')!r} read {row.get('read_as')} -> {row['got']} {row.get('ms')}ms", flush=True)

    threads = [threading.Thread(target=worker, args=(s,)) for s in SHOPS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"left: {len(jobs)}, cost.log grew ₹{reader.spent() - spent_at_start:.3f} while this ran (all servers share it)")


def summary(rows):
    out = []
    for cond in CONDITIONS:
        got = [r for r in rows if r["cond"] == cond]
        if not got:
            continue
        right = sum(r["got"] == r["expect"] for r in got)
        wrong_charge = sum(r["got"] == "charged" and r["expect"] != "charged" for r in got)
        missed_yes = sum(r["expect"] == "charged" and r["got"] != "charged" for r in got)
        ms = sorted(r["ms"] for r in got if "ms" in r)
        out.append(f"| {cond} | {right}/{len(got)} | {wrong_charge} | {missed_yes} | "
                   f"{statistics.median(ms) / 1000:.2f} s | {ms[-1] / 1000:.2f} s |")
    return "\n".join(["| audio | outcome right | charged wrongly | honest yes not charged | median time | worst time |",
                      "|---|---|---|---|---|---|", *out])


def report(tags):
    for tag in tags:
        rows = [json.loads(l) for l in (RUNS / f"{tag}.jsonl").read_text(encoding="utf-8").splitlines() if l]
        print(f"### {tag}\n\n{summary(rows)}\n")
        for r in rows:
            if r["got"] != r["expect"]:
                print(f"- {r['cond']} `{r['id']}`: heard “{r.get('heard')}”, read {r.get('read_as')}, "
                      f"{r['got']} (wanted {r['expect']})")
        print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("what", choices=("build", "run", "report"))
    p.add_argument("tags", nargs="*")
    p.add_argument("--tag", default="run")
    p.add_argument("--cond", default=",".join(CONDITIONS))
    p.add_argument("--ids", default="")
    p.add_argument("--cap", type=float, help="stop once bench/cost.log totals this many rupees")
    a = p.parse_args()
    if a.what == "build":
        build()
    elif a.what == "run":
        run(a.tag, a.cond.split(","), set(filter(None, a.ids.split(","))), a.cap or math.inf)
    else:
        report(a.tags)


if __name__ == "__main__":
    main()
