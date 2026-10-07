#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolida os 57 candidatos das 5 regioes (+ piloto PB) num unico dataset
nacional, para alimentar o mapa interativo e o relatorio nacional.
Le direto dos analise.json (fonte da verdade) e cruza com os
dados_consolidados_*.json regionais so para pegar a categoria ja
simplificada (mesma normalizacao de genero/forma usada no resto do
projeto), preservando a versao integral e referenciada em categoria_raw.
Nao altera nenhum arquivo publicado -- so le e agrega.
"""
import json
from pathlib import Path

BASE = Path("/home/claude/brasil_2026")
PB_BASE = Path("/home/claude/pb2026_v2")

# (pasta, UF, nome do estado, regiao)
ESTADOS = [
    ("nordeste/alagoas", "AL", "Alagoas", "Nordeste"),
    ("nordeste/bahia", "BA", "Bahia", "Nordeste"),
    ("nordeste/ceara", "CE", "Ceará", "Nordeste"),
    ("nordeste/maranhao", "MA", "Maranhão", "Nordeste"),
    ("nordeste/pernambuco", "PE", "Pernambuco", "Nordeste"),
    ("nordeste/piaui", "PI", "Piauí", "Nordeste"),
    ("nordeste/rio-grande-do-norte", "RN", "Rio Grande do Norte", "Nordeste"),
    ("nordeste/sergipe", "SE", "Sergipe", "Nordeste"),
    ("norte/acre", "AC", "Acre", "Norte"),
    ("norte/amapa", "AP", "Amapá", "Norte"),
    ("norte/amazonas", "AM", "Amazonas", "Norte"),
    ("norte/para", "PA", "Pará", "Norte"),
    ("norte/rondonia", "RO", "Rondônia", "Norte"),
    ("norte/tocantins", "TO", "Tocantins", "Norte"),
    ("centro-oeste/distrito-federal", "DF", "Distrito Federal", "Centro-Oeste"),
    ("centro-oeste/goias", "GO", "Goiás", "Centro-Oeste"),
    ("centro-oeste/mato-grosso", "MT", "Mato Grosso", "Centro-Oeste"),
    ("centro-oeste/mato-grosso-do-sul", "MS", "Mato Grosso do Sul", "Centro-Oeste"),
    ("sudeste/espirito-santo", "ES", "Espírito Santo", "Sudeste"),
    ("sudeste/minas-gerais", "MG", "Minas Gerais", "Sudeste"),
    ("sudeste/rio-de-janeiro", "RJ", "Rio de Janeiro", "Sudeste"),
    ("sudeste/sao-paulo", "SP", "São Paulo", "Sudeste"),
    ("sul/parana", "PR", "Paraná", "Sul"),
    ("sul/rio-grande-do-sul", "RS", "Rio Grande do Sul", "Sul"),
    ("sul/santa-catarina", "SC", "Santa Catarina", "Sul"),
]

# categorias simplificadas ja calculadas nos dados_consolidados regionais
# (mesma logica/normalizacao de genero usada em todo o projeto)
CONSOLIDADOS = {
    "Nordeste": BASE / "nordeste/analise_geral_ne/dados_consolidados.json",
    "Norte": BASE / "norte/analise_geral_norte/dados_consolidados_norte.json",
    "Centro-Oeste": BASE / "centro-oeste/analise_geral_centro_oeste/dados_consolidados_centro_oeste.json",
    "Sudeste": BASE / "sudeste/analise_geral_sudeste/dados_consolidados_sudeste.json",
    "Sul": BASE / "sul/analise_geral_sul/dados_consolidados_sul.json",
}
categoria_simpl_por_slug = {}
for regiao, path in CONSOLIDADOS.items():
    for r in json.loads(path.read_text(encoding="utf-8")):
        categoria_simpl_por_slug[r["slug"]] = r["categoria"]

resultado = []
for pasta, uf, estado_nome, regiao in ESTADOS:
    analise_path = BASE / pasta / "analise" / "analise.json"
    d = json.loads(analise_path.read_text(encoding="utf-8"))
    for c in d["candidatos"]:
        slug = c["slug"]
        det = c.get("indice_base_empirica_detalhe", {})
        resultado.append({
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "uf": uf,
            "estado": estado_nome,
            "regiao": regiao,
            "categoria": categoria_simpl_por_slug.get(slug, "não classificado"),
            "categoria_raw": c.get("categoria", ""),
            "total_palavras": c["total_palavras"],
            "indice_base_empirica_pct": c["indice_base_empirica_pct"],
            "indice_base_empirica_legado_pct": c.get("indice_base_empirica_legado_pct"),
            "n_com_base_empirica": det.get("n_trechos_com_base_empirica"),
            "n_retorica_sem_evidencia": det.get("n_trechos_retorica_sem_evidencia"),
            "n_compromisso_sem_base": det.get("n_trechos_compromisso_sem_base"),
            "n_pilar_a_diagnostico": det.get("n_pilar_a_diagnostico"),
            "n_pilar_b_efeito_mensuravel": det.get("n_pilar_b_efeito_mensuravel"),
            "n_pilar_c_evidencia_causal_externa": det.get("n_pilar_c_evidencia_causal_externa"),
            "distribuicao_tematica_pct": c.get("distribuicao_tematica_pct"),
        })

# piloto da Paraiba (regiao Nordeste, contabilizado nos "9 estados" do Nordeste)
pb_path = PB_BASE / "analise" / "analise.json"
d_pb = json.loads(pb_path.read_text(encoding="utf-8"))
for c in d_pb["candidatos"]:
    det = c.get("indice_base_empirica_detalhe", {})
    resultado.append({
        "slug": c["slug"],
        "nome": c["nome"],
        "partido": c["partido"],
        "uf": "PB",
        "estado": "Paraíba",
        "regiao": "Nordeste",
        # PB ja esta presente no dados_consolidados.json do Nordeste com a
        # categoria simplificada correta -- usa a mesma fonte que os outros
        # 54 candidatos em vez do campo "categoria" bruto do analise.json do
        # piloto (que guarda o texto sourced, nao a forma canonica).
        "categoria": categoria_simpl_por_slug.get(c["slug"], c.get("categoria", "não classificado")),
        "categoria_raw": c.get("categoria", ""),
        "total_palavras": c["total_palavras"],
        "indice_base_empirica_pct": c["indice_base_empirica_pct"],
        "indice_base_empirica_legado_pct": c.get("indice_base_empirica_legado_pct"),
        "n_com_base_empirica": det.get("n_trechos_com_base_empirica"),
        "n_retorica_sem_evidencia": det.get("n_trechos_retorica_sem_evidencia"),
        "n_compromisso_sem_base": det.get("n_trechos_compromisso_sem_base"),
        "n_pilar_a_diagnostico": det.get("n_pilar_a_diagnostico"),
        "n_pilar_b_efeito_mensuravel": det.get("n_pilar_b_efeito_mensuravel"),
        "n_pilar_c_evidencia_causal_externa": det.get("n_pilar_c_evidencia_causal_externa"),
        "distribuicao_tematica_pct": c.get("distribuicao_tematica_pct"),
    })

resultado.sort(key=lambda r: (-r["indice_base_empirica_pct"]))
for i, r in enumerate(resultado, start=1):
    r["ranking_nacional"] = i

out_dir = BASE / "nacional"
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "dados_nacionais.json"
out_path.write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Escrito: {out_path} ({len(resultado)} candidatos, {len(set(r['uf'] for r in resultado))} estados)")

# checagem rapida
regioes = {}
for r in resultado:
    regioes.setdefault(r["regiao"], set()).add(r["uf"])
for reg, ufs in regioes.items():
    print(f"  {reg}: {len(ufs)} estados, {sum(1 for r in resultado if r['regiao']==reg)} candidatos -> {sorted(ufs)}")
