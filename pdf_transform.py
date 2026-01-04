from argparse import ArgumentParser
from os import makedirs
from pypdf import PdfReader
from tools.pdf_transform_tools import process_pdf, is_pdf_file, is_already_done, mark_as_already_done
from os.path import splitext
from glob import glob
from datetime import datetime


DATE_STRING_FORMAT = "%Y%m%d_%H%M%S"
def main():
    new_dir_name = "processed_"+ datetime.now().strftime(DATE_STRING_FORMAT)

    parser = ArgumentParser(
        prog="PDF Transformer",
        description="Trasforma le scansioni mono o bi-pagina dei Libretti in file con un quadrante per pagina, ordinato e orientato correttamente per la lettura",
        epilog="Elaborazione propedeutica a OCR"
    )

    # Specifica arguments riga di comando
    parser.add_argument("-f", "--force", action="store_true", help="Forza la rielaborazione di un file già lavorato (ignora idempotenza)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modalità verbosa, mostra l'avanzamento dell'elaborazione del programma")
    parser.add_argument("input_pdfs", nargs="+", help="File da elaborare")

    # Parsing degli argomenti
    args = parser.parse_args()

    # glob() restituisce già una lista di stringhe. Senza il secondo "for", la list-comprehension restituiriebbe una lista di liste di stringhe ( list[list[str]] )
    input_file_names_expanded: list[str] = [
        file_string
        for pattern in args.input_pdfs
            for file_string in glob(pattern)
    ]

    input_pdf_file_names: list[str] = [current_file for current_file in input_file_names_expanded if is_pdf_file(current_file)]

    # Se non viene selezionato nessun file esistente, o nessun file in assoluto
    if len(input_file_names_expanded) == 0:
        print("Nessun file selezionato. Nulla da fare")
        return

    # Se tra i file selezionati non è presente neanche un PDF
    if len(input_pdf_file_names) == 0:
        print("Nessun PDF presente nei file selezionati. Nulla da fare")
        return

    makedirs(new_dir_name)

    for pdf_number, pdf_name in enumerate(input_pdf_file_names, start=1):
        if args.verbose:
            print(f"Processing ({pdf_number} / {len(input_pdf_file_names)}): {pdf_name} ...")

        #Apertura PDF corrente
        current_input_pdf = PdfReader(pdf_name)

        # Elaborazione del PDF
        # Evito la doppia elaborazione de
        if is_already_done(current_input_pdf) and not args.force:
            print("Skipping because already done. Use --force to force re-elaboration")
            continue

        output_pdf = process_pdf(current_input_pdf, args.verbose)

        # Creazione del file finale
        base_name, extension = splitext(pdf_name)[0], splitext(pdf_name)[1]

        output_pdf_file_name: str = base_name +"_processed"+extension
        output_pdf_file_path: str = new_dir_name + "/" + output_pdf_file_name

        mark_as_already_done(output_pdf)

        with open(output_pdf_file_path, "wb") as output_file:
           output_pdf.write(output_file)

        current_input_pdf.close()

if __name__ == "__main__":
    main()