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