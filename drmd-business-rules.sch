<?xml version="1.0" encoding="UTF-8"?>
<!--
  DRMD Business Rules: Schematron Co-Validation
  Companion validation rules for the DRMD XSD schema (drmd.xsd).

  PURPOSE:
  This Schematron file enforces profile-specific business rules that cannot be expressed
  in XSD 1.0. It works alongside the DRMD XSD schema to ensure full compliance with
  ISO 33401:2024, Table 1 requirements for both document profiles:
    - referenceMaterialCertificate (CRM): Certified Reference Materials
    - productInformationSheet (RM): Informative Reference Materials (All RMs)

  VALIDATION PIPELINE:
  Step 1: Validate XML instance against drmd.xsd (structural validation)
  Step 2: Validate XML instance against this Schematron file (business rule validation)
  Both steps MUST pass for a document to be considered fully compliant.
  tools/validate.py runs both steps and prints a report; tools/README.md lists the equivalent
  commands for other toolchains.

  QUERY BINDING AND TOOL SUPPORT:
  The declared query binding is xslt2, which is what SchXslt, Saxon and other current ISO
  Schematron processors expect. Every test expression in this file is nevertheless written so
  that it is also a valid XPath 1.0 expression with the same meaning, so that simpler pipelines
  (for example lxml's isoschematron, or the XSLT 1.0 skeleton) can run the same rules unchanged.
  Please preserve that property when adding rules: prefer a predicate such as
  not(x[not(y)]) over an XPath 2.0 quantified expression such as every $n in x satisfies $n/y.

  RULE CODING CONVENTION:
    RMC-nnn  = Rules specific to referenceMaterialCertificate documents
    PIS-nnn  = Rules specific to productInformationSheet documents
    DRMD-nnn = Rules applicable to ALL DRMD documents regardless of profile

  RETIRED IDENTIFIERS:
    Rule identifiers are never reused, so that a stored validation report stays readable after a
    rules update. The following identifiers were used during development and are permanently retired:
    RMC-004 (merged into RMC-010) and PIS-004 (merged into PIS-003). Their absence from the sequence
    below is intentional and is not a missing rule.

  SEVERITY LEVELS (4-Tier Model):
    role="error"             = Hard error; document is non-compliant
                               (ISO requirement level: Mandatory)
    role="conditional-error" = Conditional error; data is required when the element is applicable
                               to the specific material, but absence may be valid if not applicable
                               (ISO requirement level: Mandatory whenever applicable)
    role="warning"           = Advisory; document is compliant but improvement is recommended
                               (ISO requirement level: Recommended)
    (no rule)                = Optional requirements have no Schematron enforcement

  Copyright (c) 2024 Bundesanstalt für Materialforschung und -prüfung (BAM)
  Licensed under GNU Lesser General Public License v3.0
  Partially funded and supported by the QI-Digital project.
-->
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            queryBinding="xslt2"
            schemaVersion="1.0.0">

  <sch:title>DRMD Business Rules. ISO 33401:2024 Profile-Specific Validation</sch:title>

  <!-- ========================================================= -->
  <!-- Namespace declarations                                     -->
  <!-- ========================================================= -->
  <sch:ns prefix="drmd" uri="urn:drmd:schema"/>
  <sch:ns prefix="dcc"  uri="https://ptb.de/dcc"/>
  <sch:ns prefix="si"   uri="https://ptb.de/si"/>

  <!-- ========================================================= -->
  <!-- PHASE DEFINITIONS                                          -->
  <!-- Phases allow selective validation of rule groups.           -->
  <!-- ========================================================= -->
  <sch:phase id="all">
    <sch:active pattern="shared-structural-rules"/>
    <sch:active pattern="rmc-document-rules"/>
    <sch:active pattern="rmc-certified-property-rules"/>
    <sch:active pattern="pis-document-rules"/>
  </sch:phase>

  <sch:phase id="rmc-only">
    <sch:active pattern="shared-structural-rules"/>
    <sch:active pattern="rmc-document-rules"/>
    <sch:active pattern="rmc-certified-property-rules"/>
  </sch:phase>

  <sch:phase id="pis-only">
    <sch:active pattern="shared-structural-rules"/>
    <sch:active pattern="pis-document-rules"/>
  </sch:phase>

  <!-- ========================================================= -->
  <!-- PATTERN 1: Shared Structural Rules (All DRMD Documents)    -->
  <!-- ISO 33401:2024 requirements common to both RMs and CRMs    -->
  <!-- ========================================================= -->
  <sch:pattern id="shared-structural-rules">
    <sch:title>Shared rules applicable to all DRMD documents (both RMC and PIS)</sch:title>

    <!-- ~~~ Root document validation ~~~ -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument">

      <!-- DRMD-001: Document must declare a valid title/profile -->
      <sch:assert test="drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument"
                  id="DRMD-001" role="error">
        [DRMD-001] Every DRMD document MUST declare a titleOfTheDocument in coreData,
        specifying either 'referenceMaterialCertificate' or 'productInformationSheet'.
      </sch:assert>

      <!-- DRMD-002: At least one material must be defined (ISO 33401:2024, §5.2.4) -->
      <sch:assert test="drmd:materials/drmd:material"
                  id="DRMD-002" role="error">
        [DRMD-002] Every DRMD document MUST contain at least one material entry
        in the materials catalogue (ISO 33401:2024, §5.2.4, Name of the RM).
      </sch:assert>

      <!-- DRMD-003: At least one properties block must exist (ISO 33401:2024, §5.2.15) -->
      <sch:assert test="drmd:propertiesList/drmd:properties"
                  id="DRMD-003" role="error">
        [DRMD-003] Every DRMD document MUST contain at least one properties block
        with measurement data (ISO 33401:2024, §5.2.15, Property of interest).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Statements validation ~~~ -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument/drmd:statements">

      <!-- DRMD-004: Intended use is mandatory (ISO 33401:2024, §5.2.6) -->
      <sch:assert test="drmd:intendedUse"
                  id="DRMD-004" role="error">
        [DRMD-004] Every DRMD document MUST include an intendedUse statement
        defining the approved application scope (ISO 33401:2024, §5.2.6, Intended use).
      </sch:assert>

      <!-- DRMD-005: Storage information is mandatory (ISO 33401:2024, §5.2.10) -->
      <sch:assert test="drmd:storageInformation"
                  id="DRMD-005" role="error">
        [DRMD-005] Every DRMD document MUST include storageInformation specifying
        environmental storage conditions (ISO 33401:2024, §5.2.10, Storage information).
      </sch:assert>

      <!-- DRMD-006: Instructions for handling and use is mandatory (ISO 33401:2024, §5.2.11) -->
      <sch:assert test="drmd:instructionsForHandlingAndUse"
                  id="DRMD-006" role="error">
        [DRMD-006] Every DRMD document MUST include instructionsForHandlingAndUse
        (ISO 33401:2024, §5.2.11, Instructions for handling and use).
      </sch:assert>

      <!-- DRMD-013: Commutability must be specified whenever applicable (ISO 33401:2024, §5.2.9) -->
      <sch:assert test="drmd:commutability"
                  id="DRMD-013" role="conditional-error">
        [DRMD-013] Every DRMD document MUST include a commutability statement whenever applicable.
        Commutability is particularly important for reference materials intended for use with
        multiple measurement procedures (ISO 33401:2024, §5.2.9, Commutability:
        'Mandatory whenever applicable' for both document profiles).
      </sch:assert>

      <!-- DRMD-015: Health and safety information is recommended (ISO 33401:2024, §5.4.3) -->
      <sch:assert test="drmd:healthAndSafetyInformation"
                  id="DRMD-015" role="warning">
        [DRMD-015] DRMD documents SHOULD include healthAndSafetyInformation documenting
        hazardous material traits and protective equipment directives
        (ISO 33401:2024, §5.4.3, Health and safety information:
        'Recommended' for both document profiles).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Material validation ~~~ -->
    <sch:rule context="drmd:materials/drmd:material">

      <!-- DRMD-007: Each material must have a name (ISO 33401:2024, §5.2.4) -->
      <sch:assert test="drmd:name"
                  id="DRMD-007" role="error">
        [DRMD-007] Every material entry MUST include a name element
        (ISO 33401:2024, §5.2.4, Name of the RM).
      </sch:assert>

      <!-- DRMD-008: Minimum sample size must be specified whenever applicable (ISO 33401:2024, §5.2.7) -->
      <sch:assert test="drmd:minimumSampleSize"
                  id="DRMD-008" role="conditional-error">
        [DRMD-008] Each material entry MUST specify a minimumSampleSize whenever applicable
        to ensure representative sampling for homogeneity (ISO 33401:2024, §5.2.7, Minimum sample size:
        'Mandatory whenever applicable' for both document profiles).
      </sch:assert>

      <!-- DRMD-016: Unique identifier of the RM (ISO 33401:2024, §5.2.3) -->
      <sch:assert test="drmd:materialIdentifiers/drmd:materialIdentifier"
                  id="DRMD-016" role="error">
        [DRMD-016] Each material entry MUST carry at least one materialIdentifier giving the unique
        identifier of the reference material (ISO 33401:2024, §5.2.3, Unique identifier of the RM:
        'Mandatory' for both document profiles). The identifier must distinguish this RM from any other
        RM issued by the same producer; a product code, normally combined with a batch or lot number,
        satisfies this. Note that coreData/uniqueIdentifier identifies the DOCUMENT and does not
        satisfy §5.2.3, because one document may cover several materials and one material may be
        described by successive document revisions.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Properties must have results ~~~ -->
    <sch:rule context="drmd:propertiesList/drmd:properties">

      <!-- DRMD-009: Each properties block must contain results (ISO 33401:2024, §5.2.15) -->
      <sch:assert test="drmd:results/drmd:result"
                  id="DRMD-009" role="error">
        [DRMD-009] Every properties block MUST contain at least one result entry
        with measurement data (ISO 33401:2024, §5.2.15, Property of interest).
      </sch:assert>

      <!-- DRMD-014: Measurement procedures must be present whenever applicable (ISO 33401:2024, §5.2.14 + §5.4.2) -->
      <sch:assert test="drmd:procedures"
                  id="DRMD-014" role="conditional-error">
        [DRMD-014] Each properties block MUST include measurement procedures whenever applicable.
        This combines two ISO requirements: procedures for operationally defined measurands
        (ISO 33401:2024, §5.2.14, 'Mandatory whenever applicable' for both document profiles)
        and procedures for non-operationally defined measurands (ISO 33401:2024, §5.4.2, 'Recommended' for both document profiles). Taken together, the overall requirement
        is 'Mandatory whenever applicable'.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Administrative data validation ~~~ -->
    <sch:rule context="drmd:administrativeData">

      <!-- DRMD-010: Producer information must be present (ISO 33401:2024, §5.2.5) -->
      <sch:assert test="drmd:referenceMaterialProducer"
                  id="DRMD-010" role="error">
        [DRMD-010] Every DRMD document MUST identify the referenceMaterialProducer
        (ISO 33401:2024, §5.2.5, Name and contact details of the RM producer).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Validity must be specified ~~~ -->
    <sch:rule context="drmd:administrativeData/drmd:coreData">

      <!-- DRMD-012: Validity period must be defined (ISO 33401:2024, §5.2.8) -->
      <sch:assert test="drmd:validity"
                  id="DRMD-012" role="error">
        [DRMD-012] Every DRMD document MUST specify a validity period or condition
        (ISO 33401:2024, §5.2.8, Period of validity).
      </sch:assert>

      <!-- DRMD-011: Document version must be stated (ISO 33401:2024, §5.2.13) -->
      <sch:assert test="drmd:documentVersion"
                  id="DRMD-011" role="error">
        [DRMD-011] Every DRMD document MUST state its documentVersion in coreData
        (ISO 33401:2024, §5.2.13, Document version: 'Mandatory' for both document profiles).
        A version number, an approval date, or both are acceptable, provided the value changes
        whenever the document content changes. This requirement is also enforced structurally by
        drmd.xsd; the rule is stated here so that a Schematron report covers ISO 33401:2024,
        Table 1 in full on its own.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ========================================================= -->
  <!-- PATTERN 2: Reference Material Certificate (CRM) Rules      -->
  <!-- ISO 33401:2024 requirements specific to CRMs               -->
  <!-- ========================================================= -->
  <sch:pattern id="rmc-document-rules">
    <sch:title>Rules specific to referenceMaterialCertificate documents (CRM profile)</sch:title>

    <sch:rule context="drmd:digitalReferenceMaterialDocument[
      drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']">

      <!-- RMC-001: Metrological traceability is mandatory for CRM (ISO 33401:2024, §5.3.4) -->
      <sch:assert test="drmd:statements/drmd:metrologicalTraceability"
                  id="RMC-001" role="error">
        [RMC-001] Reference Material Certificates MUST include a metrologicalTraceability
        statement formalizing the chain of comparisons linking certified results to SI base
        units or international calibration benchmarks (ISO 33401:2024, §5.3.4, Metrological
        traceability: 'Mandatory' for RM certificate). This is not required for productInformationSheet documents.
      </sch:assert>

      <!-- RMC-002: At least one certified property block required (ISO 33401:2024, §5.3.3) -->
      <sch:assert test="drmd:propertiesList/drmd:properties[@isCertified = 'true']"
                  id="RMC-002" role="error">
        [RMC-002] Reference Material Certificates MUST have at least one properties
        block with the attribute isCertified="true" containing certified property values
        (ISO 33401:2024, §5.3.3, Property value and associated uncertainty:
        'Mandatory' for RM certificate). A certificate without certified values is structurally invalid.
      </sch:assert>

      <!-- RMC-003: Property values must exist for CRM (ISO 33401:2024, §5.3.3) -->
      <sch:assert test="drmd:propertiesList/drmd:properties/drmd:results/drmd:result"
                  id="RMC-003" role="error">
        [RMC-003] Reference Material Certificates MUST include property values
        (ISO 33401:2024, §5.3.3, Property value and associated uncertainty).
      </sch:assert>

      <!-- RMC-005: Measurement procedures should be documented (ISO 33401:2024, §5.4.2) -->
      <sch:assert test="drmd:propertiesList/drmd:properties[@isCertified = 'true']/drmd:procedures"
                  id="RMC-005" role="warning">
        [RMC-005] Reference Material Certificates SHOULD document the measurement procedures
        used for certified properties (ISO 33401:2024, §5.4.2, Measurement procedures for
        non-operationally defined measurands: 'Recommended' for both document profiles).
      </sch:assert>

      <!-- RMC-010: Responsible persons / approving officer mandatory for CRM (ISO 33401:2024, §5.3.5) -->
      <sch:assert test="drmd:administrativeData/drmd:respPersons"
                  id="RMC-010" role="error">
        [RMC-010] Reference Material Certificates MUST list responsible persons including
        the name and function of the RM producer's approving officer
        (ISO 33401:2024, §5.3.5, Name and function of the RM producer's approving officer:
        'Mandatory' for RM certificate, 'Optional' for product information sheet).
      </sch:assert>

      <!-- RMC-012: Approving officer's function must be stated (ISO 33401:2024, §5.3.5) -->
      <sch:assert test="drmd:administrativeData/drmd:respPersons/dcc:respPerson[normalize-space(dcc:role) != '']"
                  id="RMC-012" role="error">
        [RMC-012] In a Reference Material Certificate, at least one dcc:respPerson MUST state a
        dcc:role. ISO 33401:2024, §5.3.5 requires the name AND the function of the officer
        representing the RM producer who accepts responsibility for the contents of the certificate;
        RMC-010 checks that the respPersons list exists, and this rule checks that the function is
        actually recorded. The role may name the responsible organisational unit rather than a
        personal job title (§5.3.5, NOTE). The officer's name is required by dcc:respPerson itself
        and needs no separate rule.
      </sch:assert>

      <!-- RMC-011: Material description mandatory for CRM (ISO 33401:2024, §5.3.2) -->
      <sch:assert test="drmd:materials/drmd:material/drmd:description"
                  id="RMC-011" role="error">
        [RMC-011] Reference Material Certificates MUST include a description for each material
        (ISO 33401:2024, §5.3.2, Description of the material: 'Mandatory' for RM certificate,
        'Recommended' for product information sheet).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ========================================================= -->
  <!-- PATTERN 3: CRM Certified Property Value Rules              -->
  <!-- Enforces uncertainty requirements on certified data blocks  -->
  <!-- ========================================================= -->
  <sch:pattern id="rmc-certified-property-rules">
    <sch:title>Uncertainty enforcement for certified property values in RMC documents</sch:title>

    <!--
      This rule fires for every quantity inside a certified properties block
      that belongs to a referenceMaterialCertificate document.

      ISO 33401:2024, §5.3.3 requires: Property value and associated uncertainty
      is 'Mandatory' for RM certificates, but 'Optional' for product information sheets.

      The SI Format schema (D-SI) defines uncertainty as an optional xs:choice within si:realQuantityType
      containing one of: si:measurementUncertaintyUnivariate (current), si:expandedUnc (deprecated),
      or si:coverageInterval (deprecated). This Schematron rule enforces that at least one
      uncertainty representation is present for every si:real quantity within certified property blocks.
    -->

    <!-- Rule for si:real quantities inside certified properties of RMC documents -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[@isCertified = 'true']
      //drmd:result/drmd:data/drmd:quantity[si:real]">

      <!-- RMC-006: Certified real quantities must include measurement uncertainty -->
      <sch:assert test="si:real/si:measurementUncertaintyUnivariate
                        or si:real/si:expandedUnc
                        or si:real/si:coverageInterval"
                  id="RMC-006" role="error">
        [RMC-006] Certified property values expressed as si:real quantities MUST include
        measurement uncertainty (one of: si:measurementUncertaintyUnivariate, si:expandedUnc,
        or si:coverageInterval). This is required for all certified values in Reference Material
        Certificates (ISO 33401:2024, §5.3.3, Property value and associated uncertainty:
        'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>

    <!-- Rule for si:real quantities inside certified properties list data -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[@isCertified = 'true']
      //drmd:result/drmd:data/drmd:list/drmd:quantity[si:real]">

      <!-- RMC-007: Certified list quantities must include measurement uncertainty -->
      <sch:assert test="si:real/si:measurementUncertaintyUnivariate
                        or si:real/si:expandedUnc
                        or si:real/si:coverageInterval"
                  id="RMC-007" role="error">
        [RMC-007] Certified property values in list quantities expressed as si:real MUST include
        measurement uncertainty. Each si:real quantity in a certified data list must carry
        uncertainty information (ISO 33401:2024, §5.3.3, Property value and associated
        uncertainty: 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>

    <!-- Rule for si:realListXMLList quantities inside certified properties -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[@isCertified = 'true']
      //drmd:result/drmd:data/drmd:quantity[si:realListXMLList]">

      <!-- RMC-008: Certified realListXMLList quantities must include measurement uncertainty -->
      <sch:assert test="si:realListXMLList/si:measurementUncertaintyUnivariateXMLList
                        or si:realListXMLList/si:expandedUncXMLList
                        or si:realListXMLList/si:coverageIntervalXMLList"
                  id="RMC-008" role="error">
        [RMC-008] Certified property values expressed as si:realListXMLList MUST include
        measurement uncertainty (one of: si:measurementUncertaintyUnivariateXMLList,
        si:expandedUncXMLList, or si:coverageIntervalXMLList). This is required for all
        certified values in Reference Material Certificates (ISO 33401:2024, §5.3.3).
      </sch:assert>
    </sch:rule>

    <!-- Rule for si:hybrid quantities inside certified properties -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[@isCertified = 'true']
      //drmd:result/drmd:data/drmd:quantity[si:hybrid]">

      <!-- RMC-009: Certified hybrid quantities containing si:real must include uncertainty -->
      <sch:assert test="not(si:hybrid/si:real[not(si:measurementUncertaintyUnivariate
                                                  or si:expandedUnc
                                                  or si:coverageInterval)])"
                  id="RMC-009" role="error">
        [RMC-009] In certified properties blocks, every si:real quantity nested within
        a si:hybrid container MUST include measurement uncertainty (ISO 33401:2024, §5.3.3, Property value and associated uncertainty: 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ========================================================= -->
  <!-- PATTERN 4: Product Information Sheet (PIS / All RM) Rules  -->
  <!-- ISO 33401:2024 constraints specific to non-certified RMs   -->
  <!-- ========================================================= -->
  <sch:pattern id="pis-document-rules">
    <sch:title>Rules specific to productInformationSheet documents (PIS / All RM profile)</sch:title>

    <sch:rule context="drmd:digitalReferenceMaterialDocument[
      drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']">

      <!-- PIS-001: Product Information Sheets must NOT contain certified property blocks -->
      <sch:assert test="not(drmd:propertiesList/drmd:properties[@isCertified = 'true'])"
                  id="PIS-001" role="error">
        [PIS-001] Product Information Sheets MUST NOT mark any properties block as
        isCertified="true". Only Reference Material Certificate documents (CRM) may contain
        certified property values. Setting isCertified="true" on a productInformationSheet
        document constitutes a misrepresentation of the material's metrological status
        and violates the ISO 33401:2024 distinction between RMs and CRMs.
      </sch:assert>

      <!-- PIS-002: Property data should be present where values are assigned -->
      <sch:assert test="drmd:propertiesList/drmd:properties/drmd:results/drmd:result"
                  id="PIS-002" role="error">
        [PIS-002] Product Information Sheets MUST include results where
        property values are assigned (ISO 33401:2024, §5.2.15, Property of interest).
      </sch:assert>
    </sch:rule>

    <!-- PIS properties blocks should not claim certification -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']
      //drmd:properties">

      <!-- PIS-003: Individual properties blocks must not be certified -->
      <sch:assert test="not(@isCertified = 'true')"
                  id="PIS-003" role="error">
        [PIS-003] In productInformationSheet documents, individual properties blocks
        MUST NOT have isCertified="true". This attribute should be omitted or set to "false"
        for all property blocks in a Product Information Sheet. Certified property values
        are only permitted in referenceMaterialCertificate documents.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ PIS material-level validation ~~~ -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']
      //drmd:materials/drmd:material">

      <!-- PIS-005: Material description is recommended for PIS (ISO 33401:2024, §5.3.2) -->
      <sch:assert test="drmd:description"
                  id="PIS-005" role="warning">
        [PIS-005] Product Information Sheets SHOULD include a description for each material.
        While not mandatory for Product Information Sheets, material descriptions improve
        usability (ISO 33401:2024, §5.3.2, Description of the material:
        'Recommended' for product information sheet, 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
