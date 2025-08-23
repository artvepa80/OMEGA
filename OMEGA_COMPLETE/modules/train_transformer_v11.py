# train_transformer_v11.py – Entrenamiento optimizado para LotteryTransformer (OMEGA PRO AI v12.1) – Versión con syntax fixes y try-except global

import sys
import os
import logging
import torch  # Para chequeo de version

# Configurar logging AL INICIO
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("train_log.txt"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Path robusto: Calcula root normalizado (maneja macOS paths)
root_dir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.insert(0, root_dir)  # Prioriza root
logger.info(f"Root dir calculado: {root_dir}")
logger.info(f"sys.path updated: {sys.path[:3]}...")  # Log primeros 3 para depurar

# Chequeo de directorios: Verifica si utils/ existe en root
utils_path = os.path.join(root_dir, 'utils')
if not os.path.exists(utils_path):
    logger.error(f"❌ Directorio 'utils/' no encontrado en root: {root_dir}. Verifica estructura del proyecto.")
    sys.exit(1)
logger.info(f"✅ utils/ encontrado en {utils_path}.")

# Chequeo de import con try-except
try:
    from utils.transformer_data_utils import prepare_advanced_transformer_data
    logger.info("✅ Import de utils exitoso.")
except ModuleNotFoundError as e:
    logger.error(f"❌ Falló import: {str(e)}. Verifica: 1) transformer_data_utils.py en utils/, 2) Ejecuta desde root, 3) __init__.py en utils/ (vacío OK). Alternativa: Usa import absoluto 'from /absolute/path/utils...'")
    sys.exit(1)

import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from modules.lottery_transformer import LotteryTransformer

class LotteryDataset(Dataset):
    def __init__(self, X_seq, X_temp, X_pos, targets, target_sums):
        self.X_seq = torch.tensor(X_seq, dtype=torch.long) - 1 if not isinstance(X_seq, torch.Tensor) else (X_seq - 1)  # Rango 0-39
        self.X_temp = torch.tensor(X_temp, dtype=torch.float) if not isinstance(X_temp, torch.Tensor) else X_temp
        self.X_pos = torch.tensor(X_pos, dtype=torch.long) if not isinstance(X_pos, torch.Tensor) else X_pos
        self.targets = torch.tensor(targets, dtype=torch.long) - 1 if not isinstance(targets, torch.Tensor) else (targets - 1)  # Rango 0-39
        self.target_sums = torch.tensor(target_sums, dtype=torch.float) if not isinstance(target_sums, torch.Tensor) else target_sums
    
    def __len__(self):
        return len(self.X_seq)
    
    def __getitem__(self, idx):
        return {
            "numbers": self.X_seq[idx],
            "temporal": self.X_temp[idx],
            "positions": self.X_pos[idx],
            "target_numbers": self.targets[idx],
            "target_sum": self.target_sums[idx]
        }

class LotteryLoss(nn.Module):
    def __init__(self, alpha=0.7):
        super().__init__()
        self.num_loss = nn.CrossEntropyLoss(ignore_index=-1)  # Ignora si padding
        self.sum_loss = nn.MSELoss()
        self.alpha = alpha
    
    def forward(self, pred_numbers, pred_sum, target_numbers, target_sum):
        num_loss = self.num_loss(pred_numbers.view(-1, 40), target_numbers.view(-1))
        sum_loss = self.sum_loss(pred_sum.squeeze(), target_sum)
        return self.alpha * num_loss + (1 - self.alpha) * sum_loss

def train_transformer(historial_path: str, epochs: int = 100, batch_size: int = 32, lr: float = 0.001, seq_length: int = 10, val_split: float = 0.2, model_path: str = "model/transformer_model.pt", fine_tune: bool = True, dry_run: bool = False, force_cpu: bool = False):
    # Chequeo de archivo
    if not os.path.exists(historial_path):
        logger.error(f"❌ Archivo no encontrado: {historial_path}")
        return
    
    # Cargar datos
    df = pd.read_csv(historial_path)
    # Chequeo de 'fecha': si no existe, crea ficticia
    if 'fecha' not in df.columns:
        logger.warning("⚠️ No hay columna 'fecha'; creando ficticia.")
        df['fecha'] = pd.date_range(start='2000-01-01', periods=len(df), freq='D')
    
    # Manejo de NaNs en bolillas: Fill con mode
    columnas_bolillas = [c for c in df.columns if 'Bolilla' in c or c in [str(i) for i in range(1,7)]]
    for col in columnas_bolillas:
        mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else 1
        df[col] = df[col].fillna(mode_val)
    
    X_seq, X_temp, X_pos, _ = prepare_advanced_transformer_data(df, seq_length=seq_length, for_training=True)
    
    if len(X_seq) < 2:
        logger.error("❌ Historial demasiado corto para entrenamiento.")
        return
    
    logger.info(f"Shapes: X_seq {X_seq.shape}, X_temp {X_temp.shape}, X_pos {X_pos.shape}")
    
    # Targets: shift para predecir siguiente (X_seq[i] = sorteos 0 a 9, target = sorteo 10)
    targets = X_seq[:, -1, :]  # Último de cada seq como target nums
    target_sums = torch.sum(targets, dim=1)  # FIX: Usa torch.sum
    
    # Input: secuencias sin el último (para predecir)
    input_seq = X_seq[:, :-1, :]  # (n, seq-1, 6)
    input_temp = X_temp[:, :-1, :]  # Ajusta temporal/pos
    input_pos = X_pos[:, :-1]
    
    # Split train/val
    split_idx = int(len(input_seq) * (1 - val_split))
    train_seq, val_seq = input_seq[:split_idx], input_seq[split_idx:]
    train_temp, val_temp = input_temp[:split_idx], input_temp[split_idx:]
    train_pos, val_pos = input_pos[:split_idx], input_pos[split_idx:]
    train_targets, val_targets = targets[:split_idx], targets[split_idx:]
    train_sums, val_sums = target_sums[:split_idx], target_sums[split_idx:]
    
    train_dataset = LotteryDataset(train_seq, train_temp, train_pos, train_targets, train_sums)
    val_dataset = LotteryDataset(val_seq, val_temp, val_pos, val_targets, val_sums)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    logger.info(f"✅ Datos: {len(train_loader.dataset)} train, {len(val_loader.dataset)} val.")
    
    # Modelo
    model = LotteryTransformer(num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1)
    if fine_tune and os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        logger.info(f"🔄 Fine-tuning desde {model_path}.")
    
    device = torch.device("cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu"))
    logger.info(f"Device: {device}")
    model.to(device)
    
    # Chequeo de Torch version para scheduler compat
    torch_version = torch.__version__
    logger.info(f"Torch version: {torch_version}")
    verbose = True if float(torch_version.split('.')[0]) >= 1 and float(torch_version.split('.')[1]) >= 2 else False
    if not verbose:
        logger.warning("⚠️ Torch <1.2 detectado; ignorando 'verbose' en scheduler.")
    
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    
    best_val_loss = float('inf')
    loss_history = []  # Para guardar losses en CSV
    model.train()
    for epoch in range(epochs):
        train_loss = 0.0
        for batch in train_loader:
            numbers = batch['numbers'].to(device)
            temporal = batch['temporal'].to(device)
            positions = batch['positions'].to(device)
            target_numbers = batch['target_numbers'].to(device)
            target_sum = batch['target_sum'].to(device)
            
            optimizer.zero_grad()
            pred_numbers, pred_sum = model(numbers, temporal, positions)
            loss = criterion(pred_numbers, pred_sum, target_numbers, target_sum)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validación
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                numbers = batch['numbers'].to(device)
                temporal = batch['temporal'].to(device)
                positions = batch['positions'].to(device)
                target_numbers = batch['target_numbers'].to(device)
                target_sum = batch['target_sum'].to(device)
                
                pred_numbers, pred_sum = model(numbers, temporal, positions)
                loss = criterion(pred_numbers, pred_sum, target_numbers, target_sum)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader) if len(val_loader) > 0 else float('inf')
        
        # Step scheduler y log LR manual (ya que no verbose)
        prev_lr = optimizer.param_groups[0]['lr']
        scheduler.step(avg_val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        if current_lr < prev_lr:
            logger.info(f"📉 LR reducido de {prev_lr:.6f} a {current_lr:.6f}")
        
        logger.info(f"🧠 Época {epoch+1}/{epochs}: Train Loss={avg_train_loss:.4f}, Val Loss={avg_val_loss:.4f}, LR={current_lr:.6f}")
        loss_history.append({'epoch': epoch+1, 'train_loss': avg_train_loss, 'val_loss': avg_val_loss})
        
        # Checkpoint por época (para resuming)
        if not dry_run:
            epoch_path = f"{model_path}.epoch{epoch+1}"
            torch.save(model.state_dict(), epoch_path)
            logger.info(f"✅ Save por época en {epoch_path}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            if not dry_run:
                torch.save(model.state_dict(), model_path)
                logger.info(f"✅ Mejor modelo guardado en {model_path}")
            else:
                logger.info("✅ Dry run: Mejor modelo no guardado.")
        
        if avg_val_loss < 0.05:
            logger.info("✅ Early stopping por low loss.")
            break
        model.train()
    
    # Guardar history de loss en CSV
    pd.DataFrame(loss_history).to_csv('loss_history.csv', index=False)
    logger.info("✅ Loss history guardada en loss_history.csv")
    
    logger.info("✅ Entrenamiento completado.")

if __name__ == "__main__":
    try:
        historial_path = "data/historial_kabala_github.csv"  # Reemplaza con tu path real
        train_transformer(historial_path, epochs=100, fine_tune=True, dry_run=False, force_cpu=False)
    except Exception as e:
        logger.error(f"❌ Error en main: {str(e)}", exc_info=True)  # Log full traceback