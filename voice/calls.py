"""One live call per shop: flow.run in a thread, its listener fed from the board.

The listener speaks the line, then waits on the call's queue. A reply from the
page (audio or typed) is heard and read here, and its Answer goes in the queue.
Nothing in time means "no answer". A reply that reads as no answer, or none in
time, gets the line said once more. The code lines are never shown to the AI:
flow checks them in code, and waits for the code itself.
"""
import os
import queue
import threading
import time

from ai import reader
from settled import codes, flow, log, records
from settled.models import Answer, CallState

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
        self.line = None
        self.code = None
        self.progress = CallState()
        self.audio = None
        self.waiting = False
        self.hearing = False
        self.heard_at = float("-inf")
        self.done = False
        self.problem = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            flow.run(self.shop_id, self._listen, self.progress)
        except Exception as e:
            self.problem = f"call stopped: {type(e).__name__}"
        finally:
            with self.lock:
                self.waiting = False
                self.done = True

    def _listen(self, shop, said, wait=True):
        language = script.LANGUAGES[self.language]
        line = script.say(self.language, said, shop)
        english = script.english(said, shop)
        try:
            audio = sarvam.speak(line, language["code"], language["voice"])
            length = sarvam.wav_seconds(audio)
            problem = None
        except Exception as e:
            audio, length = None, len(line) / 12
            problem = f"no voice ({type(e).__name__}), read the line out"

        with self.lock:
            self.seq += 1
            self.said, self.line, self.code = english, said, language["code"]
            self.audio, self.problem = audio, problem
            self.waiting = wait
            seq = self.seq
        if not wait:
            time.sleep(length + 1)
            return None
        until = time.monotonic() + length + LISTEN

        # the code step does its own waiting in flow, so its lines are never said again here
        again = 0 if said in script.CODE_LINES else 1
        while True:
            try:
                got, answer = self.replies.get(timeout=max(0.2, until - time.monotonic()))
                if got != seq:
                    continue
                if answer.kind != "no answer" or not again:
                    break
            except queue.Empty:
                with self.lock:
                    if self.hearing:
                        continue
                    if time.monotonic() < self.heard_at + LISTEN:
                        until = self.heard_at + LISTEN
                        continue
                answer = Answer("no answer")
                if not again:
                    break
            again -= 1
            log.add(shop.id, "answered", said=english, heard=answer.words, read_as="no answer",
                    reason="nothing clear, said the line again")
            with self.lock:
                self.seq += 1
                seq = self.seq
                self.waiting = True
            until = time.monotonic() + length + LISTEN
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
            said, line, code = self.said, self.line, self.code
        try:
            if audio is not None:
                text = sarvam.hear(audio, ctype, code, seconds)
            elif not (text or "").strip():
                raise ValueError("heard nothing")
            if not text.strip():
                answer = Answer("no answer", "")
            elif line in script.CODE_LINES:
                answer = Answer("unsure", text)
            else:
                answer = reader.read(text, said)
            if audio is not None:
                answer.audio, answer.ctype = audio, ctype
            self.replies.put((seq, answer))
            if line in script.CODE_LINES:
                got, rule = codes.check(text, self.progress.code)
                read_as = "wait" if rule == "wait" else got or "no code"
            else:
                read_as = answer.kind
            return {"heard": text, "read_as": read_as}
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
                "step": self.progress.step,
                "app_code": self.progress.code,
                "recording": self.progress.recording,
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
        if log.settled(shop_id):
            raise Busy("rent already settled for this shop, so there is no second call. Run try.py reset to start over")
        call = _calls[shop_id] = Call(shop_id, language)
    call.thread.start()
    return call


def get(shop_id):
    return _calls.get(shop_id)
