#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
test_rules.py: prove that every rule in drmd-business-rules.sch actually fires.

A validation rule that is never exercised is a rule nobody can trust. This suite takes the
two known-good worked examples in examples/, breaks exactly one thing in a copy of one of
them, and checks that the expected rule, and only the expected rule, is raised.

It also checks the opposite direction: both unmodified examples must pass with no assertion
of any severity, so that a rule cannot quietly start firing on compliant documents.

Run:
    python tests/test_rules.py

Exit code 0 means every rule behaved as documented.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent
sys.path.insert(0, str(SCHEMA_DIR / "tools"))

from lxml import etree  # noqa: E402
from validate import load_schematron, run_schematron, SCH  # noqa: E402

NS = {
    "drmd": "urn:drmd:schema",
    "dcc": "https://ptb.de/dcc",
    "si": "https://ptb.de/si",
}

CRM = SCHEMA_DIR / "examples" / "reference-material-certificate.xml"
PIS = SCHEMA_DIR / "examples" / "product-information-sheet.xml"


def load(path):
    return etree.parse(str(path))


def drop(tree, xpath):
    """Remove every node matched by xpath."""
    nodes = tree.xpath(xpath, namespaces=NS)
    assert nodes, f"test setup error: nothing matched {xpath}"
    for node in nodes:
        node.getparent().remove(node)
    return tree


def set_attr(tree, xpath, name, value):
    nodes = tree.xpath(xpath, namespaces=NS)
    assert nodes, f"test setup error: nothing matched {xpath}"
    for node in nodes:
        node.set(name, value)
    return tree


def set_text(tree, xpath, value):
    nodes = tree.xpath(xpath, namespaces=NS)
    assert nodes, f"test setup error: nothing matched {xpath}"
    for node in nodes:
        node.text = value
    return tree


# Each case: (rule id, base document, description, mutation)
CASES = [
    ("DRMD-001", CRM, "titleOfTheDocument removed",
     lambda t: drop(t, "//drmd:coreData/drmd:titleOfTheDocument")),
    ("DRMD-002", CRM, "no material entries",
     lambda t: drop(t, "//drmd:materials/drmd:material")),
    ("DRMD-003", CRM, "no properties blocks",
     lambda t: drop(t, "//drmd:propertiesList/drmd:properties")),
    ("DRMD-004", CRM, "intendedUse removed",
     lambda t: drop(t, "//drmd:statements/drmd:intendedUse")),
    ("DRMD-005", CRM, "storageInformation removed",
     lambda t: drop(t, "//drmd:statements/drmd:storageInformation")),
    ("DRMD-006", CRM, "instructionsForHandlingAndUse removed",
     lambda t: drop(t, "//drmd:statements/drmd:instructionsForHandlingAndUse")),
    ("DRMD-007", CRM, "material name removed",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:name")),
    ("DRMD-008", CRM, "minimumSampleSize removed",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:minimumSampleSize")),
    ("DRMD-009", CRM, "results emptied in every properties block",
     lambda t: drop(t, "//drmd:properties/drmd:results/drmd:result")),
    ("DRMD-010", CRM, "referenceMaterialProducer removed",
     lambda t: drop(t, "//drmd:administrativeData/drmd:referenceMaterialProducer")),
    ("DRMD-011", CRM, "documentVersion removed",
     lambda t: drop(t, "//drmd:coreData/drmd:documentVersion")),
    ("DRMD-012", CRM, "validity removed",
     lambda t: drop(t, "//drmd:coreData/drmd:validity")),
    ("DRMD-013", CRM, "commutability removed",
     lambda t: drop(t, "//drmd:statements/drmd:commutability")),
    ("DRMD-014", CRM, "procedures removed from every properties block",
     lambda t: drop(t, "//drmd:properties/drmd:procedures")),
    ("DRMD-015", CRM, "healthAndSafetyInformation removed",
     lambda t: drop(t, "//drmd:statements/drmd:healthAndSafetyInformation")),
    ("DRMD-016", CRM, "materialIdentifiers removed (ISO 5.2.3)",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:materialIdentifiers")),

    ("RMC-001", CRM, "metrologicalTraceability removed from a certificate",
     lambda t: drop(t, "//drmd:statements/drmd:metrologicalTraceability")),
    ("RMC-002", CRM, "no properties block marked certified",
     lambda t: set_attr(t, "//drmd:properties[@isCertified='true']", "isCertified", "false")),
    ("RMC-003", CRM, "no results anywhere in a certificate",
     lambda t: drop(t, "//drmd:properties/drmd:results/drmd:result")),
    ("RMC-005", CRM, "procedures removed from the certified block",
     lambda t: drop(t, "//drmd:properties[@isCertified='true']/drmd:procedures")),
    ("RMC-006", CRM, "certified single quantity without uncertainty",
     lambda t: (
         drop(t, "//drmd:properties[@isCertified='true']//drmd:result/drmd:data/drmd:list"
                 "/drmd:quantity[position()>1]"),
         _promote_list_to_quantity(t),
         drop(t, "//drmd:properties[@isCertified='true']//drmd:result/drmd:data"
                 "/drmd:quantity/si:real/si:measurementUncertaintyUnivariate"),
     )[-1]),
    ("RMC-007", CRM, "certified list quantity without uncertainty",
     lambda t: drop(t, "//drmd:properties[@isCertified='true']//drmd:list/drmd:quantity[1]"
                       "/si:real/si:measurementUncertaintyUnivariate")),
    ("RMC-008", CRM, "certified si:realListXMLList without uncertainty",
     lambda t: _replace_first_certified_with_xmllist(t)),
    ("RMC-009", CRM, "certified si:hybrid with an si:real lacking uncertainty",
     lambda t: _make_certified_hybrid(t)),
    ("RMC-010", CRM, "respPersons removed from a certificate",
     lambda t: drop(t, "//drmd:administrativeData/drmd:respPersons")),
    ("RMC-011", CRM, "material description removed from a certificate",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:description")),
    ("RMC-012", CRM, "no responsible person states a function (dcc:role)",
     lambda t: drop(t, "//drmd:respPersons/dcc:respPerson/dcc:role")),

    ("PIS-001", PIS, "product information sheet marked certified",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", "true")),
    ("PIS-002", PIS, "no results in a product information sheet",
     lambda t: drop(t, "//drmd:properties/drmd:results/drmd:result")),
    ("PIS-003", PIS, "individual properties block marked certified",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", "true")),
    ("PIS-005", PIS, "material description missing from a product information sheet",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:description")),
]


def _promote_list_to_quantity(tree):
    """Move the surviving list quantity up so it sits directly under data/quantity.

    RMC-006 covers data/quantity, RMC-007 covers data/list/quantity. To exercise RMC-006 the
    quantity must be a direct child of data.
    """
    for data in tree.xpath("//drmd:properties[@isCertified='true']//drmd:result/drmd:data",
                           namespaces=NS):
        lists = data.xpath("drmd:list", namespaces=NS)
        for lst in lists:
            for quantity in lst.xpath("drmd:quantity", namespaces=NS):
                data.append(quantity)
            data.remove(lst)
    return tree


def _replace_first_certified_with_xmllist(tree):
    """Swap a certified si:real for an si:realListXMLList that carries no uncertainty."""
    quantity = tree.xpath(
        "//drmd:properties[@isCertified='true']//drmd:result/drmd:data/drmd:list"
        "/drmd:quantity[1]", namespaces=NS)[0]
    parent_list = quantity.getparent()
    data = parent_list.getparent()
    real = quantity.xpath("si:real", namespaces=NS)[0]
    quantity.remove(real)
    xmllist = etree.SubElement(quantity, "{https://ptb.de/si}realListXMLList")
    etree.SubElement(xmllist, "{https://ptb.de/si}valueXMLList").text = "6.42 3.15"
    etree.SubElement(xmllist, "{https://ptb.de/si}unitXMLList").text = "\\percent \\percent"
    # RMC-008 applies to data/quantity, not data/list/quantity.
    data.append(quantity)
    if not parent_list.xpath("drmd:quantity", namespaces=NS):
        data.remove(parent_list)
    return tree


def _make_certified_hybrid(tree):
    """Put an si:hybrid holding an uncertainty-free si:real into the certified block."""
    quantity = tree.xpath(
        "//drmd:properties[@isCertified='true']//drmd:result/drmd:data/drmd:list"
        "/drmd:quantity[1]", namespaces=NS)[0]
    parent_list = quantity.getparent()
    data = parent_list.getparent()
    real = quantity.xpath("si:real", namespaces=NS)[0]
    quantity.remove(real)
    hybrid = etree.SubElement(quantity, "{https://ptb.de/si}hybrid")
    inner = etree.SubElement(hybrid, "{https://ptb.de/si}real")
    etree.SubElement(inner, "{https://ptb.de/si}value").text = "6.42"
    etree.SubElement(inner, "{https://ptb.de/si}unit").text = "\\percent"
    data.append(quantity)
    if not parent_list.xpath("drmd:quantity", namespaces=NS):
        data.remove(parent_list)
    return tree


def main():
    sch = load_schematron(SCH)
    namespaces, phases, patterns = sch

    failures = []
    checked_rules = set()

    print("Baseline: the worked examples must raise nothing at all")
    for path in (CRM, PIS):
        findings = run_schematron(load(path), namespaces, phases, patterns, "all")
        status = "OK" if not findings else "UNEXPECTED"
        print(f"  {status:11} {path.name}: {len(findings)} finding(s)")
        if findings:
            for f in findings:
                print(f"              {f['rule_id']} {f['message'][:80]}")
            failures.append(f"{path.name} raised {len(findings)} finding(s) but should raise none")

    print("\nNegative cases: each mutation must raise its rule")
    for rule_id, base, description, mutate in CASES:
        tree = copy.deepcopy(load(base))
        mutate(tree)
        findings = run_schematron(tree, namespaces, phases, patterns, "all")
        raised = {f["rule_id"] for f in findings}
        checked_rules.add(rule_id)
        if rule_id in raised:
            extra = raised - {rule_id}
            note = f"  (also: {', '.join(sorted(extra))})" if extra else ""
            print(f"  OK          {rule_id}: {description}{note}")
        else:
            print(f"  FAILED      {rule_id}: {description} -> raised {sorted(raised) or 'nothing'}")
            failures.append(f"{rule_id} did not fire for: {description}")

    declared = set()
    for pattern in patterns:
        for rule in pattern["rules"]:
            for check in rule["checks"]:
                declared.add(check["id"])
    untested = declared - checked_rules
    print(f"\nRules declared: {len(declared)}   rules exercised: {len(checked_rules)}")
    if untested:
        print(f"  NOT EXERCISED: {', '.join(sorted(untested))}")
        failures.append(f"no test for: {', '.join(sorted(untested))}")

    print()
    if failures:
        print(f"{len(failures)} problem(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("All rules behaved as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
