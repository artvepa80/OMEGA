# tests/test_main.py
import sys
import os
import glob
import logging
import pytest
import pandas as pd
import time
from unittest.mock import Mock

# Aseguramos que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import main, parallel_svi, reportar_progreso

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_data(tmp_path):
    """Fixture para crear un archivo CSV temporal con datos de prueba."""
    data = pd.DataFrame({
        'Bolilla 1': [1, 7, 13, 19, 25] * 10,
        'Bolilla 2': [2, 8, 14, 20, 26] * 10,
        'Bolilla 3': [3, 9, 15, 21, 27] * 10,
        'Bolilla 4': [4, 10, 16, 22, 28] * 10,
        'Bolilla 5': [5, 11, 17, 23, 29] * 10,
        'Bolilla 6': [6, 12, 18, 24, 30] * 10
    })
    data_path = tmp_path / "historial_kabala_github.csv"
    data.to_csv(data_path, index=False)
    return str(data_path)

def test_main_runs(sample_data):
    """Prueba que main() se ejecute sin errores críticos."""
    try:
        result = main(
            data_path=sample_data,
            svi_profile="default",
            top_n=5,
            enable_models=["all"],
            export_formats=["csv"]
        )
        assert isinstance(result, list), "main() debe devolver una lista"
        assert all(len(item["combination"]) == 6 for item in result), "Cada combinación debe tener 6 números"
    except Exception as e:
        assert False, f"main() lanzó una excepción: {e}"

def test_parallel_svi_runs():
    """Prueba que parallel_svi() se ejecute sin errores."""
    try:
        combinations = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
        config = {"svi_batch_size": 2}
        result = parallel_svi(
            combinations=combinations,
            perfil_rng="B",
            validacion_ghost=False,
            score_historico=3.0,
            progress_callback=Mock(),
            config=config
        )
        assert isinstance(result, list), "parallel_svi() debe devolver una lista"
        assert len(result) == len(combinations), "Debe devolver una tupla por cada combinación"
    except Exception as e:
        assert False, f"parallel_svi() lanzó una excepción: {e}"

def test_reportar_progreso_runs():
    """Verifica que reportar_progreso() pueda ejecutarse correctamente."""
    try:
        reportar_progreso(1, 10, config={"progress_bar_style": {"desc": "Test", "unit": "step"}})
        reportar_progreso(10, 10)  # Cierra la barra
    except Exception as e:
        assert False, f"reportar_progreso() falló: {e}"

def test_latest_csv_exists(sample_data):
    """Confirma que un archivo CSV fue exportado en results/."""
    # Registramos el tiempo de inicio antes de ejecutar main()
    start_time = time.time()
    
    main(
        data_path=sample_data,
        svi_profile="default",
        top_n=5,
        enable_models=["all"],
        export_formats=["csv"]
    )
    
    # Buscamos todos los archivos CSV en results/
    files = glob.glob("results/svi_export_*.csv")
    assert files, "❌ No se encontró ningún archivo CSV exportado"
    
    # Obtenemos el archivo más reciente
    latest_file = max(files, key=os.path.getctime)
    
    # Verificamos que el archivo no esté vacío
    assert os.path.getsize(latest_file) > 0, "❌ El archivo CSV exportado está vacío"
    
    # Verificamos que fue creado durante esta ejecución
    file_ctime = os.path.getctime(latest_file)
    assert file_ctime >= start_time, (
        f"❌ El archivo {latest_file} fue creado antes de la prueba "
        f"(creado: {file_ctime}, inicio prueba: {start_time})"
    )

def test_duplicate_handling():
    """Test duplicate combination handling."""
    combinaciones = [
        {"combination": [1, 2, 3, 4, 5, 6]},
        {"combination": [1, 2, 3, 4, 5, 6]}
    ]
    config_viabilidad = {"log_duplicates": True}
    seen = set()
    combinaciones_finales_validas = []
    for item in combinaciones:
        combo_tuple = tuple(sorted(item["combination"]))
        if combo_tuple not in seen:
            seen.add(combo_tuple)
            combinaciones_finales_validas.append(item)
        elif config_viabilidad.get("log_duplicates", False):
            logger.info(f"Combinación duplicada eliminada: {item['combination']}")
    assert len(combinaciones_finales_validas) == 1, "Debe eliminar combinaciones duplicadas"