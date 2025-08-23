# exportador_rechazos.py – Registro de combinaciones rechazadas por FiltroEstrategico

import csv
from datetime import datetime
import os

def exportar_rechazos_filtro(rechazos: list, ruta_salida: str = "logs/rechazos_filtrados.csv"):
    """
    Exporta las combinaciones rechazadas a un archivo CSV.

    Args:
        rechazos (list): Lista de tuplas (combinacion, razones, score, source)
        ruta_salida (str): Ruta donde guardar el archivo
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    with open(ruta_salida, mode='w', newline='', encoding='utf-8') as archivo:
        writer = csv.writer(archivo)
        writer.writerow(["Combinación", "Score", "Razones", "Fuente", "Fecha"])

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for comb, razones, score, source in rechazos:
            writer.writerow([
                str(comb),
                round(score, 4),
                " | ".join(razones),
                source,
                ahora
            ])

    print(f"📄 Rechazos exportados a: {ruta_salida}")