from PIL import ImageEnhance, ImageFilter, Image
from docx import Document
import numpy as np
import pytesseract, fitz, cv2, PyPDF2, io, os


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# extrae texto de una imagen
def extraerTextoImagen(imagen):

    try:
        # se verifica si la imagen ya está en escala de grises
        if len(imagen.shape) == 2 or (len(imagen.shape) == 3 and imagen.shape[2] == 1):
            # la imagen ya está en escala de grises, no es necesario convertirla
            imagen_gris = imagen
        else:
            # la imagen está en 3 canales (RGB), hay que convertirla a escala de grises
            imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
     
        imagen_pil = Image.fromarray(imagen_gris)
        imagen_pil = ImageEnhance.Contrast(imagen_pil).enhance(2.0)
        imagen_pil = imagen_pil.filter(ImageFilter.SHARPEN)
        imagen_preprocesada = np.array(imagen_pil)

        texto = pytesseract.image_to_string(imagen_preprocesada, lang='spa')
        return texto
    
    except Exception as e:
        # Manejar cualquier excepción que ocurra durante el procesamiento de la imagen
        print(f"Error al procesar la imagen: {str(e)}")
        return ""

# procesa los documentos PDF con imagenes para convertirlos en documentos PDF de texto
def procesarPDF(pdf_ruta, archivo_salida):

    doc = fitz.open(pdf_ruta)

    nuevo_doc = fitz.open()

    for num_pagina in range(doc.page_count):
        pagina = doc[num_pagina]
        imagenes = pagina.get_images(full=True)

        for num_img, info_img in enumerate(imagenes):
            indice_img = info_img[0]
            img = doc.extract_image(indice_img)
            data_img = img["image"]
            imagen = Image.open(io.BytesIO(data_img))

            texto_imagen = extraerTextoImagen(np.array(imagen))

            if isinstance(texto_imagen, str) and texto_imagen.strip():
                nueva_pagina = nuevo_doc.new_page(width=pagina.rect.width, height=pagina.rect.height)
                nueva_pagina.insert_text((50, 50), texto_imagen)

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

# HACER FUNCION
# elimina firmas digitales en documentos pdf
def removerFirmas():
    return

directorio_entrada = r'C:\Users\aarayam\Desktop\prueba\documentos_originales'
directorio_salida = r'C:\Users\aarayam\Desktop\prueba\documentos_convertidos'

# recorre los archivos pdf del directorio para convertirlos
for archivo in os.listdir(directorio_entrada):
    if archivo.endswith(".pdf"):
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        archivo_sin_extension, _ = os.path.splitext(archivo)
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo_sin_extension}.pdf")
        procesarPDF(archivo_entrada, archivo_salida)
    elif archivo.endswith(".docx"):
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        archivo_sin_extension, _ = os.path.splitext(archivo)
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo_sin_extension}.pdf")
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