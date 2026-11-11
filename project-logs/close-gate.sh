#!/bin/bash
cd /sessions/intelligent-admiring-cori/mnt/AxiomDynamics
export PYTHONPYCACHEPREFIX=/tmp/pyc
FAIL=0
ok(){ printf '  PASS  %s\n' "$1"; }
no(){ printf '  FAIL  %s  <-- %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

echo "1. REPOSITORY"
[ "$(git status --porcelain | wc -l)" -eq 0 ] && ok "working tree clean" || no "working tree" "uncommitted changes"
git fsck --no-dangling >/dev/null 2>&1 && ok "no git object corruption" || no "git fsck" "errors"

echo "2. TEST SUITE (one run, output cached)"
timeout 550 python3 -I tests/run_tests.py > /tmp/suite.out 2>&1
LAST=$(tail -1 /tmp/suite.out)
echo "     $LAST"
echo "$LAST" | grep -q " 0 failed" && ok "suite green" || no "suite" "$LAST"

echo "3. EVERY MODULE COUNTED"
MODS=$(ls tests/test_*.py | wc -l)
SECT=$(grep -c '^== test_' /tmp/suite.out)
[ "$MODS" -eq "$SECT" ] && ok "all $MODS modules reached" || no "module coverage" "$SECT/$MODS"
awk '/^== test_/{s=$2;next} /^PASS/{c[s]++} END{for(k in c) if(c[k]==0) print k}' /tmp/suite.out | while read -r m; do no "$m" "zero tests"; done
echo "     per-module: $(awk '/^== test_/{s=$2;next} /^PASS/{c[s]++} END{n=0;for(k in c)n++;print n" modules with PASS lines"}' /tmp/suite.out)"

echo "4. TRANSCRIPTS"
L=/sessions/intelligent-admiring-cori/mnt/.claude/projects/session/57c84cfc-bbb2-4f20-b979-563d956d3303.jsonl
S1=/sessions/intelligent-admiring-cori/mnt/.claude/projects/session/1b699506-2d49-40c3-bb97-f4eb04cb2a81.jsonl
cmp -s "$S1" project-logs/transcripts/raw/2026-11-11-chat-7-part1-snapshot.jsonl && ok "part1 byte-identical to closed session" || no "part1" "differs"
N=$(wc -l < project-logs/transcripts/raw/2026-11-11-chat-7-part2-snapshot.jsonl)
head -n "$N" "$L" | cmp -s - project-logs/transcripts/raw/2026-11-11-chat-7-part2-snapshot.jsonl && ok "part2 exact prefix of live log ($N lines)" || no "part2 prefix" "mismatch"
python3 -c "
import json,glob
for p in glob.glob('project-logs/transcripts/raw/*chat-7*.jsonl'):
    for l in open(p,encoding='utf-8'):
        if l.strip(): json.loads(l)
" && ok "all chat-7 raw snapshots parse as JSONL" || no "JSONL" "unparseable line"

echo "5. CODE INTEGRITY"
python3 -I -c "import sys;sys.path.insert(0,'.');from backend import ingest_auth,key_directory,accounts,ingest,attribution" && ok "backend modules import" || no "imports" "failed"
! grep -qE "^(from|import) backend" tools/verify_key_directory.py && ok "standalone verifier imports no backend code" || no "verifier" "imports backend"
for f in tools/verify_key_directory.py tools/publish_key_directory.py tools/seed_demo_collector.py; do test -f "$f" || no "missing tool" "$f"; done
ok "all documented tools present"

echo "6. DOCUMENTATION"
! grep -rq "endpoint has no authentication" client-assets/ && ok "no doc claims unauthenticated ingest" || no "stale ingest claim" "found"
! grep -rq "has no authentication" client-assets/ && ok "no doc claims server has no auth" || no "stale server claim" "found"
python3 -c "
import zipfile,re
t=re.sub(r'<[^>]+>','',zipfile.ZipFile('project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx').read('word/document.xml').decode('utf-8'))
assert 'Stage 11' in t
assert '**' not in t and chr(96) not in t
" && ok "build history docx: Stage 11 present, no literal markup" || no "docx" "markers or missing Stage 11"

echo
[ $FAIL -eq 0 ] && { echo "GATE PASSED — 0 failures"; exit 0; } || { echo "GATE FAILED — $FAIL failure(s)"; exit 1; }
