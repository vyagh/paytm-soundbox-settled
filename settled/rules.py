from .year import refused, spoken

# He's busy and asks for a call later. Matched in plain code at every step, and it ends
# the call politely with nothing changed.
BUSY = ("busy", "bizi", "baad mein", "baad me ", "bad mein", "baad main", "call later", "later call", "call back",
        "callback", "phir se call", "phir call", "fir call", "dobara call", "free nahi", "time nahi",
        "बिज़ी", "बिजी", "व्यस्त", "बाद में", "बाद मे ", "फ्री नहीं", "टाइम नहीं", "फिर से कॉल", "दोबारा कॉल")
# He hands the phone to the owner. Matched in plain code at the name question: Settled says it's on
# the line and asks for the owner once more.
HANDOVER = ("deta hoon", "deta hu", "deti hoon", "deti hu", "de raha hoon", "de rahi hoon", "bulata hoon", "bulata hu",
            "bulati hoon", "bula raha", "bula rahi", "rukiye", "rukie", "ruko", "ek minute", "ek minat", "one minute",
            "hold on", "line pe rahiye", "देता हूँ", "देता हु", "देती हूँ", "दे रहा हूँ", "दे रही हूँ", "बुलाता हूँ",
            "बुलाती हूँ", "बुला रहा", "बुला रही", "रुकिए", "रुकिये", "रुको", "एक मिनट", "होल्ड", "लाइन पर रहिए")
# He asks if this is a machine, or to talk to a person. Matched in plain code at every step: Settled
# says it's an automated call and a person calls him back. Never "machine" alone: the Soundbox is one.
ROBOT = ("robot", "bot ", "recording", "insaan", "insan", "human", "real person", "asli aadmi", "aadmi se baat",
         "kisi aadmi", "रोबोट", "बॉट", "रिकॉर्डिंग", "इंसान", "इन्सान", "असली आदमी", "आदमी से बात", "किसी आदमी")
# His reply to "shall I carry on, or would you like a person to call you?". Asking for a person, a robot
# word again, or anything unclear gets the person; only a yes or a carry on goes on with the call.
PERSON = ("person", "vyakti", "call karo", "call kar dena", "call kariye", "व्यक्ति", "कॉल करो", "कॉल कर देना",
          "कॉल कीजिए", "कॉल करिए")
CARRY_ON = ("aage", "bolo", "boliye", "bolie", "chalo", "theek hai", "thik hai", "carry on", "go on", "continue",
            "आगे", "बोलो", "बोलिए", "बोलिये", "चलो", "ठीक है")
# A bare yes to "am I speaking with him": confirmed in plain code, before the AI reads it,
# which takes a lone "हाँ" for a garbled scrap.
YES_WORDS = {"haan", "han", "haa", "ha", "ji", "jee", "yes", "yeah", "boliye", "bolie", "speaking", "हा", "जी", "बोलिए",
             "बोलिये"}
YES_PHRASES = ("bol raha hoon", "bol raha hu", "bol rha hu", "बोल रहा हू", "बोल रहा हु")
# A haan with more words after it, read as from him, is still him, unless the words hold a "but" or a hand-over to someone else.
NOT_HIM = {"par", "pr", "lekin", "magar", "but", "papa", "beta", "deta", "bulata", "पर", "लेकिन", "मगर", "पापा", "बेटा",
           "देता", "बुलाता"}
from .models import Decision
from .records import missing


def before_call(shop):
    if shop.delivery is None or not shop.delivery.get("delivered"):
        return Decision("not charged", "box never delivered → not charged, no call")
    if shop.returned and shop.returned.get("returned"):
        return Decision("not charged", "box returned → not charged, no call")
    gaps = missing(shop)
    if gaps:
        return Decision("held", f"{', '.join(gaps)} record missing → held, a person checks")
    return Decision("call", "records in order → call")


def name(answer, first=True):
    """None when he says he is the owner, "ask again" for an unclear first reply, else
    the identity rule that ends the call. Only a clear someone else ends it at once."""
    if refused(answer.words):
        return "failed: refused"
    if bare_yes(answer.words):
        return None
    if answer.kind == "haan" and answer.speaker == "shopkeeper":
        return None
    if first and handover(answer.words):
        return "ask again"
    if answer.kind == "na" or answer.speaker == "someone else":
        return "failed: someone else"
    if answer.speaker == "shopkeeper" and yes_first(answer.words):
        return None
    if first and answer.kind != "no answer":
        return "ask again"
    return "failed: not confirmed"


def bare_yes(text):
    said = spoken(text)
    if not said.strip():
        return False
    for phrase in YES_PHRASES:
        said = said.replace(spoken(phrase), " ")
    return set(said.split()) <= YES_WORDS


def handover(text):
    """True when he says he's handing the phone to someone, or asks to hold."""
    return any(spoken(phrase) in spoken(text) for phrase in HANDOVER)


def yes_first(text):
    words = spoken(text).split()
    return bool(words) and words[0] in YES_WORDS and not any(w in NOT_HIM or w.startswith(("ruk", "रुक")) for w in words)


def unverified(rule):
    return Decision("held", f"identity {rule} → nothing changes, an SMS lets him call back")


# Questions he may ask at the plan question and the read-back before a person calls back instead.
QUESTIONS = 2


def decide(shop, answers, verified):
    """The money, from his answers on the plan question, the read-back and any Plan B offer.

    answers holds (plan, Answer) pairs, each answer to a line about that plan. The only
    write straight from what the AI read is a charge of the plan he signed, after haan
    twice from the verified owner, with no na or unsure about it. A question gets an
    answer and the line asked again, up to QUESTIONS. A na or doubt that rests on a
    salesman's promise gets the cheaper plan offered once, and a haan to it holds the
    rent until his tap in WhatsApp. Everything else holds the rent for a person, and a
    cancel, pickup or plan change waits for his own tap in WhatsApp.
    """
    before = before_call(shop)
    if before.outcome != "call":
        return before
    if not verified:
        return unverified("not verified")
    if not answers:
        return before

    signed = shop.plan(shop.signup["plan"])
    cheaper = shop.cheaper(signed)
    haans, questions, offered, complaints = {}, 0, False, 0
    for plan, answer in answers:
        if answer.cancel:
            return Decision("held", "asked to cancel or for a refund → nothing taken, the cancel waits for his tap in WhatsApp")
        if answer.kind == "question":
            questions += 1
            complaints += answer.topic == "support"
            if complaints > 1:
                return Decision("held", "a complaint again, not about the rent → nothing taken, a person calls back")
            if questions > QUESTIONS:
                return Decision("held", f"{questions} questions → nothing taken, a person calls back")
            continue
        if answer.kind == "haan" and plan != signed:
            return Decision("held", f"haan to {plan.name} → nothing taken, {plan.name} waits for his tap", plan)
        if answer.kind == "haan":
            haans[plan.id] = haans.get(plan.id, 0) + 1
            if haans[plan.id] == 2:
                return Decision("charged", f"haan, then haan again → charged at ₹{plan.price} ({plan.name})", plan)
            continue
        if answer.promise and plan == signed and cheaper and not offered:
            offered = True
            continue
        return held(answer)

    plan, last = answers[-1]
    if last.kind == "question":
        return Decision("ask again", f"question ({last.topic or 'other'}) → answered, asked again, {questions} of {QUESTIONS}", plan)
    if last.kind != "haan":
        return Decision("ask again", f"salesman promised {last.promise} → {cheaper.name} offered at ₹{cheaper.price}", cheaper)
    return Decision("ask again", f"clear haan → read ₹{plan.price} ({plan.name}) back", plan)


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


def robot(text):
    """True when he asks if he's talking to a machine, or asks for a person."""
    return any(spoken(phrase) in spoken(text) for phrase in ROBOT)


def person_later():
    return Decision("held", "asked if it's a robot or for a person → nothing changed, a person calls back")


def carry_on(answer):
    """True when his reply to the automated-call question says go on with the call."""
    if robot(answer.words) or any(spoken(phrase) in spoken(answer.words) for phrase in PERSON):
        return False
    return answer.kind == "haan" or bare_yes(answer.words) or any(spoken(phrase) in spoken(answer.words) for phrase in CARRY_ON)
