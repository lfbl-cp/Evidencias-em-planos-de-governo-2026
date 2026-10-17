"""
Constrói a tabela-base de candidatos a governador (censo completo) a partir do
arquivo consulta_cand_AAAA_BRASIL.csv do TSE (Portal de Dados Abertos).

Uso: python3 build_censo_governador.py <ano> <caminho_csv_brasil>
"""
import csv
import sys
import json
from collections import Counter

ano = sys.argv[1] if len(sys.argv) > 1 else "2026"
caminho = sys.argv[2] if len(sys.argv) > 2 else f"/home/claude/brasil_multiciclo/dados_tse/{ano}/consulta_cand_{ano}_BRASIL.csv"

CAMPOS_MANTIDOS = [
    "SG_UF", "DS_CARGO", "SQ_CANDIDATO", "NR_CANDIDATO", "NR_TURNO",
    "NR_CPF_CANDIDATO",
    "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO", "NM_PARTIDO",
    "DS_COMPOSICAO_COLIGACAO",
    "CD_SITUACAO_CANDIDATURA", "DS_SITUACAO_CANDIDATURA",
    "CD_SIT_TOT_TURNO", "DS_SIT_TOT_TURNO",
    "DT_NASCIMENTO", "DS_GENERO", "DS_GRAU_INSTRUCAO", "DS_COR_RACA",
]

# ATENÇÃO: quando a eleição vai a 2º turno, o TSE grava UMA LINHA POR TURNO para o
# mesmo SQ_CANDIDATO (turno 1 com DS_SIT_TOT_TURNO="2º TURNO", turno 2 com o
# resultado final "ELEITO"/"NÃO ELEITO"). Sem tratar isso, o mesmo candidato é
# contado duas vezes. Aqui deduplicamos por SQ_CANDIDATO, mantendo a linha do
# NR_TURNO mais alto (o resultado definitivo) e marcando quem disputou 2º turno.
raw_rows = []
with open(caminho, encoding="latin1") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        if row.get("DS_CARGO") != "GOVERNADOR":
            continue
        raw_rows.append({k: row.get(k, "").strip('"') for k in CAMPOS_MANTIDOS})

por_sq = {}
for row in raw_rows:
    sq = row["SQ_CANDIDATO"]
    por_sq.setdefault(sq, []).append(row)

candidatos = []
n_segundo_turno = 0
for sq, linhas in por_sq.items():
    linhas.sort(key=lambda r: int(r["NR_TURNO"]) if r["NR_TURNO"].isdigit() else 0)
    final = dict(linhas[-1])
    foi_2_turno = len(linhas) > 1
    final["FOI_A_2_TURNO"] = "SIM" if foi_2_turno else "NAO"
    if foi_2_turno:
        n_segundo_turno += 1
    candidatos.append(final)

CAMPOS_MANTIDOS = CAMPOS_MANTIDOS + ["FOI_A_2_TURNO"]

print(f"=== Censo de candidatos a GOVERNADOR — {ano} ===")
print(f"Linhas brutas no CSV (GOVERNADOR): {len(raw_rows)}")
print(f"Candidatos únicos (SQ_CANDIDATO deduplicado): {len(candidatos)}")
print(f"...dos quais foram a 2º turno: {n_segundo_turno}")
print(f"Total nacional: {len(candidatos)}")

por_uf = Counter(c["SG_UF"] for c in candidatos)
print(f"Estados cobertos: {len(por_uf)}")
for uf in sorted(por_uf):
    print(f"  {uf}: {por_uf[uf]}")

sit_cand = Counter(c["DS_SITUACAO_CANDIDATURA"] for c in candidatos)
sit_tot = Counter(c["DS_SIT_TOT_TURNO"] for c in candidatos)
print(f"\nSituação de candidatura: {dict(sit_cand)}")
print(f"Situação de totalização: {dict(sit_tot)}")

out_csv = f"/home/claude/brasil_multiciclo/dados_tse/{ano}/derivados/censo_governador_{ano}.csv"
out_json = f"/home/claude/brasil_multiciclo/dados_tse/{ano}/derivados/censo_governador_{ano}.json"
import os
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CAMPOS_MANTIDOS)
    writer.writeheader()
    writer.writerows(candidatos)

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(candidatos, f, ensure_ascii=False, indent=2)

print(f"\nSalvo em: {out_csv}")
print(f"Salvo em: {out_json}")
