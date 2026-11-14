#!/usr/bin/env python3
"""Every ``D07 §15.5``-style cross-reference names a section that exists.

Chat-13. The two worst defects the project has found in its documents -- the D10
claim in chat-11 and the D09 claim in chat-12 -- were both one document
contradicting *another document*. Neither the code nor a single document was
wrong on its own; the pair was. Nothing tested that class.

This is the cheap half of that class: a reference is unresolved if the target
document exists and has no heading whose number equals, extends, or contains the
cited number. A dangling reference is how a false claim travels -- D09 cited D07
§15.5 for an obligation §15.5 does not contain, and the citation made it read as
authoritative.

Headings are matched in three spellings because this docket uses all three:
``## 4.2``, ``## Part 4`` and ``## Section 4``.

Usage:
    python3 -I tools/check_cross_refs.py [docket-dir]

Exit 0 clean, 1 unresolved references, 2 docket dir missing.
"""
import glob
import os
import re
import sys

DOC_ID = re.compile(r"\b(A[12]|B0[1-5]|C0[12]|D0[0-9]|D1[0-4]|F0[0-9]|F1[0-3])\b")
REF = re.compile(
    r"\b((?:A[12]|B0[1-5]|C0[12]|D0[0-9]|D1[0-4]|F0[0-9]|F1[0-3]))"
    r"\s*(?:§|Part\s+|Section\s+)?\s*([0-9]+(?:\.[0-9]+)?)"
)
HEAD = re.compile(r"^#{2,6}\s+(?:Part|Section|Rule)?\s*([0-9]+(?:\.[0-9]+)*)", re.M)


def headings(text):
    return {m.group(1) for m in HEAD.finditer(text)}


def _segments(number):
    """``"4.5a"`` -> ``["4", "5a"]``. Letters stay attached to their segment so
    ``4.5`` can be recognised as the parent of ``4.5a``."""
    return number.split(".")


def _segment_matches(cited_seg, head_seg):
    """A cited segment matches a heading segment when equal, or when the heading
    carries a letter suffix -- ``5`` against ``5a``."""
    if cited_seg == head_seg:
        return True
    return head_seg[:-1] == cited_seg and head_seg[-1:].isalpha()


def resolves(cited, available):
    """A cited number resolves when a heading is it, extends it, or is extended by it.

    Compared **segment by segment**, never by raw string prefix. The first
    version of this function used ``cited.startswith(h)`` and so reported
    ``14.7`` as resolving against a heading numbered ``1`` -- the guard passed
    the injected mutation it existed to catch, which is the exact defect
    chat-12's audit found three of.
    """
    cited_segs = _segments(cited)
    for head in available:
        if not head:
            continue
        head_segs = _segments(head)
        n = min(len(cited_segs), len(head_segs))
        if all(_segment_matches(cited_segs[i], head_segs[i]) for i in range(n)):
            return True
    return False


def main(argv):
    docket = argv[1] if len(argv) > 1 else "client-assets/MASTER-BRIEF-DOCKET"
    if not os.path.isdir(docket):
        sys.stderr.write("no such docket directory: %s\n" % docket)
        return 2
    docs = {}
    for path in glob.glob(os.path.join(docket, "*.md")):
        stem = os.path.basename(path)
        m = DOC_ID.match(stem)
        if m:
            docs[m.group(1)] = path
    targets = {k: headings(open(p, encoding="utf-8").read()) for k, p in docs.items()}
    unresolved = []
    for k, path in sorted(docs.items()):
        text = open(path, encoding="utf-8").read()
        for m in REF.finditer(text):
            ref, cited = m.group(1), m.group(2)
            if ref == k or ref not in targets:
                continue
            if not resolves(cited, targets[ref]):
                unresolved.append((k, ref, cited))
    if not unresolved:
        print("0 unresolved cross-references across %d documents" % len(docs))
        return 0
    for k, ref, cited in sorted(set(unresolved)):
        print("%s cites %s §%s -- no such heading" % (k, ref, cited))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
