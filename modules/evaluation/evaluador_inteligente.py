# OMEGA_PRO_AI_v10.1/modules/evaluation/evaluador_inteligente.py – Versión Corregida

from pathlib import Path
from typing import Dict, List, Union, Optional
import numpy as np
import logging

# Módulos internos
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
from modules.profiling.jackpot_profiler import JackpotProfiler

# Configuración avanzada de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('EvaluadorInteligente')

class EvaluadorInteligente:
    PERFILES_VIABLES = {"B", "C"}
    UMBRAL_CONFIANZA = 60.0
    NUMEROS_COMBINACION = 6
    MIN_NUMERO = 1
    MAX_NUMERO = 40
    MAX_CONSECUTIVOS = 3  # Máximo de números consecutivos permitidos

    def __init__(
        self, 
        model_path: str = "models/gboost_model.pkl", 
        profiler_config: Optional[Dict] = None,
        verbose: bool = True
    ):
        """
        Inicializa el evaluador con modelo y perfilador configurados.
        
        Args:
            model_path: Ruta al modelo serializado
            profiler_config: Configuración para el JackpotProfiler
            verbose: Habilita mensajes de depuración
        """
        self.verbose = verbose
        self.model_path = Path(model_path)
        self.modelo = self._cargar_modelo()
        
        # Configuración dinámica para el profiler
        self.profiler = JackpotProfiler(**(profiler_config or {}))
        logger.info("✅ Profiler de jackpot inicializado")

    def _cargar_modelo(self) -> GBoostJackpotClassifier:
        """Carga el modelo con manejo de errores robusto"""
        if not self.model_path.exists():
            logger.critical(f"❌ Archivo de modelo no encontrado: {self.model_path}")
            raise FileNotFoundError(f"Archivo de modelo no encontrado: {self.model_path}")
            
        modelo = GBoostJackpotClassifier(model_path=str(self.model_path))
        try:
            modelo.load(str(self.model_path))
            logger.info(f"✅ Modelo GBoost cargado exitosamente")
            return modelo
        except Exception as e:
            logger.exception("❌ Error crítico al cargar modelo", exc_info=True)
            raise RuntimeError(f"Error al cargar modelo: {str(e)}") from e

    def _validar_combinacion(self, combinacion: List[int]) -> None:
        """Valida estrictamente la combinación según reglas del juego"""
        if not isinstance(combinacion, (list, np.ndarray)):
            raise TypeError("La combinación debe ser una lista o array")
            
        if len(combinacion) != self.NUMEROS_COMBINACION:
            raise ValueError(
                f"La combinación debe tener exactamente {self.NUMEROS_COMBINACION} números. "
                f"Recibidos: {len(combinacion)}"
            )
            
        # Normalización a enteros y validación de rango
        try:
            combinacion_enteros = [int(n) for n in combinacion]
        except (ValueError, TypeError) as e:
            raise TypeError("Todos los valores deben ser numéricos") from e
            
        # Validación estricta de rango 1-40
        numeros_invalidos = [n for n in combinacion_enteros 
                            if n < self.MIN_NUMERO or n > self.MAX_NUMERO]
        
        if numeros_invalidos:
            raise ValueError(
                f"Números fuera de rango permitido ({self.MIN_NUMERO}-{self.MAX_NUMERO}): "
                f"{numeros_invalidos}"
            )
            
        # Validación de secuencias consecutivas
        combinacion_ordenada = sorted(combinacion_enteros)
        consecutivos = 1
        max_consecutivos = 1
        
        for i in range(1, len(combinacion_ordenada)):
            if combinacion_ordenada[i] == combinacion_ordenada[i-1] + 1:
                consecutivos += 1
                max_consecutivos = max(max_consecutivos, consecutivos)
            else:
                consecutivos = 1
        
        if max_consecutivos > self.MAX_CONSECUTIVOS:
            raise ValueError(
                f"Combinación inválida: Demasiados números consecutivos ({max_consecutivos} seguidos)"
            )

    def evaluate(self, combinacion: Union[List[int], np.ndarray]) -> Dict[str, Union[str, List[float], float]]:
        """
        Evalúa una combinación numérica y devuelve su perfil predictivo.
        
        Args:
            combinacion: Secuencia numérica a evaluar (6 números entre 1-40)
            
        Returns:
            Dict con resultados de evaluación
        """
        # Validación estricta de entrada
        self._validar_combinacion(combinacion)
            
        # Predicción del modelo
        proba = self.modelo.predict_proba([combinacion])[0]
        perfil = self.profiler.predecir_perfil(combinacion)
        score_confianza = round(max(proba) * 100, 2)
        
        # Construcción de resultados
        recomendacion = self._generar_recomendacion(perfil, score_confianza)
        resultado = {
            "combinacion": combinacion,
            "perfil": perfil,
            "probabilidades": [round(p * 100, 2) for p in proba],
            "confianza": score_confianza,
            "recomendacion": recomendacion,
            "es_viable": recomendacion == "Viable"
        }
        
        # Logging de resultados
        if self.verbose:
            self._log_resultados(combinacion, perfil, proba, score_confianza, recomendacion)
            
        # Log especial para combinaciones recomendadas
        if resultado["es_viable"]:
            logger.info(f"🟢 Combinación RECOMENDADA: {combinacion} "
                         f"(Perfil: {perfil}, Confianza: {score_confianza}%)")
            
        return resultado

    def _generar_recomendacion(self, perfil: str, confianza: float) -> str:
        """Genera recomendación basada en reglas de negocio"""
        return "Viable" if (
            perfil in self.PERFILES_VIABLES and 
            confianza >= self.UMBRAL_CONFIANZA
        ) else "Bajo potencial"

    def _log_resultados(self, 
                       combinacion: list, 
                       perfil: str, 
                       proba: np.ndarray, 
                       confianza: float, 
                       recomendacion: str):
        """Registra resultados formateados en el logger"""
        labels = ["A", "B", "C"]
        probs_str = " | ".join([f"{l}={p:.2f}%" for l, p in zip(labels, proba*100)])
        
        # Usamos logger en lugar de print para integración con sistema de logs
        logger.info(f"\n🔍 Evaluando combinación: {combinacion}")
        logger.info(f"📌 Perfil detectado: {perfil}")
        logger.info(f"📊 Distribución: {probs_str}")
        logger.info(f"🧠 Nivel de confianza: {confianza:.2f}%")
        
        # Mensaje especial para recomendaciones
        if recomendacion == "Viable":
            logger.info(f"💡 Recomendación: ✅ {recomendacion}")
        else:
            logger.warning(f"💡 Recomendación: ⚠️ {recomendacion}")
        
        logger.info("─" * 50)

# Ejemplo de uso mejorado
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sistema de Evaluación de Jugadas - Jackpot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-c", "--combinaciones", 
        nargs="+", 
        type=int,
        action="append",
        help="Combinaciones a evaluar (6 números entre 1-40)",
        metavar=("N1", "N2", "N3", "N4", "N5", "N6")
    )
    parser.add_argument(
        "--model", 
        default="models/gboost_model.pkl",
        help="Ruta al modelo GBoost"
    )
    parser.add_argument(
        "-q", "--quiet", 
        action="store_true",
        help="Modo silencioso (sin logging detallado)"
    )
    parser.add_argument(
        "--max-consecutivos",
        type=int,
        default=3,
        help="Máximo de números consecutivos permitidos"
    )
    args = parser.parse_args()
    
    # Configuración inicial
    print("\n" + "="*50)
    print("  SISTEMA DE EVALUACIÓN DE JUGADAS - JACKPOT  ")
    print("="*50)
    
    evaluador = EvaluadorInteligente(
        model_path=args.model,
        profiler_config={"max_consecutivos": args.max_consecutivos},
        verbose=not args.quiet
    )
    
    # Combinaciones de prueba con validación mejorada
    combinaciones = args.combinaciones or [
        [5, 12, 23, 34, 39, 40],    # Válida (límites)
        [1, 2, 3, 4, 5, 6],          # Inválida (6 consecutivos)
        [1, 2, 3, 10, 11, 12],       # Inválida (dos grupos de 3 consecutivos)
        [5, 10, 15, 20, 25, 30],     # Válida (sin consecutivos)
        [7, 8, 9, 20, 21, 22],       # Inválida (dos grupos de 3 consecutivos)
        [1, 3, 5, 7, 9, 11],         # Válida (sin consecutivos)
        [0, 10, 20, 30, 40, 41],     # Inválida (fuera de rango)
        [1, 2, 3, 4, 5]              # Inválida (solo 5 números)
    ]
    
    for i, comb in enumerate(combinaciones):
        try:
            logger.info(f"\n▶️ Procesando combinación #{i+1}: {comb}")
            resultado = evaluador.evaluate(comb)
            logger.info(f"Resultado: {'Viable' if resultado['es_viable'] else 'No viable'}")
        except Exception as e:
            logger.error(f"❌ Error en evaluación: {str(e)}")
    
    print("\n" + "="*50)
    print("  EVALUACIÓN COMPLETADA  ")
    print("="*50)