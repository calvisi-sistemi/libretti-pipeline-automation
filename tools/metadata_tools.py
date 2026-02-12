import csv
from xml.dom import minidom
from xml.etree import ElementTree


NS: dict[str, str] = {
    "dcterms": "http://purl.org/dc/terms/"
}
"""Dizionario contenente i namespace di Dublin core adoperati (dc, dcterms) e le relative URI di specificazione"""


DUBLINCORE_NS_PREFIX = "dcterms"

FIELD_MAPPING: dict [str ,str] = {
    "Titolo": "title",
    "AutoreTesto": "creator",
    "AutoreIllustrazione": "creator",
    "AltriAutori": "contributor",
    "TipoContenuto": "type",
    "Lingua": "language",
    "Serie": "isPartOf",
    "Centuria": "isPartOf",
    "IndicazioneData": "date",
    "AnnoNormalizzato": "issued",
    "CittaDiStampa": "spatial",
    "TipografiaNormalizzata": "publisher",
    "PagineStampate": "extent",
    "CopieStampate": "extent",
    "IndicazioneCarta": "medium",
    "Piegatura": "format",
}
"""Dizionario per la corrispondenza tra i campi del catalogo CSV e tag Dublin Core"""


# ------------------------
# Funzione per creare un record XML
# ------------------------
def crea_record(root: ElementTree.Element, row: csv.DictReader) -> None :
    record = ElementTree.SubElement(
        root,
        ElementTree.QName(NS[DUBLINCORE_NS_PREFIX], "BibliographicResource")
    )

    identifier = ElementTree.SubElement(
        record,
        ElementTree.QName(NS[DUBLINCORE_NS_PREFIX], "identifier")
    )
    identifier.text = row['NumeroAssoluto']

    for field, tag in FIELD_MAPPING.items():
        raw_value = row.get(field, "").strip()

        if not raw_value or raw_value.lower() == "nessuna indicazione":
            continue

        if tag in {"creator", "contributor"}:
            values = [v.strip() for v in raw_value.split(",") if v.strip()]
        else:
            values = [raw_value]

        for value in values:
            element = ElementTree.SubElement(
                record,
                ElementTree.QName(NS[DUBLINCORE_NS_PREFIX], tag)
            )
            element.text = value


def write_pretty_xml(root: ElementTree.Element, filename: str):
    rough_string = ElementTree.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    with open(filename, "wb") as f:
        f.write(pretty_xml)

if __name__ == "__main__":
    print("Questo è un modulo da usarsi all'interno di altri script, non uno script autonomo")