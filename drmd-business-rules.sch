<?xml version="1.0" encoding="UTF-8"?>
<!--
  SPDX-FileCopyrightText: 2024-2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
  SPDX-License-Identifier: LGPL-3.0-only

  DRMD Business Rules, version 1.0.0
  Companion validation rules for the DRMD XML Schema (drmd.xsd), namespace urn:drmd:schema.

  PURPOSE:
  This Schematron file enforces the business rules for each document type that cannot be expressed
  in XSD 1.0. It works alongside the DRMD XSD schema to ensure full compliance with
  ISO 33401:2024, Table 1 requirements for both document types:
    - referenceMaterialCertificate: the RM certificate that accompanies a certified reference
      material (CRM)
    - productInformationSheet: the product information sheet that accompanies any other
      reference material (RM) (ISO 33401:2024, 3.3)

  VALIDATION PIPELINE:
  Step 1: Validate XML instance against drmd.xsd (structural validation)
  Step 2: Validate XML instance against this Schematron file (business rule validation)
  Both steps MUST pass for a document to be considered fully compliant.
  tools/validate.py runs both steps and prints a report; README.md lists the equivalent
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
    DRMD-nnn = Rules applicable to ALL DRMD documents, whatever their type

  TWO CONVENTIONS USED BY THE TESTS:
    - A properties block is certified when @isCertified is "true" or "1", the two lexical forms
      of the xs:boolean value true (leading and trailing spaces are ignored, as XML Schema does).
    - A required statement, name, description or list of procedures counts as present only when
      it has content: a statement or description needs a dcc:content with text, a dcc:file or a
      dcc:formula (a dcc:name heading alone is not enough), a name needs a dcc:content with text,
      and a list of procedures needs at least one dcc:usedMethod whose name has text.

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

  LICENCE
  This file is free software: you can redistribute it and/or modify it under the terms of the
  GNU Lesser General Public License as published by the Free Software Foundation, version 3 of
  the License. It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
  COPYING.LESSER and COPYING in the root of the repository.
  The development of the DRMD is partially funded and supported by the QI-Digital project.
-->
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            queryBinding="xslt2"
            schemaVersion="1.0.0">

  <sch:title>DRMD Business Rules: ISO 33401:2024 requirements for each document type</sch:title>

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

      <!-- DRMD-001: Document must declare its type -->
      <sch:assert test="drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument"
                  id="DRMD-001" role="error">
        [DRMD-001] Every DRMD document MUST declare a titleOfTheDocument in coreData,
        specifying either 'referenceMaterialCertificate' or 'productInformationSheet'.
      </sch:assert>

      <!-- DRMD-002: At least one material must be defined (ISO 33401:2024, 5.2.4) -->
      <sch:assert test="drmd:materials/drmd:material"
                  id="DRMD-002" role="error">
        [DRMD-002] Every DRMD document MUST contain at least one material entry
        in the materials catalogue (ISO 33401:2024, 5.2.4, Name of the RM).
      </sch:assert>

      <!-- DRMD-003: At least one properties block must exist (ISO 33401:2024, 5.2.15) -->
      <sch:assert test="drmd:propertiesList/drmd:properties"
                  id="DRMD-003" role="error">
        [DRMD-003] Every DRMD document MUST contain at least one properties block
        with measurement data (ISO 33401:2024, 5.2.15, Property of interest).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Statements validation ~~~ -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument/drmd:statements">

      <!-- DRMD-004: Intended use is mandatory (ISO 33401:2024, 5.2.6) -->
      <sch:assert test="drmd:intendedUse[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="DRMD-004" role="error">
        [DRMD-004] Every DRMD document MUST include an intendedUse statement
        giving the main intended use of the material (ISO 33401:2024, 5.2.6, Intended use).
      </sch:assert>

      <!-- DRMD-005: Storage information is mandatory (ISO 33401:2024, 5.2.10) -->
      <sch:assert test="drmd:storageInformation[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="DRMD-005" role="error">
        [DRMD-005] Every DRMD document MUST include storageInformation specifying
        environmental storage conditions (ISO 33401:2024, 5.2.10, Storage information).
      </sch:assert>

      <!-- DRMD-006: Instructions for handling and use is mandatory (ISO 33401:2024, 5.2.11) -->
      <sch:assert test="drmd:instructionsForHandlingAndUse[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="DRMD-006" role="error">
        [DRMD-006] Every DRMD document MUST include instructionsForHandlingAndUse
        (ISO 33401:2024, 5.2.11, Instructions for handling and use).
      </sch:assert>

      <!-- DRMD-013: Commutability must be specified whenever applicable (ISO 33401:2024, 5.2.9) -->
      <sch:assert test="drmd:commutability[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="DRMD-013" role="conditional-error">
        [DRMD-013] Every DRMD document MUST include a commutability statement whenever applicable.
        Commutability is particularly important for reference materials intended for use with
        multiple measurement procedures (ISO 33401:2024, 5.2.9, Commutability:
        'Mandatory whenever applicable' for both document types).
      </sch:assert>

      <!-- DRMD-015: Health and safety information is recommended (ISO 33401:2024, 5.4.3) -->
      <sch:assert test="drmd:healthAndSafetyInformation[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="DRMD-015" role="warning">
        [DRMD-015] DRMD documents SHOULD include healthAndSafetyInformation: a statement on the
        safety data sheet and, for hazardous materials, the appropriate warnings
        (ISO 33401:2024, 5.4.3, Health and safety information:
        'Recommended' for both document types).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Material validation ~~~ -->
    <sch:rule context="drmd:materials/drmd:material">

      <!-- DRMD-007: Each material must have a name (ISO 33401:2024, 5.2.4) -->
      <sch:assert test="drmd:name[dcc:content[normalize-space(.) != '']]"
                  id="DRMD-007" role="error">
        [DRMD-007] Every material entry MUST include a name element
        (ISO 33401:2024, 5.2.4, Name of the RM).
      </sch:assert>

      <!-- DRMD-008: Minimum sample size must be specified whenever applicable (ISO 33401:2024, 5.2.7) -->
      <sch:assert test="drmd:minimumSampleSize"
                  id="DRMD-008" role="conditional-error">
        [DRMD-008] Each material entry MUST specify a minimumSampleSize whenever applicable: the
        smallest amount of material for which the stated property values and uncertainties apply
        (ISO 33401:2024, 5.2.7, Minimum sample size:
        'Mandatory whenever applicable' for both document types).
      </sch:assert>

      <!-- DRMD-016: Unique identifier of the RM (ISO 33401:2024, 5.2.3) -->
      <sch:assert test="drmd:materialIdentifiers/drmd:materialIdentifier"
                  id="DRMD-016" role="error">
        [DRMD-016] Each material entry MUST carry at least one materialIdentifier giving the unique
        identifier of the reference material (ISO 33401:2024, 5.2.3, Unique identifier of the RM:
        'Mandatory' for both document types). The identifier must distinguish this RM from any other
        RM issued by the same producer; a product code, normally combined with a batch or lot number,
        satisfies this. Note that coreData/uniqueIdentifier identifies the DOCUMENT and does not
        satisfy 5.2.3, because one document may cover several materials and one material may be
        described by successive document revisions.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Properties must have results ~~~ -->
    <sch:rule context="drmd:propertiesList/drmd:properties">

      <!-- DRMD-009: Each properties block must contain results (ISO 33401:2024, 5.2.15) -->
      <sch:assert test="drmd:results/drmd:result"
                  id="DRMD-009" role="error">
        [DRMD-009] Every properties block MUST contain at least one result entry
        with measurement data (ISO 33401:2024, 5.2.15, Property of interest).
      </sch:assert>

      <!-- DRMD-014: Measurement procedures must be present whenever applicable (ISO 33401:2024, 5.2.14 and 5.4.2) -->
      <sch:assert test="drmd:procedures[dcc:usedMethod/dcc:name/dcc:content[normalize-space(.) != '']]"
                  id="DRMD-014" role="conditional-error">
        [DRMD-014] Each properties block MUST include measurement procedures whenever applicable.
        This combines two ISO requirements: procedures for operationally defined measurands
        (ISO 33401:2024, 5.2.14, 'Mandatory whenever applicable' for both document types)
        and procedures for non-operationally defined measurands (ISO 33401:2024, 5.4.2,
        'Recommended' for both document types). Taken together, the overall requirement
        is 'Mandatory whenever applicable'.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Administrative data validation ~~~ -->
    <sch:rule context="drmd:administrativeData">

      <!-- DRMD-010: Producer information must be present (ISO 33401:2024, 5.2.5) -->
      <sch:assert test="drmd:referenceMaterialProducer"
                  id="DRMD-010" role="error">
        [DRMD-010] Every DRMD document MUST identify the referenceMaterialProducer
        (ISO 33401:2024, 5.2.5, Name and contact details of the RM producer).
      </sch:assert>
    </sch:rule>

    <!-- ~~~ Validity must be specified ~~~ -->
    <sch:rule context="drmd:administrativeData/drmd:coreData">

      <!-- DRMD-012: Validity period must be defined (ISO 33401:2024, 5.2.8) -->
      <sch:assert test="drmd:validity"
                  id="DRMD-012" role="error">
        [DRMD-012] Every DRMD document MUST specify a validity period or condition
        (ISO 33401:2024, 5.2.8, Period of validity).
      </sch:assert>

      <!-- DRMD-011: Document version must be stated (ISO 33401:2024, 5.2.13) -->
      <sch:assert test="drmd:documentVersion"
                  id="DRMD-011" role="error">
        [DRMD-011] Every DRMD document MUST state its documentVersion in coreData
        (ISO 33401:2024, 5.2.13, Document version: 'Mandatory' for both document types).
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
    <sch:title>Rules specific to referenceMaterialCertificate documents (certified reference materials)</sch:title>

    <sch:rule context="drmd:digitalReferenceMaterialDocument[
      drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']">

      <!-- RMC-001: Metrological traceability is mandatory for CRM (ISO 33401:2024, 5.3.4) -->
      <sch:assert test="drmd:statements/drmd:metrologicalTraceability[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="RMC-001" role="error">
        [RMC-001] Reference Material Certificates MUST include a metrologicalTraceability
        statement that gives, for the certified values, the reference to which they are
        metrologically traceable (ISO 33401:2024, 5.3.4, Metrological traceability:
        'Mandatory' for RM certificate). This is not required for productInformationSheet documents.
      </sch:assert>

      <!-- RMC-002: At least one certified property block required (ISO 33401:2024, 5.3.3) -->
      <sch:assert test="drmd:propertiesList/drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]"
                  id="RMC-002" role="error">
        [RMC-002] Reference Material Certificates MUST have at least one properties
        block with the attribute isCertified="true" (or its equivalent "1") containing certified
        property values
        (ISO 33401:2024, 5.3.3, Property value and associated uncertainty:
        'Mandatory' for RM certificate). A certificate without certified values does not meet ISO 33401:2024.
      </sch:assert>

      <!-- RMC-003: Property values must exist for CRM (ISO 33401:2024, 5.3.3) -->
      <sch:assert test="drmd:propertiesList/drmd:properties/drmd:results/drmd:result"
                  id="RMC-003" role="error">
        [RMC-003] Reference Material Certificates MUST include property values
        (ISO 33401:2024, 5.3.3, Property value and associated uncertainty).
      </sch:assert>

      <!-- RMC-005: Measurement procedures should be documented (ISO 33401:2024, 5.4.2) -->
      <sch:assert test="drmd:propertiesList/drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]/drmd:procedures[dcc:usedMethod/dcc:name/dcc:content[normalize-space(.) != '']]"
                  id="RMC-005" role="warning">
        [RMC-005] Reference Material Certificates SHOULD document the measurement procedures
        used for certified properties (ISO 33401:2024, 5.4.2, Measurement procedures for
        non-operationally defined measurands: 'Recommended' for both document types).
      </sch:assert>

      <!-- RMC-010: Responsible persons / approving officer mandatory for CRM (ISO 33401:2024, 5.3.5) -->
      <sch:assert test="drmd:administrativeData/drmd:respPersons"
                  id="RMC-010" role="error">
        [RMC-010] Reference Material Certificates MUST list responsible persons including
        the name and function of the RM producer's approving officer
        (ISO 33401:2024, 5.3.5, Name and function of the RM producer's approving officer:
        'Mandatory' for RM certificate, 'Optional' for product information sheet).
      </sch:assert>

      <!-- RMC-012: Approving officer's function must be stated (ISO 33401:2024, 5.3.5) -->
      <sch:assert test="drmd:administrativeData/drmd:respPersons/dcc:respPerson[normalize-space(dcc:role) != '']"
                  id="RMC-012" role="error">
        [RMC-012] In a Reference Material Certificate, at least one dcc:respPerson MUST state a
        dcc:role. ISO 33401:2024, 5.3.5 requires both the name and the function of the RM
        producer's approving officer; RMC-010 checks that the respPersons list exists, and this rule
        checks that the function is recorded. The name is required by dcc:respPerson itself and
        needs no separate rule; by the note to 5.3.5 it may be the name of the responsible
        organisation.
      </sch:assert>

      <!-- RMC-011: Material description mandatory for CRM, for every material (ISO 33401:2024, 5.3.2) -->
      <sch:assert test="not(drmd:materials/drmd:material[not(drmd:description[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula])])"
                  id="RMC-011" role="error">
        [RMC-011] Reference Material Certificates MUST include a description for each material
        (ISO 33401:2024, 5.3.2, Description of the material: 'Mandatory' for RM certificate,
        'Recommended' for product information sheet).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ========================================================= -->
  <!-- PATTERN 3: CRM Certified Property Value Rules              -->
  <!-- Enforces uncertainty requirements on certified data blocks  -->
  <!-- ========================================================= -->
  <sch:pattern id="rmc-certified-property-rules">
    <sch:title>Uncertainty of the certified values in RM certificates</sch:title>

    <!--
      ISO 33401:2024, 5.3.3: an RM certificate states the property values with their associated
      uncertainties ('Mandatory' for RM certificates, 'Optional' for product information sheets).

      The four rules apply to every quantity in a certified properties block of a certificate and
      cover every numeric form that dcc:primitiveQuantityType offers:
        RMC-006  si:real, si:complex or si:constant as a single quantity (data/quantity)
        RMC-007  the same forms inside a list (data/list/quantity)
        RMC-008  si:realListXMLList or si:complexListXMLList, single or inside a list
        RMC-009  si:hybrid, single or inside a list: every number it holds, in each form that D-SI
                 allows inside si:hybrid (si:real, si:complex, si:constant, si:realListXMLList,
                 si:complexListXMLList, and the lists si:realList, si:complexList and si:list)
      A form counts as carrying an uncertainty when it holds one of the uncertainty elements that
      D-SI 2.2.1 defines for it, the older ones (si:expandedUnc, si:coverageInterval and their list
      forms) included. An uncertainty element that D-SI allows to be empty must have content.
      Values given as text (dcc:noQuantity) or as a list of codes (dcc:charsXMLList) are not checked:
      they can be qualitative or nominal values, which have no measurement uncertainty.
      D-SI 2.2.1 spells the uncertainty element of an si:real inside si:realList
      "measurementUncertaintyUnivaraite"; the test uses the spelling that the schema accepts.
    -->

    <!-- Single quantities: si:real, si:complex or si:constant directly under data -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]
      //drmd:result/drmd:data/drmd:quantity[si:real or si:complex or si:constant]">

      <!-- RMC-006: Certified single quantities must include measurement uncertainty -->
      <sch:assert test="si:real[si:measurementUncertaintyUnivariate or si:expandedUnc or si:coverageInterval]
                        or si:complex[si:ellipsoidalRegion or si:rectangularRegion]
                        or si:constant[si:valueStandardMU or si:uncertainty]"
                  id="RMC-006" role="error">
        [RMC-006] A certified property value given as a single si:real, si:complex or si:constant
        quantity MUST include its measurement uncertainty, in one of the forms that D-SI provides
        for it (si:real: si:measurementUncertaintyUnivariate, or the older si:expandedUnc or
        si:coverageInterval; si:complex: si:ellipsoidalRegion or si:rectangularRegion; si:constant:
        si:valueStandardMU or si:uncertainty). This is required for all certified values in
        Reference Material Certificates (ISO 33401:2024, 5.3.3, Property value and associated
        uncertainty: 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>

    <!-- Quantities in a list: si:real, si:complex or si:constant inside data/list -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]
      //drmd:result/drmd:data/drmd:list/drmd:quantity[si:real or si:complex or si:constant]">

      <!-- RMC-007: Certified list quantities must include measurement uncertainty -->
      <sch:assert test="si:real[si:measurementUncertaintyUnivariate or si:expandedUnc or si:coverageInterval]
                        or si:complex[si:ellipsoidalRegion or si:rectangularRegion]
                        or si:constant[si:valueStandardMU or si:uncertainty]"
                  id="RMC-007" role="error">
        [RMC-007] Certified property values in list quantities expressed as si:real, si:complex or
        si:constant MUST include measurement uncertainty, in one of the forms that D-SI provides for
        them (see RMC-006). Each quantity in a certified data list must carry uncertainty
        information (ISO 33401:2024, 5.3.3, Property value and associated uncertainty:
        'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>

    <!-- XML lists, given as a single quantity (data/quantity) or inside a list (data/list/quantity) -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]
      //drmd:result/drmd:data//drmd:quantity[si:realListXMLList or si:complexListXMLList]">

      <!-- RMC-008: Certified XML lists must include measurement uncertainty -->
      <sch:assert test="si:realListXMLList[si:measurementUncertaintyUnivariateXMLList or si:expandedUncXMLList or si:coverageIntervalXMLList
                                   or si:measurementUncertaintyMultivariateXMLList/* or si:ellipsoidalRegionXMLList
                                   or si:rectangularRegionXMLList]
                        or si:complexListXMLList[si:measurementUncertaintyBivariateXMLList/* or si:measurementUncertaintyMultivariateXMLList/*]"
                  id="RMC-008" role="error">
        [RMC-008] Certified property values expressed as si:realListXMLList or
        si:complexListXMLList, as a single quantity or inside a list, MUST include measurement
        uncertainty: for si:realListXMLList one of si:measurementUncertaintyUnivariateXMLList,
        si:measurementUncertaintyMultivariateXMLList, si:ellipsoidalRegionXMLList,
        si:rectangularRegionXMLList, or the older si:expandedUncXMLList or si:coverageIntervalXMLList;
        for si:complexListXMLList a non-empty si:measurementUncertaintyBivariateXMLList or
        si:measurementUncertaintyMultivariateXMLList. This is required for all certified values in
        Reference Material Certificates (ISO 33401:2024, 5.3.3).
      </sch:assert>
    </sch:rule>

    <!-- si:hybrid, given as a single quantity (data/quantity) or inside a list (data/list/quantity) -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'referenceMaterialCertificate']
      //drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')]
      //drmd:result/drmd:data//drmd:quantity[si:hybrid]">

      <!-- RMC-009: every number inside a certified si:hybrid must include uncertainty -->
      <sch:assert test="not(si:hybrid/si:real[not(si:measurementUncertaintyUnivariate or si:expandedUnc or si:coverageInterval)])
                        and not(si:hybrid/si:complex[not(si:ellipsoidalRegion or si:rectangularRegion)])
                        and not(si:hybrid/si:constant[not(si:valueStandardMU or si:uncertainty)])
                        and not(si:hybrid//si:realListXMLList[not(si:measurementUncertaintyUnivariateXMLList or si:expandedUncXMLList or si:coverageIntervalXMLList
                                   or si:measurementUncertaintyMultivariateXMLList/* or si:ellipsoidalRegionXMLList
                                   or si:rectangularRegionXMLList)])
                        and not(si:hybrid//si:complexListXMLList[not(si:measurementUncertaintyBivariateXMLList/* or si:measurementUncertaintyMultivariateXMLList/*)])
                        and not(si:hybrid//si:realList[not(si:listMeasurementUncertaintyUnivariate or si:listUnivariateUnc
                                   or si:ellipsoidalRegion or si:rectangularRegion
                                   or not(si:real[not(si:measurementUncertaintyUnivaraite or si:expandedUnc or si:coverageInterval)]))])
                        and not(si:hybrid//si:complexList[not(si:listBivariateUnc/* or si:ellipsoidalRegion or si:rectangularRegion
                                   or not(si:complex[not(si:ellipsoidalRegion or si:rectangularRegion)]))])"
                  id="RMC-009" role="error">
        [RMC-009] In certified properties blocks, every number nested within a si:hybrid container,
        as a single quantity or inside a list, MUST include measurement uncertainty, in one of the
        forms that D-SI provides for it: si:real, si:complex and si:constant as in RMC-006,
        si:realListXMLList and si:complexListXMLList as in RMC-008, and the lists si:realList,
        si:complexList and si:list with an uncertainty for the list or for each of its values
        (ISO 33401:2024, 5.3.3, Property value and associated uncertainty: 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ========================================================= -->
  <!-- PATTERN 4: Product Information Sheet (PIS) Rules            -->
  <!-- ISO 33401:2024 constraints for RMs other than CRMs         -->
  <!-- ========================================================= -->
  <sch:pattern id="pis-document-rules">
    <sch:title>Rules specific to productInformationSheet documents (reference materials other than CRMs)</sch:title>

    <sch:rule context="drmd:digitalReferenceMaterialDocument[
      drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']">

      <!-- PIS-001: Product Information Sheets must NOT contain certified property blocks -->
      <sch:assert test="not(drmd:propertiesList/drmd:properties[(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')])"
                  id="PIS-001" role="error">
        [PIS-001] Product Information Sheets MUST NOT mark any properties block as
        isCertified="true" (or its equivalent "1"). Only reference material certificates, which accompany
        certified reference materials, may contain certified property values. Setting isCertified="true" on a productInformationSheet
        document constitutes a misrepresentation of the material's metrological status
        and violates the ISO 33401:2024 distinction between RMs and CRMs.
      </sch:assert>

      <!-- PIS-002: Property data should be present where values are assigned -->
      <sch:assert test="drmd:propertiesList/drmd:properties/drmd:results/drmd:result"
                  id="PIS-002" role="error">
        [PIS-002] Product Information Sheets MUST include results where
        property values are assigned (ISO 33401:2024, 5.2.15, Property of interest).
      </sch:assert>
    </sch:rule>

    <!-- PIS properties blocks should not claim certification -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']
      //drmd:properties">

      <!-- PIS-003: Individual properties blocks must not be certified -->
      <sch:assert test="not(normalize-space(@isCertified) = 'true' or normalize-space(@isCertified) = '1')"
                  id="PIS-003" role="error">
        [PIS-003] In productInformationSheet documents, individual properties blocks
        MUST NOT have isCertified="true" (or its equivalent "1"). This attribute should be omitted
        or set to "false"
        for all property blocks in a Product Information Sheet. Certified property values
        are only permitted in referenceMaterialCertificate documents.
      </sch:assert>
    </sch:rule>

    <!-- ~~~ PIS material-level validation ~~~ -->
    <sch:rule context="drmd:digitalReferenceMaterialDocument[
        drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument = 'productInformationSheet']
      //drmd:materials/drmd:material">

      <!-- PIS-005: Material description is recommended for PIS (ISO 33401:2024, 5.3.2) -->
      <sch:assert test="drmd:description[dcc:content[normalize-space(.) != ''] or dcc:file or dcc:formula]"
                  id="PIS-005" role="warning">
        [PIS-005] Product Information Sheets SHOULD include a description for each material.
        While not mandatory for Product Information Sheets, material descriptions improve
        usability (ISO 33401:2024, 5.3.2, Description of the material:
        'Recommended' for product information sheet, 'Mandatory' for RM certificate).
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
