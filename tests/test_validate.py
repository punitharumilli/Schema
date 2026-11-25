#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
test_validate.py: check tools/validate.py itself, as a user runs it.

tests/test_rules.py checks the Schematron rules. This suite checks what validate.py adds around
them, on copies of the worked examples written to a temporary folder:

  * the verdicts COMPLIANT, TO CONFIRM and NOT COMPLIANT, and the exit codes 0, 3, 1 and 2;
  * the XML Schema step: the version pattern 1.0.x of @schemaVersion and the non-negative
    period of validity;
  * the IDREF check: a dangling @refId is reported, a reference to the @Id of an XML Signature
    element is accepted, as Xerces does;
  * the handling of untrusted documents: a document with a DOCTYPE is not processed, and an
    external entity is never read;
  * the clean variants of tests/test_rules.py, which must also be valid against the XML Schema.

Run:
    python tests/test_validate.py

Exit code 0 means every check passed.
"""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent
VALIDATE = SCHEMA_DIR / "tools" / "validate.py"
sys.path.insert(0, str(SCHEMA_DIR / "tools"))
sys.path.insert(0, str(HERE))

from lxml import etree  # noqa: E402
from test_rules import CLEAN_CASES, CRM, NS, PIS, drop, load, set_attr, set_text, _empty  # noqa: E402

SIGNATURE = (
    '<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="signature_1">'
    "<ds:SignedInfo>"
    '<ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>'
    '<ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>'
    '<ds:Reference URI=""><ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>'
    "<ds:DigestValue>AAAA</ds:DigestValue></ds:Reference>"
    "</ds:SignedInfo><ds:SignatureValue>AAAA</ds:SignatureValue></ds:Signature>"
)


def _refer_to_signature(tree):
    """Append an XML Signature and point the first properties block at its @Id."""
    tree.getroot().append(etree.fromstring(SIGNATURE))
    block = tree.xpath("//drmd:properties[@refId][1]", namespaces=NS)[0]
    block.set("refId", block.get("refId") + " signature_1")
    return tree


# (description, base document, mutation, expected verdict)
DOCUMENTS = [
    ("certificate as published", CRM, lambda t: t, "compliant"),
    ("product information sheet as published", PIS, lambda t: t, "compliant"),
    ("commutability removed: conditional only", CRM,
     lambda t: drop(t, "//drmd:statements/drmd:commutability"), "to confirm"),
    ("health and safety information removed: warning only", CRM,
     lambda t: drop(t, "//drmd:statements/drmd:healthAndSafetyInformation"), "compliant"),
    ("intended use left empty", CRM,
     lambda t: _empty(t, "//drmd:statements/drmd:intendedUse"), "not compliant"),
    ("schemaVersion 1.0.7 (a later patch release)", CRM,
     lambda t: set_attr(t, "/drmd:digitalReferenceMaterialDocument", "schemaVersion", "1.0.7"),
     "compliant"),
    ("schemaVersion 1.1.0 (another minor release)", CRM,
     lambda t: set_attr(t, "/drmd:digitalReferenceMaterialDocument", "schemaVersion", "1.1.0"),
     "not compliant"),
    ("negative period of validity", PIS,
     lambda t: set_text(t, "//drmd:timeAfterDispatch/drmd:period", "-P2Y"), "not compliant"),
    ("dangling @refId", CRM,
     lambda t: set_attr(t, "//drmd:properties[@refId][1]", "refId", "no_such_id"),
     "not compliant"),
    ("@refId pointing at the @Id of an XML Signature", CRM, _refer_to_signature, "compliant"),
]
DOCUMENTS += [(f"clean variant: {d}", base, mutate, "compliant") for d, base, mutate in CLEAN_CASES]


def run(*arguments):
    """Run validate.py as a user does and return (exit code, output)."""
    completed = subprocess.run(
        [sys.executable, str(VALIDATE), *map(str, arguments)],
        capture_output=True, text=True, cwd=SCHEMA_DIR,
    )
    return completed.returncode, completed.stdout + completed.stderr


def main():
    from validate import XSD, SCH, load_schematron, validate_one

    xmlschema = etree.XMLSchema(etree.parse(str(XSD)))
    sch = load_schematron(SCH)
    failures = []

    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)

        print("Verdicts")
        files = {}
        for number, (description, base, mutate, expected) in enumerate(DOCUMENTS):
            tree = copy.deepcopy(load(base))
            mutate(tree)
            path = folder / f"document-{number:02d}.xml"
            tree.write(str(path), xml_declaration=True, encoding="UTF-8")
            files[expected] = path
            verdict = validate_one(path, xmlschema, sch, "all")["verdict"]
            status = "OK" if verdict == expected else "FAILED"
            print(f"  {status:11} {description}: {verdict}")
            if verdict != expected:
                failures.append(f"{description}: {verdict}, expected {expected}")

        print("\nExit codes")
        missing = folder / "missing.xml"
        runs = [
            ("one compliant document", [files["compliant"]], 0),
            ("compliant and to confirm", [files["compliant"], files["to confirm"]], 3),
            ("to confirm and not compliant", [files["to confirm"], files["not compliant"]], 1),
            ("a file that does not exist", [missing], 2),
        ]
        for description, arguments, expected in runs:
            code, _ = run(*arguments)
            status = "OK" if code == expected else "FAILED"
            print(f"  {status:11} {description}: exit code {code}")
            if code != expected:
                failures.append(f"{description}: exit code {code}, expected {expected}")

        print("\nUntrusted documents")
        secret = folder / "secret.txt"
        secret.write_text("SECRET-CONTENT-7f3a", encoding="utf-8")
        text = CRM.read_text(encoding="utf-8")
        root_start = text.index("<drmd:digitalReferenceMaterialDocument")
        body = text[root_start:]
        version = "<drmd:documentVersion>"
        assert body.count(version) == 1, "test setup error: documentVersion not found once"
        with_entity = (
            text[:root_start]
            + f'<!DOCTYPE drmd:digitalReferenceMaterialDocument [\n'
              f'  <!ENTITY secret SYSTEM "{secret.as_uri()}">\n]>\n'
            + body.replace(version, version + "&secret;", 1)
        )
        entity_doc = folder / "entity.xml"
        entity_doc.write_text(with_entity, encoding="utf-8")
        code, output = run(entity_doc)
        from validate import INSTANCE_PARSER
        parsed = etree.tostring(etree.parse(str(entity_doc), INSTANCE_PARSER), encoding="unicode")
        checks = [
            ("a document with a DOCTYPE is reported as not compliant", code == 1),
            ("the DOCTYPE is named as the reason", "DOCTYPE" in output),
            ("the entity is referenced in the test document", "&secret;" in parsed),
            ("the external entity is not read by the parser", "SECRET-CONTENT-7f3a" not in parsed),
            ("the external entity does not appear in the report", "SECRET-CONTENT-7f3a" not in output),
        ]
        for description, passed in checks:
            print(f"  {'OK' if passed else 'FAILED':11} {description}")
            if not passed:
                failures.append(description)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("validate.py behaved as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
