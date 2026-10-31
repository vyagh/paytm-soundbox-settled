from .codes import refused, spoken

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


def consent(answer):
    """Recording only on his clear haan. The call goes on either way."""
    return "recording allowed" if answer.kind == "haan" else "no recording"


def name(answer, first=True):
    """None when he says he is the owner, "ask again" for an unclear first reply, else
    the identity rule that ends the call. Only a clear someone else ends it at once."""
    if refused(answer.words):
        return "failed: declined"
    if answer.kind == "haan" and answer.speaker == "shopkeeper":
        return None
    if answer.kind == "na" or answer.speaker == "someone else":
        return "failed: someone else"
    if first and answer.kind != "no answer":
        return "ask again"
    return "failed: not confirmed"


def unverified(rule):
    return Decision("held", f"identity {rule} → nothing changes, a person calls the registered number")


def decide(shop, answers, verified):
    """The money, from his answers to the plan question and the read-back.

    The only write straight from what the AI read is a charge, after haan twice from
    the verified owner. Everything else holds the rent for a person, and a cancel,
    pickup or plan change waits for his own tap in WhatsApp.
    """
    before = before_call(shop)
    if before.outcome != "call":
        return before
    if not verified:
        return unverified("not verified")
    if not answers:
        return before

    signed = shop.plan(shop.signup["plan"])
    first, later = answers[0], answers[1:]
    if first.kind == "haan":
        if not later:
            return Decision("ask again", "first clear haan → read the price back")
        if later[0].kind == "haan":
            return Decision("charged", f"haan, then haan again → charged at ₹{signed.price} ({signed.name})", signed)
        return held(later[0])
    return held(first)


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
