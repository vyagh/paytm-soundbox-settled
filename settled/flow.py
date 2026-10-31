from voice.script import ASK, NA_FOLLOW_UP, READ_BACK

from . import log, paytm_mock, records
from .rules import decide


def run(shop_id, listener):
    """Take one shop from due to follow-up. listener(shop, said) returns an Answer."""
    shop = records.load(shop_id)
    log.add(shop.id, "due", rule=f"first rent due {shop.signup['starts']}" if shop.signup else None)

    log.add(shop.id, "records checked", reason=_records_seen(shop))
    decision = decide(shop, [])
    if decision.outcome != "call":
        _decided(shop, decision)
        if decision.outcome == "held":
            paytm_mock.hold_rent(shop)
            paytm_mock.open_ticket(shop, decision.rule, "records")
        else:
            paytm_mock.open_ticket(shop, decision.rule, "delivery")
        return decision

    log.add(shop.id, "calling")
    answers = [_ask(shop, ASK, listener)]
    decision = _decided(shop, decide(shop, answers))

    if decision.outcome == "ask again":
        answers.append(_ask(shop, READ_BACK, listener))
        decision = _decided(shop, decide(shop, answers))

    if decision.outcome == "charged":
        paytm_mock.charge_rent(shop, decision.plan)
    elif answers[-1].kind == "na":
        decision = _after_na(shop, answers, listener)
    else:
        paytm_mock.hold_rent(shop, "unclear")
        paytm_mock.send_plan_details(shop)
        paytm_mock.open_ticket(shop, decision.rule)
    return decision


def _after_na(shop, answers, listener):
    paytm_mock.hold_rent(shop, "na")
    paytm_mock.tell_manager(shop, answers[-1].reason)
    reply = _ask(shop, NA_FOLLOW_UP, listener)
    answers.append(reply)

    if reply.plan:
        decision = _decided(shop, decide(shop, answers))
        if decision.plan:
            paytm_mock.ask_sms_confirm(shop, decision.plan)
        return decision

    decision = decide(shop, answers[:-1])
    paytm_mock.open_ticket(shop, decision.rule, "na")
    if reply.kind == "na":
        paytm_mock.book_pickup(shop)
    else:
        paytm_mock.send_plan_details(shop)
    return decision


def _ask(shop, said, listener):
    answer = listener(shop, said)
    row = log.add(shop.id, "answered", said=said, heard=answer.words, read_as=answer.kind, reason=answer.reason)
    if answer.audio:
        log.save_clip(row, answer.audio, answer.ctype)
    return answer


def _records_seen(shop):
    seen = []
    if shop.signup:
        s = shop.signup
        seen.append(f"signed up for ₹{s['price']} a {s['per']} from {s['starts']}")
    else:
        seen.append("no sign-up record")
    if shop.delivery is None:
        seen.append("no delivery record")
    elif shop.delivery.get("delivered"):
        seen.append(f"box delivered {shop.delivery.get('on')}")
    else:
        seen.append("box not delivered")
    if shop.returned is None:
        seen.append("no return record")
    elif shop.returned.get("returned"):
        seen.append("box returned")
    return ", ".join(seen)


def _decided(shop, decision):
    log.add(shop.id, "decided", rule=decision.rule, outcome=decision.outcome)
    return decision
