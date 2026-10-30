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

## Unreleased

Documentation only. The content model, the business rules and the version number are unchanged.

* The D-SI unit of mg/kg was written `\milli\gram\kilo\gram\tothe{-1}` in the annotation of
  `quantityType` (`drmd.xsd`) and in two values of `examples/product-information-sheet.xml`. D-SI
  rule R011 does not permit the prefix `\kilo` with `\gram`: the kilogram is always `\kilogram`
  (D-SI guide v1.3, DOI 10.5281/zenodo.3816686, p. 72). Both now read
  `\milli\gram\kilogram\tothe{-1}`.

---

## 1.0.0

First release.

### Changes from the pre-release review

Folded into 1.0.0 because the version had not yet been released.

* `document` at the document root is now repeatable (`maxOccurs="unbounded"`). Besides the PDF
  rendition of the RM document it can hold other documents, or several documents. This is the
  only change to the content model; every document that was valid before is still valid.
* The annotations in `drmd.xsd` were rewritten in plainer language that is closer to the
  reference material field, and a few statements that were stricter than ISO 33401:2024 were
  softened (for example the element order of `statements` is not an ISO requirement, and
  metrological traceability is not tied to accreditation).
* The `contact` annotation now states that every element of the address (`dcc:location`) is
  optional and repeatable, as `dcc:locationType` defines it.
* `drmd-business-rules.sch` is unchanged.

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
whenever applicable, `warning` for Recommended, and no rule for Optional. `README.md` lists every
rule, and `tests/test_rules.py` proves each one fires for the case it was written for.

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
  quantity kinds) rather than copied. It accepts both the QUDT local name and the full IRI, so a
  document that validates against PTB's published file also validates against this one.
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
| `tests/XercesCheck.java` | Second-opinion validation with the JDK's XSD validator |
| `tools/validate.py` | Runs both validation layers and reports by severity |
| `tools/vendor_supporting_schemas.py` | Checks, regenerates and refreshes `supporting/` |

### Validation is checked against two implementations

libxml2 and Xerces disagree in ways that matter, so continuous integration runs both:

* Xerces refuses a schema file whose `DOCTYPE` it cannot resolve, while libxml2 tolerates it.
* Xerces enforces IDREF integrity, so it rejects a `@refId` pointing at an id that does not
  exist. libxml2 accepts it silently, which means a typo passes `xmllint` and then fails in a
  Java pipeline.

Running only one implementation lets both classes of defect through.
