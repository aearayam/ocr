from PIL import ImageEnhance, ImageFilter
from PIL import Image
import numpy as np
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

imagen = cv2.imread(r'imagenes_prueba\pruebaCarta.webp')

# convierte la imagen a escala de grises
imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

imagen_pil = Image.fromarray(imagen_gris)

imagen_pil = ImageEnhance.Contrast(imagen_pil).enhance(2.0)
imagen_pil = imagen_pil.filter(ImageFilter.SHARPEN)

imagen_preprocesada = np.array(imagen_pil)

texto = pytesseract.image_to_string(imagen, lang='spa')

print('Texto de la imagen: ')
print(texto)

cv2.imshow('Imagen', imagen)
cv2.waitKey(0)
cv2.destroyAllWindows()