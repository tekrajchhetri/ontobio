from ontobio.io import assocwriter
from ontobio.io import gafparser, gpadparser
from ontobio.model.association import GoAssociation, Curie, Subject, Term, ConjunctiveSet, Evidence, ExtensionUnit
import json
import io


def test_gaf_writer():
    association = GoAssociation(
        source_line="",
        subject=Subject(
            id=Curie("PomBase", "SPAC25B8.17"),
            label="ypf1",
            type="protein",
            fullname="intramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)",
            synonyms=["ppp81"],
            taxon=Curie("NCBITaxon", "4896")
        ),
        object=Term(
            id=Curie("GO", "0000006"),
            taxon=Curie("NCBITaxon", "4896")
        ),
        negated=False,
        qualifiers=[],
        aspect="C",
        relation=Curie("BFO", "0000050"),
        interacting_taxon=Curie("NCBITaxon", "555"),
        evidence=Evidence(
            type=Curie("ECO", "0000266"),
            has_supporting_reference=[Curie("GO_REF", "0000024")],
            with_support_from=[ConjunctiveSet(
                elements=[Curie("SGD", "S000001583")]
            )]
        ),
        provided_by="PomBase",
        date="20150305",
        subject_extensions=[
            ExtensionUnit(
                relation=Curie("rdfs", "subClassOf"),
                term=Curie("UniProtKB", "P12345")
            )
        ],
        object_extensions=[
            ConjunctiveSet(elements=[
                ExtensionUnit(
                    relation=Curie("BFO", "0000050"),
                    term=Curie("X", "1")
                )
            ])
        ],
        properties=dict()
    )
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)
    # `out` will get written with gaf lines from the above assocation object
    expected = "PomBase\tSPAC25B8.17\typf1\t\tGO:0000006\tGO_REF:0000024\tISO\tSGD:S000001583\tC\tintramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)\tppp81\tprotein\ttaxon:4896|taxon:555\t20150305\tPomBase\tpart_of(X:1)\tUniProtKB:P12345"
    writer.write_assoc(association)
    print(out.getvalue())
    gaf = [line.strip("\n") for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert expected == gaf

def test_full_taxon_field_single_taxon():
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)

    taxon_field = writer._full_taxon_field("taxon:12345", None)
    assert "taxon:12345" == taxon_field

def test_full_taxon_field_interacting():
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)

    taxon_field = writer._full_taxon_field("taxon:12345", "taxon:6789")
    assert "taxon:12345|taxon:6789" == taxon_field

def test_full_taxon_empty_string_interacting_taxon():
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)

    taxon_field = writer._full_taxon_field("taxon:12345", "")
    assert "taxon:12345" == taxon_field

def test_negated_qualifers():
    gaf = ["PomBase", "SPBC11B10.09", "cdc2", "NOT", "GO:0007275", "PMID:21873635", "ISO", "PANTHER:PTN000623979|TAIR:locus:2099478", "P", "Cyclin-dependent kinase 1", "UniProtKB:P04551|PTN000624043", "protein", "taxon:284812", "20170228", "GO_Central", "", ""]
    parser = gafparser.GafParser()
    result = parser.parse_line("\t".join(gaf))
    writer = assocwriter.GafWriter()
    parsed = writer.as_tsv(result.associations[0])
    print(parsed)
    assert parsed[3] == "NOT"

    writer = assocwriter.GpadWriter()
    parsed = writer.as_tsv(result.associations[0])
    print(parsed)
    assert parsed[2] == "NOT|involved_in"

def test_roundtrip():
    """
    Start with a line, parse it, then write it. The beginning line should be the same as what was written.
    """
    line = "PomBase\tSPAC25B8.17\typf1\t\tGO:0000006\tGO_REF:0000024\tISO\tSGD:S000001583\tC\tintramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)\tppp81\tprotein\ttaxon:999|taxon:888\t20150305\tPomBase\tpart_of(X:1)\tUniProtKB:P12345"
    parser = gafparser.GafParser()
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)
    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gaf = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert line == gaf

    # Single taxon
    line = "PomBase\tSPAC25B8.17\typf1\t\tGO:0000006\tGO_REF:0000024\tISO\tSGD:S000001583\tC\tintramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)\tppp81\tprotein\ttaxon:1111\t20150305\tPomBase\tpart_of(X:1)\tUniProtKB:P12345"
    parser = gafparser.GafParser()
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out)
    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gaf = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert line == gaf

def test_gpad_qualifier_removed_in_gaf_2_1():
    # Qualifier is `part_of` and should be returned blank instead of removing the whole line
    line = "PomBase\tSPBC1348.01\tpart_of\tGO:0009897\tGO_REF:0000051\tECO:0000201\t\t\t20060201\tPomBase\t\t"
    parser = gpadparser.GpadParser()
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out, version="2.1")  # Write out to gaf 2.1

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gpad_to_gaf_line = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert gpad_to_gaf_line.split("\t")[3] == ""

    # Test with a `NOT`
    line = "PomBase\tSPBC1348.01\tNOT|part_of\tGO:0009897\tGO_REF:0000051\tECO:0000201\t\t\t20060201\tPomBase\t\t"
    parser = gpadparser.GpadParser()
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out, version="2.1")  # Write out to gaf 2.1

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gpad_to_gaf_line = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert gpad_to_gaf_line.split("\t")[3] == "NOT"

def test_gaf2_2_qualifier_to_gaf2_1():
    # Qualifier is `part_of` and should be returned blank instead of removing the whole line
    line = "WB\tWBGene00000001\taap-1\tinvolved_in\tGO:0008286\tWB_REF:WBPaper00005614|PMID:12393910\tIMP\t\tP\t\tY110A7A.10\tgene\ttaxon:6239\t20060302\tWB\t\t"
    parser = gafparser.GafParser()
    parser.version = "2.2"
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out, version="2.1")  # Write out to gaf 2.1

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gpad_to_gaf_line = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert gpad_to_gaf_line.split("\t")[3] == ""

    # Test with a `NOT`
    line = "WB\tWBGene00000001\taap-1\tNOT|involved_in\tGO:0008286\tWB_REF:WBPaper00005614|PMID:12393910\tIMP\t\tP\t\tY110A7A.10\tgene\ttaxon:6239\t20060302\tWB\t\t"
    parser = gafparser.GafParser()
    parser.version = "2.2"
    out = io.StringIO()
    writer = assocwriter.GafWriter(file=out, version="2.1")  # Write out to gaf 2.1

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)
    gpad_to_gaf_line = [line for line in out.getvalue().split("\n") if not line.startswith("!")][0]
    assert gpad_to_gaf_line.split("\t")[3] == "NOT"

def test_gaf_to_gpad2():
    line = "PomBase\tSPAC25B8.17\typf1\t\tGO:0000006\tGO_REF:0000024\tISO\tSGD:S000001583\tC\tintramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)\tppp81\tprotein\ttaxon:999|taxon:888\t20150305\tPomBase\tpart_of(X:1)\tUniProtKB:P12345"
    parser = gafparser.GafParser()
    out = io.StringIO()
    writer = assocwriter.GpadWriter(version=assocwriter.GPAD_2_0, file=out)

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)

    lines = out.getvalue().split("\n")
    assert lines[0] == "!gpa-version: 2.0"
    assert lines[1] == "PomBase:SPAC25B8.17\t\tBFO:0000050\tGO:0000006\tGO_REF:0000024\tECO:0000266\tSGD:S000001583\tNCBITaxon:888\t20150305\tPomBase\tBFO:0000050(X:1)\t"

    line = "PomBase\tSPAC25B8.17\typf1\tNOT\tGO:0000006\tGO_REF:0000024\tISO\tSGD:S000001583\tC\tintramembrane aspartyl protease of the perinuclear ER membrane Ypf1 (predicted)\tppp81\tprotein\ttaxon:999|taxon:888\t20150305\tPomBase\tpart_of(X:1)\tUniProtKB:P12345"
    parser = gafparser.GafParser()
    out = io.StringIO()
    writer = assocwriter.GpadWriter(version=assocwriter.GPAD_2_0, file=out)

    assoc = parser.parse_line(line).associations[0]
    writer.write_assoc(assoc)

    lines = out.getvalue().split("\n")
    assert lines[0] == "!gpa-version: 2.0"
    assert lines[1] == "PomBase:SPAC25B8.17\tNOT\tBFO:0000050\tGO:0000006\tGO_REF:0000024\tECO:0000266\tSGD:S000001583\tNCBITaxon:888\t20150305\tPomBase\tBFO:0000050(X:1)\t"
