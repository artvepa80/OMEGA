import os
import re

def reemplazar_is_integer(archivo):
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()

    nuevo_contenido = re.sub(
        r'(\b\w+)\.is_integer\(\)',
        r'isinstance(\1, int) or (isinstance(\1, float) and \1.is_integer())',
        contenido
    )

    if nuevo_contenido != contenido:
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        print(f"✅ Reemplazado en: {archivo}")

def escanear_directorio(directorio):
    for root, _, files in os.walk(directorio):
        for file in files:
            if file.endswith('.py'):
                reemplazar_is_integer(os.path.join(root, file))

if __name__ == "__main__":
    escanear_directorio(".")
