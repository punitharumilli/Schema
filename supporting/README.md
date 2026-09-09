# Supporting schemas

DRMD does not invent its own way of writing a measured value, an address or a signature. It
reuses four external vocabularies. Every file in this folder is a dependency of `drmd.xsd`:
without them the schema does not compile, and validation is impossible.

These files are **vendored**: committed to this repository rather than fetched at validation
time. That is deliberate. Two of the upstream files resolve their own imports over the network,
so a validator without this folder either needs internet access or silently skips imports and
then fails. Worse, a network fetch can return a different revision from one run to the next, so
two people validating the same document could reach different verdicts. With the files committed
here and `../catalog.xml` redirecting the remote addresses to them, validation is offline and
reproducible.

| File | Supplies | Namespace | Upstream |
|---|---|---|---|
| `dcc.xsd` | Shared certificate building blocks: multilingual text, rich content with attachments and formulas, contacts, responsible persons, embedded binary data, used methods, measurement metadata, and the quantity container that `drmd:quantityType` extends | `https://ptb.de/dcc` | Digital Calibration Certificate (DCC) v3.3.0, Physikalisch-Technische Bundesanstalt (PTB), https://www.ptb.de/dcc/ |
| `SI_Format.xsd` | Every numeric value, unit and measurement uncertainty | `https://ptb.de/si` | Digital System of Units (D-SI) v2.2.1, PTB, https://www.ptb.de/si/ |
| `quantitykind.xsd` | The `qudt:quantitykind` type that D-SI gives to `si:quantityTypeQUDT` | `http://qudt.org/vocab/` | See the note below |
| `xmldsig-core-schema.xsd` | The `ds:Signature` element used at the document root | `http://www.w3.org/2000/09/xmldsig#` | XML Signature Syntax and Processing (Second Edition), W3C Recommendation, https://www.w3.org/TR/xmldsig-core/ |
| `qudt.ttl` | Source vocabulary from which `quantitykind.xsd` is generated | none | QUDT Quantity Kind Vocabulary v3.0.0, http://qudt.org/vocab/quantitykind |

## Licences

`dcc.xsd` and `SI_Format.xsd` are distributed by PTB under the GNU Lesser General Public
License v3.0. `xmldsig-core-schema.xsd` is a W3C Recommendation schema, distributed under the
W3C Software Licence. QUDT is published by the QUDT.org project under the Creative Commons
Attribution 4.0 International licence (CC BY 4.0). Vendoring a file here does not change its
terms; each remains the property of its publisher and is redistributed under its own licence.

## A note on `xmldsig-core-schema.xsd`

This file is the W3C schema, with **one modification**: the `<!DOCTYPE schema ...>` declaration
and its internal subset have been removed.

**Why.** As published, the file opens with a DOCTYPE referencing the external `XMLSchema.dtd`.
Xerces, the XSD validator built into the JDK, and so the one most JVM pipelines use, cannot
fetch that DTD and refuses to read the file, reporting only *"could not find the document"*. The
knock-on effect is severe and points at the wrong place: `ds:Signature` then has no declaration,
and **the whole of `drmd.xsd` fails to compile**, with an error that names `drmd.xsd` rather than
the signature schema. libxml2 tolerates the DOCTYPE, so the problem is invisible if you only ever
validate with `xmllint`.

**Why removing it is safe.** This is verifiable, not a judgement call:

* the internal subset declares one `ATTLIST` default, `xmlns:ds`, which the root `<schema>`
  element already declares explicitly, so it changes nothing;
* it declares the entities `&dsig;`, `%p;` and `%s;`, none of which the file uses anywhere
  (zero occurrences of each);
* the set of top-level schema components is identical before and after: 49 components either way.

Both validators accept the modified file, so nothing is lost and JVM validation goes from
impossible to working.

**Reproducing it.** `tools/vendor_supporting_schemas.py --refresh` downloads the pristine W3C file
and strips the DOCTYPE automatically, so a refresh cannot silently reintroduce the breakage. To do
it by hand:

```bash
curl -sO https://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd
python - <<'EOF'
import re
s = open('xmldsig-core-schema.xsd', encoding='utf-8').read()
open('xmldsig-core-schema.xsd', 'w', encoding='utf-8').write(
    re.sub(r'<!DOCTYPE\s+schema[\s\S]*?\]>\s*', '', s, count=1))
EOF
```

## A note on `quantitykind.xsd`

This one file is **a local substitute, not a copy of the upstream file.**

D-SI v2.2.1 declares `si:quantityTypeQUDT` (and its list variants) with type
`qudt:quantitykind`, imported from `https://www.ptb.de/si/v2.2.1/qudt/quantitykind.xsd`. If that
type cannot be resolved, an element declaration in D-SI refers to a type that does not exist and
**the whole of `drmd.xsd` fails to compile**, not just the QUDT part.

The file here is generated from `qudt.ttl` by `../tools/vendor_supporting_schemas.py`. It defines
`qudt:quantitykind` as a restriction of `xs:token` enumerating all 1158 quantity kinds of QUDT
v3.0.0, in both accepted spellings:

* the QUDT local name, which is the recommended form, `MassFraction`
* the full QUDT IRI, `http://qudt.org/vocab/quantitykind/MassFraction`

It is written to accept everything the upstream file is expected to accept, so a document that
validates against PTB's published `quantitykind.xsd` also validates here. To replace it with
PTB's official file once you have network access to `www.ptb.de`:

```bash
python tools/vendor_supporting_schemas.py --refresh --only quantitykind.xsd
python tools/vendor_supporting_schemas.py --check
```

`catalog.xml` maps the same namespace either way, so no other file changes.

The type restricts `xs:token` rather than `xs:anyURI` or a union. That is a requirement, not a
style choice: `si:quantityTypeQUDT` substitutes for the abstract element `si:quantityType`, whose
type is `xs:string`, and XSD 1.0 requires a substituting element's type to be validly derived
from the head element's type. `xs:anyURI` is not derived from `xs:string`, and a union type is
not a valid derivation either, using one makes the schema fail to compile.

## Updating

```bash
# What is here, and does drmd.xsd still compile offline?
python tools/vendor_supporting_schemas.py --check

# Pull fresh copies from PTB, W3C and QUDT
python tools/vendor_supporting_schemas.py --refresh

# Rebuild quantitykind.xsd after updating qudt.ttl
python tools/vendor_supporting_schemas.py --generate-quantitykind
```

Always read the diff before committing a refresh. An upstream change can alter what counts as a
valid DRMD document, so a refresh is a schema change and belongs in `../CHANGELOG.md`. After any
refresh, run the test suite: `python tests/test_rules.py` and
`python tools/validate.py examples/*.xml`.

## Do not hand-edit these files

Apart from `quantitykind.xsd`, which is generated, and the single documented DOCTYPE removal in
`xmldsig-core-schema.xsd`, these are upstream files kept byte-for-byte as published. Editing them
would make the local copy diverge from the standard it claims to implement, and a document
validated here would then not be portable. If DRMD needs behaviour that
an upstream schema does not offer, express it in `drmd.xsd` or in `drmd-business-rules.sch`, or
raise the issue with the upstream maintainer.
