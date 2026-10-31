from .models import Decision
from .records import missing


def decide(shop, answers):
    if shop.delivery is None or not shop.delivery.get("delivered"):
        return Decision("not charged", "box never delivered → not charged, no call")

    gaps = missing(shop)
    if gaps:
        return Decision("held", f"{', '.join(gaps)} record missing → held, a person checks")

    if not answers:
        return Decision("call", "records in order → call")

    signed = shop.plan(shop.signup["plan"])
    first, later = answers[0], answers[1:]

    if first.kind == "haan":
        if not later:
            return Decision("ask again", "first clear haan → read the price back")
        second = later[0]
        if second.kind == "haan":
            return Decision("charged", f"haan, then haan again → charged at ₹{signed.price} ({signed.name})", signed)
        return _held(second)

    if first.kind == "na":
        picked = next((a.plan for a in later if a.plan), None)
        if picked:
            plan = shop.plan(picked)
            if plan is None:
                return Decision("held", f"picked {picked!r}, not in the plan record → held")
            return Decision("held", f"picked {plan.name} after na → held, he confirms by SMS", plan)
        return Decision("held", "na → hold")

    return _held(first)


def _held(answer):
    if answer.kind == "na":
        return Decision("held", "na → hold")
    return Decision("held", f"{answer.kind} → hold, a person follows up")
