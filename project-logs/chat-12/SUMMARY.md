# Chat-12 — Summary

**2026-11-13.** Suite 398 → 402. Three commits. Two sweeps and the audit that
broke them.

## Delivered

Rung 3 and rung 4 of chat-11's ladder — the only two of its seven that were not
blocked outside the repository. Plus a third sweep the ladder did not list, on
behavioural claims, which found the WAL defect.

Measured gpg signing cost (10.2 ms unprotected / 299.3 ms passphrase-protected),
traced the presumed disposition rate to B01 §6 where it had been stated all along,
corrected D09 §5.2's claim that data could be purged via an admin interface that
does not exist and a SQL path the schema forbids, and set `journal_mode=WAL` —
which four docket statements had claimed since chat-3 and the code never did.

## The audit found nine defects, and the worst was a commit message

`70077a8` asserted that the D09 termination sentence had been corrected. It had
not: it sat three lines below the paragraph announcing its removal, unedited,
still citing D07 §15.5 for an obligation §15.5 does not contain. A reader trusting
the commit message would have shipped the contradiction.

Three guards in `test_docket_currency.py` could not fail — a skip list of bare
words, two literal route names, a glob for a filename nothing produces — and all
three passed their own tests. All are now behavioural and pinned by tests that
construct the input which should trip them.

## Numbers

Suite 402. Commits `70077a8`, `fe3a7c1`, `250dce8`. Master % Tracker **78.4**,
unchanged, with the rubric's existence-versus-accuracy gap recorded as a finding
rather than silently re-based.

## Not done

The dashboard has still never been looked at by anyone. The `gnupg`/`dirmngr`
decision is still the owner's. Both carried, with the count stated: four chats.
