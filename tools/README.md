# Tools

| Script | What it does |
|---|---|
| `validate.py` | Runs both validation steps (XSD, then Schematron) over one or more instances and prints a severity-classified report. Needs only `lxml`. |
| `vendor_supporting_schemas.py` | Checks, regenerates and refreshes the third-party schemas in `../supporting/`. |
| `convert-v0.3.0-to-v1.0.0.xsl` | Converts a DRMD document of the earlier release v0.3.0 to 1.0.0 (XSLT 1.0, runs in any XSLT processor). |
| `convert_v0_3_0.py` | Runs that stylesheet with lxml and checks the result against `drmd.xsd`; with `--validate` also runs `validate.py`. |

Run them from the root of the repository:

```bash
python tools/validate.py examples/*.xml                # validate
python tools/validate.py doc.xml --json report.json    # machine-readable report
python tools/validate.py doc.xml --phase rmc-only      # certificate rules only
python tools/validate.py doc.xml --phase pis-only      # product information sheet rules only

python tools/vendor_supporting_schemas.py --check                   # CI check
python tools/vendor_supporting_schemas.py --generate-quantitykind   # rebuild from qudt.ttl
python tools/vendor_supporting_schemas.py --refresh                 # pull from upstream

python tools/convert_v0_3_0.py old.xml converted.xml --document-version 1             # v0.3.0 to 1.0.0
python tools/convert_v0_3_0.py old.xml converted.xml --document-version 1 --validate  # and validate
xsltproc --stringparam documentVersion 1 tools/convert-v0.3.0-to-v1.0.0.xsl old.xml > converted.xml
```

`convert_v0_3_0.py` exits 0 when the converted document is valid against `drmd.xsd` and 2 when
nothing was converted (not a v0.3.0 document, no `--document-version`, a DOCTYPE, or an invalid
result). With `--validate` it exits with the code of `validate.py`.

`validate.py` exits 0 when every document is COMPLIANT, 3 when none is NOT COMPLIANT but at least
one is TO CONFIRM, 1 when at least one is NOT COMPLIANT, and 2 when the validator itself could not
run.
