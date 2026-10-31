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
    "5": "five paanch panch paach panc पांच पाँच पाच",
    "6": "six chhe chhah chah che cheh chhai chhey chhe छह छः छे छै छेह",
    "7": "seven saat sat सात",
    "8": "eight aath aat ath आठ",
    "9": "nine nau nao naw नौ",
}
DIGIT = {word: d for d, words in WORDS.items() for word in words.split()}

SPLIT = re.compile(r"[\s,.;:!?\-–—/|।॥()\"'“”‘’]+")


def new():
    return f"{secrets.randbelow(9000) + 1000}"


def _token_digits(token):
    if token in DIGIT:
        return DIGIT[token]
    digits = []
    for c in token:
        if unicodedata.category(c) != "Nd":
            return None
        digits.append(str(unicodedata.digit(c)))
    return "".join(digits) or None


def read(text):
    """The code in his reply as a digit string, or None if no code could be read.

    He might say it as numerals ("3456", "34 56", "३४५६") or as words ("teen chaar
    paanch chhe", "तीन चार पांच छह"). Words like "do" (give) or "ek" (a) also count
    as digits, so the code is the one run of number tokens that comes to 4 digits.
    """
    runs, run = [], ""
    for token in SPLIT.split((text or "").lower()):
        digits = _token_digits(token) if token else None
        if digits is None:
            if run:
                runs.append(run)
            run = ""
        else:
            run += digits
    if run:
        runs.append(run)

    fits = [r for r in runs if len(r) == LENGTH]
    if len(fits) == 1:
        return fits[0]
    joined = "".join(runs)
    if not fits and len(joined) == LENGTH:
        return joined
    return joined or None


def check(text, code):
    """(what was read, the identity rule) for his reply to the code line."""
    got = read(text)
    if got is None:
        return None, "failed: no code"
    if got == code:
        return got, "verified"
    return got, "failed: wrong code"
