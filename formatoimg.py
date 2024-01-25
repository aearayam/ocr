import PyPDF2

def extraer_imagenes_desde_pdf(pdf_path):
    imagenes_formatos = set()

    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_paginas = len(pdf_reader.pages)

        for pagina_num in range(num_paginas):
            pagina = pdf_reader.pages[pagina_num]
            objetos_p = pagina['/Resources']['/XObject']

            for obj in objetos_p.get_object():
                if objetos_p[obj]['/Subtype'] == '/Image':
                    formato_img = objetos_p[obj]['/Filter'][1:]

                    # Algunos PDF pueden tener múltiples formatos especificados
                    if isinstance(formato_img, list):
                        formato_img = formato_img[0]

                    imagenes_formatos.add(formato_img)

    return imagenes_formatos

pdf_path = r"C:\Users\aarayam\Desktop\documentos_prueba\documentos_originales\pdfprueba3.pdf"
formatos_imagenes_en_pdf = extraer_imagenes_desde_pdf(pdf_path)

print("Formatos de imagen en el PDF:", formatos_imagenes_en_pdf)