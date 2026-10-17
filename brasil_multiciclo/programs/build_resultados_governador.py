"""
Agrega o arquivo de votação nominal por município/zona (já filtrado para
DS_CARGO == "Governador") em um total de votos por candidato, e junta com o
resultado final de totalização (situação por turno).

O arquivo de origem (votacao_governador_AAAA.csv) tem uma linha por
candidato x município x zona. Aqui somamos QT_VOTOS_NOMINAIS por
SQ_CANDIDATO, e (como no censo) deduplicamos por NR_TURNO — quando há 2º
turno, mantemos a linha do turno mais alto para SG_UF/situação final, mas
somamos os votos apenas do turno em que o candidato de fato concorreu
naquele município/zona (cada linha já vem marcada com seu próprio NR_TURNO,
então a soma por turno é feita separadamente e reportamos os dois).

Uso: python3 build_resultados_governador.py <ano> <caminho_csv>
"""
import csv
import sys
import json
import os
from collections import defaultdict

ano = sys.argv[1] if len(sys.argv) > 1 else "2026"
caminho = sys.argv[2] if len(sys.argv) > 2 else f"/home/claude/brasil_multiciclo/dados_tse/{ano}/votacao_governador_{ano}.csv"

votos_por_turno = defaultdict(lambda: defaultdict(int))  # sq -> turno -> votos
info_candidato = {}  # sq -> dict com dados fixos (nome, partido, uf, etc.)
sit_por_turno = {}  # sq -> turno -> (cd_sit_tot, ds_sit_tot)

with open(caminho, encoding="latin1") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        row = {k: v.strip('"') for k, v in row.items()}
        sq = row["SQ_CANDIDATO"]
        turno = row["NR_TURNO"]
        votos = int(row["QT_VOTOS_NOMINAIS"]) if row["QT_VOTOS_NOMINAIS"].strip('"').isdigit() else 0
        votos_por_turno[sq][turno] += votos
        sit_por_turno.setdefault(sq, {})[turno] = (row.get("CD_SIT_TOT_TURNO", ""), row.get("DS_SIT_TOT_TURNO", ""))
        if sq not in info_candidato:
            info_candidato[sq] = {
                "SG_UF": row["SG_UF"],
                "SQ_CANDIDATO": sq,
                "NR_CANDIDATO": row["NR_CANDIDATO"],
                "NM_CANDIDATO": row["NM_CANDIDATO"],
                "NM_URNA_CANDIDATO": row["NM_URNA_CANDIDATO"],
                "SG_PARTIDO": row["SG_PARTIDO"],
            }

resultados = []
for sq, info in info_candidato.items():
    turnos = sorted(votos_por_turno[sq].keys(), key=lambda t: int(t) if t.isdigit() else 0)
    turno_final = turnos[-1]
    cd_sit, ds_sit = sit_por_turno[sq][turno_final]
    linha = dict(info)
    linha["FOI_A_2_TURNO"] = "SIM" if len(turnos) > 1 else "NAO"
    linha["VOTOS_TURNO_1"] = votos_por_turno[sq].get("1", 0)
    linha["VOTOS_TURNO_2"] = votos_por_turno[sq].get("2", 0)
    linha["CD_SIT_TOT_TURNO"] = cd_sit
    linha["DS_SIT_TOT_TURNO"] = ds_sit
    resultados.append(linha)

print(f"=== Resultados de votação — GOVERNADOR — {ano} ===")
print(f"Candidatos com voto registrado: {len(resultados)}")

por_uf = defaultdict(int)
for r in resultados:
    por_uf[r["SG_UF"]] += 1
print(f"Estados cobertos: {len(por_uf)}")

from collections import Counter
sit = Counter(r["DS_SIT_TOT_TURNO"] for r in resultados)
print(f"Situação de totalização: {dict(sit)}")

out_csv = f"/home/claude/brasil_multiciclo/dados_tse/{ano}/derivados/resultados_governador_{ano}.csv"
out_json = f"/home/claude/brasil_multiciclo/dados_tse/{ano}/derivados/resultados_governador_{ano}.json"
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

campos = ["SG_UF", "SQ_CANDIDATO", "NR_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO",
          "SG_PARTIDO", "FOI_A_2_TURNO", "VOTOS_TURNO_1", "VOTOS_TURNO_2",
          "CD_SIT_TOT_TURNO", "DS_SIT_TOT_TURNO"]

with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campos)
    writer.writeheader()
    writer.writerows(resultados)

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\nSalvo em: {out_csv}")
print(f"Salvo em: {out_json}")
