from PIL import ImageEnhance, ImageFilter, Image
from docx import Document
import numpy as np
import psycopg2, pytesseract, fitz, cv2, PyPDF2, io, os




pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

try:
    conn = psycopg2.connect(dbname='bd_prueba', user='postgres', password='postgres', host='localhost', port=5432)
    print("Conexión a la bd exitosa!")
except psycopg2.Error as e:
    print("Error al conectar a la base de datos:", e)


# extrae texto de una imagen
def extraer_texto_imagen(imagen):

    try:
        # se verifica si la imagen ya está en escala de grises
        if len(imagen.shape) == 2 or (len(imagen.shape) == 3 and imagen.shape[2] == 1):
            # la imagen ya está en escala de grises, no es necesario convertirla
            imagen_gris = imagen
        else:
            # la imagen está en 3 canales (RGB), hay que convertirla a escala de grises (1 canal)
            imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
     
        imagen_pil = Image.fromarray(imagen_gris)
        imagen_pil = ImageEnhance.Contrast(imagen_pil).enhance(2.0)
        imagen_pil = imagen_pil.filter(ImageFilter.SHARPEN)
        imagen_preprocesada = np.array(imagen_pil)

        texto = pytesseract.image_to_string(imagen_preprocesada, lang='spa', config='--psm 6 --oem 3') #config='--psm 6 --oem 3'
        return texto.strip()
    
    except Exception as e:
        # Manejar cualquier excepción que ocurra durante el procesamiento de la imagen
        print(f"Error al procesar la imagen: {str(e)}")
        return ""

# procesa los documentos PDF con imagenes para convertirlos en documentos PDF de texto
def procesar_pdf(documento):

    try:
        cur = conn.cursor()

        # path = documento[1] + documento[5]  # se concatena la ruta con el nombre del documento
        path = os.path.join(documento[1], documento[5])

        doc = fitz.open(path)

        print(path)

        # texto normal
        texto_contenido = ""

        contador_imagenes = 0

        '''
        for bloque in doc.get_text("blocks"):
            texto_bloque = bloque[4]

            # verifica si el bloque contiene información de imagen
            if isinstance(texto_bloque, str) and texto_bloque.startswith("<image:"):
                continue

            if isinstance(texto_bloque, str) and texto_bloque.strip():
                texto_contenido += texto_bloque + " "
        '''

        for pagina in range(doc.page_count):

            page = doc[pagina]
            texto_contenido += page.get_text("text") + " "

            # Extraer imágenes
            imagenes = page.get_images(full=True)

            for num_img, info_img in enumerate(imagenes):
                indice_img = info_img[0]
                img = doc.extract_image(indice_img)

                try:
                    # Verificar si es un formato de imagen válido antes de procesarlo
                    Image.open(io.BytesIO(img["image"]))
                    
                    imagen = Image.open(io.BytesIO(img["image"]))
                    texto_imagen = extraer_texto_imagen(np.array(imagen))

                    if isinstance(texto_imagen, str) and texto_imagen.strip():
                        texto_contenido += texto_imagen + " "

                    contador_imagenes += 1
                    

                except Exception as e:
                    print(f"Error al procesar la imagen: {str(e)}")
                    contador_imagenes += 1

                

        '''
        print("Texto a insertar:", texto_contenido)
        print("Consulta SQL:", cur.mogrify("UPDATE documento SET contenido = %s WHERE id = %s;", (texto_contenido, documento[0])))
        '''
        
        print (contador_imagenes)

        # actualizar el contenido en la base de datos (insertar el texto extraido)
        cur.execute("UPDATE documento SET contenido = %s WHERE id = %s;", (texto_contenido, documento[0]))

        # Confirmar la transacción y cerrar la conexión
        conn.commit()
        cur.close()

        return True

    except Exception as e:
        print("Error durante la ejecución:", e)
        return False

# iterar sobre los registros para extraer texto de aquellos que tengan estado_procesamiento = 0
try:
    cur = conn.cursor()

    # obtener los registros con estado_procesamiento = 0
    cur.execute("SELECT * FROM documento WHERE estado_procesamiento = 0")
    documentos_sin_procesar = cur.fetchall()

    # Iterar sobre los registros y procesar el PDF
    for documento in documentos_sin_procesar:
        # print(documento[0])
        try:
            if procesar_pdf(documento):
                #print(documento[0])
                # se convierte el campo "contenido" a tsvector y se actualiza insertando al campo "contenido_vector"
                cur.execute("UPDATE documento SET contenido_vector = to_tsvector('spanish', contenido) WHERE id = %s;", (documento[0],))
                # actualiza el estado_procesamiento a 1 después de procesar
                cur.execute("UPDATE documento SET estado_procesamiento = 1 WHERE id = %s;", (documento[0],))
                conn.commit()
        except Exception as e:
            print(f"Error al procesar el documento {documento}: {e}")
            
finally:
    # se cierra la conexión
    if conn:
        conn.close()

'''
# recorre los archivos pdf del directorio para convertirlos
for archivo in os.listdir(directorio_entrada):
    if archivo.endswith(".pdf"):
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        archivo_sin_extension, _ = os.path.splitext(archivo)
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo_sin_extension}.pdf")
        procesar_pdf(archivo_entrada, archivo_salida)
    elif archivo.endswith(".docx"):
        archivo_entrada = os.path.join(directorio_entrada, archivo)
        archivo_sin_extension, _ = os.path.splitext(archivo)
        archivo_salida = os.path.join(directorio_salida, f"convertido_{archivo_sin_extension}.pdf")
        procesarWord(archivo_entrada, archivo_salida)
                
        print("documento no es PDF")
    else:
        print("documento no es PDF")

print("DOCUMENTOS CONVERTIDOS A TEXTO OK")

'''

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
                        texto_contenido = doc[num_pagina].get_text()
                        # verifica si el texto de busqueda se encuentra en el contenido del documento
                        if texto_busqueda.lower() in texto_contenido.lower():
                            documentos_coincidentes.append(ruta_archivo)
                            break
                except Exception as e:
                    print(f"Error al procesar {ruta_archivo}: {str(e)}")

    return documentos_coincidentes

'''
# codigo busqueda ejemplo
texto_a_buscar = 'HOLA' # CADENA DE TEXTO A BUSCAR

documentos_coincidentes = buscar_documentos(texto_a_buscar, directorio_salida)

if documentos_coincidentes:
    print(f"Documentos que contienen '{texto_a_buscar}':")
    for documento in documentos_coincidentes:
        print(documento)
else:
    print(f"No se encontraron documentos que contengan '{texto_a_buscar}'.")
'''

def buscar_documentos_por_texto(texto_a_buscar):
    try:

        conn = psycopg2.connect(dbname='bd_prueba', user='postgres', password='postgres', host='localhost', port=5432)

        cur = conn.cursor()

        # Convertir el texto de búsqueda a una consulta tsquery sin procesar
        tsquery = f"plainto_tsquery('spanish', %s)"
        
        # Realizar la búsqueda en la base de datos
        # cur.execute("SELECT * FROM documento WHERE contenido_vector @@ " + tsquery + ";", (texto_a_buscar,))    # solo se busca en el contenido (contenido_vector)
        cur.execute("""
            SELECT *
            FROM documento
            WHERE contenido_vector @@ """ + tsquery + """
            OR nombre_documento ILIKE %s;
        """, (texto_a_buscar, texto_a_buscar))
        resultados = cur.fetchall()

        return resultados

    except Exception as e:
        print("Error al realizar la búsqueda:", e)

    finally:
        # Cerrar la conexión al final
        if conn:
            conn.close()


texto_a_buscar = 'lorem ipsuM'
resultados = buscar_documentos_por_texto(texto_a_buscar)

print('Documentos que contienen: ' + texto_a_buscar)
if resultados:
    for resultado in resultados:
        print(resultado[5])
else:
    print("No se encontraron resultados.")