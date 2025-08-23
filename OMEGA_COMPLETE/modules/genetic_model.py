# OMEGA_PRO_AI_v10.1/modules/genetic_model.py – OMEGA PRO AI v10.1 – Mejora del Modelo Genético

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, List, Set, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy.stats import entropy

from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations

# ——————————————————————————————————————————————————————————————————————————————
# 1) Configuración tipada con dataclass y validación
# ——————————————————————————————————————————————————————————————————————————————
@dataclass
class GeneticConfig:
    pop_size: int = 50
    generations: int = 20
    tournament_size: int = 3
    elite_fraction: float = 0.1
    mutation_rate: float = 0.25
    max_mutation_attempts: int = 50
    weight_frequency: float = 0.8
    weight_decade_div: float = 1.5
    bonus_filters: float = 50.0
    penalty_duplicate: float = 100.0
    bonus_parity: float = 20.0
    penalty_decade_concentration: float = 15.0
    seed: Optional[int] = None
    verbose: bool = False
    adaptive_params: bool = True

    def __post_init__(self):
        if not 0 <= self.elite_fraction <= 1:
            raise ValueError("elite_fraction debe estar en [0,1]")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("mutation_rate debe estar en [0,1]")
        if self.pop_size < 1 or self.generations < 1:
            raise ValueError("pop_size y generations deben ser >= 1")
        if self.tournament_size < 1:
            raise ValueError("tournament_size debe ser >= 1")
        if self.max_mutation_attempts < 1:
            raise ValueError("max_mutation_attempts debe ser >= 1")

# ——————————————————————————————————————————————————————————————————————————————
# 2) Clase principal con mejoras avanzadas
# ——————————————————————————————————————————————————————————————————————————————
class GeneticModel:
    def __init__(
        self,
        data: pd.DataFrame,
        historial_set: Set[Tuple[int, ...]],
        config: GeneticConfig = GeneticConfig(),
        fitness_fn: Optional[Callable[[List[int]], float]] = None,
        filter_fn: Optional[Callable[[List[int], Set[Tuple[int, ...]]], bool]] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        if config.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        self.cfg = config
        self.rng = np.random.default_rng(config.seed)
        self.data = data
        self.external_historial = historial_set
        self.known_combinations = historial_set.copy()
        self.recent_performance: Dict[int, float] = {}
        self.filter_fn = filter_fn or FiltroEstrategico().aplicar_filtros
        self.fitness_fn = fitness_fn or self._default_fitness
        self._preprocess_frequencies()
        self.avg_frequency = np.mean(list(self.freq_map.values())) if self.freq_map else 1.0
        self.best_history = []
        self.avg_history = []
        self.std_history = []
        self.diversity_history = []
        self.top_num_history = []
        self.combo_cache: Dict[Tuple[int, ...], Dict] = {}
        
        self.logger.info("🧬 GeneticModel avanzado inicializado | %d sorteos | Semilla: %s", 
                         len(data), config.seed)

    def _get_combo_info(self, combo: List[int]) -> Dict:
        combo_tuple = tuple(sorted(combo))
        if combo_tuple in self.combo_cache:
            return self.combo_cache[combo_tuple]
        
        even_count = sum(1 for num in combo if num % 2 == 0)
        decades = set((int(num) - 1) // 10 for num in combo)
        freq_sum = sum(self.freq_map.get(num, 0) for num in combo)
        decade_counts = [0] * 4
        
        for num in combo:
            decade_idx = (int(num) - 1) // 10
            if decade_idx < 4:
                decade_counts[decade_idx] += 1
        
        info = {
            'tuple': combo_tuple,
            'even_count': even_count,
            'decades': decades,
            'decade_count': len(decades),
            'freq_sum': freq_sum,
            'decade_counts': decade_counts
        }
        
        self.combo_cache[combo_tuple] = info
        return info

    def _apply_filter(self, combo: List[int], historial: Set[Tuple[int, ...]]) -> bool:
        try:
            return self.filter_fn(combo, historial)
        except TypeError:
            return self.filter_fn(combo)

    def _preprocess_frequencies(self):
        try:
            numeric_data = self.data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                self.freq_map = (pd.Series(numeric_data.values.ravel())
                                 .value_counts()
                                 .to_dict())
            else:
                self.freq_map = {}
                
            for num in range(1, 41):
                self.freq_map.setdefault(num, 0)
                    
            self.logger.debug("Mapa de frecuencias generado")
        except Exception as e:
            self.logger.error("Error procesando frecuencias: %s", e)
            self.freq_map = {i: 1 for i in range(1, 41)}

    def _default_fitness(self, combo: List[int]) -> float:
        info = self._get_combo_info(combo)
        fitness = 0.0
        
        freq_score = 0
        for num in combo:
            base_freq = self.freq_map.get(num, 0)
            recent_bonus = self.recent_performance.get(num, 1.0)
            freq_score += base_freq * recent_bonus
            
        fitness += freq_score * self.cfg.weight_frequency
        fitness += info['decade_count'] * self.cfg.weight_decade_div
        
        for count in info['decade_counts']:
            if count > 2:
                fitness -= (count - 2) * self.cfg.penalty_decade_concentration
        
        if self._apply_filter(combo, self.external_historial):
            fitness += self.cfg.bonus_filters
        
        combo_tuple = info['tuple']
        if combo_tuple in self.external_historial:
            fitness -= self.cfg.penalty_duplicate
        
        if 2 <= info['even_count'] <= 4:
            fitness += self.cfg.bonus_parity
            
        if info['freq_sum'] > 0 and info['freq_sum'] < self.avg_frequency * 3:
            fitness += 10
            
        return fitness

    def initialize_population(self) -> List[List[int]]:
        population = []
        attempts = 0
        max_attempts = self.cfg.pop_size * 5
        all_numbers = np.arange(1, 41)
        
        while len(population) < self.cfg.pop_size and attempts < max_attempts:
            candidate = sorted(self.rng.choice(all_numbers, size=6, replace=False))
            candidate_tuple = tuple(candidate)
            
            if (candidate_tuple not in self.known_combinations and 
                self._apply_filter(candidate, self.external_historial)):
                population.append(candidate)
                self.known_combinations.add(candidate_tuple)
                self._get_combo_info(candidate)
                
            attempts += 1
            
        self.logger.info("🧬 Población inicial: %d/%d individuos", 
                         len(population), self.cfg.pop_size)
        return population

    def tournament_selection(self, population: List[List[int]], fitness: np.ndarray) -> List[List[int]]:
        pop_size = len(population)
        tournament_size = min(self.cfg.tournament_size, pop_size)
        
        competitors = self.rng.integers(0, pop_size, size=(pop_size, tournament_size))
        winner_indices = np.argmax(fitness[competitors], axis=1)
        indices = competitors[np.arange(pop_size), winner_indices]
        
        return [population[i] for i in indices]

    def crossover_flexible(self, parent1: List[int], parent2: List[int]) -> List[int]:
        info1 = self._get_combo_info(parent1)
        info2 = self._get_combo_info(parent2)
        
        odds1 = [n for n in parent1 if n % 2 != 0]
        evens1 = [n for n in parent1 if n % 2 == 0]
        odds2 = [n for n in parent2 if n % 2 != 0]
        evens2 = [n for n in parent2 if n % 2 == 0]
        
        all_odds = list(set(odds1 + odds2))
        all_evens = list(set(evens1 + evens2))
        
        possible_splits = [(2, 4), (3, 3), (4, 2)]
        probs = [0.35, 0.50, 0.15]
        odd_count, even_count = self.rng.choice(possible_splits, p=probs)
        
        if len(all_odds) < odd_count:
            missing = [n for n in range(1, 41, 2) if n not in all_odds]
            all_odds.extend(missing[:odd_count - len(all_odds)])
        
        if len(all_evens) < even_count:
            missing = [n for n in range(2, 41, 2) if n not in all_evens]
            all_evens.extend(missing[:even_count - len(all_evens)])
        
        if not all_odds or not all_evens:
            return sorted(self.rng.choice(range(1, 41), size=6, replace=False))
        
        # CORRECCIÓN: Convertir a float explícitamente
        weights_odds = np.array(
            [max(self.freq_map.get(num, 0.1), 0.1) for num in all_odds],
            dtype=float
        )
        weights_evens = np.array(
            [max(self.freq_map.get(num, 0.1), 0.1) for num in all_evens],
            dtype=float
        )
        
        try:
            weights_odds /= weights_odds.sum()
        except FloatingPointError:
            weights_odds = None
            
        try:
            weights_evens /= weights_evens.sum()
        except FloatingPointError:
            weights_evens = None
        
        try:
            selected_odds = list(self.rng.choice(all_odds, size=odd_count, replace=False, p=weights_odds))
        except ValueError:
            selected_odds = list(self.rng.choice(all_odds, size=odd_count, replace=False))
        
        try:
            selected_evens = list(self.rng.choice(all_evens, size=even_count, replace=False, p=weights_evens))
        except ValueError:
            selected_evens = list(self.rng.choice(all_evens, size=even_count, replace=False))
        
        return sorted(selected_odds + selected_evens)

    def mutate(self, individual: List[int], diversity: float) -> List[int]:
        candidate = individual.copy()
        mutation_factor = 1.0
        if self.cfg.adaptive_params:
            mutation_factor = 1.5 - min(1.0, diversity)
        
        mutation_probs = [
            min(
                0.8, 
                (0.1 + 0.9 * (self.freq_map.get(num, self.avg_frequency) / self.avg_frequency)) 
                * mutation_factor
            )
            for num in candidate
        ]
        
        current_set = set(candidate)
        options = [n for n in range(1, 41) if n not in current_set]
        
        if not options:
            return candidate
        
        for num in options:
            if num not in self.recent_performance:
                self.recent_performance[num] = 1.0
            else:
                self.recent_performance[num] = min(2.0, self.recent_performance[num] * 1.05)
        
        for i in range(len(candidate)):
            if self.rng.random() < mutation_probs[i]:
                weights = np.array([
                    (1 / (self.freq_map.get(n, 1) + 1)) * self.recent_performance.get(n, 1.0)
                    for n in options
                ])
                
                if weights.sum() > 0:
                    weights /= weights.sum()
                else:
                    weights = None
                
                try:
                    new_num = self.rng.choice(options, p=weights)
                except ValueError:
                    continue
                
                candidate[i] = new_num
                current_set.add(new_num)
                options.remove(new_num)
                if not options:
                    break
                    
        return sorted(candidate)

    def calculate_diversity(self, population: List[List[int]]) -> float:
        if not population:
            return 0.0
        
        all_nums = np.array([num for combo in population for num in combo])
        if all_nums.size == 0:
            return 0.0
            
        num_counts = np.bincount(all_nums - 1, minlength=40, weights=None)
        num_counts = num_counts / len(population)
        return entropy(num_counts) / np.log(40)

    def next_generation(self, population: List[List[int]], fitness: np.ndarray, generation: int) -> List[List[int]]:
        pop_size = len(population)
        
        if self.cfg.adaptive_params:
            elite_fraction = self.cfg.elite_fraction * max(0.5, (1 - generation/self.cfg.generations))
            if generation > 5 and (self.best_history[-1] - self.best_history[-5]) < 10:
                mutation_boost = 1.5
            else:
                mutation_boost = 1.0
        else:
            elite_fraction = self.cfg.elite_fraction
            mutation_boost = 1.0
        
        elite_size = max(1, int(elite_fraction * pop_size))
        elite_indices = np.argpartition(fitness, -elite_size)[-elite_size:]
        elite = [population[i] for i in elite_indices]
        
        diversity = self.calculate_diversity(population)
        parents = self.tournament_selection(population, fitness)
        children = []
        mutation_count = 0
        attempts = 0
        max_attempts = pop_size * 2
        
        while len(children) < pop_size - elite_size and attempts < max_attempts:
            idx = self.rng.choice(len(parents), size=2, replace=False)
            p1, p2 = parents[idx[0]], parents[idx[1]]
            
            child = self.crossover_flexible(p1, p2)
            mutated_child = self.mutate(child, diversity)
            
            if mutated_child != child:
                mutation_count += 1
                
            child_info = self._get_combo_info(mutated_child)
            if (child_info['tuple'] not in self.known_combinations and 
                self._apply_filter(mutated_child, self.external_historial)):
                children.append(mutated_child)
                self.known_combinations.add(child_info['tuple'])
                
            attempts += 1
            
        decay_factor = 0.95
        for num in list(self.recent_performance.keys()):
            self.recent_performance[num] *= decay_factor
            
        self.logger.debug("Mutaciones aplicadas: %d/%d individuos | Intentos: %d | Diversidad: %.3f", 
                          mutation_count, len(children), attempts, diversity)
        return elite + children

    def run(self) -> List[List[int]]:
        population = self.initialize_population()
        self.best_history = []
        self.avg_history = []
        self.std_history = []
        self.diversity_history = []
        self.top_num_history = []
        
        for generation in range(self.cfg.generations):
            if len(population) > 100:
                max_workers = min(8, len(population))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    fitness = list(executor.map(self.fitness_fn, population))
                fitness = np.array(fitness)
            else:
                fitness = np.array([self.fitness_fn(ind) for ind in population])
            
            best = np.max(fitness)
            avg = np.mean(fitness)
            std = np.std(fitness)
            diversity = self.calculate_diversity(population)
            
            # CÁLCULO SEGURO DE TOP NUMBERS - SIN ERRORES DE SINTÁXIS
            all_nums = np.array([num for combo in population for num in combo])
            if all_nums.size > 0:
                num_counts = np.bincount(all_nums - 1, minlength=40)
            else:
                num_counts = np.zeros(40)
            
            # SOLUCIÓN DEFINITIVA: Descomponer la operación
            sorted_indices = np.argsort(num_counts)
            top_indices = sorted_indices[-5:][::-1]  # Obtener los top 5 en orden descendente
            
            top_numbers = []
            for i in top_indices:
                num = i + 1
                count = num_counts[i]
                top_numbers.append((num, count))
            
            self.top_num_history.append(top_numbers)
            
            # Formatear para logging
            top_str = ";".join(f"{num}({count})" for num, count in top_numbers)
            
            self.best_history.append(best)
            self.avg_history.append(avg)
            self.std_history.append(std)
            self.diversity_history.append(diversity)
            
            self.logger.info(
                "🧬 Gen %2d/%2d | Mejor: %6.1f | Prom: %6.1f | σ: %5.1f | Div: %.3f | Top: %s",
                generation + 1, self.cfg.generations, best, avg, std, diversity, top_str
            )
            
            population = self.next_generation(population, fitness, generation)
            
        self.save_convergence_history()
        
        if self.best_history:
            improvement = self.best_history[-1] - self.best_history[0]
            self.logger.info("📈 Mejora total del fitness: %.1f (%.1f%%)", 
                             improvement, improvement / abs(self.best_history[0]) * 100 if self.best_history[0] else 0)
            
        return population

    def save_convergence_history(self):
        try:
            top_num_strs = [
                ";".join(f"{num}({count})" for num, count in top_list)
                for top_list in self.top_num_history
            ]
            
            # CORRECCIÓN: Paréntesis balanceados en la creación del DataFrame
            n_gens = len(self.best_history)
            history_df = pd.DataFrame({
                'generation': range(1, n_gens + 1),
                'best_fitness': self.best_history,
                'avg_fitness': self.avg_history,
                'std_fitness': self.std_history,
                'diversity': self.diversity_history,
                'top_numbers': top_num_strs
            })
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            seed_str = f"seed{self.cfg.seed}" if self.cfg.seed is not None else "noseed"
            filename = f"genetic_convergence_{timestamp}_{seed_str}.csv"
            history_df.to_csv(filename, index=False)
            self.logger.info("📊 Historial de convergencia guardado en %s", filename)
            
            best_combos = sorted(self.known_combinations, key=lambda c: self.fitness_fn(list(c)), reverse=True)[:10]
            decade_counts = np.zeros(40)
            
            for combo in best_combos:
                for num in combo:
                    decade_counts[num-1] += 1
            
            decade_df = pd.DataFrame({
                'number': range(1, 41),
                'count_in_top_combos': decade_counts
            })
            decade_df.to_csv(f"top_decades_{timestamp}_{seed_str}.csv", index=False)
            
        except Exception as e:
            self.logger.warning("⚠️ Error guardando historial: %s", e)

# ——————————————————————————————————————————————————————————————————————————————
# 3) Función de alto nivel con mejoras avanzadas
# ——————————————————————————————————————————————————————————————————————————————
def generar_combinaciones_geneticas(
    data: pd.DataFrame,
    historial_set: Set[Tuple[int, ...]],
    cantidad: int = 30,
    config: GeneticConfig = GeneticConfig(),
    logger: Optional[logging.Logger] = None
) -> List[Dict]:
    start_time = time.time()
    logger = logger or logging.getLogger(__name__)
    logger.info("🧬 Iniciando generación genética avanzada...")
    
    try:
        model = GeneticModel(
            data=data,
            historial_set=historial_set,
            config=config,
            logger=logger
        )
        population = model.run()
        
        fitness_cache = {}
        results = []
        seen = set()
        
        for combo in population:
            combo_info = model._get_combo_info(combo)
            combo_tuple = combo_info['tuple']
            
            if combo_tuple in seen or combo_tuple in historial_set:
                continue
                
            seen.add(combo_tuple)
            fitness_val = model.fitness_fn(combo)
            fitness_cache[combo_tuple] = fitness_val
            
            results.append({
                "combination": combo,
                "source": "genetico",
                "fitness": fitness_val,
                "parity": combo_info['even_count'],
                "decades": list(combo_info['decades']),
                "freq_sum": combo_info['freq_sum']
            })
        
        results.sort(key=lambda x: fitness_cache[tuple(x["combination"])], reverse=True)
        results = results[:cantidad]
        
        if len(results) < cantidad:
            needed = cantidad - len(results)
            logger.info("🔁 Generando %d combinaciones de respaldo con criterios estrictos", needed)
            backup_count = 0
            max_backup_attempts = needed * 20
            
            while backup_count < needed and max_backup_attempts > 0:
                candidate = sorted(model.rng.choice(range(1, 41), size=6, replace=False))
                candidate_info = model._get_combo_info(candidate)
                candidate_tuple = candidate_info['tuple']
                
                valid_decades = candidate_info['decade_count'] >= 3
                valid_parity = 2 <= candidate_info['even_count'] <= 4
                no_concentration = all(count <= 2 for count in candidate_info['decade_counts'])
                
                if (candidate_tuple not in seen and 
                    candidate_tuple not in historial_set and 
                    model._apply_filter(candidate, historial_set) and 
                    valid_parity and valid_decades and no_concentration):
                    
                    results.append({
                        "combination": candidate,
                        "source": "genetico_backup",
                        "fitness": 0,
                        "parity": candidate_info['even_count'],
                        "decades": list(candidate_info['decades']),
                        "freq_sum": candidate_info['freq_sum']
                    })
                    seen.add(candidate_tuple)
                    backup_count += 1
                    
                max_backup_attempts -= 1
        
        try:
            combo_list = [{"combination": item["combination"]} for item in results]
            numeric_data = data.select_dtypes(include=[np.number])
            
            if not numeric_data.empty:
                scored = score_combinations(combo_list, numeric_data, sequential=True)
                for result, score_data in zip(results, scored):
                    result["score"] = score_data.get("score", result["fitness"] / 100)
            else:
                for result in results:
                    result["score"] = result["fitness"] / 100
        except Exception as e:
            logger.warning("⚠️ Error en scoring dinámico: %s. Usando fitness normalizado", e)
            for result in results:
                result["score"] = result["fitness"] / 100
        
        valid_results = validate_results(results, historial_set)
        
        elapsed = time.time() - start_time
        logger.info("✅ %d combinaciones genéticas generadas en %.2fs", 
                    len(valid_results), elapsed)
                    
        return valid_results[:cantidad]
        
    except Exception as e:
        logger.error("❌ Error crítico en generación genética: %s", e, exc_info=True)
        return generate_fallback(cantidad, historial_set, config.seed, logger)

def validate_results(results: List[Dict], historial_set: Set[Tuple[int, ...]]) -> List[Dict]:
    valid_results = []
    seen = set()
    
    for result in results:
        combo = result["combination"]
        combo_tuple = tuple(sorted(combo))
        
        if len(set(combo)) != 6:
            continue
        if not all(1 <= num <= 40 for num in combo):
            continue
        if combo_tuple in seen or combo_tuple in historial_set:
            continue
            
        seen.add(combo_tuple)
        valid_results.append(result)
        
    return valid_results

def generate_fallback(
    cantidad: int, 
    historial_set: Set[Tuple[int, ...]],
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> List[Dict]:
    fallback = []
    rng = np.random.default_rng(seed)
    fallback_attempts = 0
    logger = logger or logging.getLogger(__name__)
    
    while len(fallback) < cantidad and fallback_attempts < cantidad * 15:
        candidate = sorted(rng.choice(range(1, 41), size=6, replace=False))
        candidate_tuple = tuple(candidate)
        
        even_count = sum(1 for n in candidate if n % 2 == 0)
        decades = set((n - 1) // 10 for n in candidate)
        decade_counts = [0] * 4
        
        for num in candidate:
            decade_idx = (int(num) - 1) // 10
            if decade_idx < 4:
                decade_counts[decade_idx] += 1
        
        valid_parity = 2 <= even_count <= 4
        valid_decades = len(decades) >= 3
        no_concentration = all(count <= 2 for count in decade_counts)
        
        if (candidate_tuple not in historial_set and 
            valid_parity and valid_decades and no_concentration):
            
            fallback.append({
                "combination": candidate,
                "source": "genetico_fallback",
                "fitness": 0,
                "score": 0.5,
                "parity": even_count,
                "decades": list(decades),
                "freq_sum": 0
            })
            
        fallback_attempts += 1
    
    success_rate = len(fallback) / fallback_attempts if fallback_attempts else 0
    logger.info(
        "🛠️ Generadas %d combinaciones de fallback | Intentos: %d | Tasa éxito: %.1f%%",
        len(fallback),
        fallback_attempts,
        success_rate * 100
    )
        
    return fallback[:cantidad]