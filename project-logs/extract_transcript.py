#!/usr/bin/env python3
"""
Extract the live session log into the readable transcript + committed raw snapshot.

Three rules, each learned the hard way on chat-3 (see transcripts/README.md):

1. De-duplicate BEFORE writing. The .jsonl appends each assistant message
   several times while streaming; without de-duplication every paragraph and
   tool call appears three or four times. De-dupe by message["id"] and by each
   tool_use block's id.
2. Drop machine-injected `user` messages: skill bodies, compaction summaries and
   slash-command wrappers all arrive with role: user but nobody typed them.
3. Verify the user turns read back as things the user actually said.

Usage: python3 project-logs/extract_transcript.py <source.jsonl> <out.md> <out-raw.jsonl>
"""
import json
import os
import shutil
import sys


def skip_machine_text(text):
    markers = (
        "Base directory for this skill:",
        "This session is being continued from a previous conversation",
        "<local-command",
        "<command-name>",
        "[Request interrupted",
    )
    return any(text.lstrip().startswith(m) or m in text[:400] for m in markers)


def text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n\n".join(p for p in parts if p.strip())


def tool_calls(content):
    out = []
    for block in content or []:
        if not (isinstance(block, dict) and block.get("type") == "tool_use"):
            continue
        name = block.get("name", "tool")
        inp = block.get("input") or {}
        label = ""
        for key in ("command", "description", "file_path", "query", "pattern",
                    "skill", "taskId", "prompt", "url", "path"):
            val = inp.get(key)
            if isinstance(val, str) and val.strip():
                label = val
                break
        if not label:
            if name.endswith("TaskUpdate") and inp.get("taskId"):
                label = "task %s -> %s" % (inp.get("taskId"), inp.get("status", ""))
            else:
                for val in inp.values():
                    if isinstance(val, str) and val.strip():
                        label = val
                        break
        label = " ".join(str(label).split())[:150]
        out.append((name, block.get("id"), label))
    return out


def main(src, out_md, out_raw):
    seen_msgs, seen_blocks = set(), set()
    turns = []

    with open(src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = rec.get("type")
            if role not in ("user", "assistant"):
                continue
            if rec.get("isSidechain"):
                continue
            msg = rec.get("message") or {}
            mid = msg.get("id")
            if mid:
                if mid in seen_msgs:
                    continue
                seen_msgs.add(mid)
            content = msg.get("content")
            text = text_of(content)
            calls = []
            for name, bid, label in tool_calls(content):
                if bid and bid in seen_blocks:
                    continue
                if bid:
                    seen_blocks.add(bid)
                calls.append((name, label))
            if role == "user":
                if not text.strip() or skip_machine_text(text):
                    continue
            if not text.strip() and not calls:
                continue
            turns.append((role, text, calls))

    # Collapse consecutive identical assistant text (streaming artifacts that
    # survived the id de-dupe because they had no id).
    deduped = []
    for role, text, calls in turns:
        if deduped and role == "assistant" and deduped[-1][0] == "assistant" \
                and deduped[-1][1] == text and deduped[-1][2] == calls:
            continue
        deduped.append((role, text, calls))

    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Chat-3\n\n")
        f.write("Extracted %d turns from the raw session log at `%s`. "
                "Tool output is omitted; tool calls are recorded inline.\n\n---\n\n"
                % (len(deduped), os.path.basename(src)))
        for role, text, calls in deduped:
            if role == "user":
                f.write("## USER\n\n" + text.strip() + "\n\n")
            else:
                f.write("## ASSISTANT\n\n")
                if text.strip():
                    f.write(text.strip() + "\n\n")
                for name, label in calls:
                    f.write("[tool: %s] %s\n\n" % (name, label))

    shutil.copyfile(src, out_raw)
    user_turns = [t for r, t, _ in deduped if r == "user"]
    print(f"turns: {len(deduped)}  (user: {len(user_turns)}, assistant: {len(deduped) - len(user_turns)})")
    print(f"raw:   {out_raw}  ({os.path.getsize(out_raw):,} bytes)")
    print("\nUser turns, for verification:")
    for i, t in enumerate(user_turns, 1):
        one = " ".join(t.split())[:110]
        print(f"  {i:2d}. {one}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
