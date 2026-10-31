"""Say every line once for the shops Settled calls, so calls play from voice/cache.

    python -m voice.warm hi [--dry]
"""
import sys

from settled import records, rules
from voice import sarvam, script


def lines(language):
    seen = []
    for shop_id in records.shop_ids():
        shop = records.load(shop_id)
        if rules.before_call(shop).outcome != "call":
            continue
        for line in script.LINES:
            text = script.say(language, line, shop)
            if text not in seen:
                seen.append(text)
    return seen


def main(args):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    language = args[0] if args else "hi"
    l = script.LANGUAGES[language]
    texts = lines(language)
    print(f"{len(texts)} lines, {sum(map(len, texts))} characters, about ₹{sum(map(len, texts)) * sarvam.TTS_PER_CHAR * 1.18:.2f} if none are cached")
    if "--dry" in args:
        return
    for text in texts:
        sarvam.speak(text, l["code"], l["voice"])
        print("cached", text)


if __name__ == "__main__":
    main(sys.argv[1:])
