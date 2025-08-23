# transformers_model.py - Modelo Transformer para predicción de combinaciones en OMEGA PRO AI

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LayerNormalization, MultiHeadAttention, Dropout, Add
from sklearn.preprocessing import MinMaxScaler

def build_transformer_block(embed_dim, num_heads, ff_dim, rate=0.1):
    inputs = Input(shape=(None, embed_dim))
    attention_output = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)(inputs, inputs)
    attention_output = Dropout(rate)(attention_output)
    out1 = LayerNormalization(epsilon=1e-6)(Add()([inputs, attention_output]))
    
    ffn_output = Dense(ff_dim, activation='relu')(out1)
    ffn_output = Dense(embed_dim)(ffn_output)
    ffn_output = Dropout(rate)(ffn_output)
    outputs = LayerNormalization(epsilon=1e-6)(Add()([out1, ffn_output]))

    return Model(inputs=inputs, outputs=outputs)

def build_transformer_model(input_shape, embed_dim=64, num_heads=4, ff_dim=128, dropout_rate=0.1):
    inputs = Input(shape=input_shape)
    transformer_block = build_transformer_block(embed_dim, num_heads, ff_dim, dropout_rate)
    x = transformer_block(inputs)
    x = Dense(64, activation='relu')(x)
    x = Dropout(dropout_rate)(x)
    outputs = Dense(input_shape[-1], activation='linear')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mse')
    return model

def prepare_transformer_data(sequences, n_steps=5):
    """
    Convierte una lista de combinaciones en formato para Transformer.
    """
    X, y = [], []
    for i in range(len(sequences) - n_steps):
        X.append(sequences[i:i+n_steps])
        y.append(sequences[i+n_steps])
    return np.array(X), np.array(y)

def train_transformer_model(data, n_steps=5, epochs=80, batch_size=16):
    """
    Entrena el modelo Transformer para predecir la siguiente combinación.
    """
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    X, y = prepare_transformer_data(data_scaled, n_steps)
    X = X.astype(np.float32)
    y = y.astype(np.float32)

    model = build_transformer_model(input_shape=(n_steps, X.shape[2]))
    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
    return model, scaler

def predict_with_transformer(model, history, scaler, n_steps=5):
    """
    Realiza una predicción basada en el historial.
    """
    input_seq = history[-n_steps:]
    input_scaled = scaler.transform(input_seq)
    input_scaled = np.expand_dims(input_scaled, axis=0)
    pred_scaled = model.predict(input_scaled, verbose=0)
    pred = scaler.inverse_transform(pred_scaled)
    return np.round(pred[0]).astype(int).tolist()
