from PIL import ImageEnhance, ImageFilter, Image
from docx import Document
import numpy as np
import pytesseract, fitz, PyPDF2, cv2, io, os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# extrae texto de una imagen
def extraerTextoImagen(imagen):
    # convierte la imagen a escala de grises
    imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    # convierte la imagen de arreglo Numpy a Image de PIL
    imagen_pil = Image.fromarray(imagen_gris)
    # mejora el contraste de la imagen
    imagen_pil = ImageEnhance.Contrast(imagen_pil).enhance(2.0)
    # se aplica un filtro de nitidez a la imagen
    imagen_pil = imagen_pil.filter(ImageFilter.SHARPEN)
    # se vuelve a convertir la imagen de Image PIL a array Numpy
    imagen_preprocesada = np.array(imagen_pil)

    # se extrae el texto de la imagen preprocesada
    texto = pytesseract.image_to_string(imagen_preprocesada, lang='spa')
    return texto

# procesa los documentos PDF con imagenes para convertirlos en documentos PDF de texto
def procesarPDF(pdf_ruta, archivo_salida):
    # se abre el documento original
    doc = fitz.open(pdf_ruta)
    # se crea un nuevo documento PDF
    nuevo_doc = fitz.open()

    # se recorren las paginas del documento original
    for num_pagina in range(doc.page_count):

        # obtiene la pagina actual del documento original
        pagina = doc[num_pagina]

        # obtiene las imagenes de la pagina actual
        imagenes = pagina.get_images(full=True)

        # recorre las imagenes de la pagina actual
        for num_img, info_img in enumerate(imagenes):
            # obtiene el indice de la pagina
            indice_img = info_img[0]
            # se extrae la imagen
            img = doc.extract_image(indice_img)
            # se obtienen los datos de la imagen
            data_img = img["image"]
            # abre la imagen con PIL a partir de los datos obtenidos
            imagen = Image.open(io.BytesIO(data_img))

            # se extrae el texto de la imagen usando el metodo extraerTextoImagen()
            texto_imagen = extraerTextoImagen(np.array(imagen))

            if isinstance(texto_imagen, str) and texto_imagen.strip():
                # crea una pagina en el documento nuevo y agrega el texto extraido
                nueva_pagina = nuevo_doc.new_page(width=pagina.rect.width, height=pagina.rect.height)
                nueva_pagina.insert_text((50, 50), texto_imagen)

        # Eliminar firmas digitales usando PyPDF2
        with io.BytesIO() as temp_buffer:
            nuevo_doc.save(temp_buffer)
            temp_buffer.seek(0)

            # Eliminar firmas digitales
            removerFirmas(temp_buffer, temp_buffer)

            temp_buffer.seek(0)
            nuevo_doc = fitz.open(pdf=temp_buffer.read())

        # se recorre cada bloque de texto en la página y se agrega al nuevo documento PDF
        for bloque in pagina.get_text("blocks"):
            texto_bloque = bloque[4]

            # verifica si el bloque contiene información de imagen
            if isinstance(texto_bloque, str) and texto_bloque.startswith("<image:"):
                continue

            if isinstance(texto_bloque, str) and texto_bloque.strip():
                nueva_pagina = nuevo_doc.new_page(width=pagina.rect.width, height=pagina.rect.height)
                nueva_pagina.insert_text((50, 50), texto_bloque)

    nuevo_doc.save(archivo_salida)


# procesar los documentos WORD con imagenes para convertirlos en documentos PDF de texto
def procesarWord(word_ruta, archivo_salida):

    # crear un nuevo documento PDF
    nuevo_doc = fitz.open()

    # se abre el documento word (.docx)
    doc = Document(word_ruta)

    # recorre cada imagen en el documento Word
    for rel in doc.part.rels:
        if "image" in doc.part.rels[rel].target_ref:
            image_blob = doc.part.rels[rel].target_part.blob
            imagen = Image.open(io.BytesIO(image_blob))
            texto_imagen = extraerTextoImagen(np.array(imagen))

            # insertar texto extraído de la imagen en el nuevo documento PDF
            if texto_imagen.strip():
                nueva_pagina = nuevo_doc.new_page(width=595, height=842)  # A4 size
                nueva_pagina.insert_text((50, 50), texto_imagen)

    # se recorre cada párrafo en el documento word
    for para in doc.paragraphs:
        
        # elimina espacios en blanco al inicio y al final
        texto = para.text.strip()

        # se saltan los parrafos vacios
        if not texto:
            continue

        # inserta texto en el nuevo documento PDF
        nueva_pagina = nuevo_doc.new_page(width=595, height=842)  # A4 size
        nueva_pagina.insert_text((50, 50), texto)

    # guarda el nuevo documento PDF
    nuevo_doc.save(archivo_salida)

# función para eliminar firmas digitales usando PyPDF2
def removerFirmas(input_buffer, output_buffer):
    pdf_reader = PyPDF2.PdfFileReader(input_buffer)
    pdf_writer = PyPDF2.PdfFileWriter()

    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        page['/Annots'] = []

        pdf_writer.addPage(page)

    pdf_writer.write(output_buffer)

directorio_entrada = r'C:\Users\cbaraya\Desktop\prueba'
directorio_salida = r'C:\Users\cbaraya\Desktop\prueba\documentos'

# recorre los archivos pdf del directorio de entrada para convertirlos
for archivo in os.listdir(directorio_entrada):
    # verifica si el archivo tiene la extension ".pdf"
    if archivo.endswith(".pdf"):
        # crea la ruta completa al archivo de entrada
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        # crea la ruta completa al archivo de salida con el nombre modificado "convertido_NOMBRE-ORIGINAL"
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo}")
        # se llama al método procesarPDF() con el archivo de entrada y salida como parametros
        procesarPDF(archivo_entrada, archivo_salida)
    elif archivo.endswith(".docx"):
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo}")
        procesarWord(archivo_entrada, archivo_salida)

print("DOCUMENTOS CONVERTIDOS A TEXTO OK")

# filtrar documentos por palabra o texto en el nombre de archivo o en el contenido
def buscar_documentos(texto_busqueda, directorio):
    documentos_coincidentes = []

    for archivo in os.listdir(directorio):
        if archivo.endswith(".pdf"):
            ruta_archivo = os.path.join(directorio, archivo)

            # verifica si el texto de busqueda esta presente en el nombre del documento
            if texto_busqueda.lower() in archivo.lower():
                documentos_coincidentes.append(ruta_archivo)
            else:
                # intenta abrir y leer el contenido del documento PDF
                try:
                    doc = fitz.open(ruta_archivo)
                    for num_pagina in range(doc.page_count):
                        texto_pagina = doc[num_pagina].get_text()
                        # verifica si el texto de busqueda se encuentra en el contenido del documento
                        if texto_busqueda.lower() in texto_pagina.lower():
                            documentos_coincidentes.append(ruta_archivo)
                            break
                except Exception as e:
                    print(f"Error al procesar {ruta_archivo}: {str(e)}")

    return documentos_coincidentes

# codigo busqueda ejemplo
texto_a_buscar = 'HOLA' # CADENA DE TEXTO A BUSCAR

documentos_coincidentes = buscar_documentos(texto_a_buscar, directorio_salida)

if documentos_coincidentes:
    print(f"Documentos que contienen '{texto_a_buscar}':")
    for documento in documentos_coincidentes:
        print(documento)
else:
    print(f"No se encontraron documentos que contengan '{texto_a_buscar}'.")