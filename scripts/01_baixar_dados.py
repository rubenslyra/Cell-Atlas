"""
Cell-Atlas — Aquisição de Dados
Baixa e organiza o conjunto de referência PBMC3k
"""
import scanpy as sc
import os

ARQUIVO_SAIDA = "dados/pbmc3k.h5ad"
os.makedirs("dados", exist_ok=True)

if os.path.exists(ARQUIVO_SAIDA):
    print("⚠️ Arquivo já existe — download ignorado.")
    exit(0)

print("📥 Baixando PBMC3k — Células Imunes Humanas")
print("Fonte: 10x Genomics / Scanpy Repository")
print("Acesso alternativo: GEO GSE139324")
print("-" * 50)

adata = sc.datasets.pbmc3k()
adata.write(ARQUIVO_SAIDA)

print(f"✅ Concluído: {adata.n_obs} células × {adata.n_vars} genes")
print(f"Salvo em: {ARQUIVO_SAIDA}")
