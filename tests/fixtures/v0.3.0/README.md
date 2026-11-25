# DRMD v0.3.0 examples

`BAM-F017.xml` and `BAM-M375a.xml` are the two example documents of the DRMD release v0.3.0,
copied unchanged from <https://github.com/QI-Data-Lab/DRMD/tree/v0.3.0> (folder `v0.3.0/xml/`,
commit `d4131807e22b9e050071b92a5a3bfa493ed9aecd`). They describe BAM reference materials.

`tests/test_convert.py` converts them to DRMD 1.0.0 and checks the result. They are test input only
and are not valid against `drmd.xsd` before the conversion.
