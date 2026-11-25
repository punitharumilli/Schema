#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
test_convert.py: check the conversion of DRMD v0.3.0 documents to DRMD 1.0.0.

The two v0.3.0 documents in tests/fixtures/v0.3.0/ are the examples of the release v0.3.0
(QI-Data-Lab/DRMD). For each of them the suite checks that

  * the converted document is valid against drmd.xsd;
  * no element or declaration of the old namespace https://example.org/drmd is left;
  * @schemaVersion is 1.0.0 and documentVersion follows uniqueIdentifier with the given value;
  * nothing is lost: every value and every attribute of the source is in the result, element by
    element, apart from the renamed materialPropertiesList and materialProperties;

and that the converter refuses what it must refuse: a document without documentVersion, a
document of another version, a document with a DOCTYPE. An XML signature is removed with a note.

Run:
    python tests/test_convert.py

Exit code 0 means every check passed.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent
CONVERT = SCHEMA_DIR / "tools" / "convert_v0_3_0.py"
FIXTURES = sorted((HERE / "fixtures" / "v0.3.0").glob("*.xml"))
OLD = "https://example.org/drmd"
NEW = "urn:drmd:schema"
RENAMED = {"materialPropertiesList": "propertiesList", "materialProperties": "properties"}

sys.path.insert(0, str(SCHEMA_DIR / "tools"))
from convert_v0_3_0 import convert  # noqa: E402  (sets the XML catalog before lxml is loaded)
from lxml import etree  # noqa: E402

failures: list[str] = []


def check(ok: bool, label: str) -> None:
    print(("  ok    " if ok else "  FAIL  ") + label)
    if not ok:
        failures.append(label)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CONVERT), *args], capture_output=True, text=True)


def signature(el: etree._Element) -> list[tuple]:
    """Every element as (namespace-mapped name, attributes, text), in document order."""
    out = []
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        q = etree.QName(e)
        ns = NEW if q.namespace == OLD else q.namespace
        name = RENAMED.get(q.localname, q.localname) if q.namespace in (OLD, NEW) else q.localname
        if q.namespace in (OLD, NEW) and name == "documentVersion":
            continue
        attrs = {k: v for k, v in e.attrib.items() if k != "schemaVersion"}
        out.append((ns, name, tuple(sorted(attrs.items())), (e.text or "").strip()))
    return out


def main() -> int:
    xsd = etree.XMLSchema(etree.parse(str(SCHEMA_DIR / "drmd.xsd")))
    check(len(FIXTURES) == 2, f"two v0.3.0 fixtures found ({len(FIXTURES)})")

    for src in FIXTURES:
        print(src.name)
        old = etree.parse(str(src))
        new, notes = convert(src, "1")
        root = new.getroot()
        check(xsd.validate(new), "valid against drmd.xsd" + ("" if xsd.validate(new) else f": {xsd.error_log.last_error}"))
        text = etree.tostring(new, encoding="unicode")
        check(OLD not in text, "no trace of the old namespace")
        check(root.get("schemaVersion") == "1.0.0", "schemaVersion is 1.0.0")
        dv = root.find(f"{{{NEW}}}administrativeData/{{{NEW}}}coreData/{{{NEW}}}documentVersion")
        check(dv is not None and dv.text == "1", "documentVersion is the given value")
        check(dv is not None and etree.QName(dv.getprevious()).localname == "uniqueIdentifier",
              "documentVersion follows uniqueIdentifier")
        check(not root.xpath("//*[local-name()='materialPropertiesList' or local-name()='materialProperties']"),
              "materialPropertiesList and materialProperties renamed")
        check(signature(old.getroot()) == signature(root), "every value and attribute carried over unchanged")
        check(not notes, "no notes for a document without signature")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = FIXTURES[0]
        print("command line")
        r = run(str(src), str(tmp / "a.xml"), "--document-version", "2025-09-10")
        check(r.returncode == 0 and (tmp / "a.xml").exists(), "converts, exit code 0")
        r = run(str(src), str(tmp / "b.xml"))
        check(r.returncode == 2 and not (tmp / "b.xml").exists() and "documentVersion" in r.stderr,
              "refuses without --document-version, exit code 2")
        r = run(str(SCHEMA_DIR / "examples" / "reference-material-certificate.xml"), str(tmp / "c.xml"),
                "--document-version", "1")
        check(r.returncode == 2 and not (tmp / "c.xml").exists(), "refuses a DRMD 1.0.0 document, exit code 2")

        doc = etree.parse(str(src))
        root = doc.getroot()
        root.set("schemaVersion", "0.2.0")
        (tmp / "v02.xml").write_bytes(etree.tostring(doc))
        r = run(str(tmp / "v02.xml"), str(tmp / "d.xml"), "--document-version", "1")
        check(r.returncode == 2 and "0.2.0" in r.stderr, "refuses schemaVersion 0.2.0, exit code 2")

        body = src.read_text(encoding="utf-8").split("?>", 1)[1]
        (tmp / "dtd.xml").write_text('<?xml version="1.0"?>\n<!DOCTYPE x [<!ENTITY e "x">]>' + body, encoding="utf-8")
        r = run(str(tmp / "dtd.xml"), str(tmp / "e.xml"), "--document-version", "1")
        check(r.returncode == 2 and not (tmp / "e.xml").exists(), "refuses a document with a DOCTYPE, exit code 2")

        doc = etree.parse(str(src))
        ds = "http://www.w3.org/2000/09/xmldsig#"
        sig = etree.SubElement(doc.getroot(), f"{{{ds}}}Signature")
        etree.SubElement(sig, f"{{{ds}}}SignedInfo")
        (tmp / "sig.xml").write_bytes(etree.tostring(doc))
        r = run(str(tmp / "sig.xml"), str(tmp / "f.xml"), "--document-version", "1")
        out = (tmp / "f.xml").read_text(encoding="utf-8") if (tmp / "f.xml").exists() else ""
        check(r.returncode == 0 and "Signature" not in out and "signature" in r.stdout,
              "removes an XML signature and says so")

        r = run(str(src), str(tmp / "g.xml"), "--document-version", "1", "--validate")
        check(r.returncode == 3 and "TO CONFIRM" in r.stdout,
              "--validate runs the business rules (BAM-F017: TO CONFIRM, exit code 3)")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed")
        return 1
    print("all conversion checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
