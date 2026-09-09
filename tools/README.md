# Tools

| Script | What it does |
|---|---|
| `validate.py` | Runs both validation steps (XSD, then Schematron) over one or more instances and prints a severity-classified report. Needs only `lxml`. |
| `vendor_supporting_schemas.py` | Checks, regenerates and refreshes the third-party schemas in `../supporting/`. |

```bash
python tools/validate.py ../examples/*.xml            # validate
python tools/validate.py doc.xml --json report.json   # machine-readable report
python tools/validate.py doc.xml --phase rmc-only     # certificate rules only

python tools/vendor_supporting_schemas.py --check                   # CI check
python tools/vendor_supporting_schemas.py --generate-quantitykind   # rebuild from qudt.ttl
python tools/vendor_supporting_schemas.py --refresh                 # pull from upstream
```

`validate.py` exits 0 when every document is compliant, 1 when one is not, and 2 when the
validator itself could not run.
