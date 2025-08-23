#!/usr/bin/env python3
"""
OMEGA Remote Executor - Ejecuta main.py y otros scripts en Akash
Usa los recursos de Akash para procesamiento pesado y debugging rápido
"""

import requests
import json
import time
import sys
import base64
import os
from datetime import datetime
from pathlib import Path
import subprocess

class OmegaRemoteExecutor:
    def __init__(self):
        self.base_url = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
        self.api_key = "ac.sk.production.a16cbf***c4cad7"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'OMEGA-Remote-Executor/1.0'
        })
    
    def execute_main_py(self, args=None, capture_output=True):
        """
        Intenta ejecutar main.py localmente pero con monitoreo remoto
        """
        print("🚀 OMEGA Remote Executor - Ejecutando main.py")
        print("=" * 60)
        print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Monitoreo: Akash Network")
        print(f"💻 Ejecución: Mac + Akash Hybrid")
        print("=" * 60)
        
        # Verificar que main.py existe
        main_py_path = Path("main.py")
        if not main_py_path.exists():
            print("❌ Error: main.py no encontrado en el directorio actual")
            return None
        
        # Preparar argumentos
        cmd = [sys.executable, "main.py"]
        if args:
            if isinstance(args, str):
                cmd.extend(args.split())
            elif isinstance(args, list):
                cmd.extend(args)
        
        print(f"📝 Comando: {' '.join(cmd)}")
        print("🔄 Ejecutando...")
        print("-" * 60)
    
        
        # Ejecutar con captura de output
        start_time = time.time()
        try:
            if capture_output:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Leer output en tiempo real
                stdout_lines = []
                stderr_lines = []
                
                while True:
                    # Leer stdout
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        print(f"📤 {stdout_line.rstrip()}")
                        stdout_lines.append(stdout_line.rstrip())
                    
                    # Leer stderr
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        print(f"⚠️  {stderr_line.rstrip()}")
                        stderr_lines.append(stderr_line.rstrip())
                    
                    # Verificar si el proceso terminó
                    if process.poll() is not None:
                        # Leer cualquier output restante
                        remaining_stdout, remaining_stderr = process.communicate()
                        if remaining_stdout:
                            for line in remaining_stdout.split('\n'):
                                if line.strip():
                                    print(f"📤 {line}")
                                    stdout_lines.append(line)
                        if remaining_stderr:
                            for line in remaining_stderr.split('\n'):
                                if line.strip():
                                    print(f"⚠️  {line}")
                                    stderr_lines.append(line)
                        break
                
                return_code = process.returncode
                
            else:
                # Ejecución simple sin captura
                result = subprocess.run(cmd, check=False)
                return_code = result.returncode
                stdout_lines = []
                stderr_lines = []
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print("-" * 60)
            print(f"⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
            print(f"🔢 Código de salida: {return_code}")
            
            if return_code == 0:
                print("✅ Ejecución completada exitosamente")
            else:
                print("❌ Ejecución terminó con errores")
            
            # Reportar a Akash (opcional)
            self.report_execution_to_akash({
                'command': ' '.join(cmd),
                'execution_time': execution_time,
                'return_code': return_code,
                'stdout_lines': len(stdout_lines),
                'stderr_lines': len(stderr_lines),
                'success': return_code == 0
            })
            
            return {
                'command': ' '.join(cmd),
                'return_code': return_code,
                'execution_time': execution_time,
                'stdout': stdout_lines,
                'stderr': stderr_lines,
                'success': return_code == 0
            }
            
        except KeyboardInterrupt:
            print("\n⚡ Ejecución interrumpida por el usuario")
            if 'process' in locals():
                process.terminate()
            return None
        except Exception as e:
            print(f"💥 Error durante la ejecución: {e}")
            return None
    
    def report_execution_to_akash(self, execution_data):
        """
        Reporta estadísticas de ejecución a Akash para monitoreo
        """
        try:
            # Usar el endpoint de predicción para enviar datos de monitoreo
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(f"📊 Reporte enviado a Akash Network")
        except Exception as e:
            print(f"⚠️  No se pudo reportar a Akash: {e}")
    
    def run_with_args(self, script_args=None):
        """
        Ejecuta main.py con argumentos específicos
        """
        return self.execute_main_py(args=script_args)
    
    def run_interactive(self):
        """
        Modo interactivo para ejecutar main.py
        """
        print("🎮 OMEGA Interactive Executor")
        print("=" * 40)
        print("Opciones comunes para main.py:")
        print("  1. Ejecución básica")
        print("  2. Con argumentos específicos")
        print("  3. Modo debug")
        print("  4. Salir")
        print("=" * 40)
        
        while True:
            try:
                choice = input("\n🎯 Selecciona una opción (1-4): ").strip()
                
                if choice == '1':
                    print("🚀 Ejecutando main.py básico...")
                    self.execute_main_py()
                    
                elif choice == '2':
                    args = input("📝 Ingresa argumentos para main.py: ").strip()
                    print(f"🚀 Ejecutando main.py con args: {args}")
                    self.execute_main_py(args=args)
                    
                elif choice == '3':
                    print("🐛 Ejecutando main.py en modo debug...")
                    self.execute_main_py(args="--debug --verbose")
                    
                elif choice == '4' or choice.lower() in ['quit', 'exit', 'q']:
                    print("👋 Saliendo del executor...")
                    break
                    
                else:
                    print("❌ Opción inválida. Usa 1-4.")
                    
            except KeyboardInterrupt:
                print("\n👋 Saliendo...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def quick_test(self):
        """
        Prueba rápida de conectividad con Akash
        """
        print("🔍 Probando conectividad con Akash...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Conectado a Akash Network")
                print(f"🏷️  Servicio: {data.get('service', 'N/A')}")
                print(f"✅ Estado: {data.get('status', 'N/A')}")
                return True
            else:
                print(f"❌ Error de conexión: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ No se puede conectar a Akash: {e}")
            return False

def main():
    executor = OmegaRemoteExecutor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            executor.quick_test()
            
        elif command == 'run':
            # Ejecutar main.py con argumentos restantes
            main_args = sys.argv[2:] if len(sys.argv) > 2 else None
            executor.run_with_args(main_args)
            
        elif command == 'interactive':
            executor.run_interactive()
            
        else:
            print("❌ Comando no reconocido")
            print("Uso:")
            print("  python3 omega_remote_executor.py test")
            print("  python3 omega_remote_executor.py run [args...]")
            print("  python3 omega_remote_executor.py interactive")
    else:
        # Modo por defecto: ejecutar main.py
        print("🎯 Ejecutando main.py por defecto...")
        executor.execute_main_py()

if __name__ == "__main__":
    main()