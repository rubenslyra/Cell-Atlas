"""
Cell-Atlas — Agrupamento com Algoritmo Leiden
Grafo de vizinhança k-NN → Múltiplas resoluções → UMAP

Referência: Traag et al. (2019) Sci Rep 9:5233
"""
import scanpy as sc
import matplotlib.pyplot as plt
import os
import sys

plt.rcParams["figure.figsize"] = (16, 4)
ENTRADA = "dados/pbmc3k_processado.h5ad"
SAIDA = "dados/pbmc3k_leiden.h5ad"

if not os.path.exists(ENTRADA):
    print("❌ Execute primeiro: 02_processar.py")
    sys.exit(1)

print("🔹 Carregando dados...")
adata = sc.read_h5ad(ENTRADA)

print("🔹 Construindo grafo de vizinhança k-NN...")
print("   Cada célula conecta-se às 15 mais semelhantes (10 primeiros PCs)")
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=10)

print("🔹 Calculando UMAP...")
sc.tl.umap(adata)

resolucoes = [0.2, 0.4, 0.6, 1.0]
print(f"🔹 Aplicando Leiden em resoluções: {resolucoes}")
for res in resolucoes:
    sc.tl.leiden(adata, resolution=res, key_added=f"leiden_{res}",
                 flavor="igraph", n_iterations=2)
    print(f"   resolução {res:4} → {adata.obs[f'leiden_{res}'].nunique()} grupos")

fig, eixos = plt.subplots(1, 4, figsize=(16, 4))
for i, res in enumerate(resolucoes):
    sc.pl.umap(adata, color=f"leiden_{res}", ax=eixos[i],
               show=False, legend_loc="on data", title=f"Resolução {res}")
plt.suptitle("Cell-Atlas — Comparação de Resoluções", y=1.05, fontsize=14)
plt.tight_layout()
plt.savefig("figuras/umap_todas_resolucoes.png", dpi=150, bbox_inches="tight")
plt.close()

adata.write(SAIDA)
print(f"✅ Concluído — salvo em: {SAIDA}")
