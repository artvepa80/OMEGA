#!/usr/bin/env python3
"""
OMEGA AI Scheduler - Sistema de Cronograma para Sorteos Kabala
Programador especializado en scheduling y automatización
"""

import schedule
import time
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import os
import logging
from pathlib import Path
import pytz
import requests
from crontab import CronTab

@dataclass
class SorteoInfo:
    """Información del sorteo"""
    fecha: datetime.date
    dia_semana: str
    numero_sorteo: int
    es_hoy: bool
    es_proximo: bool
    tiempo_restante: str

class KabalaScheduler:
    """Sistema de scheduling para sorteos de Kabala"""
    
    def __init__(self, timezone: str = "America/Lima"):
        self.timezone = pytz.timezone(timezone)
        self.dias_sorteo = [1, 3, 5]  # Martes=1, Jueves=3, Sábado=5
        self.nombres_dias = {1: "Martes", 3: "Jueves", 5: "Sábado"}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar programación
        self.setup_schedule()
    
    def get_proximos_sorteos(self, cantidad: int = 3) -> List[SorteoInfo]:
        """Obtiene los próximos sorteos de Kabala"""
        hoy = datetime.date.today()
        sorteos = []
        
        # Buscar próximos sorteos
        fecha_actual = hoy
        contador = 0
        numero_sorteo = self._calcular_numero_sorteo_base()
        
        while len(sorteos) < cantidad:
            dia_semana = fecha_actual.weekday()
            
            if dia_semana in self.dias_sorteo:
                es_hoy = fecha_actual == hoy
                es_proximo = len(sorteos) == 0 and fecha_actual >= hoy
                
                tiempo_restante = self._calcular_tiempo_restante(fecha_actual)
                
                sorteo = SorteoInfo(
                    fecha=fecha_actual,
                    dia_semana=self.nombres_dias[dia_semana],
                    numero_sorteo=numero_sorteo + contador,
                    es_hoy=es_hoy,
                    es_proximo=es_proximo,
                    tiempo_restante=tiempo_restante
                )
                
                sorteos.append(sorteo)
                contador += 1
            
            fecha_actual += datetime.timedelta(days=1)
        
        return sorteos
    
    def get_sorteo_especifico(self, fecha_objetivo: str = None) -> SorteoInfo:
        """Obtiene información de un sorteo específico"""
        if fecha_objetivo:
            try:
                fecha = datetime.datetime.strptime(fecha_objetivo, "%Y-%m-%d").date()
            except ValueError:
                fecha = datetime.date.today()
        else:
            fecha = self._get_proximo_sorteo_fecha()
        
        dia_semana = fecha.weekday()
        
        if dia_semana not in self.dias_sorteo:
            # Si no es día de sorteo, buscar el siguiente
            fecha = self._get_proximo_sorteo_fecha(desde_fecha=fecha)
            dia_semana = fecha.weekday()
        
        numero_sorteo = self._calcular_numero_sorteo_para_fecha(fecha)
        tiempo_restante = self._calcular_tiempo_restante(fecha)
        
        return SorteoInfo(
            fecha=fecha,
            dia_semana=self.nombres_dias[dia_semana],
            numero_sorteo=numero_sorteo,
            es_hoy=fecha == datetime.date.today(),
            es_proximo=True,
            tiempo_restante=tiempo_restante
        )
    
    def _get_proximo_sorteo_fecha(self, desde_fecha: datetime.date = None) -> datetime.date:
        """Obtiene la fecha del próximo sorteo"""
        if desde_fecha is None:
            desde_fecha = datetime.date.today()
        
        fecha_actual = desde_fecha
        
        # Si es hoy y aún no es la hora del sorteo, mantener hoy
        if (fecha_actual == datetime.date.today() and 
            fecha_actual.weekday() in self.dias_sorteo and 
            self._es_antes_del_sorteo()):
            return fecha_actual
        
        # Buscar siguiente día de sorteo
        for i in range(1, 8):  # Máximo 7 días para encontrar el siguiente
            fecha_test = fecha_actual + datetime.timedelta(days=i)
            if fecha_test.weekday() in self.dias_sorteo:
                return fecha_test
        
        return fecha_actual  # Fallback
    
    def _es_antes_del_sorteo(self) -> bool:
        """Verifica si aún no es la hora del sorteo de hoy"""
        ahora = datetime.datetime.now(self.timezone)
        hora_sorteo = ahora.replace(hour=21, minute=30, second=0, microsecond=0)  # 9:30 PM
        return ahora < hora_sorteo
    
    def _calcular_tiempo_restante(self, fecha_sorteo: datetime.date) -> str:
        """Calcula el tiempo restante hasta el sorteo"""
        ahora = datetime.datetime.now(self.timezone)
        
        # Hora típica del sorteo: 21:30
        datetime_sorteo = datetime.datetime.combine(
            fecha_sorteo, 
            datetime.time(21, 30)
        )
        datetime_sorteo = self.timezone.localize(datetime_sorteo)
        
        if datetime_sorteo < ahora:
            return "Sorteo realizado"
        
        diferencia = datetime_sorteo - ahora
        dias = diferencia.days
        horas, remainder = divmod(diferencia.seconds, 3600)
        minutos, _ = divmod(remainder, 60)
        
        if dias > 0:
            return f"{dias} días, {horas} horas, {minutos} minutos"
        elif horas > 0:
            return f"{horas} horas, {minutos} minutos"
        else:
            return f"{minutos} minutos"
    
    def _calcular_numero_sorteo_base(self) -> int:
        """Calcula un número de sorteo base basado en la fecha"""
        # Base: 1 de enero de 2025 = sorteo #1
        fecha_base = datetime.date(2025, 1, 1)  # Miércoles
        hoy = datetime.date.today()
        
        # Contar sorteos desde la fecha base
        sorteos_contados = 0
        fecha_actual = fecha_base
        
        while fecha_actual <= hoy:
            if fecha_actual.weekday() in self.dias_sorteo:
                sorteos_contados += 1
            fecha_actual += datetime.timedelta(days=1)
        
        return max(1, sorteos_contados)
    
    def _calcular_numero_sorteo_para_fecha(self, fecha: datetime.date) -> int:
        """Calcula el número de sorteo para una fecha específica"""
        fecha_base = datetime.date(2025, 1, 1)
        
        if fecha < fecha_base:
            return 1
        
        sorteos_contados = 0
        fecha_actual = fecha_base
        
        while fecha_actual <= fecha:
            if fecha_actual.weekday() in self.dias_sorteo:
                sorteos_contados += 1
            fecha_actual += datetime.timedelta(days=1)
        
        return max(1, sorteos_contados)
    
    def generar_prediccion_programada(self, fecha_sorteo: datetime.date = None) -> Dict[str, Any]:
        """Genera predicción para un sorteo específico"""
        self.logger.info("🎯 Generando predicción programada para Kabala...")
        
        sorteo_info = self.get_sorteo_especifico(
            fecha_sorteo.strftime("%Y-%m-%d") if fecha_sorteo else None
        )
        
        try:
            # Importar el sistema principal
            from main import main as omega_main
            
            # Ejecutar predicción
            resultado = omega_main(
                svi_profile=2,
                top_n=8,
                export_csv=True,
                export_json=True
            )
            
            # Formatear resultado
            prediccion_formateada = {
                "sorteo_info": {
                    "fecha": sorteo_info.fecha.strftime("%Y-%m-%d"),
                    "dia_semana": sorteo_info.dia_semana,
                    "fecha_legible": self._formatear_fecha_legible(sorteo_info.fecha),
                    "numero_sorteo": sorteo_info.numero_sorteo,
                    "tiempo_restante": sorteo_info.tiempo_restante,
                    "es_proximo_sorteo": sorteo_info.es_proximo
                },
                "predicciones": resultado[:3] if resultado else [],
                "total_combinaciones": len(resultado) if resultado else 0,
                "generado_en": datetime.datetime.now().isoformat(),
                "mensaje": f"Sorteo Kabala para el día {sorteo_info.dia_semana} {self._formatear_fecha_legible(sorteo_info.fecha)}",
                "recordatorio": "La Kabala se juega todos los Martes, Jueves y Sábados de cada semana"
            }
            
            # Guardar predicción con timestamp
            self._guardar_prediccion_programada(prediccion_formateada)
            
            return prediccion_formateada
            
        except Exception as e:
            self.logger.error(f"❌ Error generando predicción: {e}")
            return {
                "error": str(e),
                "sorteo_info": {
                    "fecha": sorteo_info.fecha.strftime("%Y-%m-%d"),
                    "dia_semana": sorteo_info.dia_semana,
                    "mensaje": f"Sorteo Kabala para el día {sorteo_info.dia_semana} {self._formatear_fecha_legible(sorteo_info.fecha)}"
                }
            }
    
    def _formatear_fecha_legible(self, fecha: datetime.date) -> str:
        """Formatea la fecha en español legible"""
        meses = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        dia = fecha.day
        mes = meses[fecha.month]
        año = fecha.year
        
        return f"{dia} de {mes} del {año}"
    
    def _guardar_prediccion_programada(self, prediccion: Dict[str, Any]):
        """Guarda la predicción programada"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prediccion_kabala_{timestamp}.json"
        filepath = Path("results") / filename
        
        # Crear directorio si no existe
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(prediccion, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Predicción guardada en: {filepath}")
    
    def setup_schedule(self):
        """Configura los horarios de predicción automática"""
        # Programar predicciones para días de sorteo a las 10:00 AM
        schedule.every().tuesday.at("10:00").do(self._job_prediccion_martes)
        schedule.every().thursday.at("10:00").do(self._job_prediccion_jueves)  
        schedule.every().saturday.at("10:00").do(self._job_prediccion_sabado)
        
        # Programar recordatorios 2 horas antes del sorteo
        schedule.every().tuesday.at("19:30").do(self._job_recordatorio_sorteo)
        schedule.every().thursday.at("19:30").do(self._job_recordatorio_sorteo)
        schedule.every().saturday.at("19:30").do(self._job_recordatorio_sorteo)
        
        self.logger.info("✅ Horarios de predicción automática configurados")
    
    def _job_prediccion_martes(self):
        """Job de predicción para martes"""
        self.logger.info("📅 Ejecutando predicción automática - Martes")
        fecha_martes = self._get_fecha_dia_actual_o_proximo(1)  # Martes = 1
        self.generar_prediccion_programada(fecha_martes)
    
    def _job_prediccion_jueves(self):
        """Job de predicción para jueves"""
        self.logger.info("📅 Ejecutando predicción automática - Jueves")
        fecha_jueves = self._get_fecha_dia_actual_o_proximo(3)  # Jueves = 3
        self.generar_prediccion_programada(fecha_jueves)
    
    def _job_prediccion_sabado(self):
        """Job de predicción para sábado"""
        self.logger.info("📅 Ejecutando predicción automática - Sábado")
        fecha_sabado = self._get_fecha_dia_actual_o_proximo(5)  # Sábado = 5
        self.generar_prediccion_programada(fecha_sabado)
    
    def _job_recordatorio_sorteo(self):
        """Job de recordatorio de sorteo"""
        sorteo = self.get_sorteo_especifico()
        self.logger.info(f"🔔 Recordatorio: Sorteo Kabala hoy {sorteo.dia_semana} a las 21:30")
    
    def _get_fecha_dia_actual_o_proximo(self, dia_semana_objetivo: int) -> datetime.date:
        """Obtiene la fecha del día actual si coincide, o del próximo"""
        hoy = datetime.date.today()
        
        if hoy.weekday() == dia_semana_objetivo:
            return hoy
        
        # Buscar el próximo día objetivo
        dias_adelante = (dia_semana_objetivo - hoy.weekday()) % 7
        if dias_adelante == 0:  # Es hoy pero ya pasó
            dias_adelante = 7
            
        return hoy + datetime.timedelta(days=dias_adelante)
    
    def run_scheduler(self):
        """Ejecuta el scheduler en modo daemon"""
        self.logger.info("🚀 Iniciando OMEGA AI Scheduler...")
        self.logger.info("📅 Programado para: Martes, Jueves y Sábados")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Revisar cada minuto
    
    def setup_system_cron(self):
        """Configura cron del sistema (Linux/Mac)"""
        try:
            cron = CronTab(user=True)
            
            # Limpiar jobs existentes de OMEGA
            cron.remove_all(comment='OMEGA_KABALA')
            
            # Predicción Martes 10:00 AM
            job_martes = cron.new(
                command=f'cd {os.getcwd()} && python omega_scheduler.py --predict-martes',
                comment='OMEGA_KABALA_MARTES'
            )
            job_martes.setall('0 10 * * 2')  # Martes a las 10:00
            
            # Predicción Jueves 10:00 AM  
            job_jueves = cron.new(
                command=f'cd {os.getcwd()} && python omega_scheduler.py --predict-jueves',
                comment='OMEGA_KABALA_JUEVES'
            )
            job_jueves.setall('0 10 * * 4')  # Jueves a las 10:00
            
            # Predicción Sábado 10:00 AM
            job_sabado = cron.new(
                command=f'cd {os.getcwd()} && python omega_scheduler.py --predict-sabado',
                comment='OMEGA_KABALA_SABADO'
            )
            job_sabado.setall('0 10 * * 6')  # Sábado a las 10:00
            
            # Guardar cron
            cron.write()
            
            self.logger.info("✅ Cron del sistema configurado exitosamente")
            self.logger.info("📅 Programado: Martes, Jueves, Sábados a las 10:00 AM")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando cron: {e}")
            return False
    
    def get_prediction_for_api(self, fecha_especifica: str = None) -> Dict[str, Any]:
        """Método optimizado para API que devuelve predicción formateada"""
        try:
            sorteo_info = self.get_sorteo_especifico(fecha_especifica)
            
            # Importar y ejecutar predicción
            from main import main as omega_main
            resultado = omega_main(svi_profile=2, top_n=8, export_csv=False, export_json=False)
            
            # Formatear para respuesta API
            return {
                "success": True,
                "sorteo": {
                    "fecha": sorteo_info.fecha.strftime("%Y-%m-%d"),
                    "dia": sorteo_info.dia_semana,
                    "fecha_legible": self._formatear_fecha_legible(sorteo_info.fecha),
                    "numero_sorteo": sorteo_info.numero_sorteo,
                    "tiempo_restante": sorteo_info.tiempo_restante
                },
                "predicciones": resultado[:5] if resultado else [],
                "mensaje": f"🎯 Sorteo Kabala para el día {sorteo_info.dia_semana} {self._formatear_fecha_legible(sorteo_info.fecha)}",
                "recordatorio": "🗓️ La Kabala se juega todos los Martes, Jueves y Sábados de cada semana",
                "total_combinaciones": len(resultado) if resultado else 0,
                "generado": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mensaje": "Error generando predicción para Kabala"
            }

def main():
    """Función principal del scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OMEGA AI Kabala Scheduler')
    parser.add_argument('--predict-martes', action='store_true', help='Generar predicción para martes')
    parser.add_argument('--predict-jueves', action='store_true', help='Generar predicción para jueves')
    parser.add_argument('--predict-sabado', action='store_true', help='Generar predicción para sábado')
    parser.add_argument('--setup-cron', action='store_true', help='Configurar cron del sistema')
    parser.add_argument('--run-daemon', action='store_true', help='Ejecutar en modo daemon')
    parser.add_argument('--next-sorteos', action='store_true', help='Mostrar próximos sorteos')
    
    args = parser.parse_args()
    
    scheduler = KabalaScheduler()
    
    if args.predict_martes:
        fecha = scheduler._get_fecha_dia_actual_o_proximo(1)
        scheduler.generar_prediccion_programada(fecha)
    
    elif args.predict_jueves:
        fecha = scheduler._get_fecha_dia_actual_o_proximo(3)
        scheduler.generar_prediccion_programada(fecha)
    
    elif args.predict_sabado:
        fecha = scheduler._get_fecha_dia_actual_o_proximo(5)
        scheduler.generar_prediccion_programada(fecha)
    
    elif args.setup_cron:
        scheduler.setup_system_cron()
    
    elif args.run_daemon:
        scheduler.run_scheduler()
    
    elif args.next_sorteos:
        sorteos = scheduler.get_proximos_sorteos(5)
        print("🎯 Próximos Sorteos de Kabala:")
        for sorteo in sorteos:
            print(f"   {sorteo.dia_semana} {scheduler._formatear_fecha_legible(sorteo.fecha)} - {sorteo.tiempo_restante}")
    
    else:
        # Generar predicción para el próximo sorteo
        prediccion = scheduler.generar_prediccion_programada()
        print("🎯 OMEGA AI - Predicción Kabala")
        print("=" * 50)
        print(f"📅 {prediccion.get('mensaje', 'Predicción generada')}")
        print(f"🗓️ {prediccion.get('recordatorio', '')}")
        
        if 'predicciones' in prediccion and prediccion['predicciones']:
            print(f"🎲 Top 3 Predicciones:")
            for i, pred in enumerate(prediccion['predicciones'][:3], 1):
                if isinstance(pred, dict) and 'combinacion' in pred:
                    numeros = pred['combinacion']
                    confianza = pred.get('confidence', 0)
                    print(f"   {i}. {numeros} (Confianza: {confianza:.3f})")

if __name__ == "__main__":
    main()