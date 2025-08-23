from cryptography.fernet import Fernet
import os

auth_key_path = "logs/auth_key.key"
os.makedirs("logs", exist_ok=True)

if os.path.exists(auth_key_path):
    print(f"⚠️ Ya existe una clave en: {auth_key_path}")
else:
    key = Fernet.generate_key()
    with open(auth_key_path, 'wb') as f:
        f.write(key)
    print(f"✅ Clave Fernet generada y guardada en {auth_key_path}")
