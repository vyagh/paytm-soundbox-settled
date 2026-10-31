"""Paytm's side of the follow-up, mocked. Each action is logged, and the texts it
would send go in the messages table. Nothing is actually sent."""
import json
import threading
from datetime import date, datetime

from . import log, records

DONE = "done (mock)"
# Actions that lose the customer or change his plan. The call never takes one; only his tap does.
NEGATIVE = ("book pickup", "cancel plan", "change plan")

_tapping = threading.Lock()


class Expired(Exception):
    pass


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


def charge_rent(shop, plan, tapped=False):
    if tapped:
        why = "You chose this in WhatsApp."
    else:
        yes = log.last_answer(shop.id)
        why = f"Your yes on our call{' at ' + _clock(yes['at']) if yes else ''} is noted."
    log.add_settle(shop.id, "follow-up", action="charge rent (mock)", outcome="charged",
                   rule=f"₹{plan.price} a month, {plan.name}")
    _sms(shop, f"Your Soundbox rent for {shop.name} is ₹{plan.price}/month ({plan.name}) from {_starts(shop)}. "
               f"{why} Not right? Reply NO to this SMS and we will stop it.")
    return DONE


def hold_rent(shop, tell=None):
    if tell == "no answer":
        _sms(shop, f"Nothing is charged for your Soundbox at {shop.name}. A Paytm person will call you soon.")
    return _act(shop, "hold rent", outcome="held")


# The button on his SMS that rings Paytm back: POST /api/call/<shop>/callback.
CALL_ME = [{"id": "call_me", "label": "Call me now"}]


def tell_call_me(shop):
    """To his registered number, after a call that never confirmed it was him."""
    log.message(shop.id, "shopkeeper", "SMS", "Paytm: Paytm called about your Soundbox. "
                "Tap Call me now to talk now, or call this number back.", CALL_ME)


def tell_cut(shop):
    link = live_link(shop.id)
    also = f" You can also choose yourself here: {log.get_message(link)['link']}" if link else ""
    log.message(shop.id, "shopkeeper", "SMS", f"Paytm: Our call about your Soundbox at {shop.name} got cut. Nothing was taken. "
                f"We will call you again this evening. Tap Call me now to talk now, or call this number back.{also}", CALL_ME)


def tell_call_later(shop):
    link = live_link(shop.id)
    also = f" You can also choose yourself here: {log.get_message(link)['link']}" if link else ""
    _sms(shop, f"As you asked, Paytm will call you back about your Soundbox at {shop.name}. Nothing has changed.{also}")


def book_retry(shop, when="call him again later today"):
    return _act(shop, "book retry call", rule=when)


def open_ticket(shop, why, case="unclear"):
    answer = log.last_answer(shop.id, "na" if case == "na" else None)
    if case == "delivery":
        state = "has no delivery record" if shop.delivery is None else "is marked not delivered"
        rent = f"Rent from {_starts(shop)}" if shop.signup else "Rent"
        _ticket(shop, f"Delivery team: the Soundbox for {_who(shop)} {state}. "
                      f"{rent} is not charged and the shop was not called. Please check the delivery.")
    elif case == "return":
        rent = f"Rent from {_starts(shop)}" if shop.signup else "Rent"
        _ticket(shop, f"Returns team: the Soundbox for {_who(shop)} was returned. "
                      f"{rent} is not charged and the shop was not called. Please stop the rent.")
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


def tell_manager(shop, reason, read_as="na"):
    answer = log.last_answer(shop.id, read_as)
    s = shop.signup
    text = (f"{_who(shop)} {'said no to' if read_as == 'na' else 'disputed'} the ₹{s['price']}/month Soundbox rent that {_salesman(shop)} signed up "
            f"on {_day(s['on'])} (form {s['form']}). What he said: {_his_words(answer)}. Nothing is taken.")
    log.message(shop.id, "manager", "WhatsApp", f"For {s['salesman']['name']}'s manager: {text}")
    return _act(shop, "tell manager", reason=reason)


def choices(shop, wants=None):
    """wants is the cheaper plan he said yes to on the call, if any: its choice goes first."""
    signed = shop.plan(shop.signup["plan"])
    out = [{"id": "keep_plan", "label": f"Keep {signed.name}, ₹{signed.price}/month"}]
    cheaper = shop.cheaper(signed)
    if cheaper:
        out.insert(0 if wants == cheaper else 1, {"id": "cheaper_plan", "label": f"Switch to {cheaper.name}, ₹{cheaper.price}/month"})
    out.append({"id": "cancel", "label": "Cancel and return the box"})
    return out


def send_choices(shop, call, wants=None):
    """His WhatsApp: what the record says, that nothing is taken, and the choices only he can make.
    call is the id of this call's "due" row: the choices hold for this call only. wants is the
    cheaper plan he said yes to on the call, which starts only when he taps it here."""
    s = shop.signup
    signed = shop.plan(s["plan"])
    if wants:
        then = (f"On our call you said yes to {wants.name}, ₹{wants.price}/month from {_starts(shop)}. "
                f"Tap {wants.name} here to start it: {{link}}")
    else:
        then = "A Paytm representative will call you within two days with the right plan. Or choose yourself here: {link}"
    log.message(shop.id, "shopkeeper", "WhatsApp",
                f"Paytm: Namaste {shop.owner} ji. Nothing has been taken for your Soundbox ({_serial(shop)}). "
                f"Your sign-up form {s['form']}, done by {s['salesman']['name']} on {_day(s['on'])}, says {signed.name}, "
                f"₹{signed.price}/month from {_starts(shop)}. {then}",
                choices(shop, wants), call=call)
    return _act(shop, "send choices on WhatsApp")


def _serial(shop):
    return records.record(shop.id).get("device", {}).get("serial", "no serial")


def live(msg):
    """True while his choices on this message can still be tapped: sent in this round, not
    tapped yet, and the shop's rent not settled. Only a charge, his tap or a new round ends
    them. A later call that never verifies him leaves them as they are."""
    return bool(msg and msg["choices"] and msg["call"] and msg["call"] > log.current_round()[1]
                and msg["id"] not in log.taps() and not log.settled(msg["shop"]))


def live_link(shop_id):
    """The latest message whose choices he can still tap, or None."""
    msg = log.last_choices(shop_id)
    return msg["id"] if live(msg) else None


def tap(message_id, choice):
    """His tap on a WhatsApp choice. The only way a plan is cancelled, changed or a box picked up."""
    with _tapping:
        msg = log.get_message(message_id)
        if not msg or not msg["choices"]:
            raise KeyError("no message with choices")
        offered = {c["id"]: c["label"] for c in json.loads(msg["choices"])}
        if choice not in offered:
            raise ValueError(f"not a choice on this message: {choice!r}")
        if message_id in log.taps():
            raise log.Tapped("he already chose on this message")
        if not live(msg):
            raise Expired("this link has expired")
        shop = records.load(msg["shop"])
        log.tap(message_id, choice)
        try:
            return _tapped(shop, choice, f"tapped: {offered[choice]}")
        except log.AlreadySettled:
            raise Expired("this link has expired") from None


def _tapped(shop, choice, said):
    signed = shop.plan(shop.signup["plan"])
    if choice == "keep_plan":
        charge_rent(shop, signed, tapped=True)
        log.add(shop.id, "tap", heard=said, rule=f"his tap in WhatsApp → charged at ₹{signed.price} ({signed.name})", outcome="charged")
        return {"outcome": "charged", "plan": signed.id}
    if choice == "cheaper_plan":
        plan = shop.cheaper(signed)
        charge_rent(shop, plan, tapped=True)
        log.add(shop.id, "tap", heard=said, rule=f"his tap in WhatsApp → {plan.name}, charged at ₹{plan.price}", outcome="charged")
        _act(shop, "change plan", rule=f"{signed.name} → {plan.name}")
        return {"outcome": "charged", "plan": plan.id}
    log.add_settle(shop.id, "follow-up", action="cancel plan (mock)", outcome="cancelled")
    log.add(shop.id, "tap", heard=said, rule="his tap in WhatsApp → plan cancelled, box picked up", outcome="cancelled")
    book_pickup(shop)
    return {"outcome": "cancelled", "plan": None}


def book_pickup(shop):
    _sms(shop, f"Pickup of your Soundbox at {shop.name} is booked, as you chose. Our person will call before coming. No rent will be taken.")
    return _act(shop, "book pickup")
