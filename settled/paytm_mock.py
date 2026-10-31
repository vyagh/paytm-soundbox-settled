"""Paytm's side of the follow-up, mocked. Each action is logged, and the texts it
would send go in the messages table. Nothing is actually sent."""
from datetime import date, datetime

from . import log, records

DONE = "done (mock)"


def _act(shop, action, **fields):
    log.add(shop.id, "follow-up", action=f"{action} (mock)", **fields)
    return DONE


def _who(shop):
    return f"{shop.name} ({shop.owner})" if shop.owner else shop.name


def _starts(shop):
    d = date.fromisoformat(shop.signup["starts"])
    return f"{d.day} {d:%b}"


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


def charge_rent(shop, plan):
    yes = log.last_answer(shop.id)
    when = f" at {_clock(yes['at'])}" if yes else ""
    _sms(shop, f"Your Soundbox rent for {shop.name} is ₹{plan.price}/month ({plan.name}) from {_starts(shop)}. "
               f"Your yes on our call{when} is recorded. Not right? Reply NO to this SMS and we will stop it.")
    return _act(shop, "charge rent", outcome="charged", rule=f"₹{plan.price} a month, {plan.name}")


def ask_sms_confirm(shop, plan):
    _sms(shop, f"You picked {plan.name} on our call: ₹{plan.price}/month from {_starts(shop)}. "
               f"Reply YES to this SMS to start it. Nothing is taken until you do.")
    return _act(shop, "ask him to confirm by SMS", rule=f"₹{plan.price} a month, {plan.name}")


def hold_rent(shop, tell=None):
    if tell == "na":
        _sms(shop, f"We heard you. No Soundbox rent will be taken for {shop.name} until this is sorted.")
    elif tell == "unclear":
        _sms(shop, f"Nothing is charged for your Soundbox at {shop.name}. A Paytm person will call you soon.")
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
    elif case == "na":
        _ticket(shop, f"{_who(shop)} said no to the Soundbox rent on our call. His words: {_his_words(answer)}. "
                      f"Rent is on hold. Please call him back.")
    elif answer and answer["read_as"] == "no answer":
        _ticket(shop, f"{_who(shop)} did not answer our call about the Soundbox rent. Nothing is charged. Please call him.")
    else:
        _ticket(shop, f"{_who(shop)} gave no clear yes on our call ({answer['read_as'] if answer else 'unclear'}). "
                      f"His words: {_his_words(answer)}. Nothing is charged. Please call him back.")
    return _act(shop, "open ticket", rule=why)


def book_pickup(shop):
    _sms(shop, f"Pickup of your Soundbox at {shop.name} is booked. Our person will call before coming. No rent will be taken.")
    return _act(shop, "book pickup")


def tell_manager(shop, reason):
    answer = log.last_answer(shop.id, "na")
    s = shop.signup
    text = (f"{_who(shop)} said no to the ₹{s['price']}/month Soundbox rent that {s['salesman']} signed up. "
            f"What he said: {_his_words(answer)}. Rent is on hold.")
    if answer and log.clip(answer["id"]):
        text += " Recording attached."
    log.message(shop.id, "manager", "WhatsApp", f"For {s['salesman']}'s manager: {text}")
    return _act(shop, "tell manager", reason=reason)


def send_plan_details(shop):
    return _act(shop, "send plan details")
