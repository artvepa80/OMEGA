# Agregar la función fallback_combinations al archivo __init__.py

def wrap_logger(name="default_logger"):
    import logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger

def fallback_combinations(n=5):
    """
    Retorna combinaciones fallback fijas en caso de error en los modelos.
    """
    return [
        [1, 2, 3, 4, 5, 6],
        [7, 8, 9, 10, 11, 12],
        [13, 14, 15, 16, 17, 18],
        [19, 20, 21, 22, 23, 24],
        [25, 26, 27, 28, 29, 30]
    ][:n]
