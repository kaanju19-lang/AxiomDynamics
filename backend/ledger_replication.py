"""
Scheduled, chained replication of the disposition ledger (B01 §7 item 12).

`ledger_export.py` builds **one** signed bundle when someone asks it to. That
is not replication: the gap B01 §7 item 12 and D09 §4.4 describe is that
nothing produces bundles *on a cadence*, so a week in which nobody remembers to
export is a week with no evidence, and a lost disk loses the ledger no matter
how well past bundles were signed.

D09 §4.5.4 already specifies the cadence and this module executes exactly that:

  - a **monthly full** export (every record),
  - a **weekly incremental** export (`after_id` = last id carried by the series),
  - every bundle naming the previous bundle's `signature_of()` as its
    `previous_export_hash`, so the series is a chain and not a set of snapshots,
  - a week with no new dispositions still producing a valid **zero-record**
    bundle, kept, because a missing bundle and an empty one must not look alike,
  - nothing ever overwritten.

## The air-gap constraint, which shapes everything here

D09 §3.2 promises the Platform has **no mechanism to send data to Supplier or
any external service**. So this module deliberately does *not* push anything
over a network. It writes the series to a directory on the Platform host, and
carrying that directory off the box is the Railroad's physical step (D09 §3.3:
"backup media created and managed by the Railroad"). A scheduled push would
contradict a customer-facing promise to close a control gap, which is the wrong
trade; the control that matters — *bundles exist, in order, unchained from
nothing* — is satisfied by producing them on a cadence and never losing one.

**What this does NOT do**, stated here so no document can quietly upgrade the
claim:
  - It cannot prove the series was not tampered with on disk before it was
    carried. That is what the recipient keeping each bundle detects (D09
    §4.5.4 note).
  - It cannot name the signer or date itself (B01 §7 item 11, AD-2).
  - It does not schedule *itself*. `run_due()` decides what is due and does it;
    invoking it is the operator's cron/systemd/Task Scheduler entry. On an
    air-gapped box a timer is correct and a network service is not.

## The series state, and why it is a second file rather than the ledger

The chain needs to know "which bundle came last". That is state about the
*export series*, not about the ledger, so it lives in `series.json` beside the
bundles rather than in the database — the ledger stays append-only and free of
bookkeeping that a database write could forge. The state file records the last
bundle's digest, the last id carried, and the count. It is written to a
per-process temporary file, fsynced, renamed over the old one, and the directory
entry is fsynced afterwards, so a crash leaves either the whole previous state or
the whole new one — not a half-written file, and not two concurrent runs
truncating each other's temp file.

If `series.json` is lost while bundles remain on disk, the next run cannot chain
to the previous bundle and **refuses**, naming the orphaned bundles: starting a
new series beside them would break the chain and file the new bundles as a
genesis series they do not extend. `--reanchor` exists for the case where the
operator holds the previous bundle and can name its digest and last id. It
rejoins the chain, and the recorded series then begins at the re-anchored entry
— but it does **not** restore an unbroken series: the earlier bundles stay on
disk, unrecorded, and `inspect` keeps reporting them, because their continuity
into the recorded series genuinely cannot be verified. A re-anchored series is
weaker evidence than one that was never interrupted, and it is meant to look it.
"""

import argparse
import contextlib
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional, Tuple

from . import ledger_export as le

SERIES_FILE = "series.json"
LOCK_FILE = "series.lock"
STATE_VERSION = 1

FULL = "full"
INCREMENTAL = "incremental"


# ---------------------------------------------------------------------------
# Dates — computed from the clock, injectable so tests are not calendar-bound
# ---------------------------------------------------------------------------
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_week_key(dt: datetime) -> str:
    """The ISO year-week an incremental export belongs to, e.g. '2026-W45'."""
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def month_key(dt: datetime) -> str:
    return f"{dt.year}-{dt.month:02d}"


# ---------------------------------------------------------------------------
# Mutual exclusion — two runs must not interleave read-state / write-bundle /
# write-state. Without a lock, N concurrent runs all read the same old state,
# all write a bundle, and only the last write of series.json survives: the other
# bundles become signed evidence the chain does not know about. A scheduler
# normally fires one run at a time, but "normally" is not a guarantee, and the
# damage is silent.
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def series_lock(series_dir: str) -> Iterator[None]:
    """
    Exclusive advisory lock over a series directory.

    `fcntl` on POSIX; on Windows (no `fcntl`) it falls back to an atomic
    `O_CREAT|O_EXCL` lock file, which is what an air-gapped Linux deployment
    will not need but a Windows demo host will. The lock is released on exit
    even if the body raises.
    """
    os.makedirs(series_dir, exist_ok=True)
    path = os.path.join(series_dir, LOCK_FILE)
    try:
        import fcntl  # noqa: PLC0415
    except ImportError:
        fcntl = None

    if fcntl is not None:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        return

    # Windows / no fcntl: exclusive create, with a bounded wait.
    import time

    deadline = time.time() + 30
    fd = None
    while True:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise RuntimeError(
                    f"could not acquire {path} within 30s — another run is in "
                    "progress, or a crash left a stale lock. Remove it only if "
                    "no run is active."
                )
            time.sleep(0.05)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(path)



def empty_state() -> Dict[str, object]:
    return {
        "version": STATE_VERSION,
        "last_bundle_digest": None,
        "last_bundle_file": None,
        "last_exported_at": None,
        "last_id_carried": None,
        "bundle_count": 0,
        "bundles": [],
    }


def read_state(series_dir: str) -> Dict[str, object]:
    path = os.path.join(series_dir, SERIES_FILE)
    if not os.path.exists(path):
        return empty_state()
    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    if state.get("version") != STATE_VERSION:
        raise ValueError(
            f"series state at {path} is version {state.get('version')!r}, "
            f"this build writes version {STATE_VERSION}. Refusing to guess at "
            "an older or newer format — migrate it deliberately."
        )
    return state


def orphaned_bundles(series_dir: str, state: Dict[str, object]) -> List[str]:
    """
    Bundle files on disk that the series state does not account for.

    Two ways these appear, and both are bad. A lost `series.json` leaves every
    earlier bundle unrecorded; a crash between writing a bundle and writing the
    state leaves exactly one. Either way the next run would treat itself as the
    first of a series while signed evidence sits beside it, and the chain would
    restart from nothing — silently, which is the failure this module exists to
    prevent. Naming them lets the caller refuse instead.
    """
    if not os.path.isdir(series_dir):
        return []
    known = {b["file"] for b in state["bundles"]}
    found = [
        f for f in os.listdir(series_dir)
        if f.startswith("ledger-") and f.endswith(".json")
    ]
    return sorted(f for f in found if f not in known)


def write_state(series_dir: str, state: Dict[str, object]) -> None:
    """
    Write `series.json` atomically, and never with a name another run can race.

    The temp file is created with `mkstemp` rather than a fixed `series.json.tmp`,
    because a fixed name means two concurrent runs truncate each other's temp
    file and one dies in `os.replace` with the other's file already gone — which
    is how concurrent runs strand signed bundles the state never records.

    `os.replace` is atomic for the *contents*; the directory entry is fsynced
    afterwards so a power loss cannot leave the rename half-applied. Without
    that fsync the rename is not durable and the state can silently revert to
    the previous version after a crash.
    """
    import tempfile

    path = os.path.join(series_dir, SERIES_FILE)
    body = json.dumps(state, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=SERIES_FILE + ".", suffix=".tmp", dir=series_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)

    # Durability of the rename itself, not just the bytes. Opening the directory
    # read-only and fsyncing it is the POSIX way; it fails harmlessly on platforms
    # that do not permit it, so the failure is not allowed to break the write.
    try:
        dfd = os.open(series_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# What is due
# ---------------------------------------------------------------------------
def due_exports(state: Dict[str, object], now: datetime) -> List[str]:
    """
    Which cadence periods are outstanding, in the order they must be produced.

    The week comes first. This is not arbitrary: the incremental's range is
    `after_id`, the last id the series carried, so an incremental produced
    *before* the month's full carries the records that are new since the last
    bundle. Producing the full first would advance the cursor to the ledger head
    and the incremental behind it would always be empty — which would make an
    ordinary month-boundary week indistinguishable from a genuinely quiet week,
    the exact confusion the series exists to prevent. Full-then-incremental also
    signed a full bundle citing a previous digest and then an empty bundle
    citing the full, which reads as evidence of nothing.

    The full still re-states everything, so it remains the recovery point; it
    simply is not the one that consumes new records.

    A missed week is **not** backfilled with one bundle per skipped week: the
    incremental range is `after_id`, so a single later export covers every id
    since the last bundle regardless of how many weeks were skipped. Only the
    current week is ever due.
    """
    done_months = {b["period"] for b in state["bundles"] if b["cadence"] == FULL}
    done_weeks = {b["period"] for b in state["bundles"] if b["cadence"] == INCREMENTAL}

    due: List[str] = []
    if iso_week_key(now) not in done_weeks:
        due.append(INCREMENTAL)
    if month_key(now) not in done_months:
        due.append(FULL)
    return due


# ---------------------------------------------------------------------------
# Filenames — sortable, never reused
# ---------------------------------------------------------------------------
def bundle_filename(cadence: str, period: str, now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return f"ledger-{cadence}-{period}-{stamp}.json"


# ---------------------------------------------------------------------------
# Producing one bundle
# ---------------------------------------------------------------------------
def produce(
    key: bytes,
    series_dir: str,
    cadence: str,
    now: Optional[datetime] = None,
    reanchor: Optional[Tuple[str, Optional[int]]] = None,
) -> Dict[str, object]:
    """
    Produce, chain, verify-against-previous, write and record one bundle.

    `reanchor` is `(previous_bundle_digest, last_id_carried)` for the case where
    the series state was lost but the operator holds the prior bundle. Without
    it, a series that has bundles on disk but no matching state is an error, not
    a fresh start: silently starting over would break the chain and file the
    new bundles as a genesis series beside evidence they do not extend.

    Returns the state entry for the bundle written.
    """
    now = now or _utcnow()
    os.makedirs(series_dir, exist_ok=True)

    # The whole read-state / build / write-bundle / write-state sequence runs
    # under the lock. Taking it here rather than in `run_due` means a caller who
    # invokes `produce` directly is protected too.
    with series_lock(series_dir):
        return _produce_locked(key, series_dir, cadence, now, reanchor)


def _produce_locked(
    key: bytes,
    series_dir: str,
    cadence: str,
    now: datetime,
    reanchor: Optional[Tuple[str, Optional[int]]],
) -> Dict[str, object]:
    """The body of `produce`, called with the series lock already held."""
    state = read_state(series_dir)

    # Refuse rather than restart. If bundle files exist that the state does not
    # account for, the state was lost or a previous run crashed between writing
    # a bundle and recording it. Either way the honest next step is for the
    # operator to say what the chain continues from (`--reanchor`), not for this
    # function to decide it is the first bundle of a series.
    orphans = orphaned_bundles(series_dir, state)
    if orphans and reanchor is None and state["bundle_count"] == 0:
        raise RuntimeError(
            f"{len(orphans)} bundle(s) exist in {series_dir} but series.json does "
            f"not record them (first: {orphans[0]}). Refusing to start a new "
            "series beside them — that would break the chain and file new bundles "
            "as a genesis series they do not extend. If the state was lost, name "
            "the last good bundle with --reanchor <previous_export_hash> "
            "--reanchor-last-id <id>."
        )

    prev_digest = state["last_bundle_digest"]
    last_id = state["last_id_carried"]
    if reanchor is not None:
        prev_digest, last_id = reanchor

    if prev_digest is None and state["bundle_count"] > 0:
        raise RuntimeError("series state is inconsistent: bundles recorded but no digest")
    if prev_digest is None and last_id is not None:
        raise RuntimeError("series state is inconsistent: last id with no digest")

    period = month_key(now) if cadence == FULL else iso_week_key(now)

    if cadence == FULL:
        after_id = None
    else:
        after_id = last_id

    bundle = le.build_bundle(
        key,
        after_id=after_id,
        previous_export_hash=prev_digest,
    )

    # Verify what we just built, against the previous bundle we claim to extend.
    # A bundle that fails its own verification is never written into the series:
    # a bad bundle in a series is worse than a missing one, because the next
    # bundle would then chain to garbage.
    previous_bundle = None
    if prev_digest is not None and state["last_bundle_file"]:
        prev_path = os.path.join(series_dir, state["last_bundle_file"])
        if os.path.exists(prev_path):
            with open(prev_path, "r", encoding="utf-8") as f:
                previous_bundle = json.load(f)
    result = le.verify_bundle(bundle, key, previous_bundle)
    if not result["ok"]:
        raise RuntimeError(
            "refusing to write a bundle that fails verification: "
            + ", ".join(result["failed"])
        )

    # The id carried forward is the ledger's own head, not this slice's last id.
    # An incremental that found no rows still has the ledger at the same head,
    # and a full export carries everything. Using the ledger head means the
    # next incremental's `after_id` is correct even after a zero-record week.
    m = bundle["manifest"]
    new_last_id = m["backend_head_id"] if m["backend_head_id"] is not None else last_id

    # Two runs in the same second would otherwise collide, and a bundle is never
    # overwritten: the second one gets a numeric suffix and keeps its own file.
    filename = bundle_filename(cadence, period, now)
    out_path = os.path.join(series_dir, filename)
    n = 2
    while os.path.exists(out_path):
        filename = bundle_filename(cadence, period, now) + f".{n}"
        out_path = os.path.join(series_dir, filename)
        n += 1

    body = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())

    import hashlib

    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    sidecar = out_path + ".sha256"
    with open(sidecar, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(out_path)}\n")

    entry = {
        "cadence": cadence,
        "period": period,
        "file": filename,
        "bundle_digest": digest,
        "export_signature": le.signature_of(bundle),
        "exported_at": m["exported_at"],
        # Whether this entry is a normal continuation of the recorded series or
        # the first bundle written after the series was re-anchored by hand. An
        # auditor needs to tell those apart: the first case is automatic, the
        # second means a state file was lost and the chain was rejoined from a
        # bundle the operator named. `inspect` treats a re-anchored entry as the
        # legitimate start of the recorded sequence rather than a broken link.
        "reanchored": bool(reanchor is not None),
        "record_count": m["record_count"],
        "first_id": m["first_id"],
        "last_id": m["last_id"],
        "previous_export_hash": prev_digest,
        "ledger_chain_ok": m["ledger_chain_ok"],
    }
    state["bundles"].append(entry)
    state["last_bundle_digest"] = entry["export_signature"]
    state["last_bundle_file"] = filename
    state["last_exported_at"] = m["exported_at"]
    state["last_id_carried"] = new_last_id
    state["bundle_count"] = state["bundle_count"] + 1
    write_state(series_dir, state)
    return entry


# ---------------------------------------------------------------------------
# Doing everything that is due
# ---------------------------------------------------------------------------
def run_due(
    key: bytes,
    series_dir: str,
    now: Optional[datetime] = None,
    reanchor: Optional[Tuple[str, Optional[int]]] = None,
) -> List[Dict[str, object]]:
    """Produce every outstanding cadence period.

    **Idempotent within a period, and that holds under concurrency.** The
    due-check reads `series.json`, and it must be inside the same lock as the
    writes: reading it outside meant N concurrent runs all saw both periods
    outstanding and all produced them, so a series could contain twelve W45
    incrementals and twelve November fulls, each individually valid and each
    duplicated — bundles the cadence says must not exist, which `inspect()` did
    not flag. The lock is taken once here for the whole run; `produce`'s own
    locked path is not re-entered (a second `flock` on a fresh descriptor in the
    same process would deadlock).

    `reanchor` is passed to the first bundle produced, and only the first: once
    that bundle is written the state carries the chain forward on its own.
    """
    now = now or _utcnow()
    os.makedirs(series_dir, exist_ok=True)
    made: List[Dict[str, object]] = []
    with series_lock(series_dir):
        due = due_exports(read_state(series_dir), now)
        for i, cadence in enumerate(due):
            made.append(
                _produce_locked(
                    key, series_dir, cadence, now,
                    reanchor if i == 0 else None,
                )
            )
    return made


# ---------------------------------------------------------------------------
# Read-only inspection — what a recipient or an auditor opens first
# ---------------------------------------------------------------------------
def inspect(
    series_dir: str,
    key: Optional[bytes] = None,
    now: Optional[datetime] = None,
) -> Dict[str, object]:
    """
    Read-only verification of a series. It repairs nothing.

    This is the check D09 §4.5.4 has the Railroad run quarterly before taking a
    bundle to an off-host machine, so it must actually check the things a
    quarterly check is for. An earlier version of this function compared file
    names and recorded digests and **never opened a bundle**, which meant a
    record edited inside a written bundle, or a monthly full quietly removed from
    the state, both came back "series is continuous". That is the failure mode
    the series exists to expose, reported by the tool meant to expose it.

    So it now does three things beyond listing:

      - **opens every bundle and recomputes its digest**, which catches a file
        changed after it was written, without needing the key.
      - **verifies each bundle against the one before it**, which is where
        `previous_export_link` and `no_truncation` actually get exercised. With
        `key`, this is the full `verify_bundle` including signature and every
        row hash. **Without a key the content checks still run but the signature
        is not checked, and the result says so in `verified`** — an inspection
        that silently skipped the signature would be a claim it cannot support.
      - **reports missing cadence periods** by walking month and week keys from
        the first bundle recorded to *now* — not merely to the latest bundle, so
        a deleted final month or week is bracketed rather than shrinking the
        range out of view. A gap is indistinguishable from a removed bundle
        (D09 §4.5.4), so it is a problem here rather than a note.

    `verified` in the result states what was checked, so no caller can read this
    as more than it did.
    """
    state = read_state(series_dir)
    problems: List[str] = []
    prev_digest = None
    prev_bundle = None

    for i, b in enumerate(state["bundles"]):
        path = os.path.join(series_dir, b["file"])
        if not os.path.exists(path):
            problems.append(f"bundle {i} ({b['file']}) is recorded but missing from disk")
            prev_bundle = None
            prev_digest = b["export_signature"]
            continue

        if b["previous_export_hash"] != prev_digest:
            if i == 0 and b.get("reanchored"):
                # The recorded series legitimately starts here: the state was lost
                # and the operator named the prior bundle by hand. Its
                # previous_export_hash points at a bundle this state never held,
                # which is expected, not a break. Bundles from before the loss
                # are reported separately as superseded, once.
                pass
            else:
                problems.append(
                    f"bundle {i} ({b['file']}) cites previous_export_hash "
                    f"{b['previous_export_hash']!r} but the series records {prev_digest!r}"
                )

        try:
            with open(path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        except (OSError, ValueError) as e:
            problems.append(f"bundle {i} ({b['file']}) will not parse: {e}")
            prev_bundle = None
            prev_digest = b["export_signature"]
            continue

        # The bundle's own digest, recomputed from what is on disk. This catches
        # a file edited after writing without needing the key at all, because
        # `signature_of` covers content + signature and the series recorded the
        # result. It cannot catch a *re-signed* bundle — only the key can — which
        # is exactly what `verified` discloses.
        if le.signature_of(bundle) != b["export_signature"]:
            problems.append(
                f"bundle {i} ({b['file']}) on disk does not match the digest the "
                "series recorded for it — the file was changed after it was written"
            )

        if key is not None:
            result = le.verify_bundle(bundle, key, prev_bundle)
            if not result["ok"]:
                problems.append(
                    f"bundle {i} ({b['file']}) fails verification: "
                    + ", ".join(result["failed"])
                )
        elif prev_bundle is not None:
            # No key: still exercise the two continuity checks, which need no
            # secret and are where a series breaks first.
            pm = prev_bundle.get("manifest", {})
            m = bundle.get("manifest", {})
            if m.get("previous_export_hash") != le.signature_of(prev_bundle):
                problems.append(
                    f"bundle {i} ({b['file']}) does not extend the previous bundle"
                )
            prev_head = pm.get("backend_head_id")
            if prev_head is not None and (
                m.get("backend_head_id") is None or m.get("backend_head_id") < prev_head
            ):
                problems.append(
                    f"bundle {i} ({b['file']}) reports a SHORTER ledger than the "
                    f"previous bundle: {m.get('backend_head_id')!r} < {prev_head!r}"
                )

        prev_bundle = bundle
        prev_digest = b["export_signature"]

    if state["bundles"]:
        last = state["bundles"][-1]
        if state["last_bundle_digest"] != last["export_signature"]:
            problems.append("series head does not match the last recorded bundle")

    problems.extend(_missing_periods(state, now))

    orphans = orphaned_bundles(series_dir, state)
    if orphans:
        reanchored = any(b.get("reanchored") for b in state["bundles"])
        if reanchored:
            # After a re-anchor the bundles from before the loss are still on disk
            # and still unrecorded. They remain *evidence* — the recipient was
            # given them — so they are reported, not forgiven. The recorded series
            # legitimately begins after them, but this tool cannot verify their
            # continuity into it, and a re-anchored series is weaker evidence than
            # an unbroken one. That is why this stays a problem: it is a real
            # reduction in what the series proves, not a bookkeeping loose end.
            problems.append(
                f"{len(orphans)} bundle file(s) predate the recorded series and are "
                f"unrecorded (first: {orphans[0]}). The series was re-anchored from a "
                "bundle the operator named, so its continuity into the earlier "
                "evidence cannot be verified here. Keep those bundles; they are the "
                "only record before the re-anchor."
            )
        else:
            problems.append(
                f"{len(orphans)} bundle file(s) exist on disk that the series does "
                f"not record (first: {orphans[0]}). They are signed evidence outside "
                "the chain — the state was lost or a run crashed before recording them."
            )

    return {
        "ok": not problems,
        "problems": problems,
        "verified": "signature and content" if key is not None else "content only — no key supplied, so the signature was not checked",
        "bundle_count": state["bundle_count"],
        "last_id_carried": state["last_id_carried"],
        "last_exported_at": state["last_exported_at"],
        "bundles": state["bundles"],
    }


def _is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _missing_periods(state: Dict[str, object], now: Optional[datetime] = None) -> List[str]:
    """
    Cadence periods that should have a bundle and do not.

    An earlier version walked `min..max` of the recorded periods, which had two
    defects an audit found:

      - **It hung.** The ISO-week increment rolled over at `w == 53`, but the last
        week it ever emitted was 52, so a series spanning a 53-week ISO year and
        the following W01 never advanced and `inspect()` looped forever.
      - **It could not see the last period.** Walking only to the *latest bundle
        recorded* means a deleted final month or week shrinks the range and the
        hole is never bracketed — the exact "a gap is indistinguishable from a
        removed bundle" case this is supposed to expose.

    So the walk is over real calendar arithmetic (every ISO year is 52 or 53
    weeks, computed, not assumed), and the upper bound is the *current* week and
    month rather than the latest bundle. `now` is injectable so the check does
    not depend on the wall clock in tests.

    A deployment may legitimately begin mid-month or mid-week; that only means
    the lower bound is the first *recorded* period, and nothing before it is
    expected.
    """
    bundles = state["bundles"]
    if not bundles:
        return []
    now = now or _utcnow()

    def weeks_in_iso_year(y: int) -> int:
        # A year has 53 ISO weeks iff Jan 1 is Thursday, or it is a leap year and
        # Jan 1 is Wednesday. Cheap to state, and beats guessing 52.
        jan1 = datetime(y, 1, 1).isoweekday()
        return 53 if (jan1 == 4 or (jan1 == 3 and _is_leap(y))) else 52

    def month_seq(a: str, b: str) -> List[str]:
        ya, ma = (int(x) for x in a.split("-"))
        yb, mb = (int(x) for x in b.split("-"))
        out: List[str] = []
        y, m = ya, ma
        while (y, m) <= (yb, mb):
            out.append(f"{y}-{m:02d}")
            m += 1
            if m == 13:
                y, m = y + 1, 1
        return out

    def week_seq(a: str, b: str) -> List[str]:
        ya, wa = (int(x) for x in a.split("-W"))
        yb, wb = (int(x) for x in b.split("-W"))
        out: List[str] = []
        y, w = ya, wa
        while (y, w) <= (yb, wb):
            if w > weeks_in_iso_year(y):   # roll over, however many weeks the year has
                y, w = y + 1, 1
                continue
            out.append(f"{y}-W{w:02d}")
            w += 1
        return out

    def gaps(cadence: str, seq) -> List[str]:
        periods = sorted(b["period"] for b in bundles if b["cadence"] == cadence)
        if not periods:
            return []
        # Start at the first bundle recorded; run to *now*, not to the latest
        # bundle, so a missing final period is bracketed and reported.
        current = month_key(now) if cadence == FULL else iso_week_key(now)
        end = max(periods[-1], current)
        present = set(periods)
        return [p for p in seq(periods[0], end) if p not in present]

    problems: List[str] = []
    for cadence, seq, noun in ((FULL, month_seq, "month"), (INCREMENTAL, week_seq, "week")):
        for p in gaps(cadence, seq):
            problems.append(
                f"no {cadence} bundle for {noun} {p} — the sequence has a gap, and "
                "a gap is indistinguishable from a removed bundle"
            )
    return problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cmd_run(args) -> int:
    key = le.load_key(args.key_file)
    now = None
    if args.now:
        now = datetime.fromisoformat(args.now)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
    reanchor = None
    if args.reanchor:
        reanchor = (args.reanchor, args.reanchor_last_id)
    made = run_due(key, args.series_dir, now=now, reanchor=reanchor)
    if not made:
        print("nothing due — every cadence period is already covered")
        return 0
    for e in made:
        print(f"wrote {e['file']}")
        print(f"  cadence        {e['cadence']}  ({e['period']})")
        print(f"  records        {e['record_count']}  (id {e['first_id']}..{e['last_id']})")
        print(f"  chains to      {e['previous_export_hash'] or 'nothing — this is the first bundle'}")
        print(f"  digest         {e['bundle_digest']}")
    return 0


def _cmd_inspect(args) -> int:
    key = le.load_key(args.key_file) if args.key_file else None
    r = inspect(args.series_dir, key)
    print(f"bundles   {r['bundle_count']}")
    print(f"last id   {r['last_id_carried']}")
    print(f"last at   {r['last_exported_at']}")
    print(f"verified  {r['verified']}")
    for b in r["bundles"]:
        print(f"  {b['period']:<9} {b['cadence']:<11} {b['record_count']:>4} records  {b['file']}")
    if r["problems"]:
        for p in r["problems"]:
            print(f"PROBLEM  {p}")
        print("FAILED")
        return 1
    print("OK — series is continuous and every bundle verifies")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="backend.ledger_replication",
        description="Produce the chained ledger export series on the D09 4.5.4 cadence.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="produce every outstanding cadence period")
    r.add_argument("--key-file", required=True)
    r.add_argument("--series-dir", required=True)
    r.add_argument("--now", default=None,
                   help="ISO timestamp to evaluate the cadence at, for testing")
    r.add_argument("--reanchor", default=None,
                   help="previous_export_hash of the last bundle, when series.json was lost")
    r.add_argument("--reanchor-last-id", type=int, default=None)
    r.set_defaults(fn=_cmd_run)

    i = sub.add_parser("inspect", help="verify a series read-only")
    i.add_argument("--series-dir", required=True)
    i.add_argument("--key-file", default=None,
                   help="without this the signature is not checked — see `verified`")
    i.set_defaults(fn=_cmd_inspect)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
