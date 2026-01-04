from argparse import ArgumentParser
from os import makedirs, getcwd
from pypdf import PdfReader
from tools.pdf_transform_tools import process_pdf, is_pdf_file, is_already_done, mark_as_already_done
from os.path import splitext, isdir, realpath, basename
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
    parser.add_argument("-o", "--output-dir", help="Percorso della directory di output") # Da implementare

    # Parsing degli argomenti
    args = parser.parse_args()

    #
    if args.output_dir is None: # Qualora non venisse specificata una cartella di output
        output_dir_path: str = getcwd() + "/" + new_dir_name
    elif not isdir(args.output_dir): # Qualora il percorso specificato non puntasse a una cartella valida
        print(f"Il percorso {args.output_dir} non è una cartella")
        return
    else: # Tutti gli altri casi.
        output_dir_path: str = realpath(args.output_dir) + "/" + new_dir_name

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

    input_pdf_real_paths: list[str] = [realpath(file_name) for file_name in input_pdf_file_names]

    makedirs(output_dir_path)

    for pdf_number, pdf_path in enumerate(input_pdf_real_paths, start=1):
        pdf_base_name, extension = basename(splitext(pdf_path)[0]), splitext(pdf_path)[1]

        if args.verbose:
            print(f"Processing ({pdf_number} / {len(input_pdf_file_names)}): {pdf_base_name} ...")

        #Apertura PDF corrente
        current_input_pdf = PdfReader(pdf_path)

        # Elaborazione del PDF
        # Evito la doppia elaborazione de
        if is_already_done(current_input_pdf) and not args.force:
            print("Skipping because already done. Use --force to force re-elaboration")
            continue

        output_pdf = process_pdf(current_input_pdf, args.verbose)

        output_pdf_file_name: str = pdf_base_name +"_processed"+extension
        output_pdf_file_path: str = output_dir_path + "/" + output_pdf_file_name

        mark_as_already_done(output_pdf)

        with open(output_pdf_file_path, "wb") as output_file:
           output_pdf.write(output_file)

        current_input_pdf.close()

if __name__ == "__main__":
    main()