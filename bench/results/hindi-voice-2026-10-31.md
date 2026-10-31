# Hindi replies in real voices, 2026-10-31

31 replies a kirana owner might give (`bench/audio/hindi-real/manifest.json`), spoken by Bulbul v3 in eight Hindi voices (aditya, rahul, amit, rohan, priya, ritu, neha, kavya), plus one clip with only shop noise and nobody speaking. Each clip was sent through the real voice path (board on a spare port, Saaras v4 speech-to-text, the Sarvam reader, flow.py, rules.py) in five versions:

- clean: 16 kHz
- n20, n10, n5: crowd noise mixed in at 20, 10 and 5 dB SNR. The crowd is other people's speech played backwards and overlapped, with hall echo and hiss
- phone: band-limited to 300–3400 Hz, 8 kHz, squeezed through mu-law and back

The clip answers the line named in the manifest. The other line gets a typed reply ("हाँ जी, लिया था" to the ask, "हाँ, पक्का" to the read-back), and after a na the call times out. So a misread first reply that comes out haan ends in a charge, which is what "charged wrongly" counts. Time runs from sending the reply to getting the reader's decision back (speech-to-text plus reader).

Re-run: `python bench/hindi_voice.py build`, then start a board with its own `BOARD_PORT` and `SETTLED_DB`, then `BOARD_PORT=… python bench/hindi_voice.py run --tag x --cap <total ₹>`, then `python bench/hindi_voice.py report x`.

## Results

| audio | before: right | before: charged wrongly | after: right | after: charged wrongly | after: median / worst time |
|---|---|---|---|---|---|
| clean | 29/30 | 1 | 31/31 | 0 | 0.68 s / 0.81 s |
| crowd 20 dB | not run | | 4/4 (short set) | 0 | 0.56 s / 0.56 s |
| crowd 10 dB | 29/30 | 1 | 4/4 (short set) | 0 | 0.64 s / 0.88 s |
| crowd 5 dB | 29/30 | 1 | 31/31 | 0 | 0.69 s / 1.40 s |
| phone | 29/30 | 1 | 31/31 | 0 | 0.70 s / 1.10 s |

Before, the median time was 0.64–0.70 s and the worst was 1.67 s. No honest yes went uncharged in any run.

Two caveats. In the before runs the crowd only talked for the first 8 s of the noise bed, so most n10 and n5 clips had hiss rather than voices. The after n5 run has voices across the whole clip. The short set for 20 and 10 dB is `hmm`, `nobody`, `haan-bas` and `haan-haan`, run after the first fix. The full 20 and 10 dB runs were skipped to stay inside the money.

"After" here means with the fixes below applied on a test board. They are not on main (see the end).

## What failed

1. **"hmm" got charged, in every audio version.** Saaras writes a lone "hmm" as "हम।", and the reader read that as a clear haan. With a haan at the read-back, that's ₹125 charged on a grunt. This was the only wrong outcome in 120 before-runs.
2. **Shop noise with nobody speaking, over the phone line, got charged.** Saaras made up "आप जी।" from the crowd and the reader read it as haan. Clean, 20, 10 and 5 dB versions of the same noise came back empty.
3. **An empty transcript stalls the call.** Today `calls.reply` answers 422 "heard nothing" and the call waits another `SETTLED_LISTEN_SECONDS` (20 s by default) before it counts as no answer. Nobody says the line again.
4. Everything else held up: clear and casual yes, "haan haan", haan with a but, na with a reason, confused, questions, someone else picking up, and changing his mind at the read-back. Saaras mostly heard the words exactly, even at 5 dB. Its slips were small ("लिया तो था" heard as "रिया/जिया/दिया तो था", "हाँ लिया था" heard as "खा लिया था") and none of them changed an outcome.

## Fixes for the v2 build

These were tested on the spare board, then taken back out of main's working tree, because the call flow is being rewritten on v2.

1. **Say the line once more when a reply reads as no answer** (`voice/calls.py`). When the transcript is empty, or the reader returns no answer, bump `seq` and play the same line again, once. Only a second no answer counts. An empty audio transcript becomes a no-answer reply, not a 422. A typed empty reply still gets the 422. The board page already plays any new `seq`. Result: the nobody clip ends in about 0.7 s (two tries) instead of a 20 s wait, and a "hmm" gets a second chance to be a real answer.
   ```diff
   +        again = 1
            while True:
                try:
                    got, answer = self.replies.get(timeout=max(0.2, until - time.monotonic()))
   -                if got == seq:
   +                if got == seq and answer.kind == "no answer" and again:
   +                    again -= 1
   +                    with self.lock:
   +                        self.seq += 1
   +                        seq = self.seq
   +                    until = time.monotonic() + length + LISTEN
   +                elif got == seq:
                        break
   ...
                if audio is not None:
                    text = sarvam.hear(audio, ctype, code, seconds)
   -            if not (text or "").strip():
   +            elif not (text or "").strip():
                    raise ValueError("heard nothing")
   ```
   One gap: the reply that triggered the re-ask isn't logged, because flow.py only logs the answer the listener returns. v2 should log it.
2. **Tell the reader that a filler is never haan** (`ai/prompt_hi.md`). This fixed failure 1 in all five audio versions:
   ```
   - no answer: empty, noise, or only a filler sound with no words (hmm, हम्म, उम्म; a lone "हम" is a transcribed hmm). A filler is never haan.
   Ask | हम। -> {"kind":"no answer","speaker":"shopkeeper","reason":null,"plan":null}
   ```
3. **Tell the reader that a few words answering nothing are no answer** (`ai/prompt_hi.md`). I tested this wording, and it fixed failure 2:
   ```
   Also a few words that answer nothing, like a noisy transcript would give ("आप जी", "वो तो"). These are never haan.
   ```
   It reaches too far. "हाँ जी बोलिए" (which was a question) and "अभी ग्राहक है, बाद में बात करो" (call later, which was unsure) now read as no answer too. They still end held, after a re-ask, but the "call later" reason no longer reaches the person who follows up. v2 should word it narrower, for example "one or two words with no yes, no or question in them". Spot checks with the tested wording: "जी", "हा", "हाँ", "ठीक है" still read haan, and "हेलो?" reads no answer.
4. **Not tried: Saaras key terms.** Key terms only nudge recognition of names and nouns. None of the failures were a misheard noun, and nudging toward हाँ would push noise toward yes, which is exactly the wrong direction for money. Leave them out unless real calls mishear "साउंडबॉक्स", "पेटीएम" or the salesman's name.
5. **Bench bug in `bench/voice_run.py`.** `/api/log` returns at most 500 rows, so `max(id)` over its first page stops growing once the log passes 500 rows, and the printed rows come from older calls. The fix is to page until empty (`last_id` in `bench/hindi_voice.py`). The before results above were re-graded from the board's database for this reason.

## Money

This pass: ₹14.65 in `bench/cost.log`, from a running total of ₹8.87 to ₹23.52, under the ₹15 limit. Text-to-speech was ₹2.76 (cached under `voice/cache`, so re-runs reuse it). Each full pass over 31 clips in one audio version costs about ₹1.5. Other boards write to the same log. The growth measured around my own runs adds up to ₹14.57, so nearly all of it is this pass.

`python3 bench/run.py --reader typed`: 75/75 match, 0 charged after na or unsure.
