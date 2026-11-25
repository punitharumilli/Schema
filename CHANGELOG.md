# Changelog

The version applies to the specification as a whole. `drmd.xsd` and `drmd-business-rules.sch`
carry the same number and are released together, and instance documents declare it in
`@schemaVersion`.

Future releases follow semantic versioning:

* **Major** (`2.0.0`): a breaking structural change, such as an element renamed or removed, or a
  data type changed. Parsers need migration.
* **Minor** (`1.1.0`): backward-compatible additions, and conformance rules brought closer to
  ISO 33401. Existing parsers keep working, although a document that passed before may report a
  new finding.
* **Patch** (`1.0.1`): corrections to documentation and annotations, with no change to the
  content model.

---

## 1.0.0

First release.

### Changes from the drafts shown before the release

Drafts of the schema were presented in 2025 and 2026. Release 1.0.0 differs from them as follows;
a document that was valid against a draft may report new findings.

* **Content model.** `document` at the root is repeatable, so a DRMD can hold the PDF rendition
  and other files. `schemaVersion` accepts the patch levels of 1.0 only (`1.0.x`). `period` in
  `timeAfterDispatch` no longer accepts negative durations. The unused types
  `identificationListType` and `identificationType` were removed.
* **Uncertainty of certified values (ISO 33401:2024, 5.3.3).** RMC-006 to RMC-009 now cover every
  numeric form of D-SI that a certified quantity can take: `si:real`, `si:complex`, `si:constant`,
  `si:realListXMLList` and `si:complexListXMLList`, as a single quantity or inside a list, and
  every number inside `si:hybrid`, including the lists `si:realList`, `si:complexList` and
  `si:list`. Multivariate uncertainties (covariance matrices, coverage regions) are accepted, and an
  uncertainty element that D-SI allows to be empty must have content. Before, only `si:real` and
  some list forms were checked, and a certified value in a composition table written as
  `si:hybrid` passed without an uncertainty.
* **Certified blocks.** A properties block counts as certified when `@isCertified` is "true" or
  "1", the two lexical forms of the `xs:boolean` value true. Before, "1" escaped PIS-001, PIS-003
  and the uncertainty rules.
* **Content of statements.** A required statement or description counts as present only when it
  has text, a file or a formula, a name only when it has text, and procedures only when a method
  has a name. Before, an empty element, or one with only a heading, satisfied the rule.
* **RMC-011** checks the description of every material, not of one.
* **Messages.** DRMD-004, DRMD-008, DRMD-015, RMC-001, RMC-002, RMC-006 to RMC-009 and RMC-012
  were corrected; RMC-012 now applies the note to ISO 33401:2024, 5.3.5, correctly (it concerns the
  officer's name, which may be that of the responsible organisation). ISO 33401:2024 is cited in
  one form, for example "ISO 33401:2024, 5.3.3", and "document type" is used throughout.
* **Annotations** of `drmd.xsd` were rewritten where they misdescribed an element or the standard:
  `statements`, `intendedUse`, `instructionsForHandlingAndUse`, `metrologicalTraceability`,
  `subcontractors`, `statement`, `measurementMetaData`, the period of validity (it concerns the
  material, ISO 33401:2024, 5.2.8), the values of a product information sheet, the quantity kinds,
  `si:hybrid`, and the notes on `properties` and `@isCertified`. The D-SI unit of mg/kg is
  `\milli\gram\kilogram\tothe{-1}` (D-SI guide v1.3, DOI 10.5281/zenodo.3816686, rule R011,
  p. 72), in the annotations and in the product information sheet example.
* **Examples.** The fictitious producer no longer has an identifier shaped like a ROR ID, and the
  Brinell hardness example states what its SI sibling is (force per area of the indentation).
* **Tools and tests.** `tools/validate.py` gives three verdicts (COMPLIANT, TO CONFIRM for
  conditional findings, NOT COMPLIANT; exit codes 0, 3, 1), checks that every `@refId` matches an
  ID as Xerces does, and parses documents without DTDs, entity expansion or network access.
  `tests/XercesCheck.java` and the Java example in `README.md` block external entities and remote
  schemas. `tests/test_rules.py` has a case for every rule change above, on XSD-valid documents,
  including clean cases for each uncertainty form that must be accepted;
  `tests/cross_check_xslt.py` runs all cases through a second Schematron implementation; the new
  `tests/test_validate.py` checks the verdicts and exit codes of `tools/validate.py`, the version
  and period checks of the XML Schema, the IDREF check and the handling of untrusted documents.
* **Repository.** Licence files (`COPYING.LESSER`, `COPYING`), `NOTICE`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue and pull request templates, `CITATION.cff` and
  `.zenodo.json`. The schema, the rules, the catalog, the examples, the tools and the tests carry
  SPDX licence identifiers. `supporting/README.md` and `supporting/LICENSE-W3C.txt` record the
  source, licence and any change of each third-party file. The DRMD logo (`assets/`) and the
  `LOGO_POLICY.md` that governs its use; the logo is not covered by the LGPL.

### Documents of release v0.3.0

Release 1.0.0 continues the release v0.3.0 of 2025 (QI-Data-Lab/DRMD) and keeps its elements,
their order and their types. A v0.3.0 document is not valid against 1.0.0 as it stands: the
namespace changed from `https://example.org/drmd` to `urn:drmd:schema`, `materialPropertiesList`
and `materialProperties` are now `propertiesList` and `properties`, and `coreData` requires a
`documentVersion` (ISO 33401:2024, 5.2.13). `tools/convert_v0_3_0.py` and the XSLT 1.0 stylesheet
`tools/convert-v0.3.0-to-v1.0.0.xsl` convert such documents; `tests/test_convert.py` checks the
conversion of the two v0.3.0 examples, which are kept in `tests/fixtures/v0.3.0/`.

### What it is

An XML format for the documentation that accompanies a reference material, aligned with
**ISO 33401:2024**, *Reference materials: Contents of certificates, labels and accompanying
documentation*. One structure covers both document types, and the type is chosen by
`titleOfTheDocument`:

* `referenceMaterialCertificate` for a certified reference material,
* `productInformationSheet` for any other reference material.

### Two validation layers

`drmd.xsd` defines the structure both document types share. It cannot express a requirement that
depends on the value of another element, so every requirement of the form *"if this is a
certificate, then ..."* lives in `drmd-business-rules.sch`. Both layers must pass.

Thirty-one Schematron rules cover ISO 33401:2024, Table 1, at four severity levels that map onto
the standard's own requirement levels: `error` for Mandatory, `conditional-error` for Mandatory
whenever applicable, `warning` for Recommended, and no rule for Optional (DRMD-014 combines a
Mandatory whenever applicable and a Recommended item and uses the stricter level). `README.md`
lists every rule and what the rules do not check, and `tests/test_rules.py` proves each one fires
for the cases it was written for.

### External vocabularies

DRMD does not define its own way of writing a measured value, an address or a signature. It
reuses four external schemas, all vendored under `supporting/`:

* **DCC** (PTB) for multilingual text, rich content, contacts, responsible persons, embedded
  files, used methods, and the quantity container that `drmd:quantityType` extends.
* **D-SI** (PTB) for every numeric value, unit and measurement uncertainty.
* **QUDT**, reached through D-SI rather than imported directly. D-SI declares
  `si:quantityTypeQUDT` with the type `qudt:quantitykind`, so a quantity kind can be stated
  inside any D-SI quantity.
* **XML Signature** (W3C) for the `ds:Signature` element at the document root.

Two of those files resolve their own imports over the network. `catalog.xml` maps every remote
address to the local copy, so validation runs offline and always uses the exact committed
revisions rather than whatever the network returns on the day.

Two of the vendored files needed attention, and both are documented in `supporting/README.md`:

* `quantitykind.xsd` is generated from `qudt.ttl` (QUDT Quantity Kind Vocabulary v3.0.0, 1158
  quantity kinds) rather than copied. It accepts both the QUDT local name and the full IRI, the
  forms that PTB's published file is expected to accept; it has not been compared with that file.
* `xmldsig-core-schema.xsd` has its `DOCTYPE` removed. As published it references the external
  `XMLSchema.dtd`, which Xerces cannot fetch. Xerces then refuses the file, `ds:Signature` has no
  declaration, and the whole of `drmd.xsd` fails to compile. The removal is provably inert: the
  internal subset's one `ATTLIST` default is already declared on the root element, its three
  entities have zero occurrences in the file, and the component set is identical at 49 either way.

### What is in the repository

| Path | Purpose |
|---|---|
| `drmd.xsd` | The schema: structure, types, cardinalities |
| `drmd-business-rules.sch` | The ISO 33401:2024 requirements XSD cannot express |
| `catalog.xml` | Maps remote imports to the vendored copies, for offline validation |
| `supporting/` | The four external schemas, with provenance and licences |
| `examples/` | Two worked, fully compliant instances |
| `tests/test_rules.py` | Proof that every rule fires when it should |
| `tests/cross_check_xslt.py` | Runs every test case through a second Schematron implementation |
| `tests/test_validate.py` | Proof that `tools/validate.py` gives the documented verdicts and exit codes |
| `tests/XercesCheck.java` | Second-opinion validation with the JDK's XSD validator |
| `tools/validate.py` | Runs both validation layers and reports by severity |
| `tools/vendor_supporting_schemas.py` | Checks, regenerates and refreshes `supporting/` |
| `assets/`, `LOGO_POLICY.md` | The DRMD logo and the terms for using it |

### Validation is checked against two implementations

libxml2 and Xerces disagree in ways that matter, so continuous integration runs both:

* Xerces refuses a schema file whose `DOCTYPE` it cannot resolve, while libxml2 tolerates it.
* Xerces enforces IDREF integrity, so it rejects a `@refId` pointing at an id that does not
  exist. libxml2 accepts it silently, which means a typo passes `xmllint` and then fails in a
  Java pipeline; `tools/validate.py` therefore checks IDREFs itself.

Running only one implementation lets both classes of defect through.
