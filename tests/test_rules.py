#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
test_rules.py: prove that every rule in drmd-business-rules.sch actually fires.

A validation rule that is never exercised is a rule nobody can trust. This suite takes the
two known-good worked examples in examples/, breaks exactly one thing in a copy of one of
them, and checks that the expected rule is raised. Other rules that the same change triggers
are listed next to it ("also: ..."); they do not fail the test.

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
    ("DRMD-004", CRM, "intendedUse present but empty",
     lambda t: _empty(t, "//drmd:statements/drmd:intendedUse")),
    ("DRMD-004", CRM, "intendedUse with a heading only",
     lambda t: _heading_only(t, "//drmd:statements/drmd:intendedUse")),
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
    ("DRMD-014", CRM, "procedures whose methods have empty names",
     lambda t: set_text(t, "//drmd:properties/drmd:procedures/dcc:usedMethod/dcc:name/dcc:content", " ")),
    ("DRMD-015", CRM, "healthAndSafetyInformation removed",
     lambda t: drop(t, "//drmd:statements/drmd:healthAndSafetyInformation")),
    ("DRMD-016", CRM, "materialIdentifiers removed (ISO 5.2.3)",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:materialIdentifiers")),

    ("RMC-001", CRM, "metrologicalTraceability removed from a certificate",
     lambda t: drop(t, "//drmd:statements/drmd:metrologicalTraceability")),
    ("RMC-001", CRM, "metrologicalTraceability present but empty",
     lambda t: _empty(t, "//drmd:statements/drmd:metrologicalTraceability")),
    ("RMC-001", CRM, "metrologicalTraceability with a heading only",
     lambda t: _heading_only(t, "//drmd:statements/drmd:metrologicalTraceability")),
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
    ("RMC-006", CRM, "certified single si:complex without uncertainty",
     lambda t: _certified_value(t, "complex", single=True)),
    ("RMC-006", CRM, "certified single si:constant without uncertainty",
     lambda t: _certified_value(t, "constant", single=True)),
    ("RMC-007", CRM, "certified si:complex in a list without uncertainty",
     lambda t: _certified_value(t, "complex")),
    ("RMC-007", CRM, "certified si:constant in a list without uncertainty",
     lambda t: _certified_value(t, "constant")),
    ("RMC-008", CRM, "certified si:complexListXMLList without uncertainty",
     lambda t: _certified_value(t, "complexListXMLList")),
    ("RMC-008", CRM, "certified si:complexListXMLList with an empty uncertainty element",
     lambda t: _certified_value(t, "complexListXMLList, empty uncertainty element")),
    ("RMC-009", CRM, "certified si:hybrid with an si:constant lacking uncertainty",
     lambda t: _certified_value(t, "hybrid with si:constant")),
    ("RMC-009", CRM, "certified si:hybrid with an si:realList lacking uncertainty",
     lambda t: _certified_value(t, "hybrid with si:realList")),
    ("RMC-009", CRM, "certified si:hybrid with an si:list of si:realListXMLList lacking uncertainty",
     lambda t: _certified_value(t, "hybrid with si:list of si:realListXMLList")),
    ("RMC-009", CRM, "certified si:hybrid with an si:complexList whose uncertainty is empty",
     lambda t: _certified_value(t, "hybrid with si:complexList, empty uncertainty element")),
    ("RMC-007", CRM, "certified list quantity without uncertainty",
     lambda t: drop(t, "//drmd:properties[@isCertified='true']//drmd:list/drmd:quantity[1]"
                       "/si:real/si:measurementUncertaintyUnivariate")),
    ("RMC-008", CRM, "certified si:realListXMLList without uncertainty",
     lambda t: _replace_first_certified_with_xmllist(t)),
    ("RMC-008", CRM, "certified si:realListXMLList without uncertainty, inside a list",
     lambda t: _replace_first_certified_with_xmllist(t, keep_in_list=True)),
    ("RMC-009", CRM, "certified si:hybrid with an si:real lacking uncertainty",
     lambda t: _make_certified_hybrid(t)),
    ("RMC-009", CRM, "certified si:hybrid with an si:real lacking uncertainty, inside a list",
     lambda t: _make_certified_hybrid(t, keep_in_list=True)),
    ("RMC-009", CRM, "certified si:hybrid with an si:realListXMLList lacking uncertainty",
     lambda t: _make_certified_hybrid(t, keep_in_list=True, inner="realListXMLList")),
    ("RMC-010", CRM, "respPersons removed from a certificate",
     lambda t: drop(t, "//drmd:administrativeData/drmd:respPersons")),
    ("RMC-011", CRM, "material description removed from a certificate",
     lambda t: drop(t, "//drmd:materials/drmd:material/drmd:description")),
    ("RMC-011", CRM, "second material without a description in a certificate",
     lambda t: _add_material_without_description(t)),
    ("RMC-011", CRM, "material description present but empty",
     lambda t: _empty(t, "//drmd:materials/drmd:material/drmd:description")),
    ("RMC-011", CRM, "material description with a heading only",
     lambda t: _heading_only(t, "//drmd:materials/drmd:material/drmd:description")),
    ("RMC-012", CRM, "no responsible person states a function (dcc:role)",
     lambda t: drop(t, "//drmd:respPersons/dcc:respPerson/dcc:role")),

    ("PIS-001", PIS, "product information sheet marked certified",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", "true")),
    ("PIS-001", PIS, "product information sheet marked certified with \"1\"",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", "1")),
    ("PIS-002", PIS, "no results in a product information sheet",
     lambda t: drop(t, "//drmd:properties/drmd:results/drmd:result")),
    ("PIS-003", PIS, "individual properties block marked certified",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", "true")),
    ("PIS-003", PIS, "individual properties block marked certified with \" 1 \"",
     lambda t: set_attr(t, "//drmd:propertiesList/drmd:properties", "isCertified", " 1 ")),
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


SI = "https://ptb.de/si"
DCC = "https://ptb.de/dcc"

# D-SI values without an uncertainty, in each numeric form that a certified quantity can take.
FRAGMENTS = {
    "realListXMLList": '<si:realListXMLList><si:valueXMLList>6.42 3.15</si:valueXMLList>'
                       '<si:unitXMLList>\\percent \\percent</si:unitXMLList></si:realListXMLList>',
    "hybrid with si:real": '<si:hybrid><si:real><si:value>6.42</si:value><si:unit>\\percent</si:unit>'
                           '</si:real></si:hybrid>',
    "hybrid with si:realListXMLList": '<si:hybrid><si:realListXMLList><si:valueXMLList>6.42 3.15</si:valueXMLList>'
                                      '<si:unitXMLList>\\percent \\percent</si:unitXMLList></si:realListXMLList>'
                                      '</si:hybrid>',
    "complex": '<si:complex><si:valueReal>1</si:valueReal><si:valueImag>2</si:valueImag>'
               '<si:unit>\\volt</si:unit></si:complex>',
    "constant": '<si:constant><si:value>6.42</si:value><si:unit>\\percent</si:unit></si:constant>',
    "complexListXMLList": '<si:complexListXMLList><si:valueRealXMLList>1 2</si:valueRealXMLList>'
                          '<si:valueImagXMLList>3 4</si:valueImagXMLList>'
                          '<si:unitXMLList>\\volt \\volt</si:unitXMLList></si:complexListXMLList>',
    "complexListXMLList, empty uncertainty element":
        '<si:complexListXMLList><si:valueRealXMLList>1 2</si:valueRealXMLList>'
        '<si:valueImagXMLList>3 4</si:valueImagXMLList><si:unitXMLList>\\volt \\volt</si:unitXMLList>'
        '<si:measurementUncertaintyBivariateXMLList/></si:complexListXMLList>',
    "hybrid with si:constant": '<si:hybrid><si:constant><si:value>6.42</si:value>'
                               '<si:unit>\\percent</si:unit></si:constant></si:hybrid>',
    "hybrid with si:realList": '<si:hybrid><si:realList><si:real><si:value>6.42</si:value>'
                               '<si:unit>\\percent</si:unit></si:real></si:realList></si:hybrid>',
    "hybrid with si:list of si:realListXMLList":
        '<si:hybrid><si:list><si:realListXMLList><si:valueXMLList>6.42 3.15</si:valueXMLList>'
        '<si:unitXMLList>\\percent \\percent</si:unitXMLList></si:realListXMLList></si:list></si:hybrid>',
    "hybrid with si:complexList, empty uncertainty element":
        '<si:hybrid><si:complexList><si:listBivariateUnc/><si:complex><si:valueReal>1</si:valueReal>'
        '<si:valueImag>2</si:valueImag><si:unit>\\volt</si:unit></si:complex></si:complexList></si:hybrid>',
    # Valid uncertainties that the rules must accept, one for each form that has its own elements.
    "constant with a standard uncertainty":
        '<si:constant><si:value>6.42</si:value><si:unit>\\percent</si:unit>'
        '<si:valueStandardMU>0.04</si:valueStandardMU></si:constant>',
    "complex with an ellipsoidal region":
        '<si:complex><si:valueReal>1</si:valueReal><si:valueImag>2</si:valueImag><si:unit>\\volt</si:unit>'
        '<si:ellipsoidalRegion><si:covarianceMatrix><si:column><si:covariance><si:value>0.01</si:value>'
        '<si:unit>\\volt\\tothe{2}</si:unit></si:covariance><si:covariance><si:value>0</si:value>'
        '<si:unit>\\volt\\tothe{2}</si:unit></si:covariance></si:column><si:column><si:covariance>'
        '<si:value>0</si:value><si:unit>\\volt\\tothe{2}</si:unit></si:covariance><si:covariance>'
        '<si:value>0.01</si:value><si:unit>\\volt\\tothe{2}</si:unit></si:covariance></si:column>'
        '</si:covarianceMatrix><si:coverageFactor>2.45</si:coverageFactor>'
        '<si:coverageProbability>0.95</si:coverageProbability></si:ellipsoidalRegion></si:complex>',
    "hybrid with si:realList, uncertainty for the list":
        '<si:hybrid><si:realList><si:listMeasurementUncertaintyUnivariate><si:standardMU>'
        '<si:valueStandardMU>0.04</si:valueStandardMU></si:standardMU>'
        '</si:listMeasurementUncertaintyUnivariate><si:real><si:value>6.42</si:value>'
        '<si:unit>\\percent</si:unit></si:real></si:realList></si:hybrid>',
    # D-SI 2.2.1 spells this element "measurementUncertaintyUnivaraite" inside si:realList.
    "hybrid with si:realList, uncertainty for each value":
        '<si:hybrid><si:realList><si:real><si:value>6.42</si:value><si:unit>\\percent</si:unit>'
        '<si:measurementUncertaintyUnivaraite><si:standardMU><si:valueStandardMU>0.04</si:valueStandardMU>'
        '</si:standardMU></si:measurementUncertaintyUnivaraite></si:real></si:realList></si:hybrid>',
    # A covariance matrix (multivariate) for a list of values.
    "realListXMLList with a multivariate uncertainty":
        '<si:realListXMLList><si:valueXMLList>6.42 3.15</si:valueXMLList>'
        '<si:unitXMLList>\\percent \\percent</si:unitXMLList><si:measurementUncertaintyMultivariateXMLList>'
        '<si:ellipsoidalRegionMUXMLList><si:covarianceMatrixXMLList><si:columnXMLList><si:covarianceXMLList>'
        '<si:valueXMLList>0.0016 0.0001</si:valueXMLList><si:unitXMLList>\\percent\\tothe{2} \\percent\\tothe{2}'
        '</si:unitXMLList></si:covarianceXMLList></si:columnXMLList><si:columnXMLList><si:covarianceXMLList>'
        '<si:valueXMLList>0.0001 0.0009</si:valueXMLList><si:unitXMLList>\\percent\\tothe{2} \\percent\\tothe{2}'
        '</si:unitXMLList></si:covarianceXMLList></si:columnXMLList></si:covarianceMatrixXMLList>'
        '<si:coverageFactorXMLList>2.45</si:coverageFactorXMLList>'
        '<si:coverageProbabilityXMLList>0.95</si:coverageProbabilityXMLList></si:ellipsoidalRegionMUXMLList>'
        '</si:measurementUncertaintyMultivariateXMLList></si:realListXMLList>',
}


def _certified_value(tree, form, single=False):
    """Replace the value of the first certified list quantity by a fragment of FRAGMENTS.

    With single=True the quantity is then moved to data/quantity, as a single value.
    """
    quantity = tree.xpath(
        "//drmd:properties[@isCertified='true']//drmd:result/drmd:data/drmd:list"
        "/drmd:quantity[1]", namespaces=NS)[0]
    real = quantity.xpath("si:real", namespaces=NS)[0]
    fragment = etree.fromstring(f'<w xmlns:si="{SI}">{FRAGMENTS[form]}</w>')[0]
    real.addprevious(fragment)
    quantity.remove(real)
    if single:
        lst = quantity.getparent()
        data = lst.getparent()
        data.remove(lst)
        data.append(quantity)
    return tree


def _heading_only(tree, xpath):
    """Keep only a dcc:name heading in a rich content element: no text, file or formula."""
    nodes = tree.xpath(xpath, namespaces=NS)
    assert nodes, f"test setup error: nothing matched {xpath}"
    for node in nodes:
        for child in list(node):
            node.remove(child)
        name = etree.SubElement(node, f"{{{DCC}}}name")
        etree.SubElement(name, f"{{{DCC}}}content").text = "Heading only"
    return tree


def _empty(tree, xpath):
    """Keep the element but remove all its content, leaving only spaces."""
    nodes = tree.xpath(xpath, namespaces=NS)
    assert nodes, f"test setup error: nothing matched {xpath}"
    for node in nodes:
        for child in list(node):
            node.remove(child)
        node.text = "   "
    return tree


# Documents that must raise nothing at all: valid variants of the certificate that a rule could
# wrongly reject. "1" is the other lexical form of xs:boolean true, so a block marked "1" is still
# a certified block; each uncertainty form that D-SI provides must be accepted.
CLEAN_CASES = [
    ("certified block marked isCertified=\"1\" instead of \"true\"", CRM,
     lambda t: set_attr(t, "//drmd:properties[@isCertified='true']", "isCertified", "1")),
    ("certified si:realListXMLList with only a multivariate uncertainty", CRM,
     lambda t: _certified_value(t, "realListXMLList with a multivariate uncertainty")),
    ("certified single si:constant with a standard uncertainty", CRM,
     lambda t: _certified_value(t, "constant with a standard uncertainty", single=True)),
    ("certified single si:complex with an ellipsoidal region", CRM,
     lambda t: _certified_value(t, "complex with an ellipsoidal region", single=True)),
    ("certified si:hybrid with si:realList, uncertainty for the list", CRM,
     lambda t: _certified_value(t, "hybrid with si:realList, uncertainty for the list")),
    ("certified si:hybrid with si:realList, uncertainty for each value", CRM,
     lambda t: _certified_value(t, "hybrid with si:realList, uncertainty for each value")),
]


def _add_material_without_description(tree):
    """Add a second material, a copy of the first without description and without ids.

    RMC-011 must check every material, not only that some material has a description.
    """
    first = tree.xpath("//drmd:materials/drmd:material[1]", namespaces=NS)[0]
    second = copy.deepcopy(first)
    for node in second.iter():
        for attribute in ("id", "refId"):
            node.attrib.pop(attribute, None)
    for description in second.xpath("drmd:description", namespaces=NS):
        second.remove(description)
    first.addnext(second)
    return tree


def _replace_first_certified_with_xmllist(tree, keep_in_list=False):
    """Swap a certified si:real for an si:realListXMLList that carries no uncertainty.

    By default the quantity becomes a single value (data/quantity); with keep_in_list it stays
    in data/list/quantity. RMC-008 must fire in both places.
    """
    return _certified_value(tree, "realListXMLList", single=not keep_in_list)


def _make_certified_hybrid(tree, keep_in_list=False, inner="real"):
    """Put an si:hybrid holding an uncertainty-free number into the certified block.

    By default the quantity becomes a single value (data/quantity); with keep_in_list it stays
    in data/list/quantity, where a document that lists its results as a table has it. RMC-009
    must fire in both places.
    """
    form = "hybrid with si:realListXMLList" if inner == "realListXMLList" else "hybrid with si:real"
    return _certified_value(tree, form, single=not keep_in_list)


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

    print("\nClean variants: each must raise nothing at all")
    for description, base, mutate in CLEAN_CASES:
        tree = copy.deepcopy(load(base))
        mutate(tree)
        findings = run_schematron(tree, namespaces, phases, patterns, "all")
        status = "OK" if not findings else "UNEXPECTED"
        print(f"  {status:11} {description}: {len(findings)} finding(s)")
        if findings:
            failures.append(f"{description} raised {sorted({f['rule_id'] for f in findings})}")

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
