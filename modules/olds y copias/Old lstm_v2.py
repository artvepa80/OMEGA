# lstm_v2.py – LSTM profundo con output de 6 bolillas únicas y variabilidad controlada

import numpy as np
import pandas as pd
import random
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping

def generar_combinaciones_lstm_v2(data_path="data/historial_kabala_github.csv", cantidad=30, posicional=False):
    # 1. Cargar y limpiar datos
    df = pd.read_csv(data_path)
    cols = [c for c in df.columns if "bolilla" in c.lower()]
    df = df[cols].dropna()

    if posicional:
        data = df.values.astype(int)  # Orden exacto de bolillas
    else:
        data = np.sort(df.values.astype(int), axis=1)  # Ordenadas ascendentemente

    # 2. Normalizar
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    # 3. Preparar secuencias
    X, y = [], []
    look_back = 10
    for i in range(len(scaled_data) - look_back):
        X.append(scaled_data[i:i+look_back])
        y.append(scaled_data[i+look_back])
    X, y = np.array(X), np.array(y)

    # 4. Modelo LSTM profundo
    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dropout(0.2))
    model.add(BatchNormalization())
    model.add(LSTM(128))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation="relu"))
    model.add(Dense(6))  # salida: 6 bolillas

    model.compile(optimizer="adam", loss="mse")
    early_stop = EarlyStopping(monitor="loss", patience=10, restore_best_weights=True)
    model.fit(X, y, epochs=100, batch_size=16, verbose=0, callbacks=[early_stop])

    # 5. Predecir múltiples combinaciones
    pred_combinaciones = []
    last_seq = scaled_data[-look_back:]

    intentos = 0
    max_intentos = cantidad * 5

    while len(pred_combinaciones) < cantidad and intentos < max_intentos:
        pred_scaled = model.predict(np.expand_dims(last_seq, axis=0), verbose=0)[0]
        pred = scaler.inverse_transform([pred_scaled])[0]
        pred = [int(round(x)) for x in pred]
        pred = [min(max(x, 1), 40) for x in pred]  # Limitar entre 1 y 40

        # Extraer 6 únicos válidos
        pred_set = set()
        for _ in range(20):
            if len(pred_set) == 6:
                break
            pred_set.add(random.choice(pred))

        if len(pred_set) == 6:
            combo = sorted(list(pred_set))
            if combo not in pred_combinaciones:
                pred_combinaciones.append(combo)

        intentos += 1

    return pred_combinaciones