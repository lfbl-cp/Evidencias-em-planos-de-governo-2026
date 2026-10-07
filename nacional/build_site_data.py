#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o pacote de dados que alimenta a pagina nacional interativa
(mapa clicavel + paineis). Le dados_nacionais.json (ja consolidado) e o
geojson simplificado dos estados, e escreve um unico JSON com tudo que o
HTML precisa embutir: candidatos, agregados por estado/regiao/categoria/
partido, distribuicao tematica nacional, paths do mapa.
"""
import json, statistics
from pathlib import Path
from collections import defaultdict

BASE = Path("/home/claude/brasil_2026/nacional")
cand = json.loads((BASE / "dados_nacionais.json").read_text(encoding="utf-8"))
mapa = json.loads(Path("/tmp/br_map_paths.json").read_text(encoding="utf-8"))

# --- agregados por estado (para o choropleth) ---
por_uf = defaultdict(list)
for c in cand:
    por_uf[c["uf"]].append(c)

estados_agg = {}
for uf, cs in por_uf.items():
    idxs = [c["indice_base_empirica_pct"] for c in cs]
    estados_agg[uf] = {
        "estado": cs[0]["estado"],
        "regiao": cs[0]["regiao"],
        "n_candidatos": len(cs),
        "media_indice": round(statistics.mean(idxs), 2),
        "candidatos": sorted(
            [{"slug": c["slug"], "nome": c["nome"], "partido": c["partido"],
              "categoria": c["categoria"], "indice_base_empirica_pct": c["indice_base_empirica_pct"],
              "indice_base_empirica_legado_pct": c["indice_base_empirica_legado_pct"],
              "total_palavras": c["total_palavras"], "ranking_nacional": c["ranking_nacional"]}
             for c in cs],
            key=lambda r: -r["indice_base_empirica_pct"]
        ),
    }
# estados sem dado (Roraima) ficam de fora do dict -> tratados como "sem cobertura" no front-end

# --- agregados por regiao ---
por_regiao = defaultdict(list)
for c in cand:
    por_regiao[c["regiao"]].append(c["indice_base_empirica_pct"])
regioes_agg = []
for reg, vals in por_regiao.items():
    regioes_agg.append({
        "regiao": reg,
        "n": len(vals),
        "n_estados": len(set(c["uf"] for c in cand if c["regiao"] == reg)),
        "media": round(statistics.mean(vals), 2),
        "mediana": round(statistics.median(vals), 2),
        "desvio": round(statistics.pstdev(vals), 2),
        "min": round(min(vals), 1),
        "max": round(max(vals), 1),
    })
regioes_agg.sort(key=lambda r: -r["media"])

# --- agregados por categoria politica ---
por_cat = defaultdict(list)
for c in cand:
    por_cat[c["categoria"]].append(c["indice_base_empirica_pct"])
ORDEM_CAT = ["desafiante", "incumbente pleno", "incumbente por sucessão", "candidato de continuidade"]
categorias_agg = []
for cat in ORDEM_CAT:
    vals = por_cat.get(cat, [])
    if not vals:
        continue
    categorias_agg.append({
        "categoria": cat, "n": len(vals),
        "media": round(statistics.mean(vals), 2), "mediana": round(statistics.median(vals), 2),
    })

# --- distribuicao tematica nacional media ---
temas = defaultdict(list)
for c in cand:
    dt = c.get("distribuicao_tematica_pct") or {}
    for tema, pct in dt.items():
        temas[tema].append(pct)
NOME_TEMA = {
    "economia": "Economia", "assistencia_social": "Assistência social", "outros": "Outros",
    "infraestrutura": "Infraestrutura", "gestao_publica": "Gestão pública", "educacao": "Educação",
    "seguranca": "Segurança", "saude": "Saúde", "meio_ambiente": "Meio ambiente",
}
tematica_agg = [
    {"tema": NOME_TEMA.get(t, t), "media": round(statistics.mean(v), 2)}
    for t, v in sorted(temas.items(), key=lambda kv: -statistics.mean(kv[1]))
]

# --- partidos com >=2 candidatos ---
por_partido = defaultdict(list)
for c in cand:
    por_partido[c["partido"]].append(c["indice_base_empirica_pct"])
partidos_agg = [
    {"partido": p, "n": len(v), "media": round(statistics.mean(v), 2)}
    for p, v in por_partido.items() if len(v) >= 2
]
partidos_agg.sort(key=lambda r: -r["media"])

nacional = {
    "n_candidatos": len(cand),
    "n_estados": len(set(c["uf"] for c in cand)),
    "media": round(statistics.mean(c["indice_base_empirica_pct"] for c in cand), 2),
    "mediana": round(statistics.median([c["indice_base_empirica_pct"] for c in cand]), 2),
    "desvio": round(statistics.pstdev([c["indice_base_empirica_pct"] for c in cand]), 2),
}

out = {
    "gerado_em": "28 de agosto de 2026",
    "nacional": nacional,
    "candidatos": cand,
    "estados": estados_agg,
    "regioes": regioes_agg,
    "categorias": categorias_agg,
    "tematica": tematica_agg,
    "partidos": partidos_agg,
    "mapa": mapa,
}
out_path = BASE / "site_data.json"
out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(f"Escrito {out_path} ({len(json.dumps(out))/1024:.0f} KB)")
