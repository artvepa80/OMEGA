# OMEGA_PRO_AI_v10.1/config/data_paths.py
"""
Configuración centralizada de rutas de datos para OMEGA PRO AI
"""

from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Rutas de datos
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
MODELS_DIR = BASE_DIR / 'models'
RESULTS_DIR = BASE_DIR / 'results'

# CSV principal corregido
MAIN_CSV = DATA_DIR / 'historial_kabala_github_fixed.csv'

# CSV original (backup)
ORIGINAL_CSV = DATA_DIR / 'historial_kabala_github.csv'

# Datasets procesados para cada modelo
LSTM_DATA = PROCESSED_DIR / 'lstm_data.csv'
TRANSFORMER_DATA = PROCESSED_DIR / 'transformer_data.csv'
STATISTICAL_DATA = PROCESSED_DIR / 'statistical_data.csv'

# Verificar que los archivos existan
def verify_data_files():
    """Verifica que todos los archivos de datos necesarios existan"""
    required_files = {
        'CSV Principal': MAIN_CSV,
        'LSTM Data': LSTM_DATA,
        'Transformer Data': TRANSFORMER_DATA,
        'Statistical Data': STATISTICAL_DATA
    }
    
    all_exist = True
    for name, path in required_files.items():
        if not path.exists():
            print(f"❌ Falta archivo: {name} ({path})")
            all_exist = False
        else:
            print(f"✅ {name}: {path}")
    
    return all_exist

# Configuración para diferentes módulos
MODULE_CONFIGS = {
    'ghost_rng': {
        'data_path': str(MAIN_CSV),
        'columns': ['Bolilla 1', 'Bolilla 2', 'Bolilla 3', 'Bolilla 4', 'Bolilla 5', 'Bolilla 6']
    },
    'lstm': {
        'data_path': str(LSTM_DATA),
        'sequence_length': 10,
        'features': 6
    },
    'transformer': {
        'data_path': str(TRANSFORMER_DATA),
        'sequence_length': 10,
        'features': 6
    },
    'apriori': {
        'data_path': str(STATISTICAL_DATA),
        'min_support': 0.01
    }
}

if __name__ == "__main__":
    print("Verificando archivos de datos...")
    if verify_data_files():
        print("\n✅ Todos los archivos de datos están disponibles")
    else:
        print("\n⚠️ Faltan archivos. Ejecuta fix_csv_order.py primero")