#!/usr/bin/env python3
"""
OMEGA Log Parser - Analizador de logs para sistema OMEGA PRO AI
Procesa logs y genera CSV con análisis detallado línea por línea.
"""

import re
import csv
import argparse
import sys
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import ast

class OmegaLogParser:
    """Parser especializado para logs del sistema OMEGA"""
    
    def __init__(self, include_metrics: bool = False):
        self.include_metrics = include_metrics
        self.stats = {
            'aprobaciones': 0,
            'rechazos': 0,
            'pickling_errors': 0,
            'numpy_errors': 0,
            'name_errors': 0,
            'duplicados_colapsados': 0
        }
        
        # Patrones regex compilados
        self.timestamp_pattern = re.compile(r'^\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)')
        self.level_pattern = re.compile(r'(?:\s-\s(INFO|WARNING|ERROR|DEBUG)\s-\s|\s\[(INFO|WARNING|ERROR|DEBUG)\s*\])')
        self.component_pattern = re.compile(r'\[([^:]+\.py):\d+\]|^([^-]+)\s-\s(?:INFO|WARNING|ERROR|DEBUG)')
        self.combo_pattern = re.compile(r'\[(\d+(?:\s*,\s*\d+)*)\]')
        self.score_pattern = re.compile(r'Score:\s*([0-9.]+)')
        self.reasons_pattern = re.compile(r'Razones:\s*(\[[^\]]*\])')
    
    def extract_timestamp(self, line: str) -> str:
        """Extrae timestamp de la línea"""
        match = self.timestamp_pattern.match(line)
        return match.group(1) if match else ""
    
    def extract_level(self, line: str) -> str:
        """Extrae nivel de log"""
        match = self.level_pattern.search(line)
        if match:
            return match.group(1) or match.group(2)
        return "UNKNOWN"
    
    def extract_component(self, line: str) -> str:
        """Extrae componente/módulo"""
        match = self.component_pattern.search(line)
        if match:
            return match.group(1) or match.group(2)
        return "-"
    
    def extract_combo(self, line: str) -> str:
        """Extrae combinación de números"""
        match = self.combo_pattern.search(line)
        if match:
            # Limpiar espacios y formatear
            numbers = [n.strip() for n in match.group(1).split(',')]
            return f"[{','.join(numbers)}]"
        return ""
    
    def extract_score(self, line: str) -> str:
        """Extrae score"""
        match = self.score_pattern.search(line)
        return match.group(1) if match else ""
    
    def extract_reasons(self, line: str) -> str:
        """Extrae razones de rechazo"""
        match = self.reasons_pattern.search(line)
        if match:
            return match.group(1)
        elif "Combinación no válida" in line and "Razones:" not in line:
            return "['no_especificadas']"
        return ""
    
    def categorize_line(self, line: str) -> str:
        """Categoriza la línea según contenido"""
        line_lower = line.lower()
        
        # Categorías específicas por orden de prioridad
        if any(x in line_lower for x in ["could not pickle", "_thread.rlock"]):
            return "PARALLELISM"
        elif "numpy boolean subtract" in line_lower:
            return "NUMPY_API"
        elif "name 'core_set' is not defined" in line_lower:
            return "NAME_ERROR"
        elif "combinación aprobada" in line_lower:
            return "VALIDATION"
        elif "combinación rechazada" in line_lower:
            return "FILTER"
        elif any(x in line_lower for x in ["generando respaldo", "[transformer] respaldo"]):
            return "TRANSFORMER_FALLBACK"
        elif any(x in line_lower for x in ["starting score_combinations", "arima_score calculado"]):
            return "SCORING"
        elif any(x in line_lower for x in ["error en scoring", "dynamic scoring fallback"]):
            return "SCORING_ERROR"
        elif any(x in line_lower for x in ["modelo cargado", "initialized", "transformer model initialized"]):
            return "MODEL"
        elif any(x in line_lower for x in ["iniciando pipeline", "ejecutando modelo"]):
            return "PIPELINE"
        elif any(x in line_lower for x in ["dataset limpio", "cargando datos", "no se encontraron columnas"]):
            return "DATA"
        elif any(x in line_lower for x in ["arrancando", "conexión redis", "nivel de logging"]):
            return "CONFIG"
        else:
            return "OTHER"
    
    def has_duplicate_numbers(self, combo_str: str) -> bool:
        """Verifica si una combinación tiene números duplicados"""
        if not combo_str:
            return False
        try:
            numbers = ast.literal_eval(combo_str)
            return len(numbers) != len(set(numbers))
        except:
            return False
    
    def calculate_severity(self, line: str, categoria: str, level: str, dup_count: int = 1) -> int:
        """Calcula severidad basada en contenido y categoría"""
        base_severity = 0
        
        # Severidades específicas por contenido
        if "ALERTA CRÍTICA: Tasa de aprobación < 15%" in line:
            base_severity = 4
        elif categoria == "PARALLELISM":
            base_severity = 4
        elif categoria == "NAME_ERROR":
            base_severity = 4
        elif categoria == "VALIDATION_ERROR":
            base_severity = 4
        elif categoria == "NUMPY_API":
            base_severity = 3
        elif level == "ERROR":
            base_severity = 4
        elif level == "WARNING":
            base_severity = 3
        elif categoria in ["FILTER", "SCORING_ERROR"]:
            base_severity = 2
        elif categoria in ["TRANSFORMER_FALLBACK", "DATA"]:
            base_severity = 1
        else:
            base_severity = 0
        
        # Ajuste por duplicados
        if dup_count >= 4:
            base_severity = max(base_severity, 3)
        elif dup_count >= 2:
            base_severity = max(base_severity, 2)
        
        return min(base_severity, 4)  # Cap en 4
    
    def generate_explanation_and_fix(self, categoria: str, line: str) -> Tuple[str, str]:
        """Genera explicación breve y fix sugerido"""
        explanations = {
            "PARALLELISM": ("Fallo al paralelizar por objeto no picklable", "Evitar objetos no picklables; pasar datos puros a Joblib"),
            "NUMPY_API": ("Operación booleana inválida con '-'", "Usar '^' o np.logical_xor"),
            "NAME_ERROR": ("Variable requerida no definida", "Definir/pasar core_set o manejar None"),
            "VALIDATION": ("Combinación aprobada con score OK", "—"),
            "VALIDATION_ERROR": ("Aprobada con números duplicados", "Validar unicidad antes de aprobar"),
            "FILTER": ("Combinación rechazada por reglas", "Ajustar umbrales/reglas si corresponde"),
            "TRANSFORMER_FALLBACK": ("Uso de respaldo de Transformer", "Revisar ruta/modelo principal"),
            "SCORING_ERROR": ("Fallo durante scoring", "Desactivar paralelismo o revisar objetos picklables"),
            "MODEL": ("Modelo/componente inicializado", "—"),
            "PIPELINE": ("Ejecución de pipeline/proceso", "—"),
            "DATA": ("Procesamiento de datos", "Verificar calidad y formato de datos"),
            "CONFIG": ("Configuración/arranque del sistema", "—"),
            "OTHER": ("Evento general del sistema", "Revisar configuración y datos")
        }
        
        return explanations.get(categoria, ("Evento no categorizado", "Revisar configuración y datos"))
    
    def normalize_message(self, line: str) -> str:
        """Normaliza mensaje para agrupación"""
        # Remover timestamp
        line = self.timestamp_pattern.sub('', line)
        # Remover level markers
        line = self.level_pattern.sub('', line)
        # Remover componente
        line = self.component_pattern.sub('', line)
        # Normalizar espacios
        return ' '.join(line.split())
    
    def parse_log_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Procesa archivo de log completo"""
        rows = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error leyendo archivo: {e}", file=sys.stderr)
            return []
        
        # Procesar líneas y agrupar duplicados
        line_data = []
        for line_no, line in enumerate(lines, 1):
            line = line.rstrip('\n\r')
            
            timestamp = self.extract_timestamp(line)
            level = self.extract_level(line)
            component = self.extract_component(line)
            categoria = self.categorize_line(line)
            combo = self.extract_combo(line)
            score = self.extract_score(line)
            reasons = self.extract_reasons(line)
            
            # Validar combinaciones aprobadas con duplicados
            if categoria == "VALIDATION" and self.has_duplicate_numbers(combo):
                categoria = "VALIDATION_ERROR"
            
            # Añadir números duplicados a razones si es rechazo con duplicados
            if categoria == "FILTER" and self.has_duplicate_numbers(combo):
                if reasons and "numeros_duplicados" not in reasons:
                    reasons = reasons.replace("]", ",'numeros_duplicados']")
                elif not reasons:
                    reasons = "['numeros_duplicados']"
            
            # Score anómalo
            score_anomalo = ""
            if score:
                try:
                    score_val = float(score)
                    score_anomalo = "1" if score_val > 1.0 else "0"
                except:
                    score_anomalo = ""
            
            # Mensaje normalizado para agrupación
            normalized_msg = self.normalize_message(line)
            
            line_data.append({
                'line_no': line_no,
                'timestamp': timestamp,
                'level': level,
                'component': component,
                'categoria': categoria,
                'combo': combo,
                'score': score,
                'score_anomalo': score_anomalo,
                'reasons': reasons,
                'normalized_msg': normalized_msg,
                'original_line': line
            })
        
        # Agrupar por duplicados
        groups = defaultdict(list)
        for data in line_data:
            key = (data['categoria'], data['component'], data['normalized_msg'])
            groups[key].append(data)
        
        # Procesar grupos y generar filas finales
        processed_line_nos = set()
        
        for group_items in groups.values():
            # Tomar el primer elemento cronológicamente
            group_items.sort(key=lambda x: (x['timestamp'] or '9999', x['line_no']))
            first_item = group_items[0]
            
            # Determinar level más alto
            level_priority = {'ERROR': 4, 'WARNING': 3, 'INFO': 2, 'UNKNOWN': 1}
            max_level = max(group_items, key=lambda x: level_priority.get(x['level'], 0))['level']
            
            dup_count = len(group_items)
            
            # Calcular severidad
            severity = self.calculate_severity(
                first_item['original_line'], 
                first_item['categoria'], 
                max_level, 
                dup_count
            )
            
            # Generar explicación y fix
            explanation, fix_suggestion = self.generate_explanation_and_fix(
                first_item['categoria'], 
                first_item['original_line']
            )
            
            # Actualizar estadísticas
            self.update_stats(first_item, dup_count)
            
            # Crear fila final
            row = {
                'line_no': first_item['line_no'],
                'timestamp': first_item['timestamp'],
                'level': max_level,
                'componente': first_item['component'],
                'categoria': first_item['categoria'],
                'combo': first_item['combo'],
                'score': first_item['score'],
                'score_anomalo': first_item['score_anomalo'],
                'razones': first_item['reasons'],
                'explicacion_breve': explanation,
                'fix_sugerido': fix_suggestion,
                'severidad': severity,
                'dup_count': dup_count if dup_count > 1 else ""
            }
            
            rows.append(row)
            processed_line_nos.update(item['line_no'] for item in group_items)
        
        # Ordenar por line_no del primer elemento de cada grupo
        rows.sort(key=lambda x: x['line_no'])
        
        # Añadir métricas si se solicita
        if self.include_metrics:
            rows.extend(self.generate_metrics_rows(len(rows)))
        
        return rows
    
    def update_stats(self, item: Dict, dup_count: int):
        """Actualiza estadísticas del parser"""
        if item['categoria'] == 'VALIDATION':
            self.stats['aprobaciones'] += 1
        elif item['categoria'] == 'FILTER':
            self.stats['rechazos'] += 1
        elif item['categoria'] == 'PARALLELISM':
            self.stats['pickling_errors'] += 1
        elif item['categoria'] == 'NUMPY_API':
            self.stats['numpy_errors'] += 1
        elif item['categoria'] == 'NAME_ERROR':
            self.stats['name_errors'] += 1
        
        if dup_count > 1:
            self.stats['duplicados_colapsados'] += (dup_count - 1)
    
    def generate_metrics_rows(self, total_rows: int) -> List[Dict[str, Any]]:
        """Genera filas de métricas resumen"""
        metrics_rows = []
        
        # Tasa de aprobación
        total_validations = self.stats['aprobaciones'] + self.stats['rechazos']
        tasa_aprobacion = (self.stats['aprobaciones'] / total_validations * 100) if total_validations > 0 else 0
        
        metrics_rows.extend([
            {
                'line_no': total_rows + 1,
                'timestamp': '',
                'level': 'INFO',
                'componente': '-',
                'categoria': 'METRIC',
                'combo': '',
                'score': '',
                'score_anomalo': '',
                'razones': '',
                'explicacion_breve': f"Aprobaciones={self.stats['aprobaciones']}, rechazos={self.stats['rechazos']}, tasa={tasa_aprobacion:.1f}%",
                'fix_sugerido': '',
                'severidad': 0,
                'dup_count': ''
            },
            {
                'line_no': total_rows + 2,
                'timestamp': '',
                'level': 'INFO',
                'componente': '-',
                'categoria': 'METRIC',
                'combo': '',
                'score': '',
                'score_anomalo': '',
                'razones': '',
                'explicacion_breve': f"Duplicados colapsados: {self.stats['duplicados_colapsados']}",
                'fix_sugerido': '',
                'severidad': 0,
                'dup_count': ''
            },
            {
                'line_no': total_rows + 3,
                'timestamp': '',
                'level': 'INFO',
                'componente': '-',
                'categoria': 'METRIC',
                'combo': '',
                'score': '',
                'score_anomalo': '',
                'razones': '',
                'explicacion_breve': f"Errores: pickling={self.stats['pickling_errors']}, numpy={self.stats['numpy_errors']}, name_error={self.stats['name_errors']}",
                'fix_sugerido': '',
                'severidad': 0,
                'dup_count': ''
            }
        ])
        
        return metrics_rows

def main():
    """Función principal CLI"""
    parser = argparse.ArgumentParser(
        description='Parser de logs OMEGA PRO AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python omega_log_parser.py input.log -o output.csv
  python omega_log_parser.py input.log -o output.csv --include-metrics
        """
    )
    
    parser.add_argument('input_file', help='Archivo de log de entrada')
    parser.add_argument('-o', '--output', required=True, help='Archivo CSV de salida')
    parser.add_argument('--include-metrics', action='store_true', 
                       help='Incluir filas de métricas al final')
    
    args = parser.parse_args()
    
    # Verificar archivo de entrada
    try:
        with open(args.input_file, 'r') as f:
            pass
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo {args.input_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error accediendo al archivo: {e}", file=sys.stderr)
        return 1
    
    # Procesar logs
    log_parser = OmegaLogParser(include_metrics=args.include_metrics)
    rows = log_parser.parse_log_file(args.input_file)
    
    if not rows:
        print("No se procesaron líneas válidas", file=sys.stderr)
        return 1
    
    # Escribir CSV
    fieldnames = [
        'line_no', 'timestamp', 'level', 'componente', 'categoria', 
        'combo', 'score', 'score_anomalo', 'razones', 'explicacion_breve', 
        'fix_sugerido', 'severidad', 'dup_count'
    ]
    
    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"CSV generado exitosamente: {args.output}")
        print(f"Líneas procesadas: {len(rows)}")
        if args.include_metrics:
            print("Métricas incluidas en el archivo")
        
        return 0
        
    except Exception as e:
        print(f"Error escribiendo CSV: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
