# Ingest Path — Build Record, 2026-11-11 (chat-5)

**Docket position:** None. **Internal — not for customer distribution.**

**Companion documents:** B02 §2 (the specification this implements), B01 §7 item
5 (the gap this narrows), `backend/ingest.py`, `tests/test_ingest.py`.

---

## 1. What was built, and what "built" is being claimed for

B02 §2 has specified a three-gate validation chain since the flow map was drawn:
schema, then timestamp, then physical plausibility. Until today it was drawn
dotted, and the reason it was drawn dotted is worth restating because it shaped
the build: **a flow map that starts mid-system is misleading, so the entry point
was shown as designed and labelled unbuilt rather than omitted.**

What exists now:

- `backend/ingest.py` — the three gates in order, a closed set of five outcomes,
  the ingest log table and its writer.
- `POST /api/ingest` — 64 KiB body cap, JSON parse, route to the chain, map the
  outcome to a status code.
- `tests/test_ingest.py` — 24 tests, of which one asserts the entire design
  property in a single loop (§4).
- B02 §2, B01 §7 item 5, B03's status block and `CURRENT-STATE.md` corrected to
  match.

**The claim being made is narrow: a payload either passes the chain and is
accepted for scoring, or it is refused with a named reason, and nothing else
emits an advisory.** The claim being declined is "the ingest problem is solved".
Three things are open and named in §5.

## 2. Why the gates are in that order

Gate 1 must precede 2 and 3 because gates 2 and 3 dereference fields that a
malformed payload may not have. Gate 2 must precede 3 because a reading cannot be
"physically implausible" until we know when it was taken — 212 °F is alarming at
70 mph and unremarkable on a stationary car in August.

`test_the_chain_runs_in_documented_order` feeds a payload that is bad in all
three ways and asserts the outcome is `rejected_schema`. If someone reorders the
gates, the module raises a `KeyError` on malformed input instead of naming it,
which is precisely the failure mode the module exists to prevent — so the test
would go red on the reorder, not on a cosmetic change.

## 3. Judgement calls, and what each one costs

**REJECT versus SUSPECT is a line between impossible and merely unusual, not
between bad and good.** B02 §2 draws it that way and the code follows: a journal
far *below* ambient while moving is a probe fault and is refused, because friction
only adds heat; a hot journal is *not* refused, because it is the signal the
platform exists to surface. `test_a_hot_journal_is_accepted_not_treated_as_a_sensor_fault`
exists to make the false negative impossible to introduce quietly. Refusing a
genuinely hot bearing would be the worst failure this system can have, and a
plausibility gate is exactly the kind of control that gets widened in the field
by whoever is losing the argument with it.

**A stationary hot axle is retained as SUSPECT, not scored.** Possible after a
hot-box stop, and not something to auto-score.

**Unknown fields are refused, not ignored.** Same reasoning as `bundle_no_extras`
in the export, and it is not a coincidence: a field nobody validated rides along
and a reader assumes it was checked.

**Every outcome is logged, including acceptance.** B02 §2 requires rejections to
be logged. A log containing only failures cannot answer "how much did we accept
last week", which is the question asked when someone wants to know whether the
platform was actually fed or merely connected. Accepted payloads are stored
hashed (SHA-256) and not in full, because the reading already exists downstream;
rejected payloads are stored verbatim, because an operator diagnosing a
misconfigured collector needs the bytes.

**Status codes differ per outcome** — 202 accepted, 200 suspect, 422 refused. A
collector that treats every non-200 as "retry" would retry a payload that can
never succeed until it jams its queue, and would drop one that needs a human.

## 4. The one assertion that is the design

```python
for c in cases:
    r = ingest.ingest(c, now=NOW)
    assert r.outcome != ingest.ACCEPTED
    assert r.emitted_an_advisory is False
    assert r.accepted_for_scoring is False
    assert r.reason
```

B02 §2's sentence — *malformed input fails closed; it produces no advisory and a
log entry* — written as executable text across seven payloads that fail in seven
different ways. If a future change makes any refusing path emit an advisory, this
goes red. Nothing else in the suite guards that property, so this test is the
one to keep.

## 5. What is deliberately still open

1. **The schema is a demonstration schema.** `axiom-detector-payload/v1` is built
   from the fields the physics engine actually consumes. The Railroad's real
   payload will not match it. It is declared as data (`PAYLOAD_SCHEMA`) rather
   than as code precisely so replacing it is a bounded change to one dict and its
   gate — but it *is* a change, and until it happens every payload this accepts is
   a payload shaped by us.
2. **There is no authentication on the endpoint.** Any client that can reach the
   port can write to the ingest log and, once scoring is wired, influence it. An
   unauthenticated ingest route is a data-poisoning route. This is the same gap as
   B01 §7 item 1 and is why the route belongs on a trusted segment behind the
   Railroad's own collector until AD-2 lands.
3. **Nothing downstream is wired to ingested readings.** An accepted payload is
   validated, logged and would be scorable; the demonstration fleet still ranks
   synthetic traces. **No demonstration number moves because of this build.**
   That sentence is the reason this document exists: it would be very easy for
   the next reader to assume a built ingest path means real data behind the
   numbers, and it does not.

## 6. Verification performed

- Full suite **143 passed, 0 failed** (was 119 after the chat-5 audit, 114 before
  it).
- **Each gate mutation-tested independently.** Skipping the schema gate → 14
  failures; skipping the timestamp gate → 4; skipping the plausibility gate → 3.
  Each restored to 24/24 afterwards. **A guard that has never gone red is not a
  guard.** The schema gate needed its own attention: `PAYLOAD_SCHEMA` declared
  `min`/`max` bounds that `_validate_schema` never enforced, so
  `test_out_of_range_value_is_refused_with_the_bound_in_the_message` failed on the
  first run. That is a schema that documents a limit and does not apply it, which
  is worse than one with no limit, because the comment reads as a control.
- HTTP route exercised end to end against a live `ThreadingHTTPServer`: valid →
  202 with `advisory=True`; bad schema → 422; future timestamp → 422; implausible
  → 422; stationary hot axle → 200 with `advisory=False`; non-JSON body → 422;
  and all six rows present in `ingest_log` afterwards.
- Arithmetic pass and decision-paper checker re-run; unchanged.

## 7. The lesson this pass adds

**The gate that had a documented bound and did not apply it is the one worth
remembering.** Every other defect in this build was caught by a test written
against the behaviour. That one was caught by a test written against the
*declaration* — the test asked "does an out-of-range value get refused with the
bound in the message", because PAYLOAD_SCHEMA says it is bounded. The code agreed
with the comment and the comment was not true of the code. Same shape as B01
§4.5a's false rewrite-detection claim, one layer down and smaller: **a document
is not a control, and a data structure is not a control either — only the
executed check is.**

---

*Internal. Review when the real payload schema is agreed, when AD-2 lands and the
endpoint can be authenticated, or when scoring is wired to ingested readings.*
