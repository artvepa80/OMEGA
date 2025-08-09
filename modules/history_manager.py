# OMEGA_PRO_AI_v10.1/modules/history_manager.py

import sqlite3
from typing import List

def obtener_promedio_score_historico(num: int) -> float:
    """Obtiene el score promedio histórico de un número"""
    conn = sqlite3.connect('database/omega_history.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(score) 
        FROM number_performance 
        WHERE number = ?
    """, (num,))
    result = cursor.fetchone()[0] or 0.5  # Default si no hay histórico
    conn.close()
    return float(result)

def numeros_recientes(ultimos_sorteos: int = 3) -> List[int]:
    """Obtiene números de los últimos sorteos"""
    conn = sqlite3.connect('database/omega_history.db')
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT numbers 
        FROM draws 
        ORDER BY date DESC 
        LIMIT ?
    """, (ultimos_sorteos,))
    resultados = cursor.fetchall()
    conn.close()
    
    # Aplanar lista de listas
    return [num for sublist in [eval(r[0]) for r in resultados] for num in sublist]