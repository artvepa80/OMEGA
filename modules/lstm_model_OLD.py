# Red LSTM para secuencias temporales – OMEGA PRO AI
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler

def prepare_lstm_data(sequences, n_steps=5):
    """
    Prepara datos para entrenamiento LSTM.
    """
    X, y = [], []
    for i in range(len(sequences) - n_steps):
        X.append(sequences[i:i+n_steps])
        y.append(sequences[i+n_steps])
    return np.array(X), np.array(y)

def build_lstm_model(n_steps, n_features, n_units=64, dropout_rate=0.3):
    """
    Construye modelo LSTM multicapa con Dropout.
    """
    model = Sequential()
    model.add(LSTM(n_units, return_sequences=True, input_shape=(n_steps, n_features)))
    model.add(Dropout(dropout_rate))
    model.add(LSTM(n_units))
    model.add(Dropout(dropout_rate))
    model.add(Dense(n_features, activation='linear'))
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm_model(data, n_steps=5, epochs=100, batch_size=16):
    """
    Entrena modelo LSTM con EarlyStopping.
    """
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    X, y = prepare_lstm_data(data_scaled, n_steps)
    
    model = build_lstm_model(n_steps, X.shape[2])
    early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0, callbacks=[early_stop])
    return model, scaler

def predict_next_combination(model, history, scaler, n_steps=5):
    """
    Genera una predicción de la siguiente combinación.
    """
    last_seq = history[-n_steps:]
    last_seq_scaled = scaler.transform(last_seq)
    last_seq_scaled = last_seq_scaled.reshape((1, n_steps, last_seq_scaled.shape[1]))
    
    pred_scaled = model.predict(last_seq_scaled, verbose=0)
    pred = scaler.inverse_transform(pred_scaled)
    return np.round(pred[0]).astype(int).tolist()
def generate_lstm_predictions(data, n_predictions=3):
    """
    Interfaz estándar para el sistema OMEGA.
    Usa el modelo LSTM real para predecir próximas combinaciones.
    Devuelve una lista de combinaciones predichas.
    """
    n_steps = 5
    df = pd.DataFrame(data.values)
    
    # Entrenamiento
    model, scaler = train_lstm_model(df, n_steps=n_steps)
    
    # Predicción de múltiples combinaciones
    predictions = []
    history = df.values.tolist()
    
    for _ in range(n_predictions):
        combo = predict_next_combination(model, history, scaler, n_steps=n_steps)
        predictions.append(combo)
        history.append(combo)  # retroalimentación
        
    return predictions