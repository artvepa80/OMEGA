#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrenamiento / fine-tuning del LotteryTransformer (versión 12.x)

• Carga el histórico CSV → genera tensores (secuencias, temporales, posiciones)
• Permite continuar desde un .pt previo con --fine_tune
• Ajuste: la pérdida ahora alinea batch-size de logits y etiquetas (32 ↔ 192)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np

# ────────────────────────────────────────────────────────────────────────────────
# Ajustes de ruta
ROOT_DIR = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT_DIR / "modules"
sys.path[:0] = [str(ROOT_DIR), str(MODULES_DIR)]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("train_transformer_v12")

# ────────────────────────────────────────────────────────────────────────────────
# Módulos internos
from modules.lottery_transformer import LotteryTransformer
import modules.transformer_data_utils as data_utils

# ────────────────────────────────────────────────────────────────────────────────
# Parámetros globales
NUMBERS_PER_DRAW = 6        # bolillas por sorteo
NUM_UNIQUE_NUMBERS = 40     # configuración de la cabala
SEQ_LEN = 10
BATCH_SIZE = 32
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ════════════════════════════════════════════════════════════════════════════════
# Conjunto de datos
def build_dataset(historial_csv: Path):
    df = pd.read_csv(historial_csv)
    # genera X_seq (B, 10, 6), X_temp (B, 10, 3), X_pos (B, 10)
    X_seq, X_temp, X_pos, _ = data_utils.prepare_advanced_transformer_data(
        df, seq_length=SEQ_LEN, for_training=True
    )

    # targets (el último paso de cada secuencia)
    y_numbers = torch.tensor(X_seq[:, -1, :], dtype=torch.long)       # [B, 6]
    y_sum = y_numbers.sum(dim=1, keepdim=True).float()               # [B, 1]

    dataset = TensorDataset(
        X_seq.float(), X_temp.float(), X_pos.long(), y_numbers, y_sum
    )
    return dataset


# ════════════════════════════════════════════════════════════════════════════════
# Pérdida compuesta
class LotteryCriterion(nn.Module):
    """
    Combina:
      • cross-entropy para cada bolilla (6 por sorteo)
      • L1 para la suma de las bolillas
    PARCHE 2025-08-05:
      Alinea tamaños expandiendo logits → [B*6, 40] para emparejar 6 etiquetas/sorteo
    """

    def __init__(self, num_numbers=NUM_UNIQUE_NUMBERS, lambda_sum=0.1):
        super().__init__()
        self.num_loss = nn.CrossEntropyLoss()
        self.sum_loss = nn.L1Loss()
        self.num_numbers = num_numbers
        self.lambda_sum = lambda_sum

    def forward(self, pred_numbers, pred_sum, target_numbers, target_sum):
        """
        Args
        ----
        pred_numbers : Tensor [B, 40]          Logits por número
        pred_sum     : Tensor [B, 1]           Regressión de la suma
        target_numbers : Tensor [B, 6]         Etiquetas (6 ints 1-40)
        target_sum     : Tensor [B, 1]         Suma real
        """

        B, N = target_numbers.shape  # N debe ser 6
        if pred_numbers.shape != (B, self.num_numbers):
            raise ValueError(
                f"Logits esperados [B,{self.num_numbers}], recibidos {pred_numbers.shape}"
            )

        # ── PARCHE ────────────────────────────────────────────────────────────
        # Expandir logits  →  [B, 1, 40] → repetir 6 veces → [B,6,40] → [B*6,40]
        logits_expanded = (
            pred_numbers.unsqueeze(1)      # [B,1,40]
            .repeat(1, N, 1)               # [B,6,40]
            .view(-1, self.num_numbers)    # [B*6,40]  (ej. 32*6 = 192)
        )

        num_loss = self.num_loss(
            logits_expanded,
            target_numbers.view(-1)        # [B*6]
        )
        # ─────────────────────────────────────────────────────────────────────

        sum_loss = self.sum_loss(pred_sum, target_sum)
        return num_loss + self.lambda_sum * sum_loss


# ════════════════════════════════════════════════════════════════════════════════
# Entrenamiento
def train_transformer(
    historial_path: Path,
    epochs: int = 100,
    fine_tune: bool = False,
    dry_run: bool = False,
):
    log.info("Device: %s", DEVICE)

    # Datos
    dataset = build_dataset(historial_path)
    val_split = 0.2
    val_size = int(len(dataset) * val_split)
    train_size = len(dataset) - val_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    log.info("✅ Datos: %d train, %d val.", train_size, val_size)

    # Modelo
    model = LotteryTransformer(
        num_numbers=NUM_UNIQUE_NUMBERS,
        d_model=128,
        nhead=4,
        num_layers=3,
        dropout=0.1,
    ).to(DEVICE)

    model_path = ROOT_DIR / "model" / "transformer_model.pt"
    if fine_tune and model_path.exists():
        log.info("🔄 Fine-tuning desde %s.", model_path)
        state = torch.load(model_path, map_location=DEVICE)
        model.load_state_dict(state, strict=False)

    criterion = LotteryCriterion().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # Entreno
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for X_seq, X_temp, X_pos, y_nums, y_sum in train_loader:
            X_seq, X_temp, X_pos = X_seq.to(DEVICE), X_temp.to(DEVICE), X_pos.to(DEVICE)
            y_nums, y_sum = y_nums.to(DEVICE), y_sum.to(DEVICE)

            optimizer.zero_grad()
            pred_logits, pred_sum = model(X_seq.long(), X_temp, X_pos)
            loss = criterion(pred_logits, pred_sum, y_nums, y_sum)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        val_loss = 0.0
        model.eval()
        with torch.no_grad():
            for X_seq, X_temp, X_pos, y_nums, y_sum in val_loader:
                X_seq, X_temp, X_pos = X_seq.to(DEVICE), X_temp.to(DEVICE), X_pos.to(DEVICE)
                y_nums, y_sum = y_nums.to(DEVICE), y_sum.to(DEVICE)
                pred_logits, pred_sum = model(X_seq.long(), X_temp, X_pos)
                val_loss += criterion(pred_logits, pred_sum, y_nums, y_sum).item()

        log.info(
            "Epoch %3d/%d │ train_loss=%.4f │ val_loss=%.4f",
            epoch,
            epochs,
            total_loss / len(train_loader),
            val_loss / len(val_loader),
        )

        # Early-stop / checkpoints
        if dry_run and epoch == 1:
            break

    # Guardar
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = ROOT_DIR / "model" / f"transformer_model_finetuned_{ts}.pt"
    torch.save(model.state_dict(), out_path)
    log.info("💾 Modelo guardado en %s", out_path)


# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Entrenar / Fine-tune LotteryTransformer v12")
    parser.add_argument(
        "--historial",
        default=str(ROOT_DIR / "data" / "historial_kabala_github.csv"),
        help="CSV de historial",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--fine_tune", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    train_transformer(
        Path(args.historial),
        epochs=args.epochs,
        fine_tune=args.fine_tune,
        dry_run=args.dry_run,
    )
