# enhanced_inference.py

import torch
import pandas as pd
from modules.lottery_transformer import LotteryTransformer

MODEL_PATH = "modules/enhanced_lottery_transformer.pth"
DATA_PATH = "data/historial_kabala_github.csv"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def generar_combinaciones_transformer(cantidad=5):
    # Cargar modelo
    model = LotteryTransformer(
        num_numbers=40,
        d_model=128,
        nhead=4,
        num_layers=3,
        dropout=0.1
    ).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    # Cargar datos
    df = pd.read_csv(DATA_PATH)
    bolilla_cols = [col for col in df.columns if col.lower().strip() in 
        ['bolilla 1', 'bolilla 2', 'bolilla 3', 'bolilla 4', 'bolilla 5', 'bolilla 6',
         '1', '2', '3', '4', '5', '6']]

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        last_fecha = df.iloc[-1]['fecha']
    else:
        from datetime import datetime
        last_fecha = datetime.today()

    df['numeros'] = df[bolilla_cols].astype(int).values.tolist()
    last = df.iloc[-1]
    
    # Preparar input
    numbers = torch.tensor([last['numeros']], dtype=torch.long).to(DEVICE)
    temporal = torch.tensor([[[last_fecha.year, last_fecha.month, last_fecha.day]] * 6], dtype=torch.float).to(DEVICE)
    positions = torch.tensor([[1, 2, 3, 4, 5, 6]], dtype=torch.long).to(DEVICE)

    # Inferencia
    with torch.no_grad():
        num_logits, sum_pred = model(numbers, temporal, positions)  # (1, 6, 40), (1)
        probs = torch.softmax(num_logits, dim=-1)  # (1, 6, 40)

        combinaciones = []
        for _ in range(cantidad):
            sampled = torch.multinomial(probs[0], num_samples=1).squeeze(-1) + 1  # Índices → números 1–40
            combo = sorted(sampled.tolist())
            combinaciones.append({
                "combination": combo,
                "score": 1.0,
                "source": "transformer",
                "sum_pred": round(sum_pred.item(), 2)
            })

    return combinaciones