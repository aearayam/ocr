from PIL import Image
from docx import Document
import numpy as np
import fitz, PyPDF2, io

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

        # eliminar firmas digitales usando PyPDF2
        with io.BytesIO() as temp_buffer:
            nuevo_doc.save(temp_buffer)
            temp_buffer.seek(0)

            # eliminar firmas digitales
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

# función para eliminar firmas digitales usando PyPDF2
def removerFirmas(input_buffer, output_buffer):
    pdf_reader = PyPDF2.PdfFileReader(input_buffer)
    pdf_writer = PyPDF2.PdfFileWriter()

    # recorre las paginas del documento original y elimina las firmas digitales
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        page['/Annots'] = []

        pdf_writer.addPage(page)

    # escribe el documento modificado en el buffer de salida
    pdf_writer.write(output_buffer)