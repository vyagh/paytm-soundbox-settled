"""Paytm's side of the follow-up, mocked. Each action is logged, and the texts it
would send go in the messages table. Nothing is actually sent."""
import json
from datetime import date, datetime

from . import log, records

DONE = "done (mock)"
# Actions that lose the customer or change his plan. The call never takes one; only his tap does.
NEGATIVE = ("book pickup", "cancel plan", "change plan")


def _act(shop, action, **fields):
    log.add(shop.id, "follow-up", action=f"{action} (mock)", **fields)
    return DONE


def _who(shop):
    return f"{shop.name} ({shop.owner})" if shop.owner else shop.name


def _day(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%b}"


def _starts(shop):
    return _day(shop.signup["starts"])


def _clock(at):
    t = datetime.fromisoformat(at)
    return f"{t.hour % 12 or 12}:{t:%M} {'am' if t.hour < 12 else 'pm'}"


def _sms(shop, text):
    log.message(shop.id, "shopkeeper", "SMS", f"Paytm: {text}")


def _ticket(shop, text):
    log.message(shop.id, "support", "ticket", "{ticket} · " + text)


def _his_words(answer):
    words = (answer or {}).get("heard") or (answer or {}).get("reason")
    return f'"{words}"' if words else "nothing clear"


def _salesman(shop):
    man = shop.signup["salesman"]
    return f"{man['name']} ({man['id']})"


def send_app_code(shop):
    return _act(shop, "send code to his Paytm app")


def charge_rent(shop, plan, tapped=False):
    if tapped:
        why = "You chose this in WhatsApp."
    else:
        yes = log.last_answer(shop.id)
        why = f"Your yes on our call{' at ' + _clock(yes['at']) if yes else ''} is noted."
    _sms(shop, f"Your Soundbox rent for {shop.name} is ₹{plan.price}/month ({plan.name}) from {_starts(shop)}. "
               f"{why} Not right? Reply NO to this SMS and we will stop it.")
    return _act(shop, "charge rent", outcome="charged", rule=f"₹{plan.price} a month, {plan.name}")


def hold_rent(shop, tell=None):
    if tell == "no answer":
        _sms(shop, f"Nothing is charged for your Soundbox at {shop.name}. A Paytm person will call you soon.")
    elif tell == "unverified":
        _sms(shop, f"We called {shop.name} about your Soundbox but could not confirm we were speaking with you. "
                   f"Nothing has changed. A Paytm person will call you on this number.")
    return _act(shop, "hold rent", outcome="held")


def open_ticket(shop, why, case="unclear"):
    answer = log.last_answer(shop.id, "na" if case == "na" else None)
    if case == "delivery":
        state = "has no delivery record" if shop.delivery is None else "is marked not delivered"
        rent = f"Rent from {_starts(shop)}" if shop.signup else "Rent"
        _ticket(shop, f"Delivery team: the Soundbox for {_who(shop)} {state}. "
                      f"{rent} is not charged and the shop was not called. Please check the delivery.")
    elif case == "records":
        gaps = " and ".join(records.missing(shop))
        _ticket(shop, f"{_who(shop)} has no {gaps} record. Rent is on hold and the shop was not called. Please check the records.")
    elif case == "identity":
        _ticket(shop, f"Our call to {_who(shop)} could not confirm the owner ({why}). Nothing was asked and nothing changed. "
                      f"Please call the registered number {shop.mobile}.")
    elif case == "na":
        _ticket(shop, f"{_who(shop)} said no to the Soundbox rent on our call. His words: {_his_words(answer)}. "
                      f"Nothing is taken. Please call him with the right offer. He has the choices in WhatsApp too.")
    elif case == "no answer":
        _ticket(shop, f"{_who(shop)} did not answer our call about the Soundbox rent. Nothing is charged. Please call him.")
    else:
        _ticket(shop, f"{_who(shop)} gave no clear yes on our call ({answer['read_as'] if answer else 'unclear'}). "
                      f"His words: {_his_words(answer)}. Nothing is taken. Please call him with the right offer.")
    return _act(shop, "open ticket", rule=why)


def tell_manager(shop, reason):
    answer = log.last_answer(shop.id, "na")
    s = shop.signup
    text = (f"{_who(shop)} said no to the ₹{s['price']}/month Soundbox rent that {_salesman(shop)} signed up "
            f"on {_day(s['on'])} (form {s['form']}). What he said: {_his_words(answer)}. Nothing is taken.")
    if answer and log.clip(answer["id"]):
        text += " Recording attached."
    log.message(shop.id, "manager", "WhatsApp", f"For {s['salesman']['name']}'s manager: {text}")
    return _act(shop, "tell manager", reason=reason)


def choices(shop):
    signed = shop.plan(shop.signup["plan"])
    out = [{"id": "keep_plan", "label": f"Keep {signed.name}, ₹{signed.price}/month"}]
    cheaper = shop.cheaper(signed)
    if cheaper:
        out.append({"id": "cheaper_plan", "label": f"Switch to {cheaper.name}, ₹{cheaper.price}/month"})
    out.append({"id": "cancel", "label": "Cancel and return the box"})
    return out


def send_choices(shop):
    """His WhatsApp: what the record says, that nothing is taken, and the choices only he can make."""
    s = shop.signup
    signed = shop.plan(s["plan"])
    log.message(shop.id, "shopkeeper", "WhatsApp",
                f"Paytm: Namaste {shop.owner} ji. Nothing has been taken for your Soundbox ({_serial(shop)}). "
                f"Your sign-up form {s['form']}, done by {s['salesman']['name']} on {_day(s['on'])}, says {signed.name}, "
                f"₹{signed.price}/month from {_starts(shop)}. A Paytm person will call you with the right offer. "
                f"Or choose yourself here: {{link}}",
                choices(shop))
    return _act(shop, "send choices on WhatsApp")


def _serial(shop):
    return records.record(shop.id).get("device", {}).get("serial", "no serial")


def tap(message_id, choice):
    """His tap on a WhatsApp choice. The only way a plan is cancelled, changed or a box picked up."""
    msg = log.get_message(message_id)
    if not msg or not msg["choices"]:
        raise KeyError("no message with choices")
    offered = {c["id"]: c["label"] for c in json.loads(msg["choices"])}
    if choice not in offered:
        raise ValueError(f"not a choice on this message: {choice!r}")
    shop = records.load(msg["shop"])
    log.tap(message_id, choice)

    signed = shop.plan(shop.signup["plan"])
    said = f"tapped: {offered[choice]}"
    if choice == "keep_plan":
        log.add(shop.id, "tap", heard=said, rule=f"his tap in WhatsApp → charged at ₹{signed.price} ({signed.name})", outcome="charged")
        charge_rent(shop, signed, tapped=True)
        return {"outcome": "charged", "plan": signed.id}
    if choice == "cheaper_plan":
        plan = shop.cheaper(signed)
        log.add(shop.id, "tap", heard=said, rule=f"his tap in WhatsApp → {plan.name}, charged at ₹{plan.price}", outcome="charged")
        _act(shop, "change plan", rule=f"{signed.name} → {plan.name}")
        charge_rent(shop, plan, tapped=True)
        return {"outcome": "charged", "plan": plan.id}
    log.add(shop.id, "tap", heard=said, rule="his tap in WhatsApp → plan cancelled, box picked up", outcome="cancelled")
    _act(shop, "cancel plan", outcome="cancelled")
    book_pickup(shop)
    return {"outcome": "cancelled", "plan": None}


def book_pickup(shop):
    _sms(shop, f"Pickup of your Soundbox at {shop.name} is booked, as you chose. Our person will call before coming. No rent will be taken.")
    return _act(shop, "book pickup")
