#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
validate.py: run the two mandatory DRMD validation steps over one or more XML instances.

    Step 1  XML Schema (drmd.xsd)            structural validation
    Step 2  Schematron (drmd-business-rules.sch)  ISO 33401:2024 business rules

A document is fully compliant only when step 1 passes and step 2 reports no assertion with
role "error" or "conditional-error". Warnings do not make a document non-compliant, but they
mark information that ISO 33401:2024 recommends.

Usage
    python tools/validate.py examples/*.xml
    python tools/validate.py --phase rmc-only doc.xml
    python tools/validate.py --json report.json doc.xml

Requirements
    lxml. Nothing else: the Schematron rules are evaluated directly, so no XSLT skeleton,
    no Saxon and no network access are needed. This works because every test expression in
    drmd-business-rules.sch is written to be valid XPath 1.0 as well as XPath 2.0.

Exit codes
    0  every document is compliant (errors and conditional errors: none)
    1  at least one document failed
    2  the validator could not run (missing file, unreadable schema, bad arguments)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent
XSD = SCHEMA_DIR / "drmd.xsd"
SCH = SCHEMA_DIR / "drmd-business-rules.sch"
CATALOG = SCHEMA_DIR / "catalog.xml"

SCH_NS = "http://purl.oclc.org/dsdl/schematron"

# Severities that make a document non-compliant, in report order.
BLOCKING = ("error", "conditional-error")
SEVERITY_ORDER = {"error": 0, "conditional-error": 1, "warning": 2, "info": 3}


def _fail(message: str) -> None:
    print(f"validate.py: {message}", file=sys.stderr)
    raise SystemExit(2)


# The catalog must be in the environment before libxml2 resolves the schema imports,
# otherwise the vendored copies in supporting/ are not found and the schema will not compile.
if CATALOG.is_file():
    existing = os.environ.get("XML_CATALOG_FILES", "")
    if str(CATALOG) not in existing.split():
        os.environ["XML_CATALOG_FILES"] = (existing + " " + str(CATALOG)).strip()

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    _fail("lxml is required. Install it with: pip install lxml")


def _context_to_select(context: str) -> str:
    """Turn a Schematron rule context into an XPath that selects the nodes it matches.

    A rule's @context is an XSLT match pattern, not a location path evaluated from the root:
    "drmd:materials/drmd:material" matches every drmd:material whose parent is drmd:materials,
    wherever it sits in the tree. Anchoring a relative pattern with "//" reproduces that
    behaviour exactly for the patterns used in drmd-business-rules.sch. Patterns that already
    start at the root are left alone.
    """
    context = (context or "").strip()
    if context.startswith("/") or context.startswith("("):
        return context
    return "//" + context


def load_schematron(path: Path):
    """Read the Schematron file into (namespaces, phases, patterns)."""
    doc = etree.parse(str(path))
    root = doc.getroot()

    namespaces = {
        ns.get("prefix"): ns.get("uri")
        for ns in root.findall(f"{{{SCH_NS}}}ns")
    }

    phases = {}
    for phase in root.findall(f"{{{SCH_NS}}}phase"):
        phases[phase.get("id")] = [
            active.get("pattern") for active in phase.findall(f"{{{SCH_NS}}}active")
        ]

    patterns = []
    for pattern in root.findall(f"{{{SCH_NS}}}pattern"):
        rules = []
        for rule in pattern.findall(f"{{{SCH_NS}}}rule"):
            checks = []
            for assertion in rule.findall(f"{{{SCH_NS}}}assert"):
                checks.append(
                    {
                        "kind": "assert",
                        "id": assertion.get("id") or "(no id)",
                        "role": (assertion.get("role") or "error").lower(),
                        "test": assertion.get("test"),
                        "message": " ".join((assertion.text or "").split()),
                    }
                )
            for report in rule.findall(f"{{{SCH_NS}}}report"):
                checks.append(
                    {
                        "kind": "report",
                        "id": report.get("id") or "(no id)",
                        "role": (report.get("role") or "warning").lower(),
                        "test": report.get("test"),
                        "message": " ".join((report.text or "").split()),
                    }
                )
            context = rule.get("context")
            rules.append(
                {
                    "context": context,
                    "select": _context_to_select(context),
                    "checks": checks,
                }
            )
        patterns.append({"id": pattern.get("id"), "rules": rules})

    return namespaces, phases, patterns


def run_schematron(tree, namespaces, phases, patterns, phase="all"):
    """Evaluate the rules against a parsed instance and return a list of findings.

    Schematron semantics implemented here: within one pattern each node is handled by the
    FIRST rule whose context selects it; later rules in the same pattern do not fire for
    that node. Patterns are independent of one another.
    """
    if phase not in ("#ALL", "all") and phase not in phases:
        _fail(f"unknown phase {phase!r}. Available: {', '.join(sorted(phases))}")
    active = None if phase in ("#ALL",) else phases.get(phase)

    findings = []
    for pattern in patterns:
        if active is not None and pattern["id"] not in active:
            continue
        seen = set()
        for rule in pattern["rules"]:
            try:
                nodes = tree.xpath(rule["select"], namespaces=namespaces)
            except etree.XPathEvalError as exc:
                _fail(f"cannot evaluate rule context {rule['context']!r}: {exc}")
            for node in nodes:
                # Identify the node by its canonical path. Python's id() is unusable here:
                # lxml hands out short-lived proxy objects, so a freed proxy's address can be
                # reused by the proxy for a completely different element, which would silently
                # suppress a later rule.
                key = tree.getpath(node)
                if key in seen:
                    continue  # already handled by an earlier rule in this pattern
                seen.add(key)
                for check in rule["checks"]:
                    try:
                        result = node.xpath(check["test"], namespaces=namespaces)
                    except etree.XPathEvalError as exc:
                        _fail(f"cannot evaluate test of {check['id']}: {exc}")
                    holds = bool(result) if not isinstance(result, bool) else result
                    fired = (not holds) if check["kind"] == "assert" else holds
                    if fired:
                        findings.append(
                            {
                                "rule_id": check["id"],
                                "severity": check["role"],
                                "pattern": pattern["id"],
                                "location": tree.getpath(node),
                                "line": node.sourceline,
                                "message": check["message"],
                            }
                        )
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["rule_id"]))
    return findings


def validate_one(path: Path, xmlschema, sch, phase):
    namespaces, phases, patterns = sch
    result = {
        "document": str(path),
        "xsd_valid": False,
        "xsd_errors": [],
        "schematron_findings": [],
        "compliant": False,
    }

    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        result["xsd_errors"] = [f"not well-formed XML: {exc}"]
        return result

    result["xsd_valid"] = bool(xmlschema.validate(tree))
    if not result["xsd_valid"]:
        result["xsd_errors"] = [
            f"line {e.line}: {e.message}" for e in xmlschema.error_log
        ]

    result["schematron_findings"] = run_schematron(
        tree, namespaces, phases, patterns, phase
    )
    blocking = [f for f in result["schematron_findings"] if f["severity"] in BLOCKING]
    result["compliant"] = result["xsd_valid"] and not blocking
    return result


LABEL = {
    "error": "ERROR",
    "conditional-error": "COND-ERROR",
    "warning": "WARNING",
    "info": "INFO",
}


def print_report(result):
    name = Path(result["document"]).name
    print(f"\n{name}")
    print("-" * max(len(name), 60))

    if result["xsd_valid"]:
        print("  Step 1  XSD              PASS")
    else:
        print("  Step 1  XSD              FAIL")
        for message in result["xsd_errors"][:20]:
            print(f"            {message}")
        if len(result["xsd_errors"]) > 20:
            print(f"            ... and {len(result['xsd_errors']) - 20} more")

    findings = result["schematron_findings"]
    blocking = [f for f in findings if f["severity"] in BLOCKING]
    if not findings:
        print("  Step 2  Schematron       PASS  (no assertions raised)")
    else:
        verdict = "FAIL" if blocking else "PASS with warnings"
        print(f"  Step 2  Schematron       {verdict}")
        for finding in findings:
            label = LABEL.get(finding["severity"], finding["severity"].upper())
            print(f"            [{label:10}] {finding['rule_id']}  line {finding['line']}")
            print(f"                         {finding['location']}")
            print(f"                         {finding['message']}")

    print(f"  RESULT: {'COMPLIANT' if result['compliant'] else 'NOT COMPLIANT'}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate DRMD instances against drmd.xsd and drmd-business-rules.sch."
    )
    parser.add_argument("documents", nargs="+", help="XML instance files to validate")
    parser.add_argument(
        "--phase",
        default="all",
        help="Schematron phase to run: all, rmc-only, pis-only (default: all)",
    )
    parser.add_argument("--json", metavar="FILE", help="also write the report as JSON")
    args = parser.parse_args(argv)

    for required in (XSD, SCH):
        if not required.is_file():
            _fail(f"{required} not found. Run this script from inside the schema repository.")

    try:
        xmlschema = etree.XMLSchema(etree.parse(str(XSD)))
    except etree.XMLSchemaParseError as exc:
        _fail(
            f"drmd.xsd did not compile: {exc}\n"
            f"Check that supporting/ is complete and that {CATALOG.name} is present. "
            f"Run tools/vendor_supporting_schemas.py --check for a diagnosis."
        )

    sch = load_schematron(SCH)

    results = []
    for name in args.documents:
        path = Path(name)
        if not path.is_file():
            _fail(f"{path} not found")
        result = validate_one(path, xmlschema, sch, args.phase)
        results.append(result)
        print_report(result)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nJSON report written to {args.json}")

    failed = [r for r in results if not r["compliant"]]
    print(f"\n{len(results) - len(failed)} of {len(results)} document(s) compliant.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
