# create_lottery_weights.py
import torch
from modules.lottery_transformer import LotteryTransformer

def save_initial_weights():
    model = LotteryTransformer(
        num_numbers=40,
        d_model=320,
        nhead=10,
        num_layers=8,
        dropout=0.15
    )
    for param in model.parameters():
        if param.dim() > 1:
            torch.nn.init.xavier_uniform_(param)
    torch.save(model.state_dict(), "modules/lottery_transformer_v2.pth")
    print("✅ Pesos iniciales guardados en modules/lottery_transformer_v2.pth")

if __name__ == "__main__":
    save_initial_weights()