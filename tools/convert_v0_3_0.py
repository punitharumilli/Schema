#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
convert_v0_3_0.py: convert a DRMD document of release v0.3.0 to DRMD 1.0.0.

The conversion itself is the XSLT 1.0 stylesheet convert-v0.3.0-to-v1.0.0.xsl next to this file;
this script only runs it with lxml and checks the result against drmd.xsd. What the conversion
changes is listed at the top of the stylesheet.

DRMD 1.0.0 requires a documentVersion (ISO 33401:2024, 5.2.13), which v0.3.0 did not have, so it
must be given: a version number, an approval date, or both.

Usage
    python tools/convert_v0_3_0.py old.xml converted.xml --document-version 1
    python tools/convert_v0_3_0.py old.xml converted.xml --document-version 2024-05-15 --validate

With --validate the converted document also goes through both validation steps of
tools/validate.py (XML Schema and business rules), and the exit code is the one of validate.py.

Exit codes
    0  converted, and valid against drmd.xsd (with --validate: COMPLIANT)
    1  with --validate only: NOT COMPLIANT
    2  not converted (not a v0.3.0 document, no documentVersion, unreadable file), or the result
       is not valid against drmd.xsd
    3  with --validate only: TO CONFIRM
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
XSL = HERE / "convert-v0.3.0-to-v1.0.0.xsl"
XSD = HERE.parent / "drmd.xsd"
CATALOG = HERE.parent / "catalog.xml"

# drmd.xsd finds the QUDT quantity kinds through catalog.xml; libxml2 reads the catalog list when
# lxml is first imported, so it is set here, as in validate.py.
if CATALOG.is_file() and str(CATALOG) not in os.environ.get("XML_CATALOG_FILES", "").split():
    os.environ["XML_CATALOG_FILES"] = (os.environ.get("XML_CATALOG_FILES", "") + " " + str(CATALOG)).strip()

from lxml import etree  # noqa: E402


def _parser() -> etree.XMLParser:
    # Untrusted input: no DTD, no entity expansion, no network access.
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)


def convert(source: Path, document_version: str) -> tuple[etree._ElementTree, list[str]]:
    """Return the converted document and the messages of the stylesheet."""
    doc = etree.parse(str(source), _parser())
    if doc.docinfo.doctype:
        raise ValueError("documents with a DOCTYPE are not processed")
    transform = etree.XSLT(etree.parse(str(XSL)))
    try:
        result = transform(doc, documentVersion=etree.XSLT.strparam(document_version or ""))
    except etree.XSLTApplyError as exc:
        messages = [e.message for e in transform.error_log] or [str(exc)]
        raise ValueError(messages[0]) from None
    return result, [e.message for e in transform.error_log]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Convert a DRMD v0.3.0 document to DRMD 1.0.0.")
    ap.add_argument("source", type=Path, help="DRMD v0.3.0 document")
    ap.add_argument("target", type=Path, help="file to write the DRMD 1.0.0 document to")
    ap.add_argument("--document-version", default="", metavar="TEXT",
                    help="revision of the document (required, for example 1 or the approval date)")
    ap.add_argument("--validate", action="store_true",
                    help="also run tools/validate.py (XML Schema and business rules) on the result")
    args = ap.parse_args(argv)

    try:
        result, messages = convert(args.source, args.document_version)
    except (OSError, etree.XMLSyntaxError, ValueError) as exc:
        print(f"Not converted: {exc}", file=sys.stderr)
        return 2
    for m in messages:
        print(f"Note: {m}")

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    if not schema.validate(result):
        print("The converted document is not valid against drmd.xsd:", file=sys.stderr)
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}", file=sys.stderr)
        return 2

    args.target.write_bytes(etree.tostring(result, xml_declaration=True, encoding="UTF-8", pretty_print=True))
    print(f"Converted {args.source} to {args.target} (DRMD 1.0.0, valid against drmd.xsd).")
    if not args.validate:
        print(f"Next: python tools/validate.py {args.target}  (business rules of ISO 33401:2024)")
        return 0
    return subprocess.call([sys.executable, str(HERE / "validate.py"), str(args.target)])


if __name__ == "__main__":
    sys.exit(main())
