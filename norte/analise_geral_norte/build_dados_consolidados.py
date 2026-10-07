#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstroi dados_consolidados_norte.json a partir dos analise.json atuais
(pós-correção do defeito de repair de ligaduras fi/fl), preservando
categoria_raw/categoria de cada candidato. Mesma lógica usada no Sul.
"""
import json
import re
from pathlib import Path

BASE = Path("/home/claude/brasil_2026/norte")
OLD = json.loads((BASE / "analise_geral_norte" / "dados_consolidados_norte.json").read_text(encoding="utf-8"))
OLD_BY_SLUG = {c["slug"]: c for c in OLD}

ESTADOS = [
    ("acre", "AC"),
    ("amapa", "AP"),
    ("amazonas", "AM"),
    ("para", "PA"),
    ("rondonia", "RO"),
    ("tocantins", "TO"),
]

def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx + len(marker):] if idx != -1 else text

def simplificar_categoria(raw: str) -> str:
    m = re.search(r"\s*[—–\-(]", raw)
    cat = raw[:m.start()].strip() if m else raw.strip()
    # CORRIGIDO (auditoria pós-Norte): normaliza para a forma canônica
    # masculina da taxonomia fixa do projeto ("incumbente pleno" /
    # "incumbente por sucessão" / "candidato de continuidade" /
    # "desafiante"), independente do gênero gramatical do candidato no
    # texto bruto (ex. "candidata de continuidade" para Professora
    # Dorinha) -- sem isso, o agrupamento estatístico por categoria
    # separa incorretamente candidatas mulheres do restante do grupo.
    if cat == "candidata de continuidade":
        cat = "candidato de continuidade"
    return cat

resultado = []
for pasta, uf in ESTADOS:
    d = json.loads((BASE / pasta / "analise" / "analise.json").read_text(encoding="utf-8"))
    for c in d["candidatos"]:
        slug = c["slug"]
        plano_path = BASE / pasta / "planos" / f"{slug.replace('-', '_')}.txt"
        if not plano_path.exists():
            plano_path = BASE / pasta / "planos" / f"{slug}.txt"
        raw_text = plano_path.read_text(encoding="utf-8")
        corpo = strip_header(raw_text)
        n_fortalec = len(re.findall(r"\bfortalec\w*", corpo, flags=re.IGNORECASE))
        n_ampli = len(re.findall(r"\bampli\w*", corpo, flags=re.IGNORECASE))
        total_palavras = c["total_palavras"]
        per_mil_jargao = round((n_fortalec + n_ampli) / total_palavras * 1000, 2) if total_palavras else 0.0
        old = OLD_BY_SLUG.get(slug, {})
        categoria_raw = old.get("categoria_raw", c["categoria"])
        resultado.append({
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "estado": uf,
            "categoria_raw": categoria_raw,
            "total_palavras": total_palavras,
            "indice_base_empirica_pct": c["indice_base_empirica_pct"],
            "indice_base_empirica_legado_pct": c.get("indice_base_empirica_legado_pct"),
            "n_compromisso_sem_base": c.get("indice_base_empirica_detalhe", {}).get("n_trechos_compromisso_sem_base"),
            "n_fortalec": n_fortalec,
            "n_ampli": n_ampli,
            "per_mil_jargao": per_mil_jargao,
            "categoria": simplificar_categoria(categoria_raw),
        })

out_path = BASE / "analise_geral_norte" / "dados_consolidados_norte.json"
out_path.write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Escrito: {out_path} ({len(resultado)} candidatos)")
for r in resultado:
    old = OLD_BY_SLUG.get(r["slug"], {})
    delta_idx = r["indice_base_empirica_pct"] - old.get("indice_base_empirica_pct", r["indice_base_empirica_pct"])
    delta_w = r["total_palavras"] - old.get("total_palavras", r["total_palavras"])
    print(f"  {r['estado']} {r['nome']:20s} {r['total_palavras']:7d}w ({delta_w:+d})  idx={r['indice_base_empirica_pct']:.1f}% ({delta_idx:+.1f})  jargao={r['per_mil_jargao']}/mil")
