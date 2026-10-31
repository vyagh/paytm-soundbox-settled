from voice import script
from voice.script import (ASK, CHARGED, CODE, CONSENT, FOLLOW_UP, GOODBYE_OTHER, GOODBYE_UNVERIFIED,
                          NAME_RECORDED, NAME_UNRECORDED, READ_BACK)

from . import codes, log, paytm_mock, records, rules
from .models import CallState


def run(shop_id, listener, state=None):
    """Take one shop from due to follow-up.

    listener(shop, line) says the line and returns his reply as an Answer;
    listener(shop, line, wait=False) only says it. state is what the board sees.
    """
    state = state if state is not None else CallState()
    shop = records.load(shop_id)
    if log.settled(shop.id):
        raise log.AlreadySettled(f"{shop.name}'s rent is already settled, so there is nothing to call about")
    try:
        return _run(shop, listener, state)
    finally:
        state.step = "done"


def _run(shop, listener, state):
    state.call = log.add(shop.id, "due", rule=f"first rent due {shop.signup['starts']}" if shop.signup else None)
    log.add(shop.id, "records checked", reason=_records_seen(shop))
    decision = rules.before_call(shop)
    if decision.outcome != "call":
        _decided(shop, decision)
        if decision.outcome == "held":
            paytm_mock.hold_rent(shop)
            paytm_mock.open_ticket(shop, decision.rule, "records")
        else:
            paytm_mock.open_ticket(shop, decision.rule, "delivery")
        return decision

    log.add(shop.id, "calling")
    state.step = "consent"
    reply = listener(shop, CONSENT)
    state.recording = reply.kind == "haan"
    _log_reply(shop, state, "consent", CONSENT, reply, rule=rules.consent(reply))
    if reply.kind == "no answer":
        decision = _decided(shop, rules.held(reply))
        paytm_mock.hold_rent(shop, "no answer")
        paytm_mock.open_ticket(shop, decision.rule, "no answer")
        return decision

    state.step = "identity"
    line = NAME_RECORDED if state.recording else NAME_UNRECORDED
    reply = listener(shop, line)
    failed = rules.name(reply)
    _log_reply(shop, state, "identity", line, reply, rule=failed or "name confirmed")
    if failed:
        return _unverified(shop, listener, failed)

    state.code = state.code or codes.new()
    paytm_mock.send_app_code(shop)
    reply = listener(shop, CODE)
    got, rule = codes.check(reply.words, state.code)
    _log_reply(shop, state, "identity", CODE, reply, rule=rule, read_as=got or "no code")
    if rule != "verified":
        return _unverified(shop, listener, rule)

    state.step = "ask"
    answers = [_ask(shop, state, ASK, listener)]
    decision = _decided(shop, rules.decide(shop, answers, verified=True))
    if decision.outcome == "ask again":
        state.step = "readback"
        answers.append(_ask(shop, state, READ_BACK, listener))
        decision = _decided(shop, rules.decide(shop, answers, verified=True))

    if decision.outcome == "charged":
        paytm_mock.charge_rent(shop, decision.plan)
        state.step = "done"
        _say(shop, listener, CHARGED)
        return decision

    state.step = "followup"
    paytm_mock.hold_rent(shop)
    if any(a.kind == "na" for a in answers):
        paytm_mock.tell_manager(shop, next(a.reason for a in answers if a.kind == "na"))
    paytm_mock.send_choices(shop, state.call)
    paytm_mock.open_ticket(shop, decision.rule, "na" if answers[-1].kind == "na" else "unclear")
    _say(shop, listener, FOLLOW_UP)
    return decision


def _unverified(shop, listener, rule):
    decision = _decided(shop, rules.unverified(rule))
    paytm_mock.hold_rent(shop, "unverified")
    paytm_mock.open_ticket(shop, rule, "identity")
    _say(shop, listener, GOODBYE_OTHER if rule == "failed: someone else" else GOODBYE_UNVERIFIED)
    return decision


def _ask(shop, state, line, listener):
    answer = listener(shop, line)
    _log_reply(shop, state, "answered", line, answer)
    return answer


def _log_reply(shop, state, step, line, answer, rule=None, read_as=None):
    row = log.add(shop.id, step, said=script.english(line, shop), heard=answer.words,
                  read_as=read_as or answer.kind, reason=answer.reason, rule=rule)
    if answer.audio and state.recording:
        log.save_clip(row, answer.audio, answer.ctype)


def _say(shop, listener, line):
    log.add(shop.id, "said", said=script.english(line, shop))
    listener(shop, line, wait=False)


def _records_seen(shop):
    seen = []
    if shop.signup:
        s = shop.signup
        seen.append(f"signed up {s['on']} by {s['salesman']['name']} for ₹{s['price']} a {s['per']} from {s['starts']}")
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
