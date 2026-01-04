from pypdf import PdfReader, PdfWriter, PageObject
from enum import Enum
from copy import copy
from os.path import splitext, isfile

IDEMPOTENCY_METADATA_FIELD = "/CorrectlyOrientatedAndTransformated"

class QuadrantNames(Enum):
    """Costanti con i nomi dei quadranti"""
    RIGHT_BOTTOM_QUADRANT = "right_bottom_quadrant"
    RIGHT_TOP_QUADRANT = "right_top_quadrant"
    LEFT_TOP_QUADRANT = "left_top_quadrant"
    LEFT_BOTTOM_QUADRANT = "left_bottom_quadrant"

def process_pdf(input_pdf: PdfReader, verbose: bool = False) -> PdfWriter:
    """A partire da un PDF di input, estrae, ruota e ordina opportunamente le pagine"""
    output_pdf = PdfWriter()
    original_pages: list[PageObject] = saving_original_full_pages(input_pdf.pages)
    elaborated_pages: list[PageObject] = []
    total_pages = len(input_pdf.pages)

    for page in input_pdf.pages:
        if verbose:
            print(f"    Elaborazione pagina {page.page_number+1} di {total_pages}...")

        quadrants = calculate_quadrants_coordinates(page)
        for quadrant_name, quadrant_coordinates in quadrants.items():
            # Estrazione della pagina (quadrante) del titolo
            if is_title_page(page.page_number, quadrant_name):
                title_page = crop_page(page, quadrant_coordinates)
                add_new_page(title_page, elaborated_pages)
                continue

            # Estrazione della pagina (quadrante) del colophon
            if is_colophon_page(page.page_number, quadrant_name):
                colophon_page = crop_page(page, quadrant_coordinates)
                add_new_page(colophon_page, elaborated_pages,True)# Inserisco il colophon in fondo alla fine delle pagine di output
                continue

            new_page = crop_page(page, quadrant_coordinates)

            # La nuova pagina / quadrante deve essere ruotata di 180° se e solo se
            # 1. La pagina originale era la prima del PDF
            # 2. E' il riquadro in alto a destra o quello in alto a sinistra che sta vendendo estratto

            if should_page_be_rotated(page.page_number, quadrant_name):
                new_page = new_page.rotate(180)
            add_new_page(new_page, elaborated_pages)

    # Aggiunta pagine elaborate al PDF di output
    for elaborated_page in elaborated_pages:
        output_pdf.add_page(elaborated_page)

    # Aggiunta pagine originali al PDF di output
    for original_page in original_pages:
        output_pdf.add_page(original_page)

    return output_pdf

def saving_original_full_pages(reader_pages: list[PageObject]) -> list[PageObject]:
    """ Crea una lista con una copia delle pagine di partenza """
    original_pages : list[PageObject] = []

    for page in reader_pages:
        original_pages.append(copy(page)) # Effettuo una copia in memoria della pagina, poiché altrimenti verrebbe copiato solo il riferimento al PageObject
    return original_pages

def crop_page(original_page: PageObject, coordinates: tuple[tuple[float, float], tuple[float, float]]) -> PageObject:
    """Data una pagina e una coppia di coordinate, restituisce un crop rettangolare conseguente"""    
    page_copy: PageObject = copy(original_page)
    lower_left_coordinates: tuple = coordinates[0]
    upper_right_coordinates: tuple = coordinates[1]

    page_copy.cropbox.lower_left = lower_left_coordinates
    page_copy.cropbox.upper_right = upper_right_coordinates

    return page_copy 

def calculate_quadrants_coordinates(full_page: PageObject) -> dict[QuadrantNames,tuple[tuple[float, float], tuple[float, float]]]:
    """Data una pagina, calcola le coordinate di quattro quadranti identici"""
    
    # Coordinate estreme
    left = float(full_page.mediabox.left)
    right = float(full_page.mediabox.right)
    top = float(full_page.mediabox.top)
    bottom = float(full_page.mediabox.bottom)
    
    # Coordinate medie
    vertical_center = (top+bottom) / 2
    horizontal_center = (left+right) / 2
        
    # Riga inferiore
    left_bottom, center_bottom = (left, bottom), (horizontal_center, bottom)

    # Riga centrale
    left_center, absolute_center, right_center = (left, vertical_center), (horizontal_center, vertical_center), (right, vertical_center) 

    # Riga superiore
    center_top, right_top = (horizontal_center, top), (right, top)
         
    # In PyPDF, l'area di un rettangolo da ritagliare (crop) è identificata dalle coordinate 
    # del suo angolo in basso a sinistra e da quelle del suo angolo in alto a destra
    return {
        QuadrantNames.RIGHT_BOTTOM_QUADRANT: (center_bottom, right_center),  # riquadro titolo
        QuadrantNames.RIGHT_TOP_QUADRANT:    (absolute_center, right_top),
        QuadrantNames.LEFT_TOP_QUADRANT:     (left_center, center_top),
        QuadrantNames.LEFT_BOTTOM_QUADRANT:  (left_bottom, absolute_center)  # riquadro colophon
    }

def should_page_be_rotated(page_number: int, quadrant_name: QuadrantNames) -> bool:
    """Restituisce TRUE se il quadrante corrente nella pagina corrente deve essere sottoposto a rotazine"""
    is_first_page: bool = page_number == 0
    is_content_quadrant: bool = quadrant_name in {
        QuadrantNames.RIGHT_TOP_QUADRANT,
        QuadrantNames.LEFT_TOP_QUADRANT
    }
    return is_first_page and is_content_quadrant

def is_title_page(page_number: int, quadrant_name: QuadrantNames) -> bool:
    """Restituisce TRUE se il quadrante corrente della pagina corrente contiene il titolo"""
    is_first_page: bool = page_number == 0
    is_title_quadrant: bool = quadrant_name is QuadrantNames.RIGHT_BOTTOM_QUADRANT
    return is_first_page and is_title_quadrant

def is_colophon_page(page_number: int, quadrant_name: QuadrantNames) -> bool:
    """Restituisce TRUE se il quadrante corrente della pagina corrente contiene il titolo"""
    is_first_page: bool = page_number == 0
    is_colophon_quadrant: bool = quadrant_name is QuadrantNames.LEFT_BOTTOM_QUADRANT
    return is_first_page and is_colophon_quadrant

def add_new_page(page: PageObject, elaborated_pages: list[PageObject], is_colophon: bool = False) -> None:
    """"Aggiunge una nuova pagina a una lista di pagine elaborate nella posizione corretta"""
    number_of_pages: int = len(elaborated_pages)
    if number_of_pages in (0, 1) or is_colophon:
        elaborated_pages.append(page)
    else:
        elaborated_pages.insert(-1, page)

def is_pdf_file(pdf_file: str) -> bool:
    extension = splitext(pdf_file)[1]
    return isfile(pdf_file) and extension == ".pdf"

def mark_as_already_done(output_pdf: PdfWriter) -> None:
    """"
    Segnala con un metadato opportuno i file che sono già stati elaborati.
    Fa parte delle funzioni che garantiscono l'idempotenza.
    """
    output_pdf.add_metadata({IDEMPOTENCY_METADATA_FIELD: True})

def is_already_done(input_pdf: PdfReader) -> bool:
    return IDEMPOTENCY_METADATA_FIELD in input_pdf.metadata

if __name__ == "__main__":
    print("Questo è un modulo da usarsi all'interno di altri script, non uno script autonomo")