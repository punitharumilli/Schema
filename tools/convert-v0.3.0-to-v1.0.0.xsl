<?xml version="1.0" encoding="UTF-8"?>
<!--
  SPDX-FileCopyrightText: 2026 Bundesanstalt für Materialforschung und -prüfung (BAM)
  SPDX-License-Identifier: LGPL-3.0-only

  Converts a DRMD document of the earlier release v0.3.0 (QI-Data-Lab/DRMD, namespace
  https://example.org/drmd) to DRMD 1.0.0 (namespace urn:drmd:schema).

  What changes
    1. The DRMD namespace: https://example.org/drmd becomes urn:drmd:schema.
    2. materialPropertiesList becomes propertiesList, materialProperties becomes properties.
    3. coreData gets the documentVersion that 1.0.0 requires (ISO 33401:2024, 5.2.13). v0.3.0 had
       no such element, so the value must be given as the parameter documentVersion.
    4. @schemaVersion becomes 1.0.0.
    5. An XML signature (ds:Signature) is removed: the conversion changes the signed content, so
       the old signature could never be verified again. Sign the converted document anew.
  Everything else (DCC and D-SI content, identifiers, statements, embedded files) is copied
  unchanged. The elements of 1.0.0 have the same names, order and types as in v0.3.0, apart from
  the points above.

  The result is valid against drmd.xsd. Then run the business rules, which check requirements of
  ISO 33401:2024 that v0.3.0 did not check:  python tools/validate.py converted.xml

  Runs in any XSLT 1.0 processor. The commands for Python (tools/convert_v0_3_0.py) and for
  xsltproc are in tools/README.md.
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:old="https://example.org/drmd"
    xmlns:drmd="urn:drmd:schema"
    xmlns:dcc="https://ptb.de/dcc"
    xmlns:si="https://ptb.de/si"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    exclude-result-prefixes="old ds xsi">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
  <xsl:strip-space elements="*"/>

  <!-- The revision of the document (a version number, an approval date, or both). Required. -->
  <xsl:param name="documentVersion" select="''"/>

  <xsl:variable name="NS" select="'urn:drmd:schema'"/>

  <xsl:template match="/">
    <xsl:if test="not(old:digitalReferenceMaterialDocument)">
      <xsl:message terminate="yes">Not a DRMD v0.3.0 document: the root element must be digitalReferenceMaterialDocument in the namespace https://example.org/drmd.</xsl:message>
    </xsl:if>
    <xsl:if test="not(starts-with(old:digitalReferenceMaterialDocument/@schemaVersion, '0.3.'))">
      <xsl:message terminate="yes">Only documents with schemaVersion 0.3.x can be converted; this one states <xsl:value-of select="old:digitalReferenceMaterialDocument/@schemaVersion"/>.</xsl:message>
    </xsl:if>
    <xsl:if test="normalize-space($documentVersion) = '' and not(//old:coreData/old:documentVersion)">
      <xsl:message terminate="yes">DRMD 1.0.0 requires a documentVersion (ISO 33401:2024, 5.2.13), which v0.3.0 did not have. Give it as the parameter documentVersion, for example 1 or the approval date.</xsl:message>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Root: literal element, so that the namespace declarations sit on the root only. -->
  <xsl:template match="old:digitalReferenceMaterialDocument">
    <drmd:digitalReferenceMaterialDocument>
      <xsl:apply-templates select="@*[not(namespace-uri() = 'http://www.w3.org/2001/XMLSchema-instance')]"/>
      <xsl:attribute name="schemaVersion">1.0.0</xsl:attribute>
      <xsl:apply-templates select="node()"/>
    </drmd:digitalReferenceMaterialDocument>
  </xsl:template>

  <xsl:template match="old:materialPropertiesList">
    <xsl:element name="drmd:propertiesList" namespace="{$NS}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="old:materialProperties">
    <xsl:element name="drmd:properties" namespace="{$NS}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>

  <!-- documentVersion follows uniqueIdentifier, as in drmd.xsd. -->
  <xsl:template match="old:coreData/old:uniqueIdentifier">
    <xsl:element name="drmd:uniqueIdentifier" namespace="{$NS}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
    <xsl:if test="not(../old:documentVersion)">
      <xsl:element name="drmd:documentVersion" namespace="{$NS}">
        <xsl:value-of select="normalize-space($documentVersion)"/>
      </xsl:element>
    </xsl:if>
  </xsl:template>

  <xsl:template match="ds:Signature">
    <xsl:message terminate="no">Removed an XML signature: it covered the v0.3.0 content and could not be verified after the conversion. Sign the converted document anew.</xsl:message>
  </xsl:template>

  <!-- Any other DRMD element: same local name in the 1.0.0 namespace. -->
  <xsl:template match="old:*">
    <xsl:element name="drmd:{local-name()}" namespace="{$NS}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>

  <!-- DCC, D-SI and any other element: rebuilt rather than copied, so that the old DRMD namespace
       declaration is not carried along. -->
  <xsl:template match="*">
    <xsl:element name="{name()}" namespace="{namespace-uri()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="@*">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="@old:*">
    <xsl:attribute name="drmd:{local-name()}" namespace="{$NS}">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="text()|comment()|processing-instruction()">
    <xsl:copy/>
  </xsl:template>

</xsl:stylesheet>
