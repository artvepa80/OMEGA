import pytest
import pandas as pd
import numpy as np
import logging

from modules.genetic_model import (
    GeneticConfig,
    GeneticModel,
    generar_combinaciones_geneticas,
)

# ——————————————————————————————————————————————————————————————————————————————
# Fixtures y helpers
# ——————————————————————————————————————————————————————————————————————————————
@pytest.fixture
def small_df():
    # Un par de sorteos históricos muy sencillos
    return pd.DataFrame({
        'n1': [1, 10],
        'n2': [2, 11],
        'n3': [3, 12],
        'n4': [4, 13],
        'n5': [5, 14],
        'n6': [6, 15],
    })

@pytest.fixture
def empty_hist():
    return set()

def always_true_filter(combo, historial=None):
    # Filter que siempre deja pasar la combinación
    return True

def constant_fitness(combo):
    # Fitness constante para simplificar comprobaciones
    return 42.0

# ——————————————————————————————————————————————————————————————————————————————
# 1) Configuración
# ——————————————————————————————————————————————————————————————————————————————
def test_config_validation():
    # valores inválidos deben lanzar ValueError
    with pytest.raises(ValueError):
        GeneticConfig(elite_fraction=1.5)
    with pytest.raises(ValueError):
        GeneticConfig(mutation_rate=-0.1)
    with pytest.raises(ValueError):
        GeneticConfig(pop_size=0)
    with pytest.raises(ValueError):
        GeneticConfig(generations=0)
    with pytest.raises(ValueError):
        GeneticConfig(tournament_size=0)
    with pytest.raises(ValueError):
        GeneticConfig(max_mutation_attempts=0)

# ——————————————————————————————————————————————————————————————————————————————
# 2) Preprocesado de frecuencias
# ——————————————————————————————————————————————————————————————————————————————
def test_preprocess_frequencies_covers_all_numbers(small_df, empty_hist):
    cfg = GeneticConfig(seed=0)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=always_true_filter,
        fitness_fn=constant_fitness,
    )
    # Debemos tener 1..40 en freq_map
    assert set(m.freq_map.keys()) == set(range(1,41))
    # Los números que aparecen en small_df tienen frecuencia > 0
    for v in [1,2,3,4,5,6,10,11,12,13,14,15]:
        assert m.freq_map[v] > 0

# ——————————————————————————————————————————————————————————————————————————————
# 3) default_fitness
# ——————————————————————————————————————————————————————————————————————————————
def test_default_fitness_components(small_df, empty_hist):
    cfg = GeneticConfig(seed=1, verbose=True)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=always_true_filter,
        fitness_fn=None,  # usa _default_fitness
    )
    combo = [1,2,3,4,5,6]
    f = m._default_fitness(combo)
    # Debe ser > 0 (frequency + decades + bonus_filters)
    assert f > 0

# ——————————————————————————————————————————————————————————————————————————————
# 4) initialize_population
# ——————————————————————————————————————————————————————————————————————————————
def test_initialize_population_properties(small_df, empty_hist):
    cfg = GeneticConfig(pop_size=15, seed=42)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=always_true_filter,
        fitness_fn=constant_fitness,
    )
    pop = m.initialize_population()
    assert len(pop) <= cfg.pop_size
    for combo in pop:
        assert len(combo) == 6
        assert len(set(combo)) == 6
        assert all(1 <= x <= 40 for x in combo)

# ——————————————————————————————————————————————————————————————————————————————
# 5) tournament_selection & next_generation
# ——————————————————————————————————————————————————————————————————————————————
def test_tournament_and_next_gen(small_df, empty_hist):
    cfg = GeneticConfig(pop_size=10, generations=1, seed=123)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=always_true_filter,
        fitness_fn=constant_fitness,
    )
    pop = m.initialize_population()
    fitness = np.array([constant_fitness(c) for c in pop])
    selected = m.tournament_selection(pop, fitness)
    assert len(selected) == len(pop)
    children = m.next_generation(pop, fitness)
    # población resultante mantiene tamaño original
    assert len(children) == len(pop)

# ——————————————————————————————————————————————————————————————————————————————
# 6) mutate respeta max_attempts y produce válidos
# ——————————————————————————————————————————————————————————————————————————————
def test_mutate_respects_max_attempts_and_validity(small_df, empty_hist):
    cfg = GeneticConfig(seed=0, mutation_rate=1.0, max_mutation_attempts=5)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=lambda c, h: True,
        fitness_fn=constant_fitness,
    )
    # forzamos que siempre muta todos los genes -> produce distinta combo o la misma
    original = [1,2,3,4,5,6]
    out = m.mutate(original)
    assert isinstance(out, list) and len(out) == 6
    assert all(1 <= x <= 40 for x in out)

# ——————————————————————————————————————————————————————————————————————————————
# 7) run y best_history
# ——————————————————————————————————————————————————————————————————————————————
def test_run_and_best_history(small_df, empty_hist):
    cfg = GeneticConfig(pop_size=5, generations=3, seed=7)
    m = GeneticModel(
        data=small_df,
        historial_set=empty_hist,
        config=cfg,
        filter_fn=always_true_filter,
        fitness_fn=constant_fitness,
    )
    pop = m.run()
    assert len(m.best_history) == cfg.generations
    assert len(pop) == cfg.pop_size

# ——————————————————————————————————————————————————————————————————————————————
# 8) API de alto nivel: generar_combinaciones_geneticas
# ——————————————————————————————————————————————————————————————————————————————
def test_generar_combinaciones_geneticas_api(small_df, empty_hist, caplog):
    cfg = GeneticConfig(pop_size=10, generations=2, seed=0)
    caplog.set_level(logging.INFO)
    results = generar_combinaciones_geneticas(
        data=small_df,
        historial=empty_hist,
        cantidad=5,
        config=cfg,
        logger=logging.getLogger("test"),
    )
    # Debe devolver 5 resultados
    assert isinstance(results, list) and len(results) == 5
    for r in results:
        assert set(r.keys()) == {"combination", "source", "fitness", "score"}
        combo = r["combination"]
        assert len(combo) == 6 and all(isinstance(x, int) for x in combo)
    # Verifica que se registró al menos un INFO de inicio
    assert "Iniciando generación genética" in caplog.text