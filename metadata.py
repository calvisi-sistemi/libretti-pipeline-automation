import argparse
import csv
from xml.etree import ElementTree
from tools.metadata_tools import *

# ------------------------
# Costanti
# ------------------------

CENTURIE_VALIDE = {"I", "II", "III", "IV", "V", "VI"}

# ------------------------
# Argomenti da riga di comando
# ------------------------

parser = argparse.ArgumentParser(
    description="Estrazione metadati Dublin Core dei libretti di Mal'Aria"
)

parser.add_argument(
    "--catalogo",
    required=True,
    help="Percorso del file CSV del catalogo"
)

parser.add_argument(
    "--numeri",
    help="Numero/i assoluto/i dei libretti da estrarre (separati da virgola)"
)

parser.add_argument(
    "--centuria",
    help="Centuria da estrarre (I–VI, numeri romani)"
)

args = parser.parse_args()

# ------------------------
# Validazione opzioni
# ------------------------

if args.numeri and args.centuria:
    raise ValueError(
        "Usare solo una tra --numeri e --centuria"
    )

numeri_richiesti = None
centuria_richiesta = None

if args.numeri:
    numeri_richiesti = {
        n.strip() for n in args.numeri.split(",") if n.strip()
    }

if args.centuria:
    centuria_richiesta = args.centuria.strip().upper()
    if centuria_richiesta not in CENTURIE_VALIDE:
        raise ValueError(
            f"Centuria non valida: {centuria_richiesta}. "
            "Valori ammessi: I, II, III, IV, V, VI"
        )

# ------------------------
# Namespace XML
# ------------------------

for prefix, uri in NS.items():
    ElementTree.register_namespace(prefix, uri)

# ------------------------
# Lettura CSV ed estrazione
# ------------------------

trovati = set()

with open(args.catalogo, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)

    root = ElementTree.Element(
        ElementTree.QName(NS["dcterms"], "DublinCore")
    )

    for row in reader:
        numero = row.get("NumeroAssoluto", "").strip()
        centuria = row.get("Centuria", "").strip().upper()

        # Filtro per NumeroAssoluto
        if numeri_richiesti is not None:
            if numero not in numeri_richiesti:
                continue
            trovati.add(numero)

        # Filtro per Centuria
        if centuria_richiesta is not None:
            if centuria != centuria_richiesta:
                continue

        crea_record(root, row)

    # Scrittura output
    if numeri_richiesti:
        filename = "malaria_selezione_numeri_dublin_core.xml"
    elif centuria_richiesta:
        filename = f"malaria_centuria_{centuria_richiesta}_dublin_core.xml"
    else:
        filename = "malaria_dublin_core_completo.xml"

    write_pretty_xml(root, filename)

# ------------------------
# Errore se numeri mancanti
# ------------------------

if numeri_richiesti:
    mancanti = numeri_richiesti - trovati
    if mancanti:
        raise Exception(
            "Errore: i seguenti NumeroAssoluto non sono presenti nel catalogo: "
            + ", ".join(sorted(mancanti))
        )