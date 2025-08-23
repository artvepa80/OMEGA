import pytest
from main import main, parallel_svi, reportar_progreso

def test_main_no_data_file(tmp_path):
    """Test that main exits when data file is missing."""
    with pytest.raises(SystemExit):
        main(data_path="nonexistent.csv")

def test_parallel_svi(monkeypatch):
    """Test parallel_svi with mocked batch_calcular_svi."""
    def mock_batch_svi(combo, *args):
        return [(combo, 1.0)]
    monkeypatch.setattr("main.batch_calcular_svi", mock_batch_svi)
    results = parallel_svi(
        [[1, 2, 3, 4, 5, 6]],
        "default",
        False,
        3.0,
        lambda i, t: None,
        {"svi_batch_size": 1}
    )
    assert results == [([1, 2, 3, 4, 5, 6], 1.0)]

def test_duplicate_handling(monkeypatch):
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
            log_info(f"Combinación duplicada eliminada: {item['combination']}")
    assert len(combinaciones_finales_validas) == 1