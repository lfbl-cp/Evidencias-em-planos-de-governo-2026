#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolida os dados dos 6 candidatos do Sul (RS, SC, PR) em um único JSON,
replicando exatamente a lógica usada nas regiões anteriores (Nordeste, Norte,
Centro-Oeste, Sudeste): categoria simplificada (via regex no separador
em-dash/parênteses), e densidade de jargão "fortalecer"/"ampliar" por mil
palavras, contada sobre o corpo do texto (após strip_header).
"""
import json
import re
from pathlib import Path

BASE = Path("/home/claude/brasil_2026/sul")

ESTADOS = [
    ("rio-grande-do-sul", "RS"),
    ("santa-catarina", "SC"),
    ("parana", "PR"),
]

def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx + len(marker):] if idx != -1 else text

def simplificar_categoria(raw: str) -> str:
    m = re.search(r"\s*[—–\-(]", raw)
    return raw[:m.start()].strip() if m else raw.strip()

resultado = []

for pasta, uf in ESTADOS:
    analise_path = BASE / pasta / "analise" / "analise.json"
    d = json.loads(analise_path.read_text(encoding="utf-8"))
    for c in d["candidatos"]:
        slug = c["slug"]
        plano_path = BASE / pasta / "planos" / f"{slug}.txt"
        if not plano_path.exists():
            plano_path = BASE / pasta / "planos" / f"{slug.replace('-', '_')}.txt"
        if not plano_path.exists():
            plano_path = BASE / pasta / "planos" / f"{slug.replace('_', '-')}.txt"
        raw_text = plano_path.read_text(encoding="utf-8")
        corpo = strip_header(raw_text)
        n_fortalec = len(re.findall(r"\bfortalec\w*", corpo, flags=re.IGNORECASE))
        n_ampli = len(re.findall(r"\bampli\w*", corpo, flags=re.IGNORECASE))
        total_palavras = c["total_palavras"]
        per_mil_jargao = round((n_fortalec + n_ampli) / total_palavras * 1000, 2) if total_palavras else 0.0

        resultado.append({
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "estado": uf,
            "categoria_raw": c["categoria"],
            "total_palavras": total_palavras,
            "indice_base_empirica_pct": c["indice_base_empirica_pct"],
            "indice_base_empirica_legado_pct": c.get("indice_base_empirica_legado_pct"),
            "n_compromisso_sem_base": c.get("indice_base_empirica_detalhe", {}).get("n_trechos_compromisso_sem_base"),
            "n_fortalec": n_fortalec,
            "n_ampli": n_ampli,
            "per_mil_jargao": per_mil_jargao,
            "categoria": simplificar_categoria(c["categoria"]),
        })

out_path = BASE / "analise_geral_sul" / "dados_consolidados_sul.json"
out_path.write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Escrito: {out_path} ({len(resultado)} candidatos)")
for r in resultado:
    print(f"  {r['estado']} {r['nome']:20s} {r['total_palavras']:6d}w  idx={r['indice_base_empirica_pct']:.1f}%  jargao={r['per_mil_jargao']}/mil  cat={r['categoria']}")
