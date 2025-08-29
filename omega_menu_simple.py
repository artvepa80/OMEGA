#!/usr/bin/env python3
"""
OMEGA Menu Simple - Sin problemas de bash input
"""

import subprocess
import sys
import os

def show_header():
    os.system('clear')
    print("🚀 OMEGA PRO AI v10.1 - Menú Interactivo")
    print("=" * 50)
    print("🌐 URL: https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win")
    print("⚡ Estado: Activo en Akash Network")
    print("💻 Recursos Mac: 0% | 🌐 Recursos Akash: 100%")
    print("=" * 50)

def run_command(cmd):
    """Execute command and wait for completion"""
    try:
        result = subprocess.run(cmd, shell=True, check=False)
        print("\nPresiona ENTER para continuar...")
        input()
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        input()
        return False

def generate_predictions():
    print("\n🎯 ¿Cuántas predicciones quieres generar?")
    print("1) 5 predicciones rápidas")
    print("2) 10 predicciones estándar") 
    print("3) 25 predicciones completas")
    print("4) Cantidad personalizada")
    
    choice = input("\nSelecciona (1-4): ").strip()
    
    if choice == "1":
        run_command("python3 omega_akash_client.py predict 5")
    elif choice == "2":
        run_command("python3 omega_akash_client.py predict 10")
    elif choice == "3":
        run_command("python3 omega_akash_client.py predict 25")
    elif choice == "4":
        custom = input("Ingresa cantidad (1-50): ").strip()
        try:
            num = int(custom)
            if 1 <= num <= 50:
                run_command(f"python3 omega_akash_client.py predict {num}")
            else:
                print("❌ Número debe estar entre 1 y 50")
                input()
        except:
            print("❌ Número inválido")
            input()
    else:
        print("❌ Opción inválida")
        input()

def generate_multijugada():
    print("\n🎲 MULTIJUGADAS OMEGA")
    print("=" * 30)
    print("Selecciona el tipo de multijugada:")
    print("1) 7 números (7 combinaciones)")
    print("2) 9 números (84 combinaciones)")
    print("3) 10 números (210 combinaciones)")
    
    multi_choice = input("\nTipo de multijugada (1-3): ").strip()
    
    numeros_map = {"1": "7", "2": "9", "3": "10"}
    if multi_choice not in numeros_map:
        print("❌ Opción inválida")
        input()
        return
    
    numeros = numeros_map[multi_choice]
    
    print("\n📈 ¿Cuántas series deseas?")
    print("1) 1 serie")
    print("2) 2 series")
    print("3) 3 series")
    print("4) 4 series")
    
    series_choice = input("\nCantidad de series (1-4): ").strip()
    
    if series_choice in ["1", "2", "3", "4"]:
        series = series_choice
        print(f"\n🚀 Generando multijugada de {numeros} números con {series} series...")
        run_command(f"python3 omega_akash_client.py multijugada {numeros} {series}")
    else:
        print("❌ Opción inválida")
        input()

def check_system():
    print("\n🔍 VERIFICANDO ESTADO DEL SISTEMA...")
    print("=" * 40)
    run_command("python3 omega_akash_client.py health")

def advanced_commands():
    print("\n🛠️  COMANDOS AVANZADOS")
    print("=" * 25)
    print("1) Ejecutar omega_remote_executor.py")
    print("2) Ejecutar omega_terminal_client.py")
    print("3) Ver ejecución en tiempo real")
    print("4) Volver al menú principal")
    
    choice = input("\nSelecciona (1-4): ").strip()
    
    if choice == "1":
        run_command("python3 omega_remote_executor.py run --ai-combinations 5 --advanced-ai")
    elif choice == "2":
        num_pred = input("¿Cuántas predicciones? (default 8): ").strip()
        if not num_pred:
            num_pred = "8"
        run_command(f"python3 omega_terminal_client.py predict {num_pred}")
    elif choice == "3":
        num_pred = input("¿Cuántas predicciones para ver? (default 10): ").strip()
        if not num_pred:
            num_pred = "10"
        run_command(f"python3 watch_omega_live.py {num_pred}")
    elif choice == "4":
        return
    else:
        print("❌ Opción inválida")
        input()

def show_endpoints():
    print("\n📋 INFORMACIÓN DEL SISTEMA")
    print("=" * 30)
    print("🌐 URL Principal: https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win")
    print("🔗 Health Check: /health")
    print("🎯 Predicciones: /predict")
    print("\nCOMANDOS DISPONIBLES:")
    print("=" * 25)
    print("• python3 omega_akash_client.py predict [cantidad]")
    print("• python3 omega_akash_client.py multijugada [7|9|10] [series]")
    print("• python3 omega_akash_client.py health")
    print("• python3 watch_omega_live.py [cantidad]")
    input("\nPresiona ENTER para continuar...")

def main():
    while True:
        show_header()
        print("\nSELECCIONA UNA OPCIÓN:")
        print("=" * 25)
        print("1) 🎲 Generar Predicciones OMEGA")
        print("2) 🎰 Multijugadas (7, 9, 10 números)")
        print("3) ⚡ Verificar Estado del Sistema")
        print("4) 🛠️  Comandos Avanzados")
        print("5) 📋 Mostrar URLs y Endpoints")
        print("6) 🏃 Prueba Rápida (5 predicciones)")
        print("7) 🚪 Salir")
        
        choice = input("\n👉 Tu opción (1-7): ").strip()
        
        if choice == "1":
            generate_predictions()
        elif choice == "2":
            generate_multijugada()
        elif choice == "3":
            check_system()
        elif choice == "4":
            advanced_commands()
        elif choice == "5":
            show_endpoints()
        elif choice == "6":
            print("🏃 PRUEBA RÁPIDA...")
            run_command("python3 omega_akash_client.py predict 5")
        elif choice == "7":
            print("\n👋 Saliendo del sistema OMEGA...")
            print("✅ Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Usa 1-7.")
            input("Presiona ENTER para continuar...")

if __name__ == "__main__":
    main()
