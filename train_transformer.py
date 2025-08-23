# train_transformer.py - Entrenamiento mejorado con recomendaciones
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('transformer_trainer')

# Parámetros configurables
WINDOW_SIZE = 10  # Sorteos históricos a considerar
BATCH_SIZE = 32
EPOCHS = 200
D_MODEL = 64  # Dimensión del embedding
NUM_HEADS = 4
FF_DIM = 128
DROPOUT_RATE = 0.35
L2_REG = 0.001
OUTPUT_DIR = "model"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cargar_y_preparar_datos(ruta_datos):
    """Carga y prepara los datos para el modelo Transformer"""
    logger.info("Cargando y preparando datos...")
    
    try:
        df = pd.read_csv(ruta_datos)
        columnas_bolillas = [col for col in df.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]
        
        if len(columnas_bolillas) < 6:
            logger.error("No se encontraron suficientes columnas de bolillas")
            return None, None, None
            
        datos = df[columnas_bolillas].values
        logger.info(f"Datos cargados: {datos.shape[0]} registros")
        return datos, columnas_bolillas
    except Exception as e:
        logger.error(f"Error cargando datos: {str(e)}")
        return None, None

def crear_secuencias(datos):
    """Crea secuencias deslizantes para el entrenamiento"""
    logger.info("Creando secuencias...")
    
    X, y = [], []
    for i in range(len(datos) - WINDOW_SIZE):
        # Ventana de historial
        seq = datos[i:i+WINDOW_SIZE].flatten()
        
        # Siguiente sorteo como etiqueta
        target = datos[i+WINDOW_SIZE]
        
        X.append(seq)
        y.append(target)
    
    return np.array(X), np.array(y)

def codificar_etiquetas(y):
    """Codificación multietiqueta binaria (1-40)"""
    logger.info("Codificando etiquetas...")
    
    y_encoded = np.zeros((len(y), 40))
    for i, combo in enumerate(y):
        for num in combo:
            if 1 <= num <= 40:
                y_encoded[i, int(num)-1] = 1
    return y_encoded

def construir_modelo(input_dim, output_dim):
    """Construye el modelo Transformer con las mejoras recomendadas"""
    logger.info("Construyendo modelo Transformer...")
    
    # Capa de entrada
    inputs = layers.Input(shape=(input_dim,))
    
    # Remodelar: (batch, timesteps, features)
    x = layers.Reshape((WINDOW_SIZE, 6))(inputs)
    
    # Capa de embedding
    x = layers.Dense(D_MODEL)(x)
    
    # Capa Transformer
    x = layers.MultiHeadAttention(
        num_heads=NUM_HEADS, 
        key_dim=D_MODEL//NUM_HEADS
    )(x, x)
    
    # Normalización y FFN
    x = layers.LayerNormalization(epsilon=1e-6)(x)
    x = layers.Dense(FF_DIM, activation="relu")(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Dense(D_MODEL)(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    
    # Pooling y capas densas
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    
    # Capa de salida con regularización L2
    outputs = layers.Dense(
        output_dim, 
        activation="sigmoid",
        kernel_regularizer=tf.keras.regularizers.l2(L2_REG)
    )(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )
    
    logger.info(model.summary())
    return model

def entrenar_modelo():
    """Flujo completo de entrenamiento del modelo Transformer"""
    # 1. Cargar datos
    datos, _ = cargar_y_preparar_datos("data/historial_kabala_github.csv")
    if datos is None:
        return
    
    # 2. Normalización
    scaler = MinMaxScaler()
    datos_normalizados = scaler.fit_transform(datos.reshape(-1, 1)).reshape(datos.shape)
    
    # 3. Preparar secuencias
    X, y = crear_secuencias(datos_normalizados)
    y_encoded = codificar_etiquetas(y)
    
    # 4. Construir modelo
    model = construir_modelo(X.shape[1], y_encoded.shape[1])
    
    # 5. Callbacks
    callbacks = [
        EarlyStopping(patience=15, restore_best_weights=True),
        ModelCheckpoint(
            filepath=os.path.join(OUTPUT_DIR, "transformer_model.keras"),
            save_best_only=True,
            monitor="val_loss"
        )
    ]
    
    # 6. Entrenamiento
    logger.info("Iniciando entrenamiento...")
    history = model.fit(
        X, y_encoded,
        validation_split=0.2,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    # 7. Guardar scaler
    joblib.dump(scaler, os.path.join(OUTPUT_DIR, "transformer_scaler.pkl"))
    logger.info(f"Modelo y scaler guardados en {OUTPUT_DIR}")
    
    # 8. Evaluación final
    loss, acc = model.evaluate(X, y_encoded, verbose=0)
    logger.info(f"Entrenamiento completado | Loss: {loss:.4f} | Accuracy: {acc:.4f}")

if __name__ == "__main__":
    entrenar_modelo()