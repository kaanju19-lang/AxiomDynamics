"""
Tests for scheduled chained ledger replication (B01 §7 item 12, D09 §4.5.4).

The claim under test is not "a file appears". It is:

  **A series produced on the documented cadence is continuous, every bundle
  chains to the one before it, a zero-record week is preserved rather than
  skipped, nothing is ever overwritten, and a lost state file is refused rather
  than silently re-anchored.**

Each test below is one of those, plus the ways the sequence can go wrong: a
missed month, a run twice in the same minute, a bundle missing from disk, a
state claiming a chain the files do not support, and an operator trying to
"fix" a gap by starting over.

Run: python3 -I tests/test_ledger_replication.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-repl-test-")
os.environ["AXIOM_DB_PATH"] = os.path.join(_TMPDIR, "test.db")

from backend import ledger_export as le       # noqa: E402
from backend import ledger_replication as lr  # noqa: E402
from backend import store                     # noqa: E402

KEY = b"\x33" * 32
RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh_db(n=0):
    """A throwaway ledger with `n` dispositions. Mirrors the export tests."""
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    for i in range(n):
        store.save_disposition(
            f"AD-2026-{i:04d}", f"Reviewer {i}", f"CERT-{i:03d}",
            "concur_dispatch" if i % 2 == 0 else "request_inspection",
            f"note {i}",
        )


def fresh_series():
    d = tempfile.mkdtemp(prefix="axiom-series-", dir=_TMPDIR)
    return d


def dt(*args):
    return datetime(*args, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# The cadence itself
# ---------------------------------------------------------------------------
@test
def test_first_run_produces_an_incremental_and_a_full():
    """Both periods are outstanding. The incremental comes first — see below."""
    fresh_db(3)
    d = fresh_series()
    made = lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    assert [m["cadence"] for m in made] == ["incremental", "full"], made


@test
def test_the_incremental_comes_before_the_full_and_carries_the_new_records():
    """
    Order is load-bearing. The incremental's range is `after_id`; if the full ran
    first it would advance the cursor to the ledger head and the incremental
    behind it would always be empty. Every month-boundary incremental would then
    look exactly like a quiet week.
    """
    fresh_db(3)
    d = fresh_series()
    made = lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    incr = [m for m in made if m["cadence"] == "incremental"][0]
    full = [m for m in made if m["cadence"] == "full"][0]
    assert incr["record_count"] == 3, incr
    assert full["record_count"] == 3, full
    assert full["previous_export_hash"] == incr["export_signature"]


@test
def test_a_second_run_in_the_same_week_and_month_does_nothing():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    made = lr.run_due(KEY, d, now=dt(2026, 11, 5, 2, 0))
    assert made == [], made
    assert lr.read_state(d)["bundle_count"] == 2


@test
def test_a_new_week_but_same_month_produces_only_the_incremental():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    made = lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    assert [m["cadence"] for m in made] == ["incremental"], made


@test
def test_a_new_month_produces_a_full_again():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    made = lr.run_due(KEY, d, now=dt(2026, 12, 2, 2, 0))
    assert [m["cadence"] for m in made] == ["incremental", "full"], made


@test
def test_a_skipped_week_is_covered_by_one_catch_up_not_many():
    """
    Four weeks go by. The incremental range is `after_id`, so one later export
    covers every id since the last bundle. It must not fabricate a bundle per
    skipped week, which would be several zero-record bundles for one id range.
    """
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))     # W45
    store.save_disposition("AD-2026-9000", "Late Reviewer", "CERT-900",
                           "concur_dispatch", "found late")
    made = lr.run_due(KEY, d, now=dt(2026, 12, 2, 2, 0))  # four weeks later
    incr = [m for m in made if m["cadence"] == "incremental"]
    assert len(incr) == 1, made
    assert incr[0]["period"] == "2026-W49"
    assert incr[0]["record_count"] == 1, incr[0]


# ---------------------------------------------------------------------------
# Chaining — the property the whole module exists to provide
# ---------------------------------------------------------------------------
@test
def test_every_bundle_after_the_first_chains_to_its_predecessor():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 18, 2, 0))
    state = lr.read_state(d)
    assert state["bundles"][0]["previous_export_hash"] is None
    for prev, cur in zip(state["bundles"], state["bundles"][1:]):
        assert cur["previous_export_hash"] == prev["export_signature"], (prev, cur)


@test
def test_the_previous_export_hash_is_the_signature_not_the_file_digest():
    """
    `previous_export_hash` must be `signature_of(bundle)` — what a verifier
    recomputes from content — not the sha256 of the file on disk, which changes
    with whitespace and would make the chain unverifiable by a recipient.
    """
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    first = state["bundles"][0]
    with open(os.path.join(d, first["file"]), "r", encoding="utf-8") as f:
        bundle = json.load(f)
    assert first["export_signature"] == le.signature_of(bundle)
    assert first["bundle_digest"] != first["export_signature"]


@test
def test_each_written_bundle_verifies_against_the_previous_one():
    """The end-to-end claim: a recipient holding two adjacent bundles can check."""
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    state = lr.read_state(d)
    prev = cur = None
    with open(os.path.join(d, state["bundles"][0]["file"]), encoding="utf-8") as f:
        prev = json.load(f)
    with open(os.path.join(d, state["bundles"][1]["file"]), encoding="utf-8") as f:
        cur = json.load(f)
    r = le.verify_bundle(cur, KEY, prev)
    assert r["ok"], r["failed"]


# ---------------------------------------------------------------------------
# The zero-record week — D09 §4.5.4 says it must be kept
# ---------------------------------------------------------------------------
@test
def test_a_week_with_no_new_rows_still_produces_a_kept_bundle():
    fresh_db(3)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    made = lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    incr = [m for m in made if m["cadence"] == "incremental"][0]
    assert incr["record_count"] == 0
    assert os.path.exists(os.path.join(d, incr["file"])), "empty bundle was not kept"


@test
def test_the_empty_bundle_still_verifies():
    """A zero-record bundle that fails verification is worse than no bundle."""
    fresh_db(3)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    made = lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    incr = [m for m in made if m["cadence"] == "incremental"][0]
    with open(os.path.join(d, incr["file"]), encoding="utf-8") as f:
        bundle = json.load(f)
    r = le.verify_bundle(bundle, KEY)
    assert r["ok"], r["failed"]


@test
def test_an_empty_week_does_not_rewind_the_id_cursor():
    """
    The trap: an incremental with no rows has last_id == None. If the state took
    last_id from the slice instead of the ledger head, the next incremental would
    re-export everything from the start — duplicate evidence, and a series that
    looks like it went backwards.
    """
    fresh_db(3)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))     # nothing new
    state = lr.read_state(d)
    assert state["last_id_carried"] == 3, state["last_id_carried"]
    store.save_disposition("AD-2026-8000", "R", "CERT-800", "concur_dispatch", "n")
    made = lr.run_due(KEY, d, now=dt(2026, 11, 18, 2, 0))
    incr = [m for m in made if m["cadence"] == "incremental"][0]
    assert incr["record_count"] == 1, incr
    assert incr["first_id"] == 4, incr


# ---------------------------------------------------------------------------
# Never overwrite
# ---------------------------------------------------------------------------
@test
def test_two_runs_in_the_same_second_produce_two_files():
    fresh_db(1)
    d = fresh_series()
    same = dt(2026, 11, 4, 2, 0)
    a = lr.produce(KEY, d, lr.FULL, now=same)
    b = lr.produce(KEY, d, lr.FULL, now=same)
    assert a["file"] != b["file"], (a["file"], b["file"])
    assert os.path.exists(os.path.join(d, a["file"]))
    assert os.path.exists(os.path.join(d, b["file"]))


@test
def test_a_prior_bundle_is_never_clobbered():
    """Producing repeatedly must leave every earlier file byte-identical."""
    fresh_db(1)
    d = fresh_series()
    first = lr.produce(KEY, d, lr.FULL, now=dt(2026, 11, 4, 2, 0))
    path = os.path.join(d, first["file"])
    with open(path, "rb") as f:
        before = f.read()
    lr.produce(KEY, d, lr.FULL, now=dt(2026, 11, 4, 2, 0))
    with open(path, "rb") as f:
        assert f.read() == before


# ---------------------------------------------------------------------------
# Lost state and tampering — refuse, do not paper over
# ---------------------------------------------------------------------------
@test
def test_a_lost_state_file_is_refused_not_silently_restarted():
    """
    If series.json vanishes and signed bundles remain on disk, the next run must
    refuse. Starting a new series beside them would break the chain and file the
    new bundles as a genesis series they do not extend — and `inspect()` would
    then report the *new* series as continuous, which is the silent restart this
    module exists to prevent.
    """
    fresh_db(3)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    assert lr.read_state(d)["bundle_count"] == 2
    os.remove(os.path.join(d, lr.SERIES_FILE))

    try:
        lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    except RuntimeError as e:
        assert "reanchor" in str(e).lower(), e
    else:
        raise AssertionError("a lost state file was silently restarted")


@test
def test_orphaned_bundles_are_named_before_anything_is_written():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    os.remove(os.path.join(d, lr.SERIES_FILE))
    bundles_before = {f for f in os.listdir(d) if f.startswith("ledger-")}
    try:
        lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    except RuntimeError:
        pass
    # The refusal must not have written a bundle into the orphaned directory.
    bundles_after = {f for f in os.listdir(d) if f.startswith("ledger-")}
    assert bundles_after == bundles_before, bundles_after ^ bundles_before


@test
def test_inspect_notices_a_record_edited_inside_a_written_bundle():
    """
    The audit found the first `inspect()` never opened a bundle: it compared file
    names and recorded digests, so a record edited inside a signed bundle came
    back "series is continuous". This asserts it now recomputes the file.
    """
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    path = os.path.join(d, state["bundles"][1]["file"])
    with open(path, encoding="utf-8") as f:
        bundle = json.load(f)
    bundle["records"][0]["note"] = "FORGED"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle, f)
    report = lr.inspect(d, KEY)
    assert not report["ok"], report
    assert any("changed after it was written" in p or "fails verification" in p
               for p in report["problems"]), report["problems"]


@test
def test_inspect_notices_a_missing_cadence_period():
    """A gap is indistinguishable from a removed bundle, so it is a problem."""
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 11, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 25, 2, 0))
    state = lr.read_state(d)
    # Remove the middle W46 week from the record, as though it were deleted.
    state["bundles"] = [b for b in state["bundles"] if b["period"] != "2026-W46"]
    lr.write_state(d, state)
    report = lr.inspect(d, KEY)
    assert not report["ok"], report
    assert any("2026-W46" in p for p in report["problems"]), report["problems"]


@test
def test_inspect_discloses_when_it_did_not_check_the_signature():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    with_key = lr.inspect(d, KEY)
    without = lr.inspect(d)
    assert "signature" in with_key["verified"]
    assert "no key" in without["verified"], without["verified"]


@test
def test_the_standalone_verifier_accepts_a_chained_full_export():
    """
    The audit found the fix landed in `backend/ledger_export.py` but not in
    `tools/verify_ledger_export.py` — the tool D09 §4.5.4 tells the Railroad to
    run quarterly. The standalone verifier rejected every legitimate chained
    full. The two verifiers must agree.
    """
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    full = [b for b in state["bundles"] if b["cadence"] == "full"][0]
    prev = [b for b in state["bundles"] if b["cadence"] == "incremental"][0]
    import subprocess
    keyfile = os.path.join(_TMPDIR, "e2e.key")
    with open(keyfile, "wb") as f:
        f.write(KEY)
    r = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--key-file", keyfile,
         "--bundle", os.path.join(d, full["file"]),
         "--previous-bundle", os.path.join(d, prev["file"])],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK — every check passed" in r.stdout, r.stdout
    # The full export is *scoped out of* `no_regression`, so its PASS line is
    # legitimately absent — a full re-covers the ledger by design. What must not
    # appear is a FAIL, which is what the standalone verifier emitted for every
    # chained full before the fix. Assert the absence of a failure AND the
    # presence of the checks that must still run.
    assert "FAIL" not in r.stdout, r.stdout
    for must_run in ("signature", "row_hashes", "no_truncation", "previous_export_link"):
        assert f"PASS  {must_run}" in r.stdout, f"{must_run} did not run:\n{r.stdout}"


@test
def test_the_standalone_verifier_still_rejects_an_overlapping_incremental():
    """The other half: scoping the check must not have opened the old hole."""
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    incr = [b for b in state["bundles"] if b["cadence"] == "incremental"][0]
    with open(os.path.join(d, incr["file"]), encoding="utf-8") as f:
        i_b = json.load(f)
    # A genuinely overlapping bounded export: from_id inside the range it holds.
    overlap = le.build_bundle(KEY, from_id=1, previous_export_hash=le.signature_of(i_b))
    assert not le.verify_bundle(overlap, KEY, i_b)["ok"]
    assert "no_regression" in le.verify_bundle(overlap, KEY, i_b)["failed"]


@test
def test_inspect_reports_a_bundle_that_is_recorded_but_missing():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    os.remove(os.path.join(d, state["bundles"][0]["file"]))
    report = lr.inspect(d)
    assert not report["ok"], report
    assert any("missing from disk" in p for p in report["problems"]), report["problems"]


@test
def test_inspect_reports_a_chain_that_does_not_link():
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    state["bundles"][1]["previous_export_hash"] = "f" * 64
    lr.write_state(d, state)
    report = lr.inspect(d)
    assert not report["ok"], report
    assert any("previous_export_hash" in p for p in report["problems"]), report["problems"]


@test
def test_a_bundle_edited_on_disk_is_noticed_by_verification():
    """Replication writes the bundle; verification is still what proves it."""
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    path = os.path.join(d, state["bundles"][0]["file"])
    with open(path, encoding="utf-8") as f:
        bundle = json.load(f)
    bundle["records"][0]["note"] = "altered on disk"
    assert not le.verify_bundle(bundle, KEY)["ok"]


@test
def test_reanchor_restores_the_chain_after_state_loss():
    fresh_db(2)
    d = fresh_series()
    entry = lr.produce(KEY, d, lr.FULL, now=dt(2026, 11, 4, 2, 0))
    os.remove(os.path.join(d, lr.SERIES_FILE))
    made = lr.run_due(
        KEY, d, now=dt(2026, 11, 11, 2, 0),
        reanchor=(entry["export_signature"], entry["last_id"]),
    )
    assert made, made
    state = lr.read_state(d)
    assert state["bundles"][0]["previous_export_hash"] == entry["export_signature"]


# ---------------------------------------------------------------------------
# State durability
# ---------------------------------------------------------------------------
@test
def test_missing_period_walker_survives_a_53_week_iso_year():
    """
    The audit found `inspect()` could HANG FOREVER: the week walker rolled over at
    w == 53 but never emitted 53, so a series spanning a 53-week ISO year and the
    next W01 never advanced. 2026 is a 53-week year. A quarterly tool that never
    returns is worse than one that answers wrongly.
    """
    state = {
        "bundles": [
            {"cadence": "incremental", "period": "2026-W52"},
            {"cadence": "incremental", "period": "2027-W01"},
        ]
    }
    # If this hangs, the test suite hangs. The call must simply return, and it
    # must correctly name 2026-W53 as missing — 2026 is a 53-week ISO year, so
    # skipping from W52 straight to 2027-W01 is a real gap, not a year rollover.
    out = lr._missing_periods(state, now=datetime(2027, 1, 6, tzinfo=timezone.utc))
    assert len(out) == 1 and "2026-W53" in out[0], out


@test
def test_the_week_walker_knows_a_53_week_year_from_a_52_week_one():
    """
    The rollover must be computed, not assumed. 2026 has 53 ISO weeks; 2027 has
    52. A fixed `w == 53` rollover hung on the first and would have invented a
    phantom W53 gap on the second.
    """
    def gaps_over(y):
        state = {"bundles": [
            {"cadence": "incremental", "period": f"{y}-W52"},
            {"cadence": "incremental", "period": f"{y+1}-W01"},
        ]}
        return lr._missing_periods(state, now=datetime(y + 1, 1, 6, tzinfo=timezone.utc))

    assert any("W53" in p for p in gaps_over(2026)), "2026 has 53 weeks; W53 is a real gap"
    assert gaps_over(2027) == [], "2027 has 52 weeks; W52 rolls straight to W01"


@test
def test_a_deleted_latest_month_is_reported():
    """
    The audit's other walker finding: walking only to the latest recorded bundle
    meant deleting the most recent month shrank the range and the hole vanished.
    """
    fresh_db(2)
    d = fresh_series()
    lr.run_due(KEY, d, now=dt(2026, 9, 2, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 10, 7, 2, 0))
    lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
    state = lr.read_state(d)
    state["bundles"] = [b for b in state["bundles"]
                        if not (b["cadence"] == "full" and b["period"] == "2026-11")]
    lr.write_state(d, state)
    # Evaluate as of the same moment the November full should have existed.
    report = lr.inspect(d, KEY, now=dt(2026, 11, 4, 2, 0))
    assert any("2026-11" in p for p in report["problems"]), report["problems"]


@test
def test_concurrent_run_due_calls_do_not_duplicate_bundles():
    """
    The audit's F5 finding: `due_exports` read the state OUTSIDE the lock, so N
    concurrent `run_due` calls all saw both periods outstanding and all produced
    them — twelve duplicate W45 incrementals in one series, every one recorded,
    `inspect()` reporting ok. `produce` being locked was not enough; the due-check
    is the part that must be inside it.
    """
    fresh_db(1)
    d = fresh_series()
    import threading

    def go():
        try:
            lr.run_due(KEY, d, now=dt(2026, 11, 4, 2, 0))
        except Exception:  # noqa: BLE001
            pass

    threads = [threading.Thread(target=go) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    state = lr.read_state(d)
    periods = [(b["cadence"], b["period"]) for b in state["bundles"]]
    assert len(periods) == len(set(periods)), f"duplicate bundles: {periods}"
    assert len(periods) == 2, periods


@test
def test_concurrent_runs_do_not_strand_orphan_bundles():
    """
    Without a lock the read-state/build/write-bundle/write-state sequence races:
    the audit ran twelve parallel `produce()` calls and got eleven signed bundles
    on disk that series.json never recorded, with `inspect()` reporting ok. The
    mutex is what makes "a bundle the state does not know about" impossible.

    This exercises `produce` (the locked single-bundle path). The sibling race in
    `run_due` — where the *due check* leaked outside the lock and produced
    duplicates — is covered by `test_concurrent_run_due_calls_do_not_duplicate_bundles`.
    """
    fresh_db(1)
    d = fresh_series()
    import threading

    def go(i):
        try:
            lr.produce(KEY, d, lr.FULL,
                       now=datetime(2026, 11, 4, 2, 0, i, tzinfo=timezone.utc))
        except Exception:  # noqa: BLE001
            pass

    threads = [threading.Thread(target=go, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    state = lr.read_state(d)
    on_disk = {f for f in os.listdir(d)
               if f.startswith("ledger-") and f.endswith(".json")}
    recorded = {b["file"] for b in state["bundles"]}
    assert on_disk == recorded, f"orphans: {on_disk - recorded}"
    assert lr.inspect(d, KEY)["ok"], lr.inspect(d, KEY)["problems"]


@test
def test_state_is_written_atomically_and_reads_back_identical():
    fresh_db(1)
    d = fresh_series()
    lr.produce(KEY, d, lr.FULL, now=dt(2026, 11, 4, 2, 0))
    before = lr.read_state(d)
    lr.write_state(d, before)
    assert lr.read_state(d) == before
    assert not os.path.exists(os.path.join(d, lr.SERIES_FILE + ".tmp"))


@test
def test_an_unknown_state_version_is_refused():
    d = fresh_series()
    with open(os.path.join(d, lr.SERIES_FILE), "w", encoding="utf-8") as f:
        json.dump({"version": 999, "bundles": []}, f)
    try:
        lr.read_state(d)
    except ValueError as e:
        assert "version" in str(e).lower()
    else:
        raise AssertionError("an unknown state version was accepted")


if __name__ == "__main__":
    passed = failed = 0
    for name, ok, exc in RESULTS:
        if ok:
            print(f"PASS  {name}")
            passed += 1
        else:
            print(f"FAIL  {name} -> {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
