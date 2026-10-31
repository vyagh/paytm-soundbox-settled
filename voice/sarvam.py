import base64
import hashlib
import io
import json
import time
import urllib.request
import uuid
import wave
from pathlib import Path

from ai import reader

CACHE = Path(__file__).resolve().parent / "cache"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_MODEL = "bulbul:v3"
STT_MODEL = "saaras:v4"
TIMEOUT = 20

# rupees before 18% GST (docs.sarvam.ai/api/getting-started/pricing, 2026-10-31)
TTS_PER_CHAR = 3 / 1000
STT_PER_SECOND = 0.49 / 60


def cached(text, language_code, voice):
    """Where this line's voice is kept once said."""
    name = hashlib.sha1(f"{TTS_MODEL}|{voice}|{language_code}|{text}".encode("utf-8")).hexdigest()[:16]
    return CACHE / f"{language_code}-{name}.wav"


def speak(text, language_code, voice, fresh=False):
    """WAV bytes for text, from the cache when this line was said before.
    fresh: a line the AI wrote for this turn, spoken each time and never kept."""
    path = cached(text, language_code, voice)
    if not fresh and path.exists():
        return path.read_bytes()

    body = json.dumps({
        "text": text,
        "language_code": language_code,
        "speaker": voice,
        "model": TTS_MODEL,
        "speech_sample_rate": 22050,
    }).encode("utf-8")
    reply, took = _post(TTS_URL, body, "application/json")
    audio = base64.b64decode(reply["audios"][0])
    _cost("tts", len(text) * TTS_PER_CHAR, took, chars=len(text), fresh=fresh)
    if fresh:
        return audio

    CACHE.mkdir(exist_ok=True)
    path.write_bytes(audio)
    return audio


def hear(audio, ctype, language_code, seconds):
    """Transcript of the shopkeeper's reply. seconds is the clip length, for the cost line."""
    boundary = uuid.uuid4().hex
    ext = {"audio/wav": "wav", "audio/x-wav": "wav", "audio/ogg": "ogg"}.get(ctype.split(";")[0], "webm")
    parts = [
        _field(boundary, "model", STT_MODEL),
        _field(boundary, "language_code", language_code),
        (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="reply.{ext}"\r\n'
         f"Content-Type: {ctype.split(';')[0]}\r\n\r\n").encode("utf-8") + audio + b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    reply, took = _post(STT_URL, b"".join(parts), f"multipart/form-data; boundary={boundary}")
    _cost("stt", seconds * STT_PER_SECOND, took, audio_seconds=round(seconds, 2))
    return reply.get("transcript") or ""


def wav_seconds(audio):
    with wave.open(io.BytesIO(audio)) as w:
        return w.getnframes() / w.getframerate()


def _field(boundary, name, value):
    return f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")


def _post(url, body, ctype):
    if reader.spent() >= reader.CAP:
        raise RuntimeError("spend cap reached")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": ctype, "api-subscription-key": reader._key()})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        reader._log({"api": url.rsplit("/", 1)[-1], "error": type(e).__name__, "status": getattr(e, "code", None), "rupees": 0})
        raise
    return reply, round(time.monotonic() - start, 2)


def _cost(api, rupees, took, **extra):
    reader._log({"api": api, **extra, "seconds": took, "rupees": round(rupees * reader.GST, 6)})
