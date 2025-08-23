# OMEGA PRO AI v10.1 - Configuración Estable
# Modelos problemáticos deshabilitados para estabilidad

# Modelos habilitados (estables)
ENABLE_CONSENSUS = True
ENABLE_CLUSTERING = True  
ENABLE_MONTECARLO = True
ENABLE_LSTM = True
ENABLE_GENETICO = True
ENABLE_APRIORI = True
ENABLE_INVERSE_MINING = True
ENABLE_GHOST_RNG = True

# Modelos deshabilitados (problemáticos)
ENABLE_GBOOST = False      # Feature mismatch errors
ENABLE_PROFILING = False   # Dimension issues  
ENABLE_EVALUADOR = False   # Model compatibility issues
ENABLE_TRANSFORMER = True # Mantener pero con mejor error handling

# Configuración de fallbacks
USE_SMART_FALLBACKS = True
MAX_FALLBACKS_PER_MODEL = 3
FALLBACK_SCORE = 0.5

# Logging optimizado
SUPPRESS_DIMENSION_WARNINGS = True
LOG_LEVEL = "INFO"
