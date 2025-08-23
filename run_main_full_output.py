#!/usr/bin/env python3
"""
OMEGA Full Output Runner - Ejecuta main.py mostrando TODO el output
Similar a lo que se ve en la imagen del terminal
"""

import subprocess
import sys
import os
import time
import socket
from datetime import datetime

def run_main_with_full_output(args=""):
    """
    Ejecuta main.py con TODO el output visible, incluyendo DEBUG, INFO, WARNING
    """
    print("🚀 OMEGA PRO AI v10.1 - Ejecución Completa con Output Full")
    print("=" * 80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏠 Host: {socket.gethostname()}")
    print(f"👤 Usuario: {os.getenv('USER', 'unknown')}")
    print(f"📁 Directorio: {os.getcwd()}")
    print(f"🐍 Python: {sys.executable}")
    
    # Detectar entorno
    is_akash = (
        os.path.exists('/.dockerenv') or 
        os.getenv('KUBERNETES_SERVICE_HOST') or
        'akash' in socket.gethostname().lower()
    )
    
    print(f"🌍 Entorno: {'🚀 AKASH DEPLOYMENT' if is_akash else '🏠 LOCAL'}")
    
    # Preparar comando
    cmd = [sys.executable, "main.py"]
    if args:
        if isinstance(args, str):
            cmd.extend(args.split())
        elif isinstance(args, list):
            cmd.extend(args)
    
    print(f"📝 Comando: {' '.join(cmd)}")
    print("=" * 80)
    print("🔄 Ejecutando main.py - Mostrando TODO el output...")
    print("=" * 80)
    
    # Ejecutar con output en tiempo real
    start_time = time.time()
    
    try:
        # Usar subprocess.Popen para capturar output en tiempo real
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combinar stderr con stdout
            universal_newlines=True,
            bufsize=1,  # Line buffered
            env=dict(os.environ, PYTHONUNBUFFERED='1')  # Unbuffered output
        )
        
        line_count = 0
        
        # Leer y mostrar output línea por línea
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line_count += 1
                # Mostrar cada línea tal como viene
                print(output.rstrip())
                
                # Flush para mostrar inmediatamente
                sys.stdout.flush()
        
        # Obtener código de salida
        return_code = process.poll()
        
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE EJECUCIÓN")
        print("=" * 80)
        print(f"⏱️  Tiempo total: {execution_time:.2f} segundos")
        print(f"📄 Líneas de output: {line_count}")
        print(f"🔢 Código de salida: {return_code}")
        
        if return_code == 0:
            print("✅ ¡Ejecución completada exitosamente!")
        else:
            print("❌ Ejecución terminó con errores")
            
        return return_code == 0
        
    except KeyboardInterrupt:
        print("\n⚡ Ejecución interrumpida por el usuario (Ctrl+C)")
        if process:
            process.terminate()
        return False
        
    except Exception as e:
        print(f"\n💥 Error durante la ejecución: {e}")
        return False

def main():
    """
    Función principal - permite ejecutar con argumentos
    """
    if len(sys.argv) > 1:
        # Usar argumentos pasados al script
        main_args = sys.argv[1:]
        print(f"🎯 Argumentos recibidos: {' '.join(main_args)}")
        run_main_with_full_output(main_args)
    else:
        # Ejecución por defecto - mostrar opciones
        print("🎮 OMEGA Full Output Runner")
        print("=" * 50)
        print("Opciones de ejecución:")
        print("1. Ejecución básica completa")
        print("2. Con IA avanzada")
        print("3. Modo debug completo")
        print("4. Meta-learning")
        print("5. Argumentos personalizados")
        print("6. Solo mostrar info del dataset")
        print("=" * 50)
        
        try:
            choice = input("\n🎯 Selecciona opción (1-6): ").strip()
            
            if choice == '1':
                print("🚀 Ejecución básica completa...")
                run_main_with_full_output("--top_n 8")
                
            elif choice == '2':
                print("🧠 Ejecución con IA avanzada...")
                run_main_with_full_output("--ai-combinations 10 --advanced-ai")
                
            elif choice == '3':
                print("🐛 Modo debug completo...")
                run_main_with_full_output("--enable-performance-monitoring --top_n 5")
                
            elif choice == '4':
                print("🌟 Meta-learning...")
                run_main_with_full_output("--meta-learning --enable-adaptive-learning")
                
            elif choice == '5':
                args = input("📝 Ingresa argumentos para main.py: ").strip()
                print(f"🚀 Ejecutando con: {args}")
                run_main_with_full_output(args)
                
            elif choice == '6':
                print("📊 Información del dataset...")
                run_main_with_full_output("--data-info")
                
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Cancelado por el usuario")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()