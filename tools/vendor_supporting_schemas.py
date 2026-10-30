#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Bundesanstalt für Materialforschung und -prüfung (BAM)
# SPDX-License-Identifier: LGPL-3.0-only
"""
vendor_supporting_schemas.py: manage the third-party schemas in supporting/.

DRMD does not define measurement values, units, contacts or signatures itself. It reuses four
external vocabularies, and every one of them must be present locally for drmd.xsd to compile:

    supporting/dcc.xsd                 DCC, PTB                (shared certificate building blocks)
    supporting/SI_Format.xsd           D-SI, PTB               (values, units, uncertainties)
    supporting/quantitykind.xsd        QUDT quantity kinds     (required by D-SI)
    supporting/xmldsig-core-schema.xsd XML Signature, W3C      (document signatures)
    supporting/qudt.ttl                QUDT vocabulary source  (input for quantitykind.xsd)

Two of those files fetch their own dependencies over the network. catalog.xml redirects those
addresses to the copies in supporting/, so validation never touches the internet and always uses
the exact revisions committed to this repository.

Commands
    python tools/vendor_supporting_schemas.py --check
        Report what is present, what is missing, and whether drmd.xsd compiles offline.
        This is the command to run in CI.

    python tools/vendor_supporting_schemas.py --generate-quantitykind
        Rebuild supporting/quantitykind.xsd from supporting/qudt.ttl. Use after updating the
        QUDT vocabulary.

    python tools/vendor_supporting_schemas.py --refresh
        Download the upstream schemas listed in SOURCES and overwrite the local copies.
        Requires network access to www.ptb.de and www.w3.org. Review the diff before
        committing: an upstream change can alter what counts as a valid DRMD document.

Licences of the vendored files are recorded in supporting/README.md. Refreshing does not change
those terms; it only updates the bytes.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent
SUPPORTING = SCHEMA_DIR / "supporting"
CATALOG = SCHEMA_DIR / "catalog.xml"
XSD = SCHEMA_DIR / "drmd.xsd"

# Files that can be refreshed from upstream, and where they come from.
SOURCES = {
    "dcc.xsd": "https://www.ptb.de/dcc/v3.3.0/dcc.xsd",
    "SI_Format.xsd": "https://www.ptb.de/si/v2.2.1/SI_Format.xsd",
    "quantitykind.xsd": "https://www.ptb.de/si/v2.2.1/qudt/quantitykind.xsd",
    "xmldsig-core-schema.xsd": "https://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd",
    "qudt.ttl": "https://qudt.org/vocab/quantitykind.ttl",
}

REQUIRED = [
    "dcc.xsd",
    "SI_Format.xsd",
    "quantitykind.xsd",
    "xmldsig-core-schema.xsd",
]


# --------------------------------------------------------------------------- generate

def generate_quantitykind(ttl_path: Path, out_path: Path) -> int:
    """Build a quantitykind.xsd from the QUDT Turtle vocabulary.

    The result defines {http://qudt.org/vocab/}quantitykind, the type D-SI gives to
    si:quantityTypeQUDT and its list variants. It accepts both the QUDT local name
    (recommended, e.g. MassFraction) and the full QUDT IRI, so a document that validates
    against PTB's published file also validates against this one.

    The type restricts xs:token. That is not cosmetic: si:quantityTypeQUDT substitutes for the
    abstract element si:quantityType, whose type is xs:string, and XSD 1.0 requires the
    substituting element's type to be validly derived from the head's type. A union or an
    xs:anyURI restriction would break the substitution group and the schema would not compile.
    """
    if not ttl_path.is_file():
        raise SystemExit(f"{ttl_path} not found; cannot generate {out_path.name}")

    ttl = ttl_path.read_text(encoding="utf-8")
    kinds = sorted(set(re.findall(
        r"^quantitykind:([A-Za-z0-9_-]+)\s*\n\s+a qudt:QuantityKind\b", ttl, re.M)))
    if len(kinds) < 500:
        kinds = sorted(set(re.findall(r"^quantitykind:([A-Za-z0-9_-]+)", ttl, re.M)))
    if not kinds:
        raise SystemExit(f"no quantity kinds found in {ttl_path}; is it the QUDT vocabulary?")

    match = re.search(r'rdfs:label "QUDT Quantity Kind Vocabulary Version ([0-9.]+)"', ttl)
    version = match.group(1) if match else "unknown"

    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  quantitykind.xsd: QUDT quantity-kind type for the D-SI schema (SI_Format.xsd).

  WHY THIS FILE EXISTS
  SI_Format.xsd v2.2.1 declares si:quantityTypeQUDT, si:listQuantityTypeQUDT and
  si:quantityTypeQUDTXMLList with type qudt:quantitykind, and imports that type from
  https://www.ptb.de/si/v2.2.1/qudt/quantitykind.xsd. Without a resolvable definition of
  {{http://qudt.org/vocab/}}quantitykind the whole DRMD schema fails to compile, because an
  element declaration would reference an undefined type. Vendoring the type here makes
  DRMD validation fully offline and reproducible.

  PROVENANCE
  The permitted values below are generated from supporting/qudt.ttl, the QUDT Quantity Kind
  Vocabulary version {version} (http://qudt.org/vocab/quantitykind), by
  tools/vendor_supporting_schemas.py. {len(kinds)} quantity kinds are enumerated.

  STATUS: LOCAL SUBSTITUTE
  This is a local substitute for PTB's published quantitykind.xsd, not a copy of it. It is
  written to accept every value PTB's file is expected to accept: for each QUDT quantity kind
  both the local name (recommended, e.g. "MassFraction") and the full QUDT IRI
  (e.g. "http://qudt.org/vocab/quantitykind/MassFraction") are permitted. Run
  tools/vendor_supporting_schemas.py with the "refresh" option to replace this file with PTB's
  official one when network access to www.ptb.de is available; the XML catalog (catalog.xml)
  resolves the same namespace either way, so no other file needs to change.

  The type derives from xs:token, which is required: si:quantityTypeQUDT substitutes for the
  abstract element si:quantityType (type xs:string), and XSD 1.0 requires the substituting
  element's type to be validly derived from the head element's type.

  QUDT is published by the QUDT.org project under the Creative Commons Attribution 4.0
  International licence (CC BY 4.0). See https://qudt.org/ for terms and attribution.

  Generated: {datetime.date.today().isoformat()}
-->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:qudt="http://qudt.org/vocab/"
           targetNamespace="http://qudt.org/vocab/"
           elementFormDefault="qualified"
           version="{version}">

  <xs:simpleType name="quantitykind">
    <xs:annotation>
      <xs:documentation xml:lang="en">
        A QUDT quantity kind: the kind of quantity being reported (for example Mass,
        MassFraction, AmountOfSubstanceConcentration), independent of the unit in which the
        value is expressed. Give either the QUDT local name (recommended) or the full QUDT IRI.
      </xs:documentation>
    </xs:annotation>
    <xs:restriction base="xs:token">
"""
    body = "".join(f'      <xs:enumeration value="{k}"/>\n' for k in kinds)
    body += "\n      <!-- Full QUDT IRI form of the same quantity kinds -->\n"
    body += "".join(
        f'      <xs:enumeration value="http://qudt.org/vocab/quantitykind/{k}"/>\n'
        for k in kinds
    )
    footer = """    </xs:restriction>
  </xs:simpleType>

</xs:schema>
"""
    out_path.write_text(header + body + footer, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(SCHEMA_DIR)}: {len(kinds)} quantity kinds "
          f"from QUDT {version}")
    return len(kinds)


# --------------------------------------------------------------------------- refresh

DOCTYPE_RE = re.compile(r"<!DOCTYPE\s+schema[\s\S]*?\]>\s*", re.I)


def strip_doctype(data: bytes) -> bytes:
    """Remove the internal DTD subset from the W3C XML Signature schema.

    As published, xmldsig-core-schema.xsd opens with a DOCTYPE that references the external
    XMLSchema.dtd and declares an internal subset. Xerces, the XSD validator built into the JDK
    and therefore the one most JVM pipelines use, refuses to read the file: it cannot fetch
    XMLSchema.dtd, and reports only "could not find the document". The knock-on effect is severe
    and misleading: ds:Signature then has no declaration, and the WHOLE of drmd.xsd fails to
    compile with an error that names drmd.xsd rather than the real cause.

    Removing the DOCTYPE is safe, and this is verifiable rather than a matter of judgement:

      * the internal subset declares one ATTLIST default (xmlns:ds) that the root <schema>
        element already declares explicitly, so it changes nothing;
      * it declares the entities &dsig;, %p; and %s;, none of which the file uses at all (zero
        occurrences of each);
      * the set of top-level schema components is byte-for-byte identical before and after,
        at 49 components.

    libxml2 accepts the file either way, so nothing is lost by stripping it, and JVM validation
    goes from impossible to working. tests/test_rules.py and the CI workflow both check that the
    schema still compiles after a refresh.
    """
    return DOCTYPE_RE.sub(b"", data, count=1)


def refresh(names) -> int:
    problems = 0
    for name in names:
        url = SOURCES.get(name)
        if url is None:
            print(f"  SKIP    {name}: no upstream address recorded")
            continue
        target = SUPPORTING / name
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
        except Exception as exc:  # network, TLS, proxy, 404, all reported the same way
            print(f"  FAILED  {name}: {exc}")
            print(f"          (kept the existing local copy at {target.relative_to(SCHEMA_DIR)})")
            problems += 1
            continue
        note = ""
        if name == "xmldsig-core-schema.xsd":
            stripped = strip_doctype(data)
            if stripped != data:
                note = "  (DOCTYPE removed so the file loads in Xerces, see strip_doctype)"
                data = stripped
        target.write_bytes(data)
        print(f"  OK      {name}: {len(data):,} bytes from {url}{note}")
    return problems


# --------------------------------------------------------------------------- check

def check() -> int:
    problems = 0

    print("Files in supporting/")
    for name in REQUIRED + ["qudt.ttl"]:
        path = SUPPORTING / name
        if path.is_file():
            print(f"  present  {name:28} {path.stat().st_size:>10,} bytes")
        else:
            required = name in REQUIRED
            print(f"  MISSING  {name:28} {'(required)' if required else '(optional)'}")
            if required:
                problems += 1

    print("\nCatalog")
    if CATALOG.is_file():
        print(f"  present  {CATALOG.name}")
    else:
        print(f"  MISSING  {CATALOG.name} - remote imports will not resolve offline")
        problems += 1

    print("\nOffline compilation of drmd.xsd")
    try:
        import os
        os.environ["XML_CATALOG_FILES"] = str(CATALOG)
        from lxml import etree
        etree.XMLSchema(etree.parse(str(XSD)))
        print("  OK       drmd.xsd compiled with no network access")
    except ImportError:
        print("  SKIPPED  lxml is not installed, cannot test compilation")
    except Exception as exc:
        print(f"  FAILED   {exc}")
        problems += 1

    print()
    if problems:
        print(f"{problems} problem(s) found.")
    else:
        print("supporting/ is complete and drmd.xsd compiles offline.")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--check", action="store_true",
                        help="report what is present and whether drmd.xsd compiles offline")
    parser.add_argument("--generate-quantitykind", action="store_true",
                        help="rebuild supporting/quantitykind.xsd from supporting/qudt.ttl")
    parser.add_argument("--refresh", action="store_true",
                        help="download the upstream schemas and overwrite the local copies")
    parser.add_argument("--only", nargs="*", metavar="FILE",
                        help="with --refresh, limit to these file names")
    args = parser.parse_args(argv)

    if not any([args.check, args.generate_quantitykind, args.refresh]):
        parser.print_help()
        return 2

    SUPPORTING.mkdir(exist_ok=True)
    problems = 0

    if args.refresh:
        print("Refreshing vendored schemas from upstream")
        problems += refresh(args.only or list(SOURCES))
        print()

    if args.generate_quantitykind:
        generate_quantitykind(SUPPORTING / "qudt.ttl", SUPPORTING / "quantitykind.xsd")
        print()

    if args.check:
        problems += check()

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
