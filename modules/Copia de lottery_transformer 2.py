# modules/lottery_transformer.py
import torch
import torch.nn as nn

class LotteryTransformer(nn.Module):
    def __init__(self, num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1):
        super().__init__()
        self.d_model = d_model

        # 1. Embeddings con dropout
        self.number_embedding = nn.Embedding(num_numbers + 1, d_model, padding_idx=0)
        self.embed_dropout = nn.Dropout(dropout)

        # 2. Codificación posicional entrenable
        self.pos_embedding = nn.Embedding(1000, d_model)

        # 3. Codificación temporal mejorada con normalización estable
        self.temp_encoder = nn.Sequential(
            nn.Linear(3, d_model),
            nn.GELU(),
            nn.LayerNorm(d_model, eps=1e-6)  # eps=1e-6 para mejor estabilidad
        )

        # 4. Pre-normalización con eps=1e-6
        self.pre_norm = nn.LayerNorm(d_model, eps=1e-6)

        # 5. Capas Transformer con normalización mejorada
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dropout=dropout,
            batch_first=True,
            norm_first=True
        )
        # Configuración de eps=1e-6 para todas las capas de normalización
        encoder_layer.norm1 = nn.LayerNorm(d_model, eps=1e-6)
        encoder_layer.norm2 = nn.LayerNorm(d_model, eps=1e-6)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 6. Mecanismo de atención para suma y predicción
        self.attn_pool = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=1,
            dropout=dropout,
            batch_first=True
        )
        self.pool_query = nn.Parameter(torch.randn(1, 1, d_model))

        # 7. Cabezas de predicción con normalización estable
        self.num_head = nn.Sequential(
            nn.LayerNorm(d_model, eps=1e-6),
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, num_numbers)
        )

        self.sum_head = nn.Sequential(
            nn.LayerNorm(d_model, eps=1e-6),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 1)
        )

    def forward(self, numbers, temporal, positions):
        # Validación de dimensiones de entrada
        assert numbers.dim() == 3, (
            f"Input 'numbers' debe tener 3 dimensiones [batch, seq, 6]. "
            f"Recibido: {numbers.dim()} dimensiones (shape={numbers.shape})"
        )
        
        # Manejo de batch vacío
        if numbers.size(0) == 0:
            # Crear outputs vacíos con dimensiones adecuadas
            device = numbers.device
            num_logits = torch.zeros(0, 40, device=device)
            sum_pred = torch.zeros(0, 1, device=device)
            return num_logits, sum_pred

        # Embedding de números (vector de 6 por paso → sumamos embeddings)
        num_emb = self.number_embedding(numbers)        # [batch, seq, 6, d_model]
        num_emb = num_emb.sum(dim=2)                   # [batch, seq, d_model]
        num_emb = self.embed_dropout(num_emb)

        # Embedding posicional
        pos_emb = self.pos_embedding(positions)         # [batch, seq, d_model]

        # Embedding temporal
        temp_emb = self.temp_encoder(temporal)          # [batch, seq, d_model]

        # Suma total + normalización
        x = num_emb + pos_emb + temp_emb
        x = self.pre_norm(x)

        # Paso por Transformer
        context = self.transformer(x)                   # [batch, seq, d_model]

        # Pooling de contexto
        batch_size = context.size(0)
        query = self.pool_query.expand(batch_size, 1, -1)
        pooled_vec, _ = self.attn_pool(query, context, context)
        pooled_vec = pooled_vec.squeeze(1)
        
        # Asegurar que no perdemos la dimensión del batch
        if pooled_vec.dim() == 1:
            pooled_vec = pooled_vec.unsqueeze(0)

        # Predicción
        num_logits = self.num_head(pooled_vec)
        sum_pred = self.sum_head(pooled_vec)

        return num_logits, sum_pred