# Security policy

This repository publishes an XML Schema, Schematron rules, two example documents and two small
Python tools. It runs no service. A security problem here would most likely be one of these:

* a construct in `drmd.xsd`, in `drmd-business-rules.sch` or in a vendored file under
  `supporting/` that makes a validator fetch remote content, expand entities or consume
  excessive resources;
* a weakness in `tools/validate.py` or `tools/vendor_supporting_schemas.py`, for example in how
  they parse untrusted XML;
* a rule that lets a document pass although it presents uncertified values as certified, or a
  certified value without an uncertainty.

## Supported versions

| Version | Supported |
|---|---|
| 1.0.x | Yes |

## Reporting a vulnerability

Please do **not** open a public issue for a security problem. Report it privately, either through
GitHub's private vulnerability reporting ("Report a vulnerability" on the Security tab of this
repository), or by e-mail to [drmd@bam.de](mailto:drmd@bam.de) with "DRMD security" in the
subject.

Please include the file and version concerned, a description of the problem and, where possible,
a small XML document that shows it. Do not send confidential documents.

BAM confirms receipt, assesses the report and publishes a correction as a new version (see
`CHANGELOG.md`). We will tell you before the correction is published and, if you wish, name you
in the changelog.

## Validating untrusted documents

DRMD documents come from many producers. When you validate a document you did not create:

* resolve the schemas through `catalog.xml` and switch off network access (for example
  `xmllint --nonet`), so that no validation step fetches anything from the internet;
* do not let your XML parser resolve external entities or DTDs in the instance document;
* treat a structurally valid `ds:Signature` as unchecked until an XML Signature library has
  verified the digests, the signature value and the certificate chain.
