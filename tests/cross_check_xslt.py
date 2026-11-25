#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
cross_check_xslt.py: run every case of test_rules.py through a second Schematron implementation.

tools/validate.py evaluates the rules itself, as XPath. This check compiles the same rule file
with the ISO Schematron skeleton for XSLT 1.0 that ships with lxml (lxml.isoschematron) and
compares, for the two worked examples and for every case of tests/test_rules.py, the set of rule
identifiers that each implementation reports. They must be identical.

The rule file declares the XSLT 2.0 query binding; every test is also valid XPath 1.0, so for
this check the binding is changed to "xslt" in memory. The file on disk is not changed.

Run:
    python tests/cross_check_xslt.py

Exit code 0 means both implementations agree on every case.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

from lxml import etree, isoschematron  # noqa: E402
import test_rules as cases  # noqa: E402
from validate import SCH, load_schematron, run_schematron  # noqa: E402

SVRL = "{http://purl.oclc.org/dsdl/svrl}"


def main():
    source = SCH.read_bytes().replace(b'queryBinding="xslt2"', b'queryBinding="xslt"', 1)
    xslt = isoschematron.Schematron(etree.fromstring(source), store_report=True)
    namespaces, phases, patterns = load_schematron(SCH)

    def by_xslt(tree):
        xslt.validate(tree)
        report = xslt.validation_report
        return sorted({e.get("id") for e in report.iter(SVRL + "failed-assert")})

    def by_validate(tree):
        return sorted({f["rule_id"] for f in run_schematron(tree, namespaces, phases, patterns, "all")})

    documents = [(f"example {p.name}", p, lambda t: t) for p in (cases.CRM, cases.PIS)]
    documents += [(f"clean: {d}", base, mutate) for d, base, mutate in cases.CLEAN_CASES]
    documents += [(f"{rule}: {d}", base, mutate) for rule, base, d, mutate in cases.CASES]

    differences = 0
    for description, base, mutate in documents:
        tree = copy.deepcopy(cases.load(base))
        mutate(tree)
        a, b = by_xslt(tree), by_validate(tree)
        if a != b:
            differences += 1
            print(f"  DIFFERENT   {description}: XSLT {a}, validate.py {b}")
    print(f"{len(documents)} documents compared, {differences} difference(s).")
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
