"""
Tests for the SBOM generator and verifier (D09 §4.4 / §7.2).

The claim under test is the one D09 §4.4 disclosed as missing: a customer can
independently verify the dependency chain. That claim has two halves, and the
tests are split along them:

  1. THE DOCUMENT describes the installation — component set, version, and a
     digest over the bytes that were actually installed.
  2. THE VERIFIER catches substitution — a changed tree, a changed version, a
     component that is declared but absent, a component present but undeclared.

A bill of materials that describes the build host instead of the release is the
failure mode this suite exists to prevent: it is worse than no SBOM, because a
customer reading "153 components including ufw and Twisted" draws a wrong
conclusion about what we ship, and one reading "1 component" about a scoped
release draws a right one.

Run: python3 -I tests/test_sbom.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "sbom.py")
REQS = os.path.join(ROOT, "requirements.txt")

RESULTS = []


def test(fn):
    try:
        fn()
    except AssertionError as exc:
        RESULTS.append((fn.__name__, False, exc))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, "%s: %s" % (type(exc).__name__, exc)))
    else:
        RESULTS.append((fn.__name__, True, None))
    return fn


def run(*args, cwd=None):
    p = subprocess.run([sys.executable, "-I", "-B", TOOL, *args],
                       capture_output=True, text=True, cwd=cwd or ROOT)
    return p.returncode, p.stdout + p.stderr


TMP = tempfile.mkdtemp(prefix="axiom-sbom-")


def gen(scope=True, label="test"):
    out = os.path.join(TMP, "sbom-%s.json" % label)
    args = ["generate", "--out", out, "--env-label", label]
    if scope:
        args += ["--requirements", REQS]
    rc, txt = run(*args)
    assert rc == 0, txt
    with open(out, encoding="utf-8") as fh:
        return out, json.load(fh)


# ---------------------------------------------------------------------------
# 1. The document describes the release, not the build host
# ---------------------------------------------------------------------------
@test
def test_a_scoped_sbom_lists_only_the_declared_dependency_and_its_closure():
    _, doc = gen(scope=True, label="scoped")
    names = [c["name"].lower().replace("_", "-") for c in doc["components"]]
    assert names == ["numpy"], names


@test
def test_an_unscoped_sbom_lists_everything_installed_and_says_so():
    """
    The difference is the point, not a bug: without a scope the tool has no way
    to know what the release is, and must not guess. What it must not do is
    describe the build host while claiming to describe the release.
    """
    _, scoped = gen(scope=True, label="s")
    _, wide = gen(scope=False, label="w")
    assert len(wide["components"]) > len(scoped["components"]), (
        "an unscoped run must list more than a scoped one on this host")
    assert len(wide["components"]) > 1, (
        "the build host should carry more than one distribution; if this fails "
        "the test is not exercising the distinction")


@test
def test_the_document_is_cyclonedx_json_and_names_its_python():
    _, doc = gen(label="meta")
    assert doc["bomFormat"] == "CycloneDX"
    assert doc["specVersion"] == "1.5"
    assert doc["serialNumber"].startswith("urn:uuid:")
    props = {p["name"]: p["value"] for p in doc["metadata"]["properties"]}
    # Which interpreter produced it is load-bearing: the deployment image pins
    # 3.11 and a demo host is not 3.11, so an SBOM without this line can be
    # compared against the wrong environment and pass.
    assert props["axiom:python-version"].startswith(
        ".".join(str(x) for x in sys.version_info[:2])), props
    assert props["axiom:env-label"] == "meta"


@test
def test_the_component_carries_a_sha256_over_its_installed_tree():
    _, doc = gen(label="hash")
    c = doc["components"][0]
    assert c["purl"].startswith("pkg:pypi/")
    h = [x for x in c["hashes"] if x["alg"] == "SHA-256"]
    assert len(h) == 1 and len(h[0]["content"]) == 64, c["hashes"]
    assert int(h[0]["content"], 16) != 0


@test
def test_bundled_native_libraries_are_disclosed_not_hidden_behind_the_package_name():
    """
    numpy is not one library. The wheel packs a fortran runtime, libquadmath and
    OpenBLAS; they execute inside our process, so they are inside the supply
    chain. An SBOM that stops at "numpy 2.2.6" tells a reviewer nothing about
    them.
    """
    _, doc = gen(label="bundled")
    c = doc["components"][0]
    bundled = c.get("axiom:bundled-libraries") or []
    if sys.platform == "win32":
        return  # wheel layout differs; the property is still emitted
    names = [b["name"] for b in bundled]
    assert any("openblas" in n.lower() for n in names), names
    for b in bundled:
        assert len(b["sha256"]) == 64, b
        assert b["size_bytes"] > 0, b


# ---------------------------------------------------------------------------
# 2. The verifier catches substitution
# ---------------------------------------------------------------------------
@test
def test_an_untouched_installation_verifies():
    out, _ = gen(label="clean")
    rc, txt = run("verify", "--sbom", out, "--requirements", REQS)
    assert rc == 0, txt
    assert "matches the SBOM" in txt, txt


@test
def test_a_changed_tree_hash_is_caught():
    """The substitution case: same name, same version, different bytes."""
    out, doc = gen(label="tamper")
    doc["components"][0]["hashes"][0]["content"] = "0" * 64
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "tree_hash_numpy" in txt, txt


@test
def test_a_changed_version_is_caught_by_name():
    out, doc = gen(label="ver")
    doc["components"][0]["version"] = "9.9.9"
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "version_numpy" in txt, txt


@test
def test_a_component_declared_but_not_installed_is_caught():
    out, doc = gen(label="ghost")
    ghost = dict(doc["components"][0])
    ghost["name"] = "requests"
    ghost["purl"] = "pkg:pypi/requests@2.0.0"
    doc["components"].append(ghost)
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "no_declared_component_is_missing" in txt, txt


@test
def test_a_component_installed_but_not_declared_is_caught():
    """
    The dangerous direction. An unaccounted dependency is a dependency nobody
    reviewed, and it is present in the process. Removing the only component
    from the SBOM is exactly what a release built without scoping, or a
    hand-edited SBOM, would look like.
    """
    out, doc = gen(label="extra")
    doc["components"] = []
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "no_installed_component_is_unlisted" in txt, txt


@test
def test_a_non_cyclonedx_document_is_refused():
    bad = os.path.join(TMP, "notacyclonedx.json")
    json.dump({"bomFormat": "SPDX", "components": []},
              open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "is_cyclonedx" in txt, txt


@test
def test_a_component_with_no_hash_fails_rather_than_passing_vacuously():
    out, doc = gen(label="nohash")
    doc["components"][0]["hashes"] = []
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, txt
    assert "hash_present_numpy" in txt, txt


@test
def test_strict_env_fails_on_a_version_mismatch_but_default_does_not():
    out, doc = gen(label="env")
    for p in doc["metadata"]["properties"]:
        if p["name"] == "axiom:python-version":
            p["value"] = "3.11.9"
    bad = out.replace(".json", "-bad.json")
    json.dump(doc, open(bad, "w", encoding="utf-8"))

    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 0, ("default verify should tolerate an env difference and "
                     "report it: %s" % txt)

    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS,
                  "--strict-env")
    assert rc == 1, txt
    assert "python_version" in txt, txt


@test
def test_the_tool_imports_nothing_outside_the_standard_library():
    """
    Same discipline as the export verifier: a customer verifying a supply-chain
    document should not need to install anything to do it.
    """
    import ast
    src = open(TOOL, encoding="utf-8").read()
    mods = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    allowed = {"argparse", "hashlib", "json", "os", "platform", "sys", "uuid",
               "datetime", "importlib", "__future__"}
    unexpected = mods - allowed
    assert not unexpected, unexpected


@test
def test_a_duplicate_json_key_in_an_sbom_is_not_silently_resolved():
    """
    json.load keeps the last duplicate, so a document carrying two 'version'
    keys is read one way by us and the other way by a first-key-wins viewer.
    Refused rather than resolved, for the same reason the ledger bundle is.
    """
    out, doc = gen(label="dup")
    good = open(out, encoding="utf-8").read()
    # Insert a second version key into the first component, textually.
    marker = '"version": "%s"' % doc["components"][0]["version"]
    assert marker in good, "expected to find the version field verbatim"
    tampered = good.replace(marker, marker + ', "version": "0.0.1"', 1)
    bad = out.replace(".json", "-dup.json")
    open(bad, "w", encoding="utf-8").write(tampered)
    rc, txt = run("verify", "--sbom", bad, "--requirements", REQS)
    assert rc == 1, ("a duplicate key must be refused, not resolved; got: %s"
                     % txt)
    # Asserting only on the exit code would pass for the wrong reason: with the
    # key silently resolved to 0.0.1, the version check also fails. The refusal
    # itself has to be what is asserted.
    assert "REFUSED" in txt and "duplicate JSON key" in txt, (
        "expected the loader to refuse the document, not a downstream check to "
        "trip on the resolved value; got: %s" % txt)
    assert "version_numpy" not in txt, (
        "the version check fired, meaning the duplicate was resolved rather "
        "than refused; got: %s" % txt)


# ---------------------------------------------------------------------------
def main():
    print(f"{len(RESULTS)} tests")
    bad = 0
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f" -> {exc!r}"))
        bad += 0 if ok else 1
    print(f"\n{len(RESULTS) - bad} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
