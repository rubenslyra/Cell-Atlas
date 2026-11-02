"""
Cell-Atlas — Anotação Biológica
Identificação de genes marcadores e correspondência com tipos celulares

Marcadores de referência para PBMC:
  CD3E, CD3D, TRAC → Células T
  MS4A1, CD79A, CD79B → Células B
  CD14, LYZ, S100A9 → Monócitos
  NKG7, GNLY, KLRD1 → Células NK
"""
import scanpy as sc
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

plt.rcParams["figure.figsize"] = (10, 6)
ENTRADA = "dados/pbmc3k_leiden.h5ad"
RES_ALVO = "leiden_0.6"

if not os.path.exists(ENTRADA):
    print("❌ Execute primeiro: 03_agrupar.py")
    sys.exit(1)

print("🔹 Carregando agrupamentos...")
adata = sc.read_h5ad(ENTRADA)

print(f"🔹 Identificando genes marcadores — {RES_ALVO}...")
sc.tl.rank_genes_groups(adata, groupby=RES_ALVO, method="wilcoxon")

os.makedirs("figuras", exist_ok=True)
os.makedirs("resultados", exist_ok=True)

sc.pl.rank_genes_groups(adata, n_genes=5, sharey=False, show=False)
plt.savefig("figuras/genes_marcadores.png", dpi=150, bbox_inches="tight")
plt.close()

print("🔹 Verificando marcadores clássicos...")
marcadores = {
    "Células T": ["CD3E", "CD3D", "TRAC"],
    "Células B": ["MS4A1", "CD79A"],
    "Monócitos": ["CD14", "LYZ"],
    "Células NK": ["NKG7", "GNLY"],
}
marcadores_flat = []
for genes in marcadores.values():
    marcadores_flat.extend(genes)
# Remove duplicates while preserving order
marcadores_flat = list(dict.fromkeys(marcadores_flat))
# Use raw if available for marker visualization
if adata.raw is not None:
    adata_vis = adata.raw.to_adata()
    adata_vis.obs = adata.obs
    adata_vis.obsm = adata.obsm
    adata_vis.uns = adata.uns
else:
    adata_vis = adata
valid_markers = [g for g in marcadores_flat if g in adata_vis.var_names]
sc.pl.umap(adata_vis, color=valid_markers, ncols=4, show=False)
plt.savefig("figuras/marcadores_classicos.png", dpi=150, bbox_inches="tight")
plt.close()

tabela = pd.DataFrame()
for g in sorted(adata.obs[RES_ALVO].unique()):
    top = adata.uns["rank_genes_groups"]["names"][g][:3]
    tabela = pd.concat([tabela, pd.DataFrame({
        "Grupo": [g], "Top_genes": [", ".join(top)],
        "Celulas": [(adata.obs[RES_ALVO] == g).sum()]
    })])
tabela.to_csv("resultados/resumo_grupos.csv", index=False)

print("\n📋 RESUMO DOS GRUPOS:")
print(tabela.to_string(index=False))
print("\n✅ Anotação concluída!")
print("💡 Compare 'Top_genes' com marcadores clássicos acima para identificar cada tipo celular.")
