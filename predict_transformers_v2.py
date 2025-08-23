# predict_transformers_v2.py - Versión estable con validación dimensional
import torch
import numpy as np
import argparse
from modules.lottery_transformer import LotteryTransformer
from utils.transformer_data_utils import preparar_datos_transformer
from modules.filters.dynamic_filter import score_dinamico_total

# Argumentos CLI
parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True, help="Ruta al modelo .pt")
parser.add_argument("--data", type=str, required=True, help="CSV con historial")
parser.add_argument("--seq", type=int, default=90, help="Longitud de la secuencia")
args = parser.parse_args()

# Cargar modelo
model = LotteryTransformer()
model.load_state_dict(torch.load(args.model, map_location=torch.device("cpu")))
model.eval()

# Preparar datos
X_seq, X_temp, X_pos, _ = preparar_datos_transformer(args.data, seq_length=args.seq)

# Selección del último batch
entrada_seq = X_seq[-1]
entrada_temp = X_temp[-1]
entrada_pos = X_pos[-1]

# Validación y expansión de dimensiones si es necesario
if entrada_seq.ndim == 2:
    entrada_seq = entrada_seq.unsqueeze(0)
if entrada_temp.ndim == 2:
    entrada_temp = entrada_temp.unsqueeze(0)
if entrada_pos.ndim == 2:
    entrada_pos = entrada_pos.unsqueeze(0)

# Verificación de dimensiones
print(f"✅ Entrada seq shape: {entrada_seq.shape}")
print(f"✅ Entrada temp shape: {entrada_temp.shape}")
print(f"✅ Entrada pos shape: {entrada_pos.shape}")

# Inferencia
with torch.no_grad():
    num_logits, _ = model(entrada_seq, entrada_temp, entrada_pos)
    probs = torch.sigmoid(num_logits[0]).numpy().flatten()
    top6_idx = np.argsort(probs)[-6:]
    top6_numbers = sorted(int(i + 1) for i in top6_idx)

# Evaluar con filtro dinámico y SVI
try:
    resultado = score_dinamico_total(top6_numbers, contexto="transformer", modo="normal")

    if isinstance(resultado, dict):
        resultado_final = sorted(int(x) for x in resultado.get("combinacion", top6_numbers))
        svi = round(resultado.get("svi", 0), 3)
    else:
        # fallback si solo devuelve lista
        resultado_final = sorted(int(x) for x in resultado)
        svi = 0.0

except Exception as e:
    print(f"⚠️ Error en score dinámico: {e}")
    resultado_final = top6_numbers
    svi = 0.0


# Mostrar resultado
print("🎯 Combinación sugerida:", resultado_final)
print("📈 SVI Score:", svi)