# cluster_predictor.py – Análisis profundo de clústeres OMEGA
import pandas as pd
from modules.clustering_model import apply_clustering
from collections import Counter

def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))

def main():
    print("📊 Análisis de clústeres OMEGA – Versión extendida")
    
    # Cargar historial
    df = pd.read_csv("data/historial_kabala_github.csv")
    df_numeric = df.select_dtypes(include='number').dropna()

    # Aplicar clustering
    labels, centroids = apply_clustering(df_numeric)

    # Mostrar resultados
    print(f"\n🔢 Total de sorteos: {len(df_numeric)}")
    print(f"🧠 Clústeres encontrados: {len(centroids)}")

    # Conteo por clúster
    cluster_count = Counter(labels)

    for i, centroide in enumerate(centroids):
        members = df_numeric[labels == i].values.tolist()

        avg_hamming = sum(hamming_distance(centroide, m) for m in members) / len(members)
        print(f"\n🧬 Clúster {i+1}")
        print(f"  🔹 Combinaciones en el clúster: {cluster_count[i]}")
        print(f"  🔸 Centroide: {centroide}")
        print(f"  🔻 Distancia Hamming promedio al centroide: {avg_hamming:.2f}")

    print("\n✅ Análisis completo. Puedes usar los centroides como semillas estratégicas.")

if __name__ == "__main__":
    main()
