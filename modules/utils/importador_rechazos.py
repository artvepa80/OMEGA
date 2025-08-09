# importador_rechazos.py – Carga de combinaciones rechazadas previas

import csv
import re
from typing import List, Tuple, Set

def parse_number_string(num_str: str) -> int:
    """
    Convierte una cadena de número que podría ser de tipo numpy (np.int64)
    a un entero Python nativo.
    
    Args:
        num_str (str): Cadena que representa un número
        
    Returns:
        int: Valor entero convertido
    """
    # Buscar patrones como 'np.int64(15)'
    match = re.search(r'np\.int\d+\((\d+)\)', num_str)
    if match:
        return int(match.group(1))
    
    # Buscar patrones como '15' (entero normal)
    if num_str.isdigit():
        return int(num_str)
    
    # Buscar números en cualquier formato
    digits = re.findall(r'\d+', num_str)
    if digits:
        return int(digits[0])
    
    # Valor por defecto si no se puede parsear
    return 0

def importar_combinaciones_rechazadas(ruta_csv: str = "logs/rechazos_filtrados.csv") -> Set[Tuple[int]]:
    """
    Carga las combinaciones rechazadas desde un archivo CSV.
    
    Args:
        ruta_csv (str): Ruta al archivo exportado con rechazos
    
    Returns:
        Set de combinaciones rechazadas como tuplas ordenadas
    """
    rechazadas = set()

    try:
        with open(ruta_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                raw = fila["Combinación"]
                
                # Limpiar y procesar la cadena
                cleaned = raw.strip("[] ").replace(" ", "")
                numeros = []
                
                # Manejar diferentes formatos de números
                for num_str in cleaned.split(","):
                    try:
                        num = parse_number_string(num_str)
                        numeros.append(num)
                    except Exception as e:
                        print(f"⚠️ Error procesando número '{num_str}': {e}")
                
                # Solo añadir combinaciones válidas
                if len(numeros) == 6 and all(1 <= num <= 40 for num in numeros):
                    rechazadas.add(tuple(sorted(numeros)))
                else:
                    print(f"⚠️ Combinación inválida descartada: {raw}")
    except FileNotFoundError:
        print(f"⚠️ Archivo no encontrado: {ruta_csv}")
    except Exception as e:
        print(f"❌ Error al leer rechazos: {e}")

    return rechazadas