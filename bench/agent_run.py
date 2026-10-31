"""Messy Hindi and Hinglish replies through the call, with the AI writing Settled's lines.

    SETTLED_CAP=50 python bench/agent_run.py [--cases id,id]

A turn with a "kind" (or an "intent" at the year question) is read as labelled and
never reaches the model, so a case pays only for the replies it tests. Every other
turn goes to ai.agent, one call at a time. A 429 is waited out and the turn asked
again, and the case is marked. Each AI reply, whether code used its line, what was
said and the model's seconds go to bench/results/agent-run-<date>.json.
"""
import argparse
import json
import os
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

NAME = {"text": "haan ji, main hi bol raha hoon", "kind": "haan", "next": "ask_year", "say": ""}
GUPTA = {"text": "1978"}
SHARMA = {"text": "1984"}
ONE_RUPEE = ("हाँ लिया तो था, पर ये तो तुम झूठ बोल रहे हो। जो सेल्समैन आया था वो एक रुपया बता के गया था, "
             "आप एक सौ पच्चीस बोल रहे हो। ये कोई बात थोड़ी हुई?")

CASES = [
    {"id": "one-rupee", "shop": "gupta", "turns": [NAME, GUPTA, {"text": ONE_RUPEE}, {"text": "haan theek hai"},
                                                    {"text": "haan pakka"}], "want": "held"},
    {"id": "loot-at-year", "shop": "gupta", "turns": [NAME, {"text": "तू मेरे पैसे लूटेगा?"}, GUPTA]},
    {"id": "fraud-at-year", "shop": "gupta", "turns": [NAME, {"text": "ye fraud call hai kya? pehle bhi aisa call aaya tha"}, GUPTA]},
    {"id": "fraud-plain", "shop": "gupta", "turns": [NAME, {"text": "ye fraud call hai kya? mujhe bharosa nahi"}, GUPTA]},
    {"id": "otp-worry", "shop": "sharma", "turns": [NAME, {"text": "OTP to nahi mangoge na? mere bhai ke saath fraud hua tha"}, SHARMA]},
    {"id": "who-at-name", "shop": "gupta", "turns": [{"text": "aap kaun bol rahe ho, kahan se?"}, {"text": "haan main Mahesh hi hoon"}]},
    {"id": "angry-year", "shop": "gupta", "turns": [NAME, {"text": "bakwaas band karo, roz roz call aata hai, nahi batana kuch"}],
     "want": "held"},
    {"id": "cheaper", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "koi sasta plan nahi hai kya? 125 zyada lagta hai"}],
     "want": "held"},
    {"id": "cheaper-hinglish", "shop": "sharma", "turns": [NAME, SHARMA, {"text": "bhai kam wala plan batao na, itna nahi de paunga"}],
     "want": "held"},
    {"id": "when-start", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "ye paisa kab se katega?"}]},
    {"id": "what-charge", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "ye kis cheez ka rent hai? maine to box free mein liya tha"}]},
    {"id": "free-promise", "shop": "sharma", "turns": [NAME, SHARMA, {"text": "salesman ne bola tha free hai, ab paise kyun?"}],
     "want": "held"},
    {"id": "lower-promise", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "nahi bhai, Anil ne 50 rupaye bola tha mahine ka"}],
     "want": "held"},
    {"id": "plain-na", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "nahi chahiye mujhe ye, maine nahi liya"}], "want": "held"},
    {"id": "take-it-back", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "isko wapas le jao, kaam ka nahi hai"}], "want": "held"},
    {"id": "think", "shop": "sharma", "turns": [NAME, SHARMA, {"text": "abhi soch ke batata hoon, ghar pe baat karni padegi"}],
     "want": "held"},
    {"id": "off-topic", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "mera QR code kaam nahi kar raha, uska kya karu?"}]},
    {"id": "son-answers", "shop": "gupta", "turns": [{"text": "papa dukaan pe nahi hai, main beta bol raha hoon"}]},
    {"id": "worker-answers", "shop": "sharma", "turns": [{"text": "seth ji bahar gaye hain, main naukar hoon"}]},
    {"id": "cheated", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "tum log chor ho, dhokha diya hai humein"}], "want": "held"},
    {"id": "yes-chatty", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "haan haan liya tha bhai, Anil aaya tha, sab theek hai"},
                                                     {"text": "haan kar do"}], "want": "charged"},
    {"id": "readback-question", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "haan liya tha", "kind": "haan", "next": "read_back", "say": ""},
                                                            {"text": "isme GST alag se lagega kya?"}]},
    {"id": "refund-ask", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "pichle mahine ka paisa wapas karo pehle"}]},
    {"id": "manager", "shop": "sharma", "turns": [NAME, SHARMA, {"text": "apne manager se baat karao, tum se nahi karni"}]},
    {"id": "b-then-yes", "shop": "gupta", "turns": [NAME, GUPTA, {"text": "79 wala plan hai na, wahi chahiye"}, {"text": "haan"},
                                                     {"text": "haan ji"}], "want": "held"},
    {"id": "mixed", "shop": "sharma", "turns": [NAME, SHARMA, {"text": "haan bhi aur na bhi, pehle batao kitne ka hai exactly"}]},
]


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", help="comma-separated case ids, default all")
    args = parser.parse_args(argv)

    from ai import agent, reader
    from settled import flow, log, year
    from settled.models import Answer, CallState
    from voice import script

    cases = [c for c in CASES if not args.cases or c["id"] in args.cases.split(",")]
    out, rows = ROOT / "bench" / "results" / f"agent-run-{date.today().isoformat()}.json", []
    start = reader.spent()

    def logged():
        return reader.COST_LOG.read_text(encoding="utf-8").splitlines() if reader.COST_LOG.exists() else []

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for n, case in enumerate(cases):
            if reader.spent() >= reader.CAP:
                print(f"stopped: ₹{reader.spent():.4f} spent, cap ₹{reader.CAP}")
                break
            os.environ["SETTLED_DB"] = str(Path(tmp) / f"{n}.db")
            state, turns, spoken, replies, hit = CallState(), iter(case["turns"]), [], [], 0

            def ask(text, said, shop):
                nonlocal hit
                for tries in range(4):
                    before = len(logged())
                    answer = agent.read(text, said, shop, state.turn, state.call)
                    new = [json.loads(line) for line in logged()[before:] if line]
                    if not any(e.get("status") == 429 for e in new):
                        seconds = next((e["seconds"] for e in new if "seconds" in e), None)
                        return answer, seconds
                    hit += 1
                    time.sleep(5 * (tries + 1))
                return answer, None

            def listener(shop, said, wait=True):
                spoken.append(said)
                if not wait:
                    return None
                turn = next(turns, None)
                text = "" if turn is None else turn["text"]
                is_year = said in script.YEAR_LINES
                if not text.strip():
                    return Answer("no answer", "")
                if is_year and "intent" in turn:
                    return Answer("unsure", text, intent=turn["intent"], say=turn.get("say"), next=turn.get("next"))
                if is_year and year.check(text, shop.born)[1] != "failed: no year":
                    return Answer("unsure", text)
                if "kind" in turn:
                    return Answer(turn["kind"], text, say=turn.get("say") or None, next=turn.get("next"))
                answer, seconds = ask(text, script.english(said, shop), shop)
                replies.append({"step": state.turn["step"], "his": text, "kind": answer.intent or answer.kind,
                                "speaker": answer.speaker, "topic": answer.topic, "promise": answer.promise,
                                "next": answer.next, "say": answer.say, "seconds": seconds, "answer": answer})
                return answer

            decision = flow.run(case["shop"], listener, state)
            fresh = [str(s) for s in spoken if isinstance(s, script.Fresh)]
            for r in replies:
                a = r.pop("answer")
                r["used"] = bool(a.say) and a.say in fresh
                r["said_as"] = a.say
                r["kept_next"] = a.next
            why = [r["rule"] for r in log.rows(case["shop"]) if r["rule"] and "ai's line not used" in r["rule"]]
            got = decision.outcome if decision.outcome != "charged" else f"charged:{decision.plan.id}"
            row = {"id": case["id"], "shop": case["shop"], "outcome": got, "want": case.get("want"),
                   "rule": decision.rule, "replies": replies, "fallbacks": why, "hit_429": hit,
                   "said": [script.say("hi", s, None) if isinstance(s, script.Fresh) else script.english(s, _shop(case["shop"]))
                            for s in spoken]}
            rows.append(row)
            flag = "" if not case.get("want") or got.startswith(case["want"]) else "  WANT " + case["want"]
            print(f"{case['id']:<20}{got:<16}{len(replies)} ai, {sum(r['used'] for r in replies)} used"
                  f"{', 429 x' + str(hit) if hit else ''}{flag}")

    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    seconds = sorted(r["seconds"] for row in rows for r in row["replies"] if r["seconds"] is not None)
    if seconds:
        print(f"agent seconds: median {seconds[len(seconds) // 2]:.2f}, worst {seconds[-1]:.2f}, {len(seconds)} calls")
    print(f"cost this run: ₹{reader.spent() - start:.4f} (incl. GST), all runs: ₹{reader.spent():.4f}")
    print(f"results: {out}")


def _shop(shop_id):
    from settled import records
    return records.load(shop_id)


if __name__ == "__main__":
    main(sys.argv[1:])
