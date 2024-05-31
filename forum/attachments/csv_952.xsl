<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">
  <!-- xlog version 1.1.0 -->
  <!-- usage: AltovaXML -xslt2 csv.xsl -in results.xml -out results.csv -->
  <xsl:output method="text" indent="yes" encoding="UTF-8"/>

  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="started" />
  <xsl:template match="experiment-setup" />

  <xsl:template match="measurements">
    <xsl:text>Run #,File,Conc. [mg/ml],Description,Rg [nm],stdev(Rg),I(0),1st Guinier point,last Guinier point,Dmax [nm],Molecular mass [kDa],Volume [nm],Quality [%]</xsl:text>
    <xsl:text>&#10;</xsl:text>

    <xsl:for-each select="file">
      <xsl:value-of select="run-number" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="@name" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(concentration, '0.0')" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="description" /><xsl:value-of select="','"/>
      <xsl:if test="autorg/radius-of-gyration &gt; 0">
         <xsl:value-of select="format-number(autorg/radius-of-gyration, '0.00')" />
      </xsl:if>
      <xsl:value-of select="','"/>
      <xsl:value-of select="autorg/radius-of-gyration-stdev" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(autorg/zero-angle-intensity, '0.00')" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="autorg/first-point" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="autorg/last-point" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(autognom/maximum-distance, '0.0')" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(autosub/molecular-weight, '0')" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(dammif/volume, '0')" />
      <xsl:value-of select="','"/>
      <xsl:value-of select="format-number(autorg/quality, '0')" />
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
