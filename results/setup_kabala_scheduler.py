#!/usr/bin/env python3
"""
OMEGA AI Kabala Scheduler Setup
Script de instalación y configuración automática
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import platform

def install_dependencies():
    """Instala dependencias necesarias para el scheduler"""
    print("📦 Instalando dependencias...")
    
    dependencies = [
        'schedule',
        'pytz',
        'python-crontab',
        'python-dateutil'
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} instalado exitosamente")
        except subprocess.CalledProcessError:
            print(f"❌ Error instalando {dep}")
            return False
    
    return True

def create_scheduler_config():
    """Crea archivo de configuración del scheduler"""
    print("⚙️ Creando configuración del scheduler...")
    
    config = {
        "scheduler_config": {
            "timezone": "America/Lima",
            "dias_sorteo": {
                "martes": 1,
                "jueves": 3, 
                "sabado": 5
            },
            "horarios": {
                "prediccion_automatica": "10:00",
                "recordatorio_sorteo": "19:30",
                "hora_sorteo": "21:30"
            },
            "configuracion": {
                "auto_export_csv": True,
                "auto_export_json": True,
                "guardar_historial": True,
                "enviar_notificaciones": False
            }
        },
        "api_config": {
            "titulo": "OMEGA AI Kabala Predictor",
            "descripcion": "Sistema AI especializado en predicciones para sorteos Kabala",
            "version": "10.1",
            "loteria": "Kabala",
            "dias_sorteo_texto": "Martes, Jueves y Sábados",
            "hora_sorteo": "21:30 (Perú)"
        }
    }
    
    config_path = Path("config") / "kabala_scheduler.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuración guardada en: {config_path}")
    return config_path

def setup_service_files():
    """Crea archivos de servicio para diferentes sistemas"""
    print("🛠️ Creando archivos de servicio...")
    
    # Systemd service (Linux)
    systemd_content = f"""[Unit]
Description=OMEGA AI Kabala Scheduler
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'omega')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}
ExecStart={sys.executable} omega_scheduler.py --run-daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_dir = Path("service_files")
    service_dir.mkdir(exist_ok=True)
    
    with open(service_dir / "omega-kabala-scheduler.service", 'w') as f:
        f.write(systemd_content)
    
    # Windows Task Scheduler script
    windows_script = f"""@echo off
REM OMEGA AI Kabala Scheduler - Windows Task
cd /d "{os.getcwd()}"
python omega_scheduler.py --run-daemon
"""
    
    with open(service_dir / "omega_scheduler_windows.bat", 'w') as f:
        f.write(windows_script)
    
    # macOS LaunchAgent
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omega.kabala.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.getcwd()}/omega_scheduler.py</string>
        <string>--run-daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{os.getcwd()}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.getcwd()}/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{os.getcwd()}/logs/scheduler_error.log</string>
</dict>
</plist>
"""
    
    with open(service_dir / "com.omega.kabala.scheduler.plist", 'w') as f:
        f.write(plist_content)
    
    print("✅ Archivos de servicio creados en: service_files/")

def create_quick_start_scripts():
    """Crea scripts de inicio rápido"""
    print("🚀 Creando scripts de inicio rápido...")
    
    # Script para obtener próximo sorteo
    quick_predict = """#!/usr/bin/env python3
from omega_scheduler import KabalaScheduler

scheduler = KabalaScheduler()
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
"""
    
    with open("quick_predict.py", 'w') as f:
        f.write(quick_predict)
    
    # Script para mostrar próximos sorteos
    next_sorteos = """#!/usr/bin/env python3
from omega_scheduler import KabalaScheduler

scheduler = KabalaScheduler()
sorteos = scheduler.get_proximos_sorteos(7)

print("📅 Próximos Sorteos Kabala:")
print("=" * 40)

for sorteo in sorteos:
    icon = "🎯" if sorteo.es_proximo else "📅"
    status = " (HOY)" if sorteo.es_hoy else " (PRÓXIMO)" if sorteo.es_proximo else ""
    
    print(f"{icon} {sorteo.dia_semana} {scheduler._formatear_fecha_legible(sorteo.fecha)}{status}")
    print(f"    ⏰ {sorteo.tiempo_restante}")
    print(f"    #️⃣ Sorteo #{sorteo.numero_sorteo}")
    print()
"""
    
    with open("show_next_sorteos.py", 'w') as f:
        f.write(next_sorteos)
    
    # Hacer ejecutables en sistemas Unix
    if os.name != 'nt':
        os.chmod("quick_predict.py", 0o755)
        os.chmod("show_next_sorteos.py", 0o755)
    
    print("✅ Scripts de inicio rápido creados:")
    print("   - quick_predict.py (predicción inmediata)")
    print("   - show_next_sorteos.py (próximos sorteos)")

def setup_logging():
    """Configura el sistema de logging"""
    print("📝 Configurando sistema de logging...")
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Crear archivos de log vacíos
    log_files = [
        "scheduler.log",
        "scheduler_error.log",
        "predictions.log",
        "api_access.log"
    ]
    
    for log_file in log_files:
        log_path = logs_dir / log_file
        if not log_path.exists():
            log_path.touch()
    
    print(f"✅ Logs configurados en: {logs_dir}")

def test_scheduler():
    """Prueba el scheduler"""
    print("🧪 Probando el scheduler...")
    
    try:
        from omega_scheduler import KabalaScheduler
        
        scheduler = KabalaScheduler()
        
        # Probar obtener próximo sorteo
        proximo = scheduler.get_sorteo_especifico()
        print(f"✅ Próximo sorteo: {proximo.dia_semana} {scheduler._formatear_fecha_legible(proximo.fecha)}")
        
        # Probar próximos sorteos
        sorteos = scheduler.get_proximos_sorteos(3)
        print(f"✅ Encontrados {len(sorteos)} próximos sorteos")
        
        # Probar API integration
        result = scheduler.get_prediction_for_api()
        if result.get('success'):
            print("✅ API integration funcionando correctamente")
        else:
            print("⚠️ API integration con advertencias")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando scheduler: {e}")
        return False

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    system = platform.system()
    
    print("\n🎯 OMEGA AI Kabala Scheduler - Instalación Completada!")
    print("=" * 60)
    print("\n📋 COMANDOS DISPONIBLES:")
    print("   python omega_scheduler.py                    # Predicción inmediata")
    print("   python omega_scheduler.py --next-sorteos     # Próximos sorteos")
    print("   python omega_scheduler.py --setup-cron       # Configurar cron")
    print("   python omega_scheduler.py --run-daemon       # Ejecutar en background")
    print("   python quick_predict.py                      # Predicción rápida")
    print("   python show_next_sorteos.py                  # Mostrar calendario")
    
    print("\n🚀 INICIAR API:")
    print("   python api_kabala_integration.py             # API completa")
    print("   Endpoints: /predict, /sorteos, /health")
    
    print("\n⚙️ CONFIGURAR SERVICIO AUTOMÁTICO:")
    
    if system == "Linux":
        print("   sudo cp service_files/omega-kabala-scheduler.service /etc/systemd/system/")
        print("   sudo systemctl enable omega-kabala-scheduler")
        print("   sudo systemctl start omega-kabala-scheduler")
    
    elif system == "Darwin":  # macOS
        print("   cp service_files/com.omega.kabala.scheduler.plist ~/Library/LaunchAgents/")
        print("   launchctl load ~/Library/LaunchAgents/com.omega.kabala.scheduler.plist")
    
    elif system == "Windows":
        print("   Usar Task Scheduler con: service_files/omega_scheduler_windows.bat")
        print("   Configurar para ejecutar en inicio del sistema")
    
    print("\n📅 HORARIOS AUTOMÁTICOS:")
    print("   • Martes 10:00 AM   - Predicción automática")
    print("   • Jueves 10:00 AM   - Predicción automática") 
    print("   • Sábado 10:00 AM   - Predicción automática")
    print("   • 19:30 (días sorteo) - Recordatorio 2h antes")
    
    print("\n🎲 KABALA INFO:")
    print("   • Días: Martes, Jueves, Sábados")
    print("   • Hora: 21:30 (Lima, Perú)")
    print("   • Números: 6 números del 1 al 40")
    
    print("\n✅ Sistema listo para usar!")

def main():
    """Función principal de setup"""
    print("🎯 OMEGA AI Kabala Scheduler - Setup")
    print("=" * 50)
    
    # 1. Instalar dependencias
    if not install_dependencies():
        print("❌ Error instalando dependencias")
        return False
    
    # 2. Crear configuración
    create_scheduler_config()
    
    # 3. Setup archivos de servicio
    setup_service_files()
    
    # 4. Crear scripts rápidos
    create_quick_start_scripts()
    
    # 5. Configurar logging
    setup_logging()
    
    # 6. Probar scheduler
    if not test_scheduler():
        print("⚠️ Scheduler instalado pero con advertencias")
    
    # 7. Mostrar instrucciones
    show_usage_instructions()
    
    return True

if __name__ == "__main__":
    main()