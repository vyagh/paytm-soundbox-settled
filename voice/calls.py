"""One live call per shop: flow.run in a thread, its listener fed from the board.

The listener speaks the line, then waits on the call's queue. A reply from the
page (audio or typed) is heard and read here, and its Answer goes in the queue.
Nothing in time means "no answer".
"""
import os
import queue
import threading
import time

from ai import reader
from settled import flow, records
from settled.models import Answer

from . import sarvam, script

LISTEN = float(os.environ.get("SETTLED_LISTEN_SECONDS") or 20)


class Busy(Exception):
    pass


class Call:
    def __init__(self, shop_id, language):
        self.shop_id = shop_id
        self.language = language
        self.lock = threading.Lock()
        self.replies = queue.Queue()
        self.seq = 0
        self.said = None
        self.code = None
        self.audio = None
        self.waiting = False
        self.hearing = False
        self.heard_at = float("-inf")
        self.done = False
        self.problem = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            flow.run(self.shop_id, self._listen)
        except Exception as e:
            self.problem = f"call stopped: {type(e).__name__}"
        finally:
            with self.lock:
                self.waiting = False
                self.done = True

    def _listen(self, shop, said):
        language = script.LANGUAGES[self.language]
        line = language[said]
        try:
            audio = sarvam.speak(line, language["code"], language["voice"])
            length = sarvam.wav_seconds(audio)
            problem = None
        except Exception as e:
            audio, length = None, len(line) / 12
            problem = f"no voice ({type(e).__name__}), read the line out"

        with self.lock:
            self.seq += 1
            self.said, self.code = said, language["code"]
            self.audio, self.problem = audio, problem
            self.waiting = True
            seq = self.seq
        until = time.monotonic() + length + LISTEN

        while True:
            try:
                got, answer = self.replies.get(timeout=max(0.2, until - time.monotonic()))
                if got == seq:
                    break
            except queue.Empty:
                with self.lock:
                    if self.hearing:
                        continue
                    if time.monotonic() < self.heard_at + LISTEN:
                        until = self.heard_at + LISTEN
                        continue
                    answer = Answer("no answer")
                    break
        with self.lock:
            self.waiting = False
        return answer

    def reply(self, seq, text=None, audio=None, ctype="", seconds=0.0):
        with self.lock:
            if not self.waiting or seq != self.seq:
                raise Busy("not waiting for a reply")
            if self.hearing:
                raise Busy("still hearing the last reply")
            self.hearing = True
            said, code = self.said, self.code
        try:
            if audio is not None:
                text = sarvam.hear(audio, ctype, code, seconds)
            if not (text or "").strip():
                raise ValueError("heard nothing")
            answer = reader.read(text, said)
            if audio is not None:
                answer.audio, answer.ctype = audio, ctype
            self.replies.put((seq, answer))
            return {"heard": text, "read_as": answer.kind}
        finally:
            with self.lock:
                self.hearing = False
                self.heard_at = time.monotonic()

    def state(self):
        with self.lock:
            return {
                "active": not self.done,
                "seq": self.seq,
                "said": self.said,
                "voice": self.audio is not None,
                "waiting": self.waiting,
                "hearing": self.hearing,
                "problem": self.problem,
            }


_calls = {}
_lock = threading.Lock()


def start(shop_id, language=None):
    language = language or records.load(shop_id).language
    if language not in script.LANGUAGES:
        raise ValueError(f"no language {language!r}")
    with _lock:
        call = _calls.get(shop_id)
        if call and not call.done:
            raise Busy("a call to this shop is already on")
        call = _calls[shop_id] = Call(shop_id, language)
    call.thread.start()
    return call


def get(shop_id):
    return _calls.get(shop_id)
