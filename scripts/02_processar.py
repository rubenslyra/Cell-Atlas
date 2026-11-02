"""
Cell-Atlas — Pré-processamento Completo
Etapas: QC → Filtragem → Normalização → PCA
Base: Luecken & Theis (2019) Mol Syst Biol 15:e8746
"""
import scanpy as sc
import matplotlib.pyplot as plt
import os
import sys

plt.rcParams["figure.figsize"] = (6, 4)
ENTRADA = "dados/pbmc3k.h5ad"
SAIDA = "dados/pbmc3k_processado.h5ad"

if not os.path.exists(ENTRADA):
    print("❌ Execute primeiro: 01_baixar_dados.py")
    sys.exit(1)

print("🔹 Carregando dados brutos...")
adata = sc.read_h5ad(ENTRADA)
print(f"   Inicial: {adata.n_obs} células × {adata.n_vars} genes")

print("🔹 Controle de qualidade...")
adata.var["mt"] = adata.var_names.str.startswith("MT-")
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True)

print("🔹 Filtragem...")
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_cells(adata, max_genes=2500)
adata = adata[adata.obs["pct_counts_mt"] < 5, :]
sc.pp.filter_genes(adata, min_cells=3)
print(f"   Após filtro: {adata.n_obs} células × {adata.n_vars} genes")

print("🔹 Normalização e seleção de genes...")
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)

print("🔹 PCA...")
adata.raw = adata
sc.pp.scale(adata, max_value=10)
sc.tl.pca(adata, svd_solver="arpack")

os.makedirs("figuras", exist_ok=True)
sc.pl.pca_variance_ratio(adata, log=True, show=False)
plt.savefig("figuras/pca_variancia.png", dpi=150, bbox_inches="tight")
plt.close()

adata.write(SAIDA)
print(f"✅ Concluído — salvo em: {SAIDA}")
