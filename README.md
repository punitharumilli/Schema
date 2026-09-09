# DRMD Schema

**Digital Reference Material Document**, an XML format for reference material certificates and
product information sheets, aligned with **ISO 33401:2024**, *Reference materials: Contents of
certificates, labels and accompanying documentation*.

This repository holds the schema and its validation rules. The best practice guidelines for
producers, software vendors, laboratories and auditors live in the companion documentation
repository.

```
schema/
├── drmd.xsd                     the schema: structure, types, cardinalities
├── drmd-business-rules.sch      Schematron: the ISO 33401:2024 requirements XSD cannot express
├── catalog.xml                  XML catalog, so validation runs offline and reproducibly
├── CHANGELOG.md
├── supporting/                  vendored third-party schemas (DCC, D-SI, QUDT, XMLDSig)
├── examples/                    two worked, fully compliant instances
├── tests/                       proof that every rule fires when it should
└── tools/                       validate.py, vendor_supporting_schemas.py
```

---

## Quick start

```bash
pip install lxml

# Validate the worked examples (XSD + Schematron in one pass)
python tools/validate.py examples/*.xml

# Validate your own document
python tools/validate.py my-certificate.xml

# Check that the vendored dependencies are complete and the schema compiles offline
python tools/vendor_supporting_schemas.py --check

# Prove every business rule still fires
python tests/test_rules.py
```

---

## Two document types

The type is set by `titleOfTheDocument`, and it changes which rules apply.

| Type | XML value | What it is |
|---|---|---|
| Reference Material Certificate | `referenceMaterialCertificate` | Accompanies a **certified** reference material (CRM). At least one property value carries a measurement uncertainty, and the document states metrological traceability. |
| Product Information Sheet | `productInformationSheet` | Accompanies **any other** reference material (ISO 33401:2024, 3.3). Uncertainty and traceability are permitted but not required. |

A common misunderstanding is worth stating plainly: **values on a product information sheet are
not approximate.** They are real measurement results. What distinguishes a certificate is not the
quality of the number but the formal apparatus around it: a stated uncertainty and a stated
traceability chain. A product information sheet may include both voluntarily, and doing so is
good practice; what it may never do is mark a properties block `isCertified="true"`, because that
would present the material as certified when it is not.

---

## Why two validation files

`drmd.xsd` describes the structure that both document types share. It can say *"validity is
required"*. It cannot say *"if this is a certificate, then metrological traceability is
required"*. XSD 1.0 has no way to make a requirement depend on the value of another element.

`drmd-business-rules.sch` makes exactly those conditional statements. It reads
`titleOfTheDocument` and applies the ISO 33401:2024 requirements for that document type.

**Both must pass.** An XSD-valid document can still be non-compliant with ISO 33401:2024, and
running the XSD alone gives a false sense of correctness.

```
your-document.xml
       │
       ├──► drmd.xsd                  structure, names, data types, cardinalities
       │
       └──► drmd-business-rules.sch   ISO 33401:2024 requirements, per document type
                                      + severity: error / conditional-error / warning
```

---

## Severity: the four-tier model

Each Schematron rule carries a `role` that maps directly to an ISO 33401:2024 requirement level.

| Tier | `role` | ISO level | Meaning |
|---|---|---|---|
| Hard error | `error` | Mandatory | The document is non-compliant. The element is required without exception. |
| Conditional error | `conditional-error` | Mandatory whenever applicable | Required **if it applies to this material**. Where it genuinely does not apply, absence is acceptable, and the producer, not the validator, makes that judgement. |
| Warning | `warning` | Recommended | The document is compliant. The element is recommended and improves usability. |
| No rule | none | Optional | Accepted when present, never flagged when absent. |

`conditional-error` is a custom role. The Schematron specification allows any string in `@role`,
and standard processors report it as an ordinary failed assertion in their SVRL output. A
validation pipeline should read the `role` attribute and classify accordingly. A tool that
treats every failed assertion as a hard error will wrongly reject documents where a conditional
requirement genuinely does not apply.

### What to do with a conditional error

It is a question, not a verdict: *does this apply to your material?*

* **Yes, it applies**: add the information. The document is not compliant without it.
* **No, it does not apply**: record why. Do not leave the reader guessing: a
  `commutability` statement reading "commutability has not been assessed for this material" is
  more useful, and more honest, than an absent element. Where the element must genuinely be
  omitted, note the justification in your own quality records, because an auditor will ask.

---

## Document structure

```
digitalReferenceMaterialDocument              @schemaVersion required
│
├── administrativeData                                        [both]
│   ├── coreData
│   │   ├── titleOfTheDocument     5.2.2                      [both]
│   │   ├── uniqueIdentifier       identifies the DOCUMENT    [both]
│   │   ├── documentVersion        5.2.13                     [both]
│   │   ├── documentIdentifiers                               [optional]
│   │   └── validity               5.2.8                      [both]
│   ├── referenceMaterialProducer  5.2.5                      [both]
│   └── respPersons                5.3.5   name + function    [CRM required, PIS optional]
│
├── materials                                                 [both]
│   └── material  (repeatable)
│       ├── name                   5.2.4                      [both]
│       ├── description            5.3.2                      [CRM required, PIS recommended]
│       ├── materialClass                                     [optional, repeatable]
│       ├── minimumSampleSize      5.2.7                      [mandatory whenever applicable]
│       ├── itemQuantities                                    [optional]
│       └── materialIdentifiers    5.2.3   identifies the RM  [both]
│
├── propertiesList                                            [both]
│   └── properties  (repeatable)          @isCertified, true only in a certificate
│       ├── name                                              [both]
│       ├── description                                       [optional]
│       ├── procedures             5.2.14 / 5.4.2             [mandatory whenever applicable]
│       ├── results                5.2.15 / 5.3.3             [both]
│       │   └── result  (repeatable) → data → quantity | list/quantity
│       └── measurementMetaData                               [optional]
│
├── statements                                                [both]
│   ├── intendedUse                5.2.6                      [both]
│   ├── commutability              5.2.9                      [mandatory whenever applicable]
│   ├── storageInformation         5.2.10                     [both]
│   ├── instructionsForHandlingAndUse  5.2.11                 [both]
│   ├── metrologicalTraceability   5.3.4                      [CRM required, PIS optional]
│   ├── healthAndSafetyInformation 5.4.3                      [recommended]
│   ├── subcontractors             5.4.4                      [optional]
│   ├── legalNotice                5.4.6                      [optional]
│   ├── referenceToCertificationReport 5.4.7                  [optional]
│   └── statement  (repeatable catch-all)                     [optional]
│
├── comment                                                   [optional]
├── document        embedded human-readable rendition         [optional]
└── ds:Signature    XMLDSig, repeatable                       [optional]
```

### Two identifiers that are easy to confuse

`coreData/uniqueIdentifier` identifies **the document**. `material/materialIdentifiers` carries
the unique identifier of **the reference material** required by ISO 33401:2024, 5.2.3, normally
a product code plus a batch or lot number.

They are not interchangeable, and using the document identifier for 5.2.3 is a real compliance
gap: one document can cover several materials, and one material is described by successive
document revisions. Rule DRMD-016 enforces the material identifier.

---

## How each ISO 33401:2024, Table 1 requirement is met

| Requirement | Subclause | Product info sheet | RM certificate | Enforced by |
|---|---|---|---|---|
| Title of the document | 5.2.2 | Mandatory | Mandatory | XSD (`titleOfTheDocument`, enumerated) + DRMD-001 |
| Unique identifier of the RM | 5.2.3 | Mandatory | Mandatory | **DRMD-016** (`material/materialIdentifiers`) |
| Name of the RM | 5.2.4 | Mandatory | Mandatory | XSD + DRMD-002, DRMD-007 |
| Name and contact details of the RM producer | 5.2.5 | Mandatory | Mandatory | XSD + DRMD-010 |
| Intended use | 5.2.6 | Mandatory | Mandatory | XSD + DRMD-004 |
| Minimum sample size | 5.2.7 | Mandatory whenever applicable | Mandatory whenever applicable | DRMD-008 (conditional-error) |
| Period of validity | 5.2.8 | Mandatory | Mandatory | XSD + DRMD-012 |
| Commutability | 5.2.9 | Mandatory whenever applicable | Mandatory whenever applicable | DRMD-013 (conditional-error) |
| Storage information | 5.2.10 | Mandatory | Mandatory | XSD + DRMD-005 |
| Instructions for handling and use | 5.2.11 | Mandatory | Mandatory | XSD + DRMD-006 |
| Document components | 5.2.12 | Mandatory | Mandatory | Satisfied structurally, see the note below |
| Document version | 5.2.13 | Mandatory | Mandatory | XSD + **DRMD-011** |
| Measurement procedures, operationally defined measurands | 5.2.14 | Mandatory whenever applicable | Mandatory whenever applicable | DRMD-014 (conditional-error) |
| Property of interest | 5.2.15 | Mandatory | Mandatory | DRMD-003, DRMD-009 |
| **Description of the material** | **5.3.2** | Recommended | **Mandatory** | RMC-011 (error) / PIS-005 (warning) |
| **Property value and associated uncertainty** | **5.3.3** | Optional | **Mandatory** | RMC-002, RMC-006 … RMC-009 |
| **Metrological traceability** | **5.3.4** | Optional | **Mandatory** | RMC-001 |
| **Name and function of the approving officer** | **5.3.5** | Optional | **Mandatory** | RMC-010 (name) + **RMC-012** (function) |
| Measurement procedures, non-operationally defined measurands | 5.4.2 | Recommended | Recommended | RMC-005 (warning); also covered by DRMD-014 |
| Health and safety information | 5.4.3 | Recommended | Recommended | DRMD-015 (warning) |
| Subcontractors | 5.4.4 | Optional | Optional | XSD element, no rule |
| Indicative values | 5.4.5 | Optional | Optional | A properties block with `isCertified` false or omitted |
| Legal notice | 5.4.6 | Optional | Optional | XSD element, no rule |
| Reference to a certification report | 5.4.7 | Optional | Optional | XSD element, no rule |

**Document components (5.2.12).** ISO 33401:2024 asks that all components be recognisable as part
of the whole document and that the end be clearly marked. A DRMD instance meets this by being a
single well-formed XML document with one root element: its start and end are explicit, and every
component is inside it by construction. `@schemaVersion` states which specification the components
follow, `documentVersion` which revision, and `uniqueIdentifier` binds them to one instance. No
Schematron rule is defined, because an assertion that always holds would only add noise.

**Clause 6, Labels.** ISO 33401:2024 Clause 6 governs the physical label on the container, not the
electronic document, so it is out of scope for the schema. It matters for producers all the same:
the label must allow the right RM document to be identified, which in practice means printing the
identifier that appears in `material/materialIdentifiers`. Keeping those values byte-identical is
what makes the link between the physical unit and the digital document work.

---

## Complete rule catalogue

### Shared rules (every DRMD document)

| Rule | Severity | ISO | What it checks |
|---|---|---|---|
| DRMD-001 | error | 5.2.2 | `titleOfTheDocument` is declared |
| DRMD-002 | error | 5.2.4 | At least one `material` entry exists |
| DRMD-003 | error | 5.2.15 | At least one `properties` block exists |
| DRMD-004 | error | 5.2.6 | `intendedUse` is present |
| DRMD-005 | error | 5.2.10 | `storageInformation` is present |
| DRMD-006 | error | 5.2.11 | `instructionsForHandlingAndUse` is present |
| DRMD-007 | error | 5.2.4 | Every material has a `name` |
| DRMD-008 | conditional-error | 5.2.7 | `minimumSampleSize` is present where applicable |
| DRMD-009 | error | 5.2.15 | Every `properties` block has at least one `result` |
| DRMD-010 | error | 5.2.5 | `referenceMaterialProducer` is identified |
| DRMD-011 | error | 5.2.13 | `documentVersion` is stated |
| DRMD-012 | error | 5.2.8 | `validity` is specified |
| DRMD-013 | conditional-error | 5.2.9 | `commutability` is stated where applicable |
| DRMD-014 | conditional-error | 5.2.14, 5.4.2 | `procedures` are documented where applicable |
| DRMD-015 | warning | 5.4.3 | `healthAndSafetyInformation` is included |
| DRMD-016 | error | 5.2.3 | Every material carries a `materialIdentifier` |

### Certificate-only rules

| Rule | Severity | ISO | What it checks |
|---|---|---|---|
| RMC-001 | error | 5.3.4 | `metrologicalTraceability` is present |
| RMC-002 | error | 5.3.3 | At least one `properties` block has `isCertified="true"` |
| RMC-003 | error | 5.3.3 | Property values exist |
| RMC-005 | warning | 5.4.2 | Certified blocks document their `procedures` |
| RMC-006 | error | 5.3.3 | Certified `si:real` quantities carry uncertainty |
| RMC-007 | error | 5.3.3 | Certified `si:real` inside a list carries uncertainty |
| RMC-008 | error | 5.3.3 | Certified `si:realListXMLList` carries uncertainty |
| RMC-009 | error | 5.3.3 | Every `si:real` inside a certified `si:hybrid` carries uncertainty |
| RMC-010 | error | 5.3.5 | `respPersons` lists the approving officer |
| RMC-011 | error | 5.3.2 | Every material has a `description` |
| RMC-012 | error | 5.3.5 | At least one responsible person states a function (`dcc:role`) |

### Product information sheet rules

| Rule | Severity | ISO | What it checks |
|---|---|---|---|
| PIS-001 | error | 3.3 | No `properties` block is marked `isCertified="true"` |
| PIS-002 | error | 5.2.15 | Results exist where values are assigned |
| PIS-003 | error | 3.3 | No individual `properties` block claims certification |
| PIS-005 | warning | 5.3.2 | Every material has a `description` |

Rule identifiers are never reused. **RMC-004** and **PIS-004** were used during development and
are permanently retired; the gaps in the sequence are intentional.

---

## How misuse is prevented

| What someone tries | What happens |
|---|---|
| A certificate with no traceability statement | RMC-001 (error) |
| A certificate with no certified properties block | RMC-002 (error) |
| A certified value with no uncertainty | RMC-006 … RMC-009 (error) |
| A certificate with no approving officer, or with a name but no function | RMC-010, RMC-012 (error) |
| A product information sheet marked `isCertified="true"` | PIS-001 and PIS-003 (error) |
| A document with no identifier for the material itself | DRMD-016 (error) |
| A plain product information sheet with no traceability | Valid. Traceability is optional for that type. |

---

## Offline and reproducible validation

`drmd.xsd` depends on four external schemas, all vendored in `supporting/`. Two of them fetch
their own imports over the network. Without `catalog.xml`, a validator either needs internet
access or silently skips imports and then fails to compile the schema. A network fetch can also
return a different revision from one run to the next, so two people could reach different
verdicts on the same document.

`catalog.xml` redirects each remote address to the local copy. Point your tools at it:

```bash
export XML_CATALOG_FILES=/path/to/schema/catalog.xml
xmllint --noout --nonet --schema drmd.xsd my-document.xml
```

`tools/validate.py` sets this for you. See `supporting/README.md` for the provenance and licence
of each vendored file, and for the one file that is a locally generated substitute rather than a
copy (`quantitykind.xsd`).

---

## Validating from other toolchains

### Python (recommended)

```bash
python tools/validate.py my-document.xml --json report.json
```

`tools/validate.py` runs both steps, classifies findings by severity, prints XPath locations and
line numbers, and exits non-zero when a document is not compliant. It needs only `lxml`: the
Schematron rules are evaluated directly, so there is no XSLT skeleton to download and no network
access required.

If you prefer `lxml.isoschematron`, note that it implements the XSLT 1.0 binding and will refuse
a file declaring `queryBinding="xslt2"`. Every test expression in `drmd-business-rules.sch` is
deliberately written to be valid XPath 1.0 as well, so the rules themselves work under either
binding, but you would need to change the declared binding, or use a processor that supports
XSLT 2.0.

### xmllint (structure only)

```bash
XML_CATALOG_FILES=catalog.xml xmllint --noout --nonet --schema drmd.xsd my-document.xml
```

This is step 1 only. It does not check any ISO 33401:2024 business rule.

### Java / Xerces (step 1 in a JVM pipeline)

Xerces, the XSD validator built into the JDK, does **not** read libxml2's `XML_CATALOG_FILES`
environment variable. Give it the catalog explicitly, or it will try to fetch the PTB schemas over
the network and fail:

```java
import javax.xml.catalog.*;
import javax.xml.validation.*;
import javax.xml.transform.stream.StreamSource;
import java.io.File;
import java.nio.file.Path;

CatalogResolver resolver = CatalogManager.catalogResolver(
        CatalogFeatures.builder().with(CatalogFeatures.Feature.RESOLVE, "continue").build(),
        Path.of("catalog.xml").toUri());

SchemaFactory factory = SchemaFactory.newInstance("http://www.w3.org/2001/XMLSchema");
factory.setResourceResolver(resolver);
Schema schema = factory.newSchema(new File("drmd.xsd"));

Validator validator = schema.newValidator();
validator.setResourceResolver(resolver);
validator.validate(new StreamSource(new File("my-document.xml")));
```

Set an `ErrorHandler` on the **`SchemaFactory`** as well as on the `Validator`. Without one, a
schema that failed to compile surfaces as a confusing error about an unrelated element rather than
as the missing import that actually caused it.

Xerces is worth running even if your main pipeline is Python: it enforces IDREF integrity, which
libxml2 does not, so it catches a `@refId` typo that `xmllint` accepts silently.

### Saxon and the ISO Schematron skeleton (step 2 in any JVM pipeline)

```bash
# Compile the Schematron to XSLT (once)
java -jar saxon.jar -s:drmd-business-rules.sch \
     -xsl:iso_schematron_skeleton_for_xslt2.xsl -o:drmd-rules.xsl

# Validate a document; the output is SVRL
java -jar saxon.jar -s:my-document.xml -xsl:drmd-rules.xsl -o:report.svrl
```

Then read `svrl:failed-assert` from the report and branch on its `@role`: `error` and
`conditional-error` make the document non-compliant, `warning` does not. Skeletons are published
at <https://github.com/Schematron/schematron>; Saxon-HE is at
<https://www.saxonica.com/download/java.xml>.

---

## Questions that come up

**Can a product information sheet include uncertainty?**
Yes. ISO 33401:2024 lists it as Optional for that document type, and stating it is good practice.
What is forbidden is marking the block as certified.

**Are product information sheet values approximate?**
No. They are valid measurement results. The difference is the formal uncertainty and traceability
statement, not the quality of the measurement.

**Why one schema instead of two?**
Both types share almost all of their structure. Two schemas would mean fixing every bug twice and
letting them drift apart. One structure plus conditional rules keeps them in step.

**A conditional error is blocking my document, but the requirement does not apply.**
Then say so in the document. An explicit statement that commutability was not assessed, or that a
minimum sample size does not apply to this material, is more useful to your reader than silence,
and it clears the rule. Suppressing the rule instead leaves the reader unable to tell the
difference between "not applicable" and "forgotten".

**Which version should a document declare?**
`1.0.0`, the first release.

---

## Licence

Copyright (c) 2024 Bundesanstalt für Materialforschung und -prüfung (BAM).
Licensed under the GNU Lesser General Public License v3.0.
The development of the Digital Reference Material Document (DRMD) is partially funded and
supported by the QI-Digital project.

Files in `supporting/` are third-party and remain under their own licences; see
`supporting/README.md`.
