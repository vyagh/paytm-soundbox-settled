import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = {".venv", "__pycache__", ".git"}


def sources():
    out = {}
    for path in [*ROOT.rglob("*.py"), *ROOT.glob("ai/*.md")]:
        if SKIP.isdisjoint(path.relative_to(ROOT).parts):
            try:
                out[path] = path.stat().st_mtime_ns
            except OSError:
                pass
    return out


def start():
    return subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env={**os.environ, "PYTHONUNBUFFERED": "1"})


def stop(child):
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def main():
    seen = sources()
    child = start()
    try:
        while True:
            time.sleep(1)
            now = sources()
            if now != seen:
                changed = sorted(p.relative_to(ROOT).as_posix() for p in now.keys() ^ seen.keys() | {p for p in now if now.get(p) != seen.get(p)})
                seen = now
                stop(child)
                print(f"restarting server: {', '.join(changed)} changed", flush=True)
                child = start()
    except KeyboardInterrupt:
        pass
    finally:
        stop(child)


if __name__ == "__main__":
    main()
