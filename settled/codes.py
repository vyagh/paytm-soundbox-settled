"""The 4-digit code sent to his Paytm app, and reading it back out of what he said.

This is plain code on purpose: the AI never sees the code or decides whether it matched.
"""
import re
import secrets
import unicodedata

LENGTH = 4

WORDS = {
    "0": "zero shunya shoonya shunye sunya sifar sifr शून्य शुन्य जीरो ज़ीरो सिफ़र सिफर",
    "1": "one ek aik एक",
    "2": "two do doo दो",
    "3": "three teen tin तीन",
    "4": "four char chaar chār चार",
    "5": "five paanch panch paach panc pach पांच पाँच पाच",
    "6": "six chhe chhah chah che cheh chhai chhey chhe छह छः छे छै छेह",
    "7": "seven saat sat सात",
    "8": "eight aath aat ath आठ",
    "9": "nine nau nao naw नौ",
}
# Hindi says the code in pairs too: "chauntees chhappan" is 3456.
PAIRS = {
    "10": "das दस", "11": "gyarah gyara igyarah ग्यारह", "12": "barah bara बारह", "13": "terah tera तेरह",
    "14": "chaudah chauda चौदह", "15": "pandrah pandra पंद्रह पन्द्रह", "16": "solah sola सोलह",
    "17": "satrah satra सत्रह", "18": "atharah athara अठारह", "19": "unnis unis उन्नीस",
    "20": "bees बीस", "21": "ikkis इक्कीस", "22": "bais baees बाईस", "23": "teis teyis तेईस",
    "24": "chaubis चौबीस", "25": "pachchis pachis पच्चीस", "26": "chhabbis छब्बीस", "27": "sattais सत्ताईस",
    "28": "atthais athais अट्ठाईस अठ्ठाईस", "29": "untis उनतीस", "30": "tees तीस", "31": "iktis इकतीस इकत्तीस",
    "32": "battis बत्तीस", "33": "taintis tetis तैंतीस तेंतीस", "34": "chautis chauntis चौंतीस चौतीस",
    "35": "paintis pentis पैंतीस", "36": "chhattis छत्तीस", "37": "saintis सैंतीस", "38": "artis adtis अड़तीस",
    "39": "untalis उनतालीस", "40": "chalis चालीस", "41": "iktalis इकतालीस", "42": "bayalis बयालीस",
    "43": "taintalis tentalis तैंतालीस तेंतालीस", "44": "chavalis chauvalis चवालीस चौवालीस", "45": "paintalis pentalis पैंतालीस",
    "46": "chhiyalis छियालीस", "47": "saintalis सैंतालीस", "48": "artalis adtalis अड़तालीस", "49": "unchas उनचास",
    "50": "pachas पचास", "51": "ikyavan इक्यावन", "52": "bavan बावन", "53": "tirpan tirepan तिरपन तिरेपन",
    "54": "chauvan चौवन", "55": "pachpan पचपन", "56": "chhappan छप्पन", "57": "sattavan सत्तावन",
    "58": "atthavan athavan अट्ठावन अठ्ठावन", "59": "unsath उनसठ", "60": "saath साठ", "61": "iksath इकसठ",
    "62": "basath बासठ", "63": "tirsath तिरसठ", "64": "chausath chaunsath चौंसठ चौसठ", "65": "painsath pensath पैंसठ",
    "66": "chhiyasath छियासठ", "67": "sadsath sarsath सड़सठ", "68": "arsath adsath अड़सठ", "69": "unhattar उनहत्तर",
    "70": "sattar सत्तर", "71": "ikhattar इकहत्तर", "72": "bahattar बहत्तर", "73": "tihattar तिहत्तर",
    "74": "chauhattar चौहत्तर", "75": "pachhattar पचहत्तर", "76": "chhihattar छिहत्तर", "77": "satattar सतहत्तर",
    "78": "athattar अठहत्तर", "79": "unasi unyasi उन्यासी उनासी", "80": "assi अस्सी", "81": "ikyasi इक्यासी",
    "82": "bayasi बयासी", "83": "tirasi तिरासी", "84": "chaurasi चौरासी", "85": "pachasi पचासी",
    "86": "chhiyasi छियासी", "87": "sattasi सत्तासी", "88": "atthasi अट्ठासी अठ्ठासी", "89": "navasi नवासी",
    "90": "nabbe नब्बे", "91": "ikyanve इक्यानवे", "92": "banve बानवे", "93": "tiranve तिरानवे",
    "94": "chauranve चौरानवे", "95": "pachanve पचानवे", "96": "chhiyanve छियानवे", "97": "sattanve सत्तानवे",
    "98": "atthanve अट्ठानवे", "99": "ninyanve निन्यानवे",
}

# English pairs: "thirty four fifty six" is 3456.
ENGLISH = {
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen", "15": "fifteen", "16": "sixteen",
    "17": "seventeen", "18": "eighteen", "19": "nineteen", "20": "twenty", "30": "thirty", "40": "forty fourty",
    "50": "fifty", "60": "sixty", "70": "seventy", "80": "eighty", "90": "ninety",
}
TENS = {"twenty", "thirty", "forty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety"}

# Waits, not tries: he's opening the app or looking for the code. Matched as the start of a word.
WAIT = ("minut", "minat", "mint", "sec", "sekand", "ruk", "wait", "hold", "dekh", "khol", "aay", "aaya", "aya", "aagaya",
        "abhi", "मिन", "सेक", "रुक", "देख", "खोल", "आय", "आई", "आए", "अभी", "वेट")
# A bare "haan" or "ji" to the code line means he's about to read it.
ACK = {"haan", "han", "ha", "ji", "jee", "ok", "okay", "acha", "achha", "accha", "theek", "thik", "hai", "hmm",
       "हाँ", "हां", "हा", "जी", "ओके", "अच्छा", "ठीक", "है", "हम्म"}


# He won't give the code, or wants to know who's asking first. A fair answer to a call
# asking for a code: respected at once, never asked again.
REFUSE = ("nahi bataunga", "nahi bataoonga", "nahin bataunga", "nhi bataunga", "nahi bataungi", "nahi batata",
          "kyun bataun", "kyu bataun", "kyon bataun", "kyun batau", "kyu batau", "nahi dunga", "nahi doonga",
          "nahi dungi", "aap kaun ho", "ap kaun ho", "pehle batao", "pahle batao", "won't tell", "will not tell",
          "not telling", "why should i", "नहीं बताऊंगा", "नहीं बताउंगा", "नहीं बताऊंगी", "क्यों बताऊं", "क्यूं बताऊं",
          "क्यों बताऊ", "नहीं दूंगा", "नहीं दूंगी", "आप कौन हो", "आप कौन हैं", "पहले बताओ", "पहले बताइए")


def _plain(text):
    return (text or "").lower().replace("\u0902", "").replace("\u0901", "").replace("\u093c", "")


def spoken(text):
    """His words, lowercased and spaced one way, with a space at the end, for matching phrases."""
    return " ".join(_tokens(_plain(text))) + " "


def refused(text):
    """True when he declines to give the code or asks who's calling first."""
    return any(spoken(phrase) in spoken(text) for phrase in REFUSE)


def _key(token):
    """One spelling for the many: "chauntees" and "chautis", "chhappan" and "chappan"."""
    if not token.isascii():
        return token.replace("\u0902", "").replace("\u0901", "").replace("\u093c", "")
    token = token.replace("ee", "i").replace("oo", "u").replace("w", "v")
    return "".join(c for i, c in enumerate(token) if i == 0 or c != token[i - 1])


DIGIT = {_key(word): d for d, words in (WORDS | PAIRS | ENGLISH).items() for word in words.split()}

SPLIT = re.compile(r"[\s,.;:!?\-–—/|।॥()\"'“”‘’]+")


def new():
    return f"{secrets.randbelow(9000) + 1000}"


def _token_digits(token):
    if _key(token) in DIGIT:
        return DIGIT[_key(token)]
    digits = []
    for c in token:
        if unicodedata.category(c) != "Nd":
            return None
        digits.append(str(unicodedata.digit(c)))
    return "".join(digits) or None


def _runs(text):
    runs, run, tens = [], "", False
    for token in _tokens(text):
        digits = _token_digits(token)
        if digits is None:
            if run:
                runs.append(run)
            run = ""
        elif tens and len(digits) == 1 and digits != "0":
            run = run[:-1] + digits
        else:
            run += digits
        tens = digits is not None and token in TENS
    if run:
        runs.append(run)
    # the code said twice in a row comes in as one run of 8
    return [r[:LENGTH] if len(r) == 2 * LENGTH and r[:LENGTH] == r[LENGTH:] else r for r in runs]


def _tokens(text):
    return [t for t in SPLIT.split((text or "").lower()) if t]


def read(text):
    """The code in his reply as a digit string, or None if no code could be read.

    He might say it as numerals ("3456", "34 56", "३४५६"), as words ("teen chaar
    paanch chhe", "तीन चार पांच छह"), in pairs ("chauntees chhappan") or twice.
    Words like "do" (give) or "ek" (a) also count as digits, so the code is the one
    run of number tokens that comes to 4 digits.
    """
    runs = _runs(text)
    fits = {r for r in runs if len(r) == LENGTH}
    if len(fits) == 1:
        return fits.pop()
    joined = "".join(runs)
    if not fits and len(joined) == LENGTH:
        return joined
    return joined or None


def waiting(text):
    """True when the reply asks him to be given time: silence, "ek minute", "ruko, app khol raha hoon",
    a bare "haan". A reply with a 4-digit code in it is never a wait."""
    if any(len(r) == LENGTH for r in _runs(text)):
        return False
    tokens = _tokens(text)
    if not tokens:
        return True
    return all(t in ACK for t in tokens) or any(t.startswith(WAIT) for t in tokens)


def check(text, code):
    """(what was read, the rule) for his reply to the code line. The rule is "verified",
    "wait" when he needs time, "failed: declined" when he won't give it, or the identity
    rule of a wrong or missing code."""
    got = read(text)
    if got == code:
        return got, "verified"
    if refused(text):
        return got, "failed: declined"
    if waiting(text):
        return None, "wait"
    if got is None:
        return None, "failed: no code"
    return got, "failed: wrong code"
