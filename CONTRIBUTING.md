# Contributing

The DRMD schema and its business rules are maintained by the Bundesanstalt für
Materialforschung und -prüfung (BAM). BAM publishes the official releases in this repository.

## Reporting an error or asking for a change

Please open an issue in this repository, using one of the templates, or write to
[drmd@bam.de](mailto:drmd@bam.de). Describe the problem, the element or rule concerned (for
example `RMC-012`) and, where possible, a small XML example. Do not send confidential documents,
and do not paste text from ISO 33401:2024 or other licensed standards: the subclause number is
enough.

Security problems are reported privately, as described in [SECURITY.md](SECURITY.md).

BAM reviews every request. Accepted changes are made by BAM in this repository and released as a
new version, recorded in `CHANGELOG.md`.

## Pull requests

Pull requests are welcome; please open an issue first, so that the change can be discussed before
work starts. A change to `drmd.xsd` or `drmd-business-rules.sch` needs a test in
`tests/test_rules.py` (a change to `tools/validate.py` needs one in `tests/test_validate.py`) and
an entry in `CHANGELOG.md` that says whether it is a major, minor or patch change. A change that
adds, updates or removes a third-party file also updates its source, licence and copyright notice
in `supporting/README.md` and `NOTICE`. Before you open the pull request, run:

```bash
python tests/test_rules.py
python tests/cross_check_xslt.py
python tests/test_validate.py
python tools/validate.py examples/*.xml
python tools/vendor_supporting_schemas.py --check
```

The same checks, and a second XSD validation with Xerces, run automatically on every pull
request.

By submitting a contribution, you confirm that you have the right to do so, and you agree that it
is published under the licence of this repository, the GNU Lesser General Public License,
version 3 (see `COPYING.LESSER`; GitHub Terms of Service, section D.6).

## Changed copies

The licence allows you to make and pass on changed versions. If you do, the licence requires you
to keep the copyright and licence notices, to mark your version prominently as changed, with a
relevant date, and to license it under the GNU Lesser General Public License, version 3. The
licence gives no right to use the name or logo of BAM, and a changed version must not be
presented as BAM's DRMD schema. The DRMD logo is not covered by the licence: a changed version
must not carry it (see the [Logo Policy](LOGO_POLICY.md)).

We also ask you, without this being a condition of the licence, not to publish a changed schema
under the DRMD namespace (`urn:drmd:schema`) or with a DRMD version number, because these identify
BAM's official releases, and to tell us about your change, so that everyone can benefit from it
in the official version.

## Code of conduct

Everyone taking part in this project is asked to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
