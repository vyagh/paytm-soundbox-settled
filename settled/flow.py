import time

from voice import script
from voice.script import (A_CHARGE, A_OTHER, A_PRICE, A_START, A_WHO, ASK, ASK_AGAIN, CALL_LATER, CALLBACK, CHARGED,
                          CLOSING, DECLINED, FOLLOW_UP, GOODBYE_OTHER, GOODBYE_UNVERIFIED, GREETING, NAME_AFTER_WHO,
                          NAME_AGAIN, OFFER_AGAIN, OFFER_B, PROMISE_FREE, PROMISE_LOWER, PROMISE_ONE, READ_BACK,
                          READ_BACK_B, REASSURE, SOFT, WHO_WHY, YEAR, YEAR_AGAIN, YEAR_WRONG, YEAR_WAIT)

from . import log, paytm_mock, records, rules, year
from .models import CallState

# The year of birth is asked at most 3 times in all, the first ask included. "ek minute",
# a pause or silence get "take your time" instead of "I didn't get that", within about 45 s.
YEAR_ASKS = 3
YEAR_WAIT_SECONDS = 45
# What he meant, as the AI read it, to the identity rule plain code acts on.
INTENT_RULES = {"wait": "wait", "refuse": "failed: refused", "angry": "failed: angry", "scared": "scared",
                "who": "who", "question": "who"}
EXPLAIN = {"scared": REASSURE, "who": WHO_WHY}
EXPLAINED = {"scared": "reassured, ", "who": "said who's calling, "}
# A question at the plan or the read-back, as the AI read it, to the line that answers it.
# Plain code says the line, then asks the same thing again.
ANSWERS = {"price": A_PRICE, "start": A_START, "charge": A_CHARGE, "who": A_WHO, "other": A_OTHER}
TOPICS = {"cheaper": "cheaper plan", "price": "price", "start": "start date", "charge": "what the charge is",
          "who": "who's calling", "other": "other"}
# A salesman's promise his na or doubt rests on, to the line that owns it and offers the cheaper plan.
PROMISES = {"one rupee": PROMISE_ONE, "free": PROMISE_FREE, "lower price": PROMISE_LOWER}
OFFERS = (OFFER_B, OFFER_AGAIN, *PROMISES.values())
# the same question again, shorter, after an answer
AGAIN = {ASK: ASK_AGAIN, **{line: OFFER_AGAIN for line in OFFERS}}


class HungUp(Exception):
    """He hung up, or the line dropped, while Settled waited for his reply."""


class _Busy(Exception):
    def __init__(self, line, answer):
        super().__init__(line)
        self.line, self.answer = line, answer


def run(shop_id, listener, state=None, callback=False):
    """Take one shop from due to follow-up.

    listener(shop, line) says the line and returns his reply as an Answer;
    listener(shop, line, wait=False) only says it. state is what the board sees.
    callback is a call he started, by tapping "Call me now" or calling the number back.
    """
    state = state if state is not None else CallState()
    shop = records.load(shop_id)
    if log.settled(shop.id):
        raise log.AlreadySettled(f"{shop.name}'s rent is already settled this round, so there is nothing to call about")
    try:
        return _run(shop, listener, state, callback)
    except HungUp:
        return cut(shop.id, "he hung up or the line dropped")
    except Exception:
        if state.call:
            _decided(shop, rules.stopped())
        raise
    finally:
        state.step = "done"


def _run(shop, listener, state, callback=False):
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

    log.add(shop.id, "calling", rule="callback: he tapped Call me now or called the number back" if callback else None)
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
        asked_who = reply.kind == "question" or year.asks_who(reply.words)
        _log_reply(shop, state, "identity", line, reply,
                   rule="asked who's calling → said who, asked once more" if asked_who else "not clear → asked once more")
        if asked_who:
            _say(shop, listener, WHO_WHY)
        line = NAME_AFTER_WHO if asked_who else NAME_AGAIN
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
        return _unverified(shop, listener, rule, DECLINED if rule in ("failed: refused", "failed: angry") else None)

    decision, answers, offered = _plan(shop, state, listener)
    signed = shop.plan(shop.signup["plan"])
    # a no or a salesman's promise about the plan he signed goes to the salesman's manager, whatever comes after
    told = next((a for plan, a in answers if plan == signed and (a.kind == "na" or a.promise)), None)
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
        if told:
            paytm_mock.tell_manager(shop, told.reason, _read_as(told), took=decision.plan)
        state.step = "done"
        _say(shop, listener, CHARGED)
        return decision
    last = answers[-1][1]
    if last.kind == "no answer":
        return _silent(shop)
    _decided(shop, decision)

    state.step = "followup"
    paytm_mock.hold_rent(shop)
    if told:
        paytm_mock.tell_manager(shop, told.reason, _read_as(told))
    paytm_mock.send_choices(shop, state.call)
    paytm_mock.open_ticket(shop, decision.rule, "na" if last.kind == "na" else "unclear")
    # the apology only for anger, a complaint or distress; calm doubt gets time to think
    if offered or not any(a.upset for _, a in answers):
        ending = SOFT if last.kind == "unsure" and not offered else CALLBACK
    else:
        ending = FOLLOW_UP
    _say(shop, listener, ending)
    _say(shop, listener, CLOSING)
    return decision


def _plan(shop, state, listener):
    """(decision, the (plan, answer) pairs, whether a promise line offered the cheaper plan).

    Asks the plan from his record, answers his questions, and reads the price back
    after a haan. rules.decide picks the money and when to stop."""
    signed = shop.plan(shop.signup["plan"])
    plan, line, answers, offered = signed, ASK, [], False
    state.step = "ask"
    while True:
        answer = _ask(shop, state, line, listener)
        answers.append((plan, answer))
        decision = rules.decide(shop, answers, verified=True)
        if decision.outcome != "ask again":
            return decision, answers, offered
        _decided(shop, decision)
        if answer.kind == "question":
            if answer.topic == "cheaper" and plan == signed and shop.cheaper(signed):
                plan, line = shop.cheaper(signed), OFFER_B
                state.step = "ask"
                continue
            if answer.topic in ANSWERS and not (answer.topic == "price" and plan != signed):
                _say(shop, listener, ANSWERS[answer.topic])
            line = AGAIN.get(line, line)
        elif answer.kind == "haan":
            plan = decision.plan
            line = READ_BACK if plan == signed else READ_BACK_B
            state.step = "readback"
        else:
            plan, line, offered = decision.plan, PROMISES[answer.promise], True
            state.step = "ask"


def _year(shop, state, listener):
    """(year.VERIFIED once his reply names the year of birth on record, else the identity
    rule that ends the call; True when every ask got silence).

    A reply with no year in it carries what the AI read he meant. Plain code picks the
    answer: a who or why gets who's calling, a scared reply gets told no money, OTP or
    PIN is asked, and both get the year asked again within the same 3 asks."""
    line, last, heard = YEAR, "failed: no year", False
    until = time.monotonic() + YEAR_WAIT_SECONDS
    for asked in range(1, YEAR_ASKS + 1):
        reply = listener(shop, line)
        got, rule = year.check(reply.words, shop.born)
        if rule == "failed: no year" and reply.intent:
            if reply.intent == "busy":
                raise _Busy(line, reply)
            rule = INTENT_RULES.get(reply.intent, rule)
        heard = heard or bool(reply.words.strip())
        waited = rule == "wait"
        if rule in (year.VERIFIED, "failed: wrong year", "failed: refused", "failed: angry"):
            last = rule
        done = rule in (year.VERIFIED, "failed: refused", "failed: angry") or asked == YEAR_ASKS \
            or (waited and time.monotonic() >= until)
        if done:
            note = last
        elif waited:
            note = "waiting for the year"
        else:
            note = f"{rule.removeprefix('failed: ')} → {EXPLAINED.get(rule, '')}asked again, {asked} of {YEAR_ASKS} asks"
        read_as = reply.intent or (rule if rule in ("wait", "who") else got or "no year")
        _log_reply(shop, state, "identity", line, reply, rule=note, read_as=read_as)
        if done:
            return last, not heard
        if rule in EXPLAIN:
            _say(shop, listener, EXPLAIN[rule])
            line = YEAR
        else:
            line = YEAR_WAIT if waited else YEAR_WRONG if rule == "failed: wrong year" else YEAR_AGAIN
    return last, not heard


def _unverified(shop, listener, rule, line=None):
    """Nothing changes. An SMS lets him call back, and unless he said no to telling us,
    Paytm calls the registered number again this evening."""
    decision = _decided(shop, rules.unverified(rule))
    paytm_mock.hold_rent(shop)
    paytm_mock.tell_call_me(shop)
    paytm_mock.open_ticket(shop, rule, "identity")
    if rule not in ("failed: refused", "failed: angry"):
        paytm_mock.book_retry(shop, "call him again this evening")
    _say(shop, listener, line or (GOODBYE_OTHER if rule == "failed: someone else" else GOODBYE_UNVERIFIED))
    return decision


def _silent(shop):
    """Silence after the line was said again ends the call the same way as a cut line."""
    decision = _decided(shop, rules.cut("no answer"))
    paytm_mock.tell_cut(shop)
    paytm_mock.book_retry(shop, "call him again this evening")
    return decision


def cut(shop_id, why):
    """The line dropped or he hung up: nothing changes in money, his open choices stay,
    an SMS says so and a retry call is booked."""
    shop = records.load(shop_id)
    log.add(shop.id, "cut", rule=why)
    decision = _decided(shop, rules.cut(why))
    paytm_mock.tell_cut(shop)
    paytm_mock.book_retry(shop, "call him again this evening")
    return decision


def _ask(shop, state, line, listener):
    answer = listener(shop, line)
    _log_reply(shop, state, "answered", line, answer, read_as=_read_as(answer))
    return answer


def _read_as(answer):
    if answer.kind == "question":
        return f"question: {TOPICS.get(answer.topic, 'other')}"
    return answer.kind


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
