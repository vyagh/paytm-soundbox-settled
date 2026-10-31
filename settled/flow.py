import time

from voice import script
from voice.script import (ASK, CALL_LATER, CHARGED, CLOSING, DECLINED, FOLLOW_UP, GOODBYE_OTHER, GOODBYE_UNVERIFIED,
                          GREETING, NAME_AGAIN, READ_BACK, YEAR, YEAR_AGAIN, YEAR_WAIT)

from . import log, paytm_mock, records, rules, year
from .models import CallState

# The year of birth is asked at most 3 times in all, the first ask included. "ek minute",
# a pause or silence get "take your time" instead of "I didn't get that", within about 45 s.
YEAR_ASKS = 3
YEAR_WAIT_SECONDS = 45


class HungUp(Exception):
    """He hung up, or the line dropped, while Settled waited for his reply."""


class _Busy(Exception):
    def __init__(self, line, answer):
        super().__init__(line)
        self.line, self.answer = line, answer


def run(shop_id, listener, state=None):
    """Take one shop from due to follow-up.

    listener(shop, line) says the line and returns his reply as an Answer;
    listener(shop, line, wait=False) only says it. state is what the board sees.
    """
    state = state if state is not None else CallState()
    shop = records.load(shop_id)
    if log.settled(shop.id):
        raise log.AlreadySettled(f"{shop.name}'s rent is already settled this round, so there is nothing to call about")
    try:
        return _run(shop, listener, state)
    except HungUp:
        return cut(shop.id, "he hung up or the line dropped")
    except Exception:
        if state.call:
            _decided(shop, rules.stopped())
        raise
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
    try:
        return _call(shop, _busy_aware(listener), state)
    except _Busy as busy:
        step = "answered" if state.step in ("ask", "readback") else state.step
        _log_reply(shop, state, step, busy.line, busy.answer, rule="busy → call back later")
        decision = _decided(shop, rules.call_later())
        paytm_mock.tell_call_later(shop)
        paytm_mock.book_retry(shop)
        _say(shop, listener, CALL_LATER)
        return decision


def _busy_aware(listener):
    """"Busy hoon, baad mein call karo" at any step ends the call, checked in plain code."""
    def listen(shop, line, wait=True):
        if not wait:
            return listener(shop, line, wait=False)
        answer = listener(shop, line)
        if rules.busy(answer.words):
            raise _Busy(line, answer)
        return answer
    return listen


def _call(shop, listener, state):
    state.step = "identity"
    line = GREETING
    reply = listener(shop, line)
    failed = rules.name(reply)
    if failed == "ask again":
        _log_reply(shop, state, "identity", line, reply, rule="not clear → asked once more")
        line = NAME_AGAIN
        reply = listener(shop, line)
        failed = rules.name(reply, first=False)
    _log_reply(shop, state, "identity", line, reply, rule=failed or "name confirmed")
    if reply.kind == "no answer":
        return _silent(shop)
    if failed:
        return _unverified(shop, listener, failed)

    rule, silent = _year(shop, state, listener)
    if silent:
        return _silent(shop)
    if rule != year.VERIFIED:
        return _unverified(shop, listener, rule, DECLINED if rule == "failed: refused" else None)

    state.step = "ask"
    answers = [_ask(shop, state, ASK, listener)]
    decision = rules.decide(shop, answers, verified=True)
    if decision.outcome == "ask again":
        _decided(shop, decision)
        state.step = "readback"
        answers.append(_ask(shop, state, READ_BACK, listener))
        decision = rules.decide(shop, answers, verified=True)

    if decision.outcome == "charged":
        try:
            paytm_mock.charge_rent(shop, decision.plan)
        except log.AlreadySettled:
            # his tap on an earlier WhatsApp settled the rent while this call was on
            decision = _decided(shop, rules.settled_meanwhile())
            state.step = "done"
            _say(shop, listener, FOLLOW_UP)
            return decision
        _decided(shop, decision)
        state.step = "done"
        _say(shop, listener, CHARGED)
        return decision
    if answers[-1].kind == "no answer":
        return _silent(shop)
    _decided(shop, decision)

    state.step = "followup"
    paytm_mock.hold_rent(shop)
    if any(a.kind == "na" for a in answers):
        paytm_mock.tell_manager(shop, next(a.reason for a in answers if a.kind == "na"))
    paytm_mock.send_choices(shop, state.call)
    paytm_mock.open_ticket(shop, decision.rule, "na" if answers[-1].kind == "na" else "unclear")
    _say(shop, listener, FOLLOW_UP)
    _say(shop, listener, CLOSING)
    return decision


def _year(shop, state, listener):
    """(year.VERIFIED once his reply names the year of birth on record, else the identity
    rule that ends the call; True when every ask got silence)."""
    line, last, heard = YEAR, "failed: no year", False
    until = time.monotonic() + YEAR_WAIT_SECONDS
    for asked in range(1, YEAR_ASKS + 1):
        reply = listener(shop, line)
        got, rule = year.check(reply.words, shop.born)
        heard = heard or bool(reply.words.strip())
        waited = rule == "wait"
        if not waited:
            last = rule
        done = rule in (year.VERIFIED, "failed: refused") or asked == YEAR_ASKS or (waited and time.monotonic() >= until)
        if done:
            note = last
        elif waited:
            note = "waiting for the year"
        else:
            note = f"{rule.removeprefix('failed: ')} → asked again, {asked} of {YEAR_ASKS} asks"
        _log_reply(shop, state, "identity", line, reply, rule=note, read_as="wait" if waited else got or "no year")
        if done:
            return last, not heard
        line = YEAR_WAIT if waited else YEAR_AGAIN
    return last, not heard


def _unverified(shop, listener, rule, line=None):
    decision = _decided(shop, rules.unverified(rule))
    paytm_mock.hold_rent(shop, "unverified")
    paytm_mock.open_ticket(shop, rule, "identity")
    _say(shop, listener, line or (GOODBYE_OTHER if rule == "failed: someone else" else GOODBYE_UNVERIFIED))
    return decision


def _silent(shop):
    """Silence after the line was said again ends the call the same way as a cut line."""
    decision = _decided(shop, rules.cut("no answer"))
    paytm_mock.tell_cut(shop)
    paytm_mock.book_retry(shop)
    return decision


def cut(shop_id, why):
    """The line dropped or he hung up: nothing changes in money, his open choices stay,
    an SMS says so and a retry call is booked."""
    shop = records.load(shop_id)
    log.add(shop.id, "cut", rule=why)
    decision = _decided(shop, rules.cut(why))
    paytm_mock.tell_cut(shop)
    paytm_mock.book_retry(shop)
    return decision


def _ask(shop, state, line, listener):
    answer = listener(shop, line)
    _log_reply(shop, state, "answered", line, answer)
    return answer


def _log_reply(shop, state, step, line, answer, rule=None, read_as=None):
    log.add(shop.id, step, said=script.english(line, shop), heard=answer.words,
            read_as=read_as or answer.kind, reason=answer.reason, rule=rule)


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
