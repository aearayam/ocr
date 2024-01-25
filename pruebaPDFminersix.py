from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def extraer_texto_de_imagen_pdf(pdf_path):
    texto_total = ""
    
    # Extraer texto del PDF utilizando pdfminer.six
    texto_pdf = extract_text(pdf_path)

    # Agregar texto extraído del PDF al resultado final
    texto_total += texto_pdf

    # Convertir páginas del PDF a imágenes y extraer texto con OCR
    imagenes = convert_from_path(pdf_path)

    for i, imagen in enumerate(imagenes):
        # Guardar imagen como archivo temporal (opcional)
        imagen.save(f"pagina_{i + 1}.png")

        # Utilizar pytesseract para extraer texto de la imagen
        texto_imagen = pytesseract.image_to_string(imagen, lang='spa')

        # Agregar texto extraído de la imagen al resultado final
        texto_total += texto_imagen

    return texto_total

# Ejemplo de uso
pdf_path = r"C:\Users\aarayam\Desktop\documentos_prueba\documentos_originales\Documento (65).pdf"
texto_extraido = extraer_texto_de_imagen_pdf(pdf_path)
print(texto_extraido)