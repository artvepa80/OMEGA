# train_transformer_pytorch.py
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
import os
import logging
from modules.lottery_transformer import LotteryTransformer
from datetime import datetime

# Configuración básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('transformer_trainer')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1. Clase Dataset personalizada
class LotteryDataset(Dataset):
    def __init__(self, num_samples=1000):
        self.data = []
        # Generar datos de ejemplo (deberías reemplazar esto con tus datos reales)
        for i in range(num_samples):
            numbers = sorted(np.random.choice(range(1, 41), 6, replace=False))
            date = datetime(2020 + i % 4, (i % 12) + 1, (i % 28) + 1)
            self.data.append({
                'numbers': numbers,
                'temporal': [date.year, date.month, date.day],
                'position': list(range(1, 7))
            })
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            'numbers': torch.tensor(item['numbers'], dtype=torch.long),
            'temporal': torch.tensor(item['temporal'], dtype=torch.float),
            'position': torch.tensor(item['position'], dtype=torch.long)
        }

# 2. Función de pérdida personalizada
class LotteryLoss(nn.Module):
    def __init__(self, alpha=0.7):
        super().__init__()
        self.alpha = alpha
        self.num_loss = nn.CrossEntropyLoss()
        self.sum_loss = nn.L1Loss()
    
    def forward(self, num_logits, sum_pred, target_numbers, target_sum):
        loss_num = self.num_loss(num_logits.view(-1, 40), target_numbers.view(-1) - 1)
        loss_sum = self.sum_loss(sum_pred, target_sum.float())
        return self.alpha * loss_num + (1 - self.alpha) * loss_sum

# 3. Entrenamiento principal
def train_model():
    # Configurar modelo
    model = LotteryTransformer(
        num_numbers=40,
        d_model=128,  # Reducido para entrenamiento rápido
        nhead=4,
        num_layers=3,
        dropout=0.1
    ).to(device)
    
    # Dataset y DataLoader
    dataset = LotteryDataset(5000)  # 5000 muestras de ejemplo
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Optimizador y pérdida
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    loss_fn = LotteryLoss(alpha=0.7)
    
    # Entrenamiento
    model.train()
    for epoch in range(10):  # Sólo 10 épocas para prueba
        total_loss = 0
        for batch in loader:
            numbers = batch['numbers'].to(device)
            temporal = batch['temporal'].to(device)
            position = batch['position'].to(device)
            
            # Targets: los números mismos y su suma
            target_numbers = numbers
            target_sum = numbers.sum(dim=1)
            
            # Predicción
            num_logits, sum_pred = model(numbers, temporal, position)
            
            # Calcular pérdida
            loss = loss_fn(num_logits, sum_pred, target_numbers, target_sum)
            
            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        logger.info(f"Epoch {epoch+1}/10 | Loss: {total_loss/len(loader):.4f}")
    
    # Guardar modelo
    torch.save(model.state_dict(), "modules/enhanced_lottery_transformer.pth")
    logger.info("✅ Modelo entrenado y guardado en modules/enhanced_lottery_transformer.pth")

if __name__ == "__main__":
    train_model()