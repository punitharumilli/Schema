/*
 * XercesCheck.java: validate DRMD instances with the JDK's own XSD validator.
 *
 * WHY A SECOND VALIDATOR
 * tools/validate.py uses lxml, which is libxml2. Xerces, built into the JDK, is the validator
 * most JVM pipelines use, and it disagrees with libxml2 in two ways that have already caused
 * real defects in this schema:
 *
 *   1. Xerces refuses to read a schema file whose DOCTYPE it cannot resolve. The W3C signature
 *      schema ships with exactly such a DOCTYPE, and the result was that ds:Signature had no
 *      declaration and the WHOLE of drmd.xsd failed to compile, reported against drmd.xsd rather than
 *      against the signature schema. libxml2 tolerated it, so the breakage was invisible to the
 *      Python checks. supporting/xmldsig-core-schema.xsd now has that DOCTYPE stripped; this
 *      check is what stops it coming back.
 *
 *   2. Xerces enforces IDREF integrity ("cvc-id.1: There is no ID/IDREF binding for IDREF"),
 *      libxml2 does not. A @refId typo therefore passes xmllint and fails in Java.
 *
 * Running only one implementation lets both classes of defect through.
 *
 * NOTE ON THE CATALOG
 * Xerces does not read libxml2's XML_CATALOG_FILES environment variable. The catalog has to be
 * handed to it explicitly, through a CatalogResolver set on BOTH the SchemaFactory and the
 * Validator. Without it, Xerces tries to fetch the PTB schemas over the network.
 *
 * Usage
 *     javac tests/XercesCheck.java -d /tmp/xerces
 *     java -cp /tmp/xerces XercesCheck catalog.xml drmd.xsd examples/*.xml
 *
 * Exit code 0 if the schema compiled and every instance is valid, 1 otherwise.
 */

import javax.xml.catalog.CatalogFeatures;
import javax.xml.catalog.CatalogManager;
import javax.xml.catalog.CatalogResolver;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXParseException;

import java.io.File;
import java.nio.file.Path;

public class XercesCheck {

    /** Collects errors instead of throwing on the first one, so a run reports everything. */
    static final class Collector implements ErrorHandler {
        private final String tag;
        int errors = 0;

        Collector(String tag) {
            this.tag = tag;
        }

        @Override
        public void warning(SAXParseException e) {
            System.out.println("  [" + tag + " warning] " + e.getMessage());
        }

        @Override
        public void error(SAXParseException e) {
            errors++;
            System.out.println("  [" + tag + "] line " + e.getLineNumber() + ": " + e.getMessage());
        }

        @Override
        public void fatalError(SAXParseException e) {
            errors++;
            System.out.println("  [" + tag + " fatal] " + e.getMessage());
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("usage: XercesCheck <catalog.xml> <drmd.xsd> <instance.xml>...");
            System.exit(2);
        }

        CatalogResolver resolver = CatalogManager.catalogResolver(
                CatalogFeatures.builder()
                        .with(CatalogFeatures.Feature.RESOLVE, "continue")
                        .build(),
                Path.of(args[0]).toUri());

        SchemaFactory factory = SchemaFactory.newInstance("http://www.w3.org/2001/XMLSchema");
        factory.setResourceResolver(resolver);
        // An error handler on the FACTORY matters as much as one on the validator: without it,
        // a schema that failed to compile surfaces as a confusing complaint about an unrelated
        // element rather than as the missing import that actually caused it.
        Collector schemaErrors = new Collector("schema");
        factory.setErrorHandler(schemaErrors);

        Schema schema = factory.newSchema(new File(args[1]));
        if (schemaErrors.errors > 0) {
            System.out.println("FAILED: drmd.xsd did not compile under Xerces "
                    + "(" + schemaErrors.errors + " error(s)).");
            System.out.println("Check that catalog.xml resolves every remote import, and that no "
                    + "vendored schema carries a DOCTYPE Xerces cannot read.");
            System.exit(1);
        }
        System.out.println("drmd.xsd compiled under Xerces with no network access.");

        int invalid = 0;
        for (int i = 2; i < args.length; i++) {
            Validator validator = schema.newValidator();
            validator.setResourceResolver(resolver);
            Collector instanceErrors = new Collector("instance");
            validator.setErrorHandler(instanceErrors);
            validator.validate(new StreamSource(new File(args[i])));
            System.out.println((instanceErrors.errors == 0 ? "  valid    " : "  INVALID  ")
                    + new File(args[i]).getName());
            if (instanceErrors.errors > 0) {
                invalid++;
            }
        }

        System.out.println(invalid == 0
                ? "All instances valid under Xerces."
                : invalid + " instance(s) invalid under Xerces.");
        System.exit(invalid == 0 ? 0 : 1);
    }
}
