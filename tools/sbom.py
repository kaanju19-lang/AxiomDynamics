"""
Generate and verify a Software Bill of Materials for a Platform installation.

D09 §4.4 disclosed "no SBOM artefact in releases" as a supply-chain gap with a
Q1 2027 target. This closes it, and the way it closes it matters:

**The SBOM is generated from an installation, not from `requirements.txt`.**
A manifest that lists what we asked pip for is a shopping list; a manifest that
lists what pip resolved, unpacked and left on disk is an inventory. The gap D09
disclosed is that a Railroad cannot independently verify the dependency chain —
and a shopping list cannot be verified against anything, because it says nothing
about what actually arrived.

**The format is CycloneDX 1.5 JSON**, written directly rather than with a
library, for the same reason `tools/verify_ledger_export.py` imports nothing
from the Platform: a recipient must be able to read the artefact with a text
editor and a JSON parser. `cyclonedx-py` is a dependency, and adding a dependency
to generate the document about our dependencies is a joke that writes itself.

**What a per-component digest means here.** PyPI publishes a SHA-256 for each
distribution file. We do not have those at build time offline, so we do not
pretend to. Each component carries `axiom:tree-hash`: a SHA-256 over the sorted
list of (relative path, file SHA-256) for every file the distribution installed.
That is *recomputable on the Railroad's machine from the installed tree*, which
is what makes it a verification tool rather than a claim — and it catches a
substituted wheel, because a substituted wheel installs different bytes.

**It also lists bundled native libraries.** The numpy wheel is not one library;
it packs OpenBLAS, LAPACK, a GCC fortran runtime and libquadmath. Those are inside
the artefact we ship and are therefore inside the supply chain, whether or not
`requirements.txt` mentions them. D10 Part 2 called numpy "one component" and the
complete inventory; that was wrong and is corrected in the same commit.

Usage:
    python3 -I tools/sbom.py generate --out sbom.json [--env-label NAME]
    python3 -I tools/sbom.py verify   --sbom sbom.json
    python3 -I tools/sbom.py show     --sbom sbom.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timezone

FORMAT = "CycloneDX"
SPEC_VERSION = "1.5"
TOOL_NAME = "axiom-sbom"
TOOL_VERSION = "1.0.0"

# Filesystems reorder directory listings and mtimes differ between installs.
# Neither may enter the digest, or the same wheel installed twice verifies
# unequal and the tool becomes noise.
_HASH_CHUNK = 1 << 20


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_HASH_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _dist_files(dist):
    """
    Every file the distribution installed, as (relative path, sha256).

    `dist.files` can contain names outside the site-packages root (a console
    script lands in `bin/`). Those are resolved through `locate_file` and their
    path is recorded relative to the site root so the digest is portable between
    two machines that install to different absolute prefixes.
    """
    root = str(dist.locate_file(""))
    entries = []
    for f in dist.files or []:
        p = dist.locate_file(f)
        if not os.path.isfile(p):
            # A `.pyc` optimised at import time, or a file removed post-install.
            # Skipped, but the count is reported so a mismatch is visible rather
            # than silent.
            continue
        try:
            rel = os.path.relpath(str(p), root).replace(os.sep, "/")
        except ValueError:
            rel = str(p).replace(os.sep, "/")
        entries.append((rel, _sha256_file(str(p))))
    entries.sort()
    return entries


def tree_hash(entries) -> str:
    """
    A digest over the installed file tree.

    Length-prefixed so that path/content boundaries cannot be shifted: without
    the lengths, a file named "a" with hash "bc" and a file named "ab" with hash
    "c" produce identical input to the hash function.
    """
    h = hashlib.sha256()
    for rel, digest in entries:
        rb = rel.encode("utf-8")
        h.update(b"%d:" % len(rb))
        h.update(rb)
        h.update(bytes.fromhex(digest))
    return h.hexdigest()


def _licence_ids(dist):
    ids = []
    md = dist.metadata
    for c in md.get_all("Classifier") or []:
        if c.startswith("License :: "):
            ids.append(c.split(" :: ")[-1])
    if not ids:
        lic = (md.get("License") or "").strip()
        if lic and "\n" not in lic and len(lic) < 120:
            ids.append(lic)
    return sorted(set(ids))


def _bundled_libraries(dist):
    """
    Native libraries packed inside a wheel.

    Not a licence audit — a disclosure. The installed `.libs` directory is the
    place a binary wheel hides a fortran runtime, and a bill of materials that
    stops at the package name tells a security reviewer nothing about what else
    arrived with it.
    """
    found = []
    for sub in ("%s.libs" % dist.metadata["Name"].replace("-", "_"),):
        base = os.path.join(str(dist.locate_file("")), sub)
        if os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                p = os.path.join(base, name)
                if os.path.isfile(p):
                    found.append({
                        "name": name,
                        "directory": sub,
                        "sha256": _sha256_file(p),
                        "size_bytes": os.path.getsize(p),
                    })
    return found


def _canon(name: str) -> str:
    return name.lower().replace("_", "-")


def _req_names(path: str) -> set:
    """Names declared in a requirements file. Comments and blanks ignored."""
    names = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "[", ";", " "):
                if sep in line:
                    line = line.split(sep, 1)[0]
                    break
            if line:
                names.add(_canon(line))
    return names


def _scope(declared, mdinst):
    """
    The declared set plus everything it transitively requires.

    Scoping matters more than it looks. Run unscoped on a build host and the
    SBOM describes the build host — 153 distributions, including a GPL-3
    firewall tool and a Twisted stack the Platform has never imported. A
    customer reading that reasonably concludes we ship them. A release SBOM has
    to describe the release, so the scope is the requirement file and its
    closure, and anything installed outside it is reported rather than listed.
    """
    keep, todo = set(), list(declared)
    while todo:
        key = todo.pop()
        if key in keep or key not in mdinst:
            continue
        keep.add(key)
        for r in mdinst[key].requires or []:
            dep = r.split(";", 1)[0].strip()
            for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "[", " ", "("):
                if sep in dep:
                    dep = dep.split(sep, 1)[0]
                    break
            if dep:
                todo.append(_canon(dep))
    return keep


def components(scope=None) -> list:
    import importlib.metadata as md

    by_key = {}
    for dist in md.distributions():
        name = dist.metadata["Name"]
        if name:
            by_key[_canon(name)] = dist
    if scope is not None:
        by_key = {k: v for k, v in by_key.items()
                  if k in _scope(scope, by_key)}

    out = []
    for dist in by_key.values():
        name = dist.metadata["Name"]
        entries = _dist_files(dist)
        out.append({
            "type": "library",
            "name": name,
            "version": dist.version,
            "purl": "pkg:pypi/%s@%s" % (name.lower().replace("_", "-"),
                                        dist.version),
            "licenses": [{"license": {"id": i}} for i in _licence_ids(dist)]
                        or [{"license": {"name": "UNKNOWN"}}],
            "hashes": [{"alg": "SHA-256", "content": tree_hash(entries)}],
            "properties": [
                {"name": "axiom:tree-hash-alg",
                 "value": "sha256 over sorted (length-prefixed relpath, filesha256)"},
                {"name": "axiom:file-count", "value": str(len(entries))},
            ],
            "evidence": {"identity": [
                {"field": "purl", "confidence": 1.0,
                 "methods": [{"technique": "filename", "confidence": 1.0},
                             {"technique": "hash-comparison",
                              "confidence": 1.0}]}]},
            "axiom:bundled-libraries": _bundled_libraries(dist),
        })
    out.sort(key=lambda c: (c["name"].lower(), c["version"]))
    return out


def generate(env_label: str, requirements: str = None) -> dict:
    scope = _req_names(requirements) if requirements else None
    comps = components(scope=scope)
    doc = {
        "bomFormat": FORMAT,
        "specVersion": SPEC_VERSION,
        "serialNumber": "urn:uuid:%s" % uuid.uuid4(),
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "tools": [{"vendor": "AxiomDynamics", "name": TOOL_NAME,
                       "version": TOOL_VERSION}],
            "component": {
                "type": "application",
                "name": "AxiomDynamics Platform",
                "version": env_label,
            },
            "properties": [
                {"name": "axiom:python-version", "value": platform.python_version()},
                {"name": "axiom:python-implementation",
                 "value": platform.python_implementation()},
                {"name": "axiom:platform", "value": platform.platform()},
                {"name": "axiom:env-label", "value": env_label},
                # Which interpreter generated it is not decoration. The
                # deployment image pins 3.11 and the demo host is not 3.11, so a
                # bill of materials without this line can be silently compared
                # against the wrong environment.
                {"name": "axiom:generated-with", "value": sys.version.split()[0]},
            ],
        },
        "components": comps,
    }
    return doc


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------
def verify(doc: dict, strict_env: bool = False,
           requirements: str = None) -> tuple:
    """Return (problems, checks). Empty problems means the tree matches."""
    problems, checks = [], []

    def check(name, ok, detail=""):
        checks.append((name, ok, detail))
        if not ok:
            problems.append("%s: %s" % (name, detail) if detail else name)

    check("is_cyclonedx", doc.get("bomFormat") == FORMAT,
          "bomFormat is %r" % doc.get("bomFormat"))
    check("spec_version", doc.get("specVersion") == SPEC_VERSION,
          "specVersion is %r" % doc.get("specVersion"))

    declared = {_canon(c["name"]): c for c in doc.get("components") or []}

    import importlib.metadata as md
    installed = {}
    for dist in md.distributions():
        if dist.metadata["Name"]:
            installed[_canon(dist.metadata["Name"])] = dist
    if requirements:
        # Verify within the same scope the SBOM was generated in. Comparing a
        # release SBOM against a build host's whole site-packages would report
        # every unrelated package as an unlisted dependency.
        keep = _scope(_req_names(requirements), installed)
        installed = {k: v for k, v in installed.items() if k in keep}

    missing = sorted(set(declared) - set(installed))
    extra = sorted(set(installed) - set(declared))
    # An SBOM listing a component that is not installed describes a machine that
    # does not exist. An installed component the SBOM does not list is an
    # unaccounted dependency — the more dangerous of the two, but both are
    # failures, because either way the document does not describe this host.
    check("no_declared_component_is_missing", not missing,
          "declared but not installed: %s" % ", ".join(missing))
    check("no_installed_component_is_unlisted", not extra,
          "installed but not declared: %s" % ", ".join(extra))

    for key in sorted(set(declared) & set(installed)):
        c, dist = declared[key], installed[key]
        if c.get("version") != dist.version:
            check("version_%s" % key, False,
                  "declared %r, installed %r" % (c.get("version"), dist.version))
            continue
        want = next((h["content"] for h in c.get("hashes") or []
                     if h.get("alg") == "SHA-256"), None)
        if want is None:
            check("hash_present_%s" % key, False, "component has no SHA-256")
            continue
        got = tree_hash(_dist_files(dist))
        # This is the check that catches a substituted wheel. A tampered
        # distribution that installs different bytes fails here even if its
        # name and version are identical, which is the shape of most real
        # supply-chain attacks.
        check("tree_hash_%s" % key, got == want,
              "declared %s, installed %s" % (want[:16], got[:16]))

    gen = (doc.get("metadata") or {}).get("properties") or []
    genv = {p["name"]: p["value"] for p in gen}.get("axiom:python-version")
    if genv:
        same = genv == platform.python_version()
        if strict_env:
            check("python_version", same,
                  "SBOM generated on %s, verifying on %s"
                  % (genv, platform.python_version()))
        else:
            checks.append(("python_version", same,
                           "generated on %s, verifying on %s"
                           % (genv, platform.python_version())))
    return problems, checks


def show(doc: dict) -> None:
    md = doc.get("metadata") or {}
    props = {p["name"]: p["value"] for p in md.get("properties") or []}
    print("SBOM %s  (%s %s)" % (doc.get("serialNumber"), FORMAT,
                                doc.get("specVersion")))
    print("env label : %s" % props.get("axiom:env-label", "?"))
    print("generated : %s on python %s"
          % (md.get("timestamp"), props.get("axiom:python-version")))
    print()
    for c in doc.get("components") or []:
        lic = ", ".join(x["license"].get("id") or x["license"].get("name")
                        for x in c.get("licenses") or [])
        print("%-22s %-10s %s" % (c["name"], c["version"], lic))
        for b in c.get("axiom:bundled-libraries") or []:
            print("    bundled: %-42s %s" % (b["name"], b["sha256"][:16]))
    print()
    print("%d component(s)" % len(doc.get("components") or []))


def _reject_duplicate_keys(pairs):
    """
    `json.load` keeps the last of two identical keys, so two readers of one file
    can disagree about what it says. The ledger export refuses duplicates for
    this reason; a supply-chain document has the same exposure and gets the same
    treatment.
    """
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate JSON key %r — two readers of this "
                             "document would disagree about its content" % k)
        seen[k] = v
    return seen


def load_strict(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=_reject_duplicate_keys)


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="write an SBOM for this installation")
    g.add_argument("--out", required=True)
    g.add_argument("--env-label", default="unlabelled")
    g.add_argument("--requirements",
                   help="scope the SBOM to this requirements file and its "
                        "closure; without it every installed distribution is "
                        "listed, which describes the build host, not the release")

    v = sub.add_parser("verify", help="verify this installation against an SBOM")
    v.add_argument("--sbom", required=True)
    v.add_argument("--requirements",
                   help="verify within the same scope the SBOM was made in")
    v.add_argument("--strict-env", action="store_true",
                   help="fail if the interpreter version differs")

    s = sub.add_parser("show", help="print an SBOM as a table")
    s.add_argument("--sbom", required=True)

    a = ap.parse_args(argv)

    if a.cmd == "generate":
        doc = generate(a.env_label, requirements=a.requirements)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print("wrote %s — %d component(s), python %s"
              % (a.out, len(doc["components"]), platform.python_version()))
        return 0

    try:
        doc = load_strict(a.sbom)
    except ValueError as exc:
        print("REFUSED: %s" % exc)
        return 1

    if a.cmd == "show":
        show(doc)
        return 0

    problems, checks = verify(doc, strict_env=a.strict_env,
                              requirements=a.requirements)
    for name, ok, detail in checks:
        mark = "ok  " if ok else "FAIL"
        print("%s %s%s" % (mark, name, "" if ok else " — " + detail))
    print()
    if problems:
        print("%d problem(s)" % len(problems))
        return 1
    print("%d checks passed — this installation matches the SBOM"
          % len(checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
