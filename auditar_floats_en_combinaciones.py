import os
import ast

def analizar_lista_float(node):
    if isinstance(node, ast.List):
        elementos = node.elts
        return all(isinstance(e, ast.Constant) and isinstance(e.value, float) for e in elementos)
    return False

def escanear_archivo(ruta):
    with open(ruta, 'r', encoding='utf-8') as archivo:
        try:
            tree = ast.parse(archivo.read(), filename=ruta)
        except SyntaxError:
            return []

    hallazgos = []
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Assign):
            if analizar_lista_float(nodo.value):
                linea = nodo.lineno
                hallazgos.append((ruta, linea))
    return hallazgos

def escanear_directorio(raiz="."):
    resultados = []
    for carpeta, _, archivos in os.walk(raiz):
        for archivo in archivos:
            if archivo.endswith(".py") and "venv" not in carpeta:
                ruta_completa = os.path.join(carpeta, archivo)
                resultados += escanear_archivo(ruta_completa)
    return resultados

if __name__ == "__main__":
    hallazgos = escanear_directorio()
    if hallazgos:
        print("⚠️ Listas de floats detectadas como posibles combinaciones mal tipadas:\n")
        for ruta, linea in hallazgos:
            print(f"📄 {ruta} (línea {linea})")
    else:
        print("✅ No se encontraron listas sospechosas con floats. Todas parecen ser combinaciones de enteros.")
