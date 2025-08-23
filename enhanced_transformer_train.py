# enhanced_transformer_train.py

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader, random_split
import os
import logging
from modules.lottery_transformer import LotteryTransformer
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('transformer_trainer')

# Crear directorio para modelos si no existe
os.makedirs("modules", exist_ok=True)

class LotteryDataset(Dataset):
    def __init__(self, file_path="data/historial_kabala_github.csv"):
        try:
            df = pd.read_csv(file_path)
            bolilla_cols = [col for col in df.columns if col.lower().strip() in 
                            ['bolilla 1', 'bolilla 2', 'bolilla 3', 'bolilla 4', 'bolilla 5', 'bolilla 6',
                             'b1', 'b2', 'b3', 'b4', 'b5', 'b6']]
            if len(bolilla_cols) != 6:
                raise ValueError(f"❌ No se encontraron 6 columnas de bolillas. Encontradas: {bolilla_cols}")
            df['numeros'] = df[bolilla_cols].astype(int).values.tolist()
            if 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])

            self.data = []
            for _, row in df.iterrows():
                combo = sorted(row['numeros'])
                if len(combo) == 6 and all(1 <= num <= 40 for num in combo):
                    if 'fecha' in df.columns:
                        year = row['fecha'].year
                        month = row['fecha'].month
                        day = row['fecha'].day
                    else:
                        year = 2020
                        month = 1
                        day = 1
                    self.data.append({
                        'numbers': combo,
                        'temporal': [year, month, day],
                        'position': list(range(1, 7))
                    })

            logger.info(f"✅ Cargados {len(self.data)} combinaciones históricas")

        except Exception as e:
            logger.error(f"❌ Error cargando datos: {str(e)}")
            self.data = []

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        temporal_data = [item['temporal']] * 6
        return {
            'numbers': torch.tensor(item['numbers'], dtype=torch.long),
            'temporal': torch.tensor(temporal_data, dtype=torch.float),
            'position': torch.tensor(item['position'], dtype=torch.long)
        }

class LotteryLoss(nn.Module):
    def __init__(self, alpha=0.85):
        super().__init__()
        self.alpha = alpha
        self.num_loss = nn.CrossEntropyLoss()
        self.sum_loss = nn.L1Loss()

    def forward(self, num_logits, sum_pred, target_numbers, target_sum):
        loss_num = self.num_loss(num_logits.view(-1, 40), target_numbers.view(-1) - 1)
        loss_sum = self.sum_loss(sum_pred, target_sum.float())  # No hace falta unsqueeze aquí
        return self.alpha * loss_num + (1 - self.alpha) * loss_sum

def train_model():
    dataset = LotteryDataset()
    if len(dataset) == 0:
        logger.error("No hay datos para entrenar. Saliendo...")
        return

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"🚀 Usando dispositivo: {device}")

    model = LotteryTransformer(
        num_numbers=40,
        d_model=128,
        nhead=4,
        num_layers=3,
        dropout=0.1
    ).to(device)

    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=5
    )
    loss_fn = LotteryLoss(alpha=0.85)

    best_val_loss = float('inf')
    patience_counter = 0
    max_patience = 10

    for epoch in range(100):
        model.train()
        train_loss = 0
        for batch in train_loader:
            numbers = batch['numbers'].to(device)
            temporal = batch['temporal'].to(device)
            position = batch['position'].to(device)

            target_numbers = numbers
            target_sum = numbers.sum(dim=1, keepdim=True)

            num_logits, sum_pred = model(numbers, temporal, position)
            loss = loss_fn(num_logits, sum_pred, target_numbers, target_sum)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                numbers = batch['numbers'].to(device)
                temporal = batch['temporal'].to(device)
                position = batch['position'].to(device)

                target_numbers = numbers
                target_sum = numbers.sum(dim=1, keepdim=True)

                num_logits, sum_pred = model(numbers, temporal, position)
                loss = loss_fn(num_logits, sum_pred, target_numbers, target_sum)

                val_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        logger.info(f"Epoch {epoch+1}/100 | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        scheduler.step(avg_val_loss)

        if avg_val_loss < best_val_loss * 0.999:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), "modules/enhanced_lottery_transformer.pth")
            logger.info(f"💾 Modelo guardado (val loss: {avg_val_loss:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1
            logger.info(f"⏳ No hay mejora significativa ({patience_counter}/{max_patience})")
            if patience_counter >= max_patience:
                logger.info("✅ Early stopping activado por falta de mejora")
                break

        if avg_val_loss < 0.1:
            logger.info("✅ Early stopping activado por pérdida mínima")
            break

if __name__ == "__main__":
    start_time = datetime.now()
    logger.info("🚀 Iniciando entrenamiento del modelo...")
    train_model()
    end_time = datetime.now()
    logger.info(f"🏁 Entrenamiento completado en {end_time - start_time}!")
    logger.info("💾 Modelo guardado en: modules/enhanced_lottery_transformer.pth")