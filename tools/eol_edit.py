#!/usr/bin/env python3
"""Byte-exact find/replace that preserves whatever line endings a file already uses.

Every docket edit in this project has to survive one trap: the working tree mixes
CRLF and LF, and a naive text round-trip rewrites every ending in the file. That
turned a one-line fix into a 167-line diff in chat-9 and a 1,248-line one in
chat-3. Read the bytes, replace in bytes, write the bytes back, and the endings
are whatever they were.

Usage:
    python3 -I tools/eol_edit.py <file> <old-file> <new-file>
    python3 -I tools/eol_edit.py <file> --show-ending

Old and new text are read from their own files so the caller never has to worry
about shell quoting. Newlines in those files are matched against EITHER ending in
the target, because the caller writes plain lines and cannot know which the
target holds.

Exit codes: 0 changed, 1 no match (nothing written), 2 matched more than once
(nothing written -- an ambiguous edit is refused, not guessed).
"""
import sys


def normalize(blob: bytes) -> bytes:
    return blob.replace(b"\r\n", b"\n")


def main(argv):
    if len(argv) == 3 and argv[2] == "--show-ending":
        data = open(argv[1], "rb").read()
        crlf = data.count(b"\r\n")
        lf = data.count(b"\n") - crlf
        print(f"CRLF={crlf} LF_ONLY={lf}")
        return 0
    if len(argv) != 4:
        sys.stderr.write(__doc__)
        return 3

    path, old_path, new_path = argv[1], argv[2], argv[3]
    raw = open(path, "rb").read()
    old = normalize(open(old_path, "rb").read()).rstrip(b"\n")
    new = normalize(open(new_path, "rb").read()).rstrip(b"\n")

    # Detect the dominant ending and use it for the replacement text.
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    ending = b"\r\n" if crlf > lf else b"\n"
    new = new.replace(b"\n", ending)

    # Match the old text under either ending by normalising a copy and mapping
    # offsets back. Simpler and safer: try the exact bytes first, then the
    # all-CRLF and all-LF variants of the search text.
    candidates = [old, old.replace(b"\n", b"\r\n")]
    hits = [c for c in candidates if raw.count(c) == 1]
    if not hits:
        total = sum(raw.count(c) for c in candidates)
        if total == 0:
            sys.stderr.write("no match: the old text is not present\n")
            return 1
        sys.stderr.write(f"ambiguous: {total} matches, refusing to guess\n")
        return 2

    out = raw.replace(hits[0], new, 1)
    with open(path, "wb") as fh:
        fh.write(out)
    label = "CRLF" if ending == b"\r\n" else "LF"
    print(f"changed 1 occurrence in {path} (ending={label})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
