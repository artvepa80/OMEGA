# 🚀 OMEGA Akash Network Setup Guide

## Prerrequisitos

### 1. Instalar Akash CLI

```bash
# Para macOS
curl -sSfL https://raw.githubusercontent.com/akash-network/akash/main/install.sh | sh
export PATH="$PATH:./bin"

# O usando Homebrew
brew tap akash-network/tap
brew install akash-network/tap/akash
```

### 2. Crear Wallet de Akash

```bash
# Crear nueva wallet
akash keys add omega-wallet

# Guardar la información de recuperación (IMPORTANTE!)
# Anota tu seed phrase en un lugar seguro

# Ver dirección de la wallet
akash keys show omega-wallet -a
```

### 3. Obtener AKT Tokens

Necesitas tokens AKT para pagar el deployment:

**Opción A - Comprar AKT:**
- Exchange: Gate.io, Osmosis, Kraken
- Cantidad recomendada: 100-500 AKT

**Opción B - Testnet (para pruebas):**
```bash
# Configurar testnet
export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/testnet"
export AKASH_VERSION="$(curl -s https://api.github.com/repos/akash-network/akash/releases/latest | jq -r '.tag_name')"
export AKASH_CHAIN_ID="$(curl -s "$AKASH_NET/chain-id.txt")"
export AKASH_NODE="$(curl -s "$AKASH_NET/rpc-nodes.txt" | head -1)"

# Solicitar tokens de testnet
curl -X POST \
  "https://faucet.testnet-02.aksh.pw/faucet" \
  -H "Content-Type: application/json" \
  -d "{\"address\":\"$(akash keys show omega-wallet -a)\"}"
```

### 4. Verificar Balance

```bash
# Verificar balance
akash query bank balances $(akash keys show omega-wallet -a) \
  --node https://rpc.akash.forbole.com:443
```

### 5. Crear Certificado

```bash
akash tx cert create client \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443 \
  --chain-id akashnet-2 \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.15
```

## Deployment de OMEGA

Una vez configurado todo lo anterior:

```bash
# 1. Ir al directorio de OMEGA
cd /Users/user/Documents/OMEGA_PRO_AI_v10.1/OMEGA_COMPLETE

# 2. Ejecutar deployment
./deploy-akash.sh

# O deployment manual paso a paso:

# 2a. Crear deployment
akash tx deployment create deploy/akash-deployment.yaml \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443 \
  --chain-id akashnet-2 \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.15 \
  --broadcast-mode block \
  -y

# 2b. Ver bids (esperar 30 segundos)
akash query market bid list \
  --owner $(akash keys show omega-wallet -a) \
  --dseq <DSEQ_FROM_PREVIOUS_COMMAND> \
  --node https://rpc.akash.forbole.com:443

# 2c. Crear lease con el mejor bid
akash tx market lease create \
  --dseq <DSEQ> \
  --provider <PROVIDER_ADDRESS> \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443 \
  --chain-id akashnet-2 \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.15 \
  --broadcast-mode block \
  -y

# 2d. Enviar manifest
akash provider send-manifest deploy/akash-deployment.yaml \
  --dseq <DSEQ> \
  --provider <PROVIDER> \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443
```

## Monitoreo

```bash
# Ver status del deployment
akash provider lease-status \
  --dseq <DSEQ> \
  --provider <PROVIDER> \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443

# Ver logs
akash provider service-logs \
  --dseq <DSEQ> \
  --provider <PROVIDER> \
  --service omega-gpu \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443
```

## URLs de Acceso

Una vez desplegado, obtendrás URLs como:
- **OMEGA API**: `https://xxx.provider.akash.pro:8000`
- **Metrics**: `https://xxx.provider.akash.pro:8080`

## Testing

```bash
# Health check
curl https://your-omega-url.provider.akash.pro:8000/health

# Generar predicciones
curl -X POST https://your-omega-url.provider.akash.pro:8000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "perfil_svi": "moderado"}'
```

## Costos Estimados

- **GPU RTX4090**: ~50-100 AKT/día
- **Sin GPU**: ~5-20 AKT/día
- **Storage**: Incluido en el precio base

## Cerrar Deployment

```bash
akash tx market lease close \
  --dseq <DSEQ> \
  --provider <PROVIDER> \
  --from omega-wallet \
  --node https://rpc.akash.forbole.com:443 \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.15
```

## Troubleshooting

**Error "insufficient funds":**
- Compra más tokens AKT
- Reduce los recursos en `deploy/akash-deployment.yaml`

**Error "no bids received":**
- Reduce GPU requirements
- Aumenta el precio máximo en el deployment
- Intenta en horario de menor demanda

**Error "manifest rejected":**
- Verifica sintaxis del YAML
- Reduce memory/CPU requirements
- Verifica que la imagen Docker sea accesible

---

🎯 **OMEGA está optimizado y listo para Akash Network con todos los fixes aplicados!**