#!/bin/bash
# Every path below is derived at runtime. The previous version hardcoded one
# session's mount (/sessions/intelligent-admiring-cori) and one chat's
# transcript ids, so it only ever passed in the session that wrote it — a gate
# that cannot run in another session is not a gate.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
# A fresh cache dir per run: /tmp/pyc may exist owned by another user, and a
# stale cache dir is the same class of trap as a stale suite output file.
PYC=$(mktemp -d /tmp/gate-pyc.XXXXXX) || PYC=/tmp
export PYTHONPYCACHEPREFIX="$PYC"
CLEAN="rm -rf '$PYC'"
trap 'eval "$CLEAN"' EXIT

# IMPORTANT: the suite runs under `-I`, and `-I` sets sys.pycache_prefix to
# None, DISCARDING PYTHONPYCACHEPREFIX. Exporting the env var above therefore
# does nothing for an isolated run — bytecode goes to the source tree, which is
# how eleven .pyc files appeared under backend/ and tests/ during chat-8's
# close. Pass -X pycache_prefix= explicitly. Verified both ways, as in
# assets/mutation-ingest-auth.py.
PYC_FLAG="-X pycache_prefix=$PYC"

# The session mount is this repo's parent two levels up: <mount>/AxiomDynamics.
MOUNT="$(cd .. && pwd)"
LOGDIR="$MOUNT/.claude/projects/session"
FAIL=0
ok(){ printf '  PASS  %s\n' "$1"; }
no(){ printf '  FAIL  %s  <-- %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

echo "1. REPOSITORY"
[ "$(git status --porcelain | wc -l)" -eq 0 ] && ok "working tree clean" || no "working tree" "uncommitted changes"
git fsck --no-dangling >/dev/null 2>&1 && ok "no git object corruption" || no "git fsck" "errors"

echo "2. TEST SUITE (one run, output cached)"
# A fixed /tmp path can be owned by another user and unwritable — the redirect
# then fails, tail reads a PREVIOUS run's file, and the gate passes on a stale
# number. That happened on chat-8's first close (it read chat-7's 346 while the
# real suite was 359). The output file must be created fresh and be readable.
SUITE_OUT=$(mktemp /tmp/gate-suite.XXXXXX) || { no "suite output" "mktemp failed"; SUITE_OUT=/dev/null; }
trap 'rm -rf "$PYC" "$SUITE_OUT"' EXIT
timeout 550 python3 -I $PYC_FLAG tests/run_tests.py > "$SUITE_OUT" 2>&1
RC=$?
LAST=$(tail -1 "$SUITE_OUT")
echo "     $LAST"
[ "$RC" -eq 0 ] && [ -s "$SUITE_OUT" ] || no "suite" "runner exited $RC (see $SUITE_OUT)"
echo "$LAST" | grep -qE "^[0-9]+ passed, 0 failed$" && ok "suite green: $LAST" || no "suite" "$LAST"

echo "3. EVERY MODULE COUNTED"
MODS=$(ls tests/test_*.py | wc -l)
SECT=$(grep -c '^== test_' "$SUITE_OUT")
[ "$MODS" -eq "$SECT" ] && ok "all $MODS modules reached" || no "module coverage" "$SECT/$MODS"
awk '/^== test_/{s=$2;next} /^PASS/{c[s]++} END{for(k in c) if(c[k]==0) print k}' "$SUITE_OUT" | while read -r m; do no "$m" "zero tests"; done
echo "     per-module: $(awk '/^== test_/{s=$2;next} /^PASS/{c[s]++} END{n=0;for(k in c)n++;print n" modules with PASS lines"}' "$SUITE_OUT")"

echo "4. TRANSCRIPTS"
# The live log is whichever .jsonl in the session dir was modified last — the
# id changes every chat, and hardcoding it is what broke this gate once.
L=$(ls -t "$LOGDIR"/*.jsonl 2>/dev/null | head -1)
if [ -z "$L" ]; then
  no "live log" "no .jsonl under $LOGDIR"
else
  ok "live log found: $(basename "$L") ($(wc -l < "$L") lines)"
  # The newest committed snapshot must be an exact prefix of the live log: the
  # snapshot is taken mid-chat, then the chat runs on. A mismatch means the
  # snapshot was taken from a different session or edited after the fact.
  SNAP=$(ls -t project-logs/transcripts/raw/*chat-*.jsonl 2>/dev/null | head -1)
  N=$(wc -l < "$SNAP")
  head -n "$N" "$L" | cmp -s - "$SNAP" \
    && ok "$(basename "$SNAP") is an exact $N-line prefix of the live log" \
    || no "snapshot prefix" "$(basename "$SNAP") is not a prefix of the live log"
fi
python3 -c "
import json,glob
bad=0; n=0
for p in glob.glob('project-logs/transcripts/raw/*.jsonl'):
    for i,l in enumerate(open(p,encoding='utf-8'),1):
        if l.strip():
            try: json.loads(l)
            except Exception as e:
                bad+=1; print('%s:%d %s' % (p,i,e))
            n+=1
print('%d lines, %d unparseable' % (n,bad))
raise SystemExit(1 if bad else 0)
" && ok "every raw snapshot parses as JSONL" || no "JSONL" "unparseable line"
# The readable extraction must exist and carry the operator's own turns.
NEWEST_CHAT=$(ls project-logs/transcripts/*chat-*.md 2>/dev/null | sed 's/.*chat-\([0-9]*\).*/\1/' | sort -n | tail -1)
MD=$(ls project-logs/transcripts/*chat-$NEWEST_CHAT*.md 2>/dev/null | head -1)
[ -n "$MD" ] && [ "$(grep -c '^## USER' "$MD")" -ge 1 ] \
  && ok "readable transcript for chat-$NEWEST_CHAT: $(grep -c '^## USER' "$MD") user turns" \
  || no "readable transcript" "no chat-$NEWEST_CHAT .md with user turns"

echo "5. CODE INTEGRITY"
python3 -I $PYC_FLAG -c "import sys;sys.path.insert(0,'.');from backend import ingest_auth,key_directory,accounts,ingest,attribution" && ok "backend modules import" || no "imports" "failed"
! grep -qE "^(from|import) backend" tools/verify_key_directory.py && ok "standalone verifier imports no backend code" || no "verifier" "imports backend"
for f in tools/verify_key_directory.py tools/publish_key_directory.py tools/seed_demo_collector.py; do test -f "$f" || no "missing tool" "$f"; done
ok "all documented tools present"
# Bytecode must not reach the source tree. Tracked .pyc is a repo-hygiene defect
# (B01 §7 item 9) and an ignored __pycache__ in the working tree is the symptom
# of a cache prefix that is not being honoured.
STRAY=$(find backend tests tools -name "*.pyc" -newermt "-15 minutes" 2>/dev/null | wc -l)
[ "$STRAY" -eq 0 ] && ok "the suite wrote no bytecode into the source tree" \
  || no "pycache leak" "$STRAY fresh .pyc files under the source tree"
! git ls-files | grep -qE "\.pyc$" && ok "no .pyc is tracked" || no "tracked bytecode" "a .pyc is committed"

echo "6. DOCUMENTATION"
! grep -rq "endpoint has no authentication" client-assets/ && ok "no doc claims unauthenticated ingest" || no "stale ingest claim" "found"
! grep -rq "has no authentication" client-assets/ && ok "no doc claims server has no auth" || no "stale server claim" "found"
# The docx must match its OWN generator, not a stage number frozen at chat-7.
# Asserting "Stage 11 is present" passed while the document was a stage behind
# and would keep passing forever. Compare against the generator's top stage.
GEN_TOP=$(grep -oE 'H2\("Stage [0-9]+' project-logs/build-history-summary.js | grep -oE '[0-9]+' | sort -n | tail -1)
python3 -c "
import zipfile,re,sys
top=int(sys.argv[1])
t=re.sub(r'<[^>]+>','',zipfile.ZipFile('project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx').read('word/document.xml').decode('utf-8'))
missing=[s for s in range(1,top+1) if ('Stage %d ' % s) not in t]
assert not missing, 'docx is missing stage(s) %s that the generator defines' % missing
assert '**' not in t and chr(96) not in t, 'literal markdown markup in the docx'
print('docx carries stages 0-%d' % top)
" "$GEN_TOP" && ok "build history docx matches its generator (through Stage $GEN_TOP), no literal markup" || no "docx" "does not match generator or carries markup"
# The generator itself lags the newest chat. That is a real outstanding task, so
# it is printed loudly every close rather than left to be discovered. The test is
# whether the generator mentions the newest chat anywhere, not whether some
# stage counter has passed it — stage numbers and chat numbers do not align.
NEWEST_CHAT_DIR=$(ls -d project-logs/chat-*/ 2>/dev/null | grep -oE 'chat-[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
if [ -n "$NEWEST_CHAT_DIR" ] && ! grep -q "chat-$NEWEST_CHAT_DIR" project-logs/build-history-summary.js; then
  printf '  NOTE  the build-history generator has no Stage for chat-%s —\n' "$NEWEST_CHAT_DIR"
  printf '        the docx is consistent with its generator but one stage behind the record.\n'
  printf '        Outstanding task: add Stage 12 and rebuild.\n'
fi

echo
[ $FAIL -eq 0 ] && { echo "GATE PASSED — 0 failures"; exit 0; } || { echo "GATE FAILED — $FAIL failure(s)"; exit 1; }
