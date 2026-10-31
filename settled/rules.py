import re
import unicodedata

from . import year
from .year import refused, spoken

# He's busy and asks for a call later. Matched in plain code at every step, and it ends
# the call politely with nothing changed.
BUSY = ("busy", "bizi", "baad mein", "baad me ", "bad mein", "baad main", "call later", "later call", "call back",
        "callback", "phir se call", "phir call", "fir call", "dobara call", "free nahi", "time nahi",
        "बिज़ी", "बिजी", "व्यस्त", "बाद में", "बाद मे ", "फ्री नहीं", "टाइम नहीं", "फिर से कॉल", "दोबारा कॉल")
from .models import Decision
from .records import missing


def before_call(shop):
    if shop.delivery is None or not shop.delivery.get("delivered"):
        return Decision("not charged", "box never delivered → not charged, no call")
    gaps = missing(shop)
    if gaps:
        return Decision("held", f"{', '.join(gaps)} record missing → held, a person checks")
    return Decision("call", "records in order → call")


def name(answer, first=True):
    """None when he says he is the owner, "ask again" for an unclear first reply, else
    the identity rule that ends the call. Only a clear someone else ends it at once."""
    if refused(answer.words):
        return "failed: refused"
    if answer.kind == "haan" and answer.speaker == "shopkeeper":
        return None
    if answer.kind == "na" or answer.speaker == "someone else":
        return "failed: someone else"
    if first and answer.kind != "no answer":
        return "ask again"
    return "failed: not confirmed"


def unverified(rule):
    return Decision("held", f"identity {rule} → nothing changes, an SMS lets him call back")


# Questions he may ask at the plan question and the read-back before a person calls back instead.
QUESTIONS = 2


def decide(shop, answers, verified):
    """The money, from his answers on the plan question, the read-back and any Plan B offer.

    answers holds (plan, Answer) pairs, each answer to a line about that plan. The only
    write straight from what the AI read is a charge, after haan twice to the plan he
    signed from the verified owner, with no na or unsure about it. Haan twice to the
    cheaper plan holds the rent: only his tap in WhatsApp starts it. A question gets an
    answer and the line asked again, up to QUESTIONS. A na or doubt that rests on a
    salesman's promise gets the cheaper plan offered once. Everything else holds the
    rent for a person, and a cancel, pickup or plan change waits for his own tap in WhatsApp.
    """
    before = before_call(shop)
    if before.outcome != "call":
        return before
    if not verified:
        return unverified("not verified")
    if not answers:
        return before

    signed = shop.plan(shop.signup["plan"])
    cheaper = shop.cheaper(signed)
    haans, questions, offered = {}, 0, False
    for plan, answer in answers:
        if answer.kind == "question":
            questions += 1
            if questions > QUESTIONS:
                return Decision("held", f"{questions} questions → nothing taken, a person calls back")
            continue
        if answer.kind == "haan":
            haans[plan.id] = haans.get(plan.id, 0) + 1
            if haans[plan.id] == 2 and plan != signed:
                return Decision("held", f"haan, then haan again to {plan.name} → nothing changes on the call, "
                                        f"his tap in WhatsApp starts it", plan)
            if haans[plan.id] == 2:
                return Decision("charged", f"haan, then haan again → charged at ₹{plan.price} ({plan.name})", plan)
            continue
        if answer.promise and plan == signed and cheaper and not offered:
            offered = True
            continue
        return held(answer)

    plan, last = answers[-1]
    if last.kind == "question":
        return Decision("ask again", f"question ({last.topic or 'other'}) → answered, asked again, {questions} of {QUESTIONS}", plan)
    if last.kind != "haan":
        return Decision("ask again", f"salesman promised {last.promise} → {cheaper.name} offered at ₹{cheaper.price}", cheaper)
    return Decision("ask again", f"clear haan → read ₹{plan.price} ({plan.name}) back", plan)


def held(answer):
    if answer.kind == "na":
        return Decision("held", "na → nothing taken, a person calls with the right offer")
    return Decision("held", f"{answer.kind} → nothing taken, a person follows up")


def settled_meanwhile():
    return Decision("not charged", "his tap settled the rent during the call → nothing more taken")


def cut(why):
    return Decision("held", f"{why} → nothing changed, Paytm calls again")


def stopped():
    return Decision("held", "call stopped by an error → nothing changed, a person follows up")


def busy(text):
    """True when he says he's busy or asks to be called later."""
    return any(spoken(phrase) in spoken(text) for phrase in BUSY)


def call_later():
    return Decision("held", "busy, asked for a call later → nothing changed, Paytm calls back")


# What the AI may pick as Settled's next step, by the kind of reply it read. Code checks
# its pick against these, and the money still comes only from decide().
def allowed(step, can_offer=False):
    if step == "name":
        return {"haan": ["ask_year"], "question": ["ask_name"], "unsure": ["ask_name"], "na": ["end"]}
    if step == "year":
        return {"wait": ["wait"], "refuse": ["end"], "angry": ["end"], "busy": ["end"],
                "scared": ["ask_year"], "who": ["ask_year"], "question": ["ask_year"], "other": ["ask_year"]}
    offer = ["offer_plan_b"] if can_offer else []
    return {"haan": ["confirm" if step.startswith("readback") else "read_back"], "question": ["answer", *offer],
            "na": ["end", *offer], "unsure": ["end", *offer]}


# A line the AI wrote is said only when it passes every check here; otherwise Settled says its fixed line.
SAY_MAX = 220
CURRENCY = ("रुपय", "रुपए", "रूपय", "रूपए", "रु", "rupay", "rupee", "rupe", "rs", "inr")
# asking for any of these is what a scam call does
SECRETS = ("otp", "ओटीपी", "pin", "पिन", "कोड", "code", "पासवर्ड", "password", "cvv", "सीवीवी", "upi", "यूपीआई",
           "अकाउंट नंबर", "account number", "खाता नंबर", "कार्ड नंबर", "card number")
# money moves and plan changes the call never makes: only his tap does
NEVER = ("रिफंड", "refund", "रीफंड", "लौटा", "कैशबैक", "cashback", "डिस्काउंट", "discount", "छूट", "कैंसल", "cancel",
         "रद्द", "बंद कर", "पिकअप", "pickup", "ले जाएंगे", "ले जाएँगे", "ले जाएगें", "ले जायेंगे", "उठा ले", "बदल दिया",
         "बदल देंगे", "बदल दूं", "बदल दूँ", "चालू कर दिया", "शुरू कर दिया", "माफ़ कर देंगे", "माफ कर देंगे")
# allowed only when he said them first
HIS_WORDS = ("मुफ़्त", "मुफ्त", "फ्री", "फ़्री", "free", "muft")
NEGATION = {"नहीं", "नही", "मत", "न", "never", "not", "no", "कभी"}
MANAGER = ("मैनेजर", "manager", "मेनेजर")


def say_ok(say, shop, heard, kind, step):
    """None when the AI's line can be said, else why not. heard is his reply this turn."""
    if not isinstance(say, str):
        return "not text"
    text = say.strip()
    low = text.lower()
    his = (heard or "").lower()
    if len(text) > SAY_MAX:
        return "too long"
    if not any("ऀ" <= c <= "ॿ" for c in text):
        return "not in Hindi"
    # a clause's verb comes last, so "OTP नहीं माँग रहे" negates the ask and "घबराइए मत, OTP बताइए" does not
    for clause in re.split(r"[।.!?,;\n]+", low):
        tokens = year._tokens(clause)
        for i, token in enumerate(tokens):
            if any(_has(token, w) for w in SECRETS) and not NEGATION & set(tokens[i + 1:]):
                return "asks for a secret"
            if ("कट" in token or "काट" in token) and not NEGATION & set(tokens[:i]):
                return "says money will be taken"
    if any(w in low for w in NEVER) or ("वापस" in low and not re.search(r"वापस\s*(कॉल|फ़ोन|फोन|call)", low)):
        return "promises a refund, cancel, pickup or plan change"
    if any(w in low for w in HIS_WORDS) and not any(w in his for w in HIS_WORDS):
        return "promises something free"
    if any(w in low for w in MANAGER) and not (kind == "na" or step == "offer_plan_b"):
        return "says his manager is told when code won't tell him"
    prices = {str(p.price) for p in shop.plans}
    his_numbers = set(_numbers(his))
    days = {str(int(d[-2:])) for d in _dates(shop)} | {d[:4] for d in _dates(shop)}
    amounts, digits = _amounts(text)
    if any(a not in prices | his_numbers for a in amounts):
        return "an amount not in his record"
    if any(d not in prices | his_numbers | days for d in digits):
        return "a number not in his record"
    return None


def _has(sentence, word):
    if word.isascii():
        return re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", sentence) is not None
    return word in sentence


def _dates(shop):
    s = shop.signup or {}
    return [d for d in (s.get("on"), s.get("starts"), (shop.delivery or {}).get("on")) if d]


def _numbers(text):
    return [str(int(run)) for run in year._runs(text) if run.isdigit()]


def _amounts(text):
    """(amounts said as money, every numeral) in the AI's line, as digit strings."""
    tokens = [t for t in year.SPLIT.split(text.lower().replace("₹", " ₹ ")) if t]
    amounts, run = [], []
    for i, token in enumerate(tokens):
        if token == "₹":
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            amounts.extend(_numbers(nxt) or ["?"])
            continue
        if year._token_digits(token) is not None or year._key(token) in year.HUNDRED:
            run.append(token)
            continue
        if run and token.startswith(CURRENCY):
            amounts.extend(_numbers(" ".join(run)) or ["?"])
        run = []
    digits = [str(int("".join(str(unicodedata.digit(c)) for c in m))) for m in re.findall(r"\d+", text)]
    return amounts, digits
