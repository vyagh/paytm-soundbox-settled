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


def name(answer):
    """None when he says he is the owner, else the identity rule that ends the call."""
    if answer.kind == "haan" and answer.speaker == "shopkeeper":
        return None
    if answer.kind == "na" or answer.speaker == "someone else":
        return "failed: someone else"
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
