# exportador_resultados.py – Exporta combinaciones finales a CSV

import csv
import os
from datetime import datetime

def exportar_combinaciones(combinaciones, path="results/final_omega.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Combinación", "Score", "Fuente"])
        
        for item in combinaciones:
            fila = [
                now,
                "-".join(str(n) for n in item["combination"]),
                round(item.get("score", 0.0), 4),
                item.get("source", "desconocido")
            ]
            writer.writerow(fila)
    
    print(f"\n📦 Combinaciones exportadas a: {path}")