# train_transformer.py – Training script for LotteryTransformer (OMEGA PRO AI v12.0)
import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import logging
from torch.utils.data import Dataset, DataLoader
from lottery_transformer import LotteryTransformer

class LotteryDataset(Dataset):
    def __init__(self, sequences, targets, target_sums):
        self.sequences = np.array(sequences) - 1  # 🔁 Asegurar rango 0–39
        self.targets = np.array(targets) - 1      # 🔁 Asegurar rango 0–39
        self.target_sums = target_sums
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return {
            "numbers": torch.tensor(self.sequences[idx], dtype=torch.long),
            "temporal": torch.zeros((6, 3), dtype=torch.float),  # Placeholder
            "target_numbers": torch.tensor(self.targets[idx], dtype=torch.long),
            "target_sum": torch.tensor(self.target_sums[idx], dtype=torch.float)
        }

class LotteryLoss(nn.Module):
    """Custom loss combining number and sum predictions"""
    def __init__(self, alpha=0.7):
        super().__init__()
        self.num_loss = nn.CrossEntropyLoss()
        self.sum_loss = nn.MSELoss()
        self.alpha = alpha
    
    def forward(self, pred_numbers, pred_sum, target_numbers, target_sum):
        num_loss = self.num_loss(pred_numbers.view(-1, 40), target_numbers.view(-1))
        sum_loss = self.sum_loss(pred_sum.squeeze(), target_sum)
        return self.alpha * num_loss + (1 - self.alpha) * sum_loss

def train_transformer(historial_df, epochs=100, batch_size=32, model_path="model/transformer_model.pt", logger=None):
    """
    Train LotteryTransformer model.
    
    Args:
        historial_df (pd.DataFrame): Historical lottery data
        epochs (int): Number of training epochs
        batch_size (int): Batch size
        model_path (str): Path to save trained model
        logger: Logger instance or callable
    """
    # Configurar logger
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
    elif not callable(getattr(logger, 'info', None)):
        def log_wrapper(msg):
            logger.info(msg)
        logger = log_wrapper

    # Preparar datos
    columnas_bolillas = [col for col in historial_df.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]
    if len(columnas_bolillas) < 6:
        logger("❌ No se encontraron columnas válidas")
        return
    
    historial = historial_df[columnas_bolillas].values.astype(int)
    if len(historial) < 11:
        logger("❌ Historial demasiado corto")
        return
    
    # Crear secuencias
    sequences = []
    targets = []
    target_sums = []
    for i in range(len(historial) - 10):
        seq = historial[i+9]
        target = historial[i+10]
        sequences.append(seq)
        targets.append(target)
        target_sums.append(np.sum(target))
    
    dataset = LotteryDataset(sequences, targets, target_sums)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Inicializar modelo
    model = LotteryTransformer(num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = LotteryLoss(alpha=0.7)
    
    # Entrenamiento
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in loader:
            numbers = batch['numbers'].to(device)
            temporal = batch['temporal'].to(device)
            batch_size = numbers.shape[0]
            seq_len = numbers.shape[1]  # ✅ Definir correctamente
            positions = torch.arange(0, seq_len).unsqueeze(0).repeat(batch_size, 1).to(device)
            target_numbers = batch['target_numbers'].to(device)
            target_sum = batch['target_sum'].to(device)
            
            optimizer.zero_grad()
            pred_numbers, pred_sum = model(numbers, temporal, positions)
            loss = criterion(pred_numbers, pred_sum, target_numbers, target_sum)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(loader)
        logger.info(f"🧠 Época {epoch+1}/{epochs}: Pérdida promedio = {avg_loss:.4f}")
        if avg_loss < 0.05:
            logger.info("✅ Early stopping activado")
            break
    
    # Guardar modelo
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save(model.state_dict(), model_path)
    logger.info(f"✅ Modelo guardado en {model_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    historial_df = pd.read_csv("data/historial_kabala_github.csv")
    train_transformer(historial_df, epochs=100, logger=logger)
