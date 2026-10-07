#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 1 (25/08/2026): duas analises adicionais sobre frases_classificadas.jsonl
1) Sensibilidade do indice a JARGAO_TERMOS (leave-one-out + subamostragem)
2) Indice de cobertura alternativo (denominador = frases de compromisso/
   proposta, identificadas por verbos de acao, nao so frases com jargao)
Nao toca em nenhum arquivo publicado do projeto -- so le frases_classificadas
e escreve saidas novas nesta mesma pasta.
"""
import json
import re
import random
from collections import defaultdict
from pathlib import Path

IN_PATH = Path("/home/claude/brasil_2026/metodologia/indice_base_empirica/frases_classificadas.jsonl")
OUT_DIR = Path("/home/claude/brasil_2026/metodologia/indice_base_empirica")

JARGAO_TERMOS = [
    "eficiência", "eficiente", "modernização", "modernizar", "qualidade",
    "fortalecimento", "fortalecer", "valorização", "valorizar",
    "aprimoramento", "aprimorar", "excelência", "sinergia", "inovador",
    "inovadora", "transformação", "transformar", "sustentável",
    "sustentabilidade", "robusto", "robusta", "amplo", "ampla", "amplos",
    "amplas", "diversos", "diversas", "governança", "otimização",
    "otimizar", "integrado", "integrada", "consolidar", "consolidação",
    "estruturante", "estruturantes", "articular", "articulação",
    "potencializar", "referência nacional", "de excelência",
    "políticas públicas", "desenvolvimento sustentável", "gestão eficiente",
]

# Lista de verbos/expressoes de compromisso programatico (proposito: capturar
# "faz uma proposta de acao", independente de ter jargao ou evidencia) --
# deliberadamente ampla; e uma escolha de constructo alternativa, nao uma
# verdade objetiva -- ver nota de metodologia.
PROPOSAL_RE = re.compile(
    r"\b(implementar|implantar|criar|ampliar|garantir|construir|reduzir(?:emos|á)?|"
    r"aumentar|fortalecer|promover|desenvolver|expandir|instituir|estabelecer|"
    r"assegurar|viabilizar|elaborar|executar|investir|oferecer|disponibilizar|"
    r"realizar|instalar|modernizar|qualificar|capacitar|estimular|apoiar|"
    r"vamos |iremos |irá |será[- ]?(?:criad|implantad|construíd|ampliad)|"
    r"criação de|construção de|implantação de|ampliação de|modernização de|"
    r"reforma de|reforma do|reforma da|programa de|política de)\b",
    re.IGNORECASE,
)


def load():
    """Carrega e pre-computa, por frase, os indices dos termos de jargao que
    batem (contra a lista completa) -- permite recalcular com_base/retorica
    sob qualquer subconjunto via interseccao de conjuntos, sem re-escanear a
    string da frase a cada rodada (necessario para rodar 200 subamostras
    sobre 133 mil frases em tempo viavel)."""
    term_idx = {t: i for i, t in enumerate(JARGAO_TERMOS)}
    records = []
    with open(IN_PATH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if not r["com_base"]:
                frase_low = r["frase"].lower()
                r["_jargao_bits"] = frozenset(i for t, i in term_idx.items() if t in frase_low)
            else:
                r["_jargao_bits"] = frozenset()
            records.append(r)
    return records


def indice_com_jargao(records, jargao_idx_set):
    """Recalcula com_base/retorica por candidato, dado um conjunto de INDICES
    de termos de jargao (nao os termos em si -- ver load())."""
    by_cand = defaultdict(lambda: [0, 0])  # [n_base, n_ret]
    for r in records:
        key = (r["estado"], r["slug"])
        d = by_cand[key]
        if r["com_base"]:
            d[0] += 1
        elif r["_jargao_bits"] & jargao_idx_set:
            d[1] += 1
    result = {}
    for key, (n_base, n_ret) in by_cand.items():
        n = n_base + n_ret
        result[key] = round(n_base / n * 100, 2) if n else 0.0
    return result


def main():
    records = load()
    print(f"Carregado: {len(records)} frases")

    all_idx = set(range(len(JARGAO_TERMOS)))

    # --- baseline com a lista publicada ---
    baseline = indice_com_jargao(records, all_idx)

    # --- leave-one-out: remove 1 termo por vez ---
    loo_deltas = defaultdict(list)  # termo -> lista de |delta| por candidato
    for i, termo in enumerate(JARGAO_TERMOS):
        subset = all_idx - {i}
        idx = indice_com_jargao(records, subset)
        for key, v in idx.items():
            delta = abs(v - baseline[key])
            loo_deltas[termo].append(delta)

    print("\n=== Sensibilidade leave-one-out (top 10 termos que mais mudam o indice) ===")
    loo_avg = sorted(
        ((termo, sum(ds) / len(ds), max(ds)) for termo, ds in loo_deltas.items()),
        key=lambda x: -x[1],
    )
    for termo, avg_d, max_d in loo_avg[:10]:
        print(f"  {termo:30s} delta medio={avg_d:.3f}pp  delta maximo={max_d:.2f}pp")

    # --- subamostragem aleatoria: 200 sorteios de 80% da lista de jargao ---
    random.seed(20260825)  # fixo para reprodutibilidade -- unico uso de random neste script
    n_draws = 200
    per_cand_values = defaultdict(list)
    keep_n = max(1, int(len(JARGAO_TERMOS) * 0.8))
    idx_list = list(range(len(JARGAO_TERMOS)))
    for _ in range(n_draws):
        subset = set(random.sample(idx_list, keep_n))
        idx = indice_com_jargao(records, subset)
        for key, v in idx.items():
            per_cand_values[key].append(v)

    print(f"\n=== Faixa de variacao do indice sob {n_draws} subamostras de 80% da lista de jargao (amostra de candidatos) ===")
    faixa_larguras = []
    for key, vals in per_cand_values.items():
        lo, hi = min(vals), max(vals)
        faixa_larguras.append(hi - lo)
    faixa_larguras.sort()
    print(f"  largura media da faixa: {sum(faixa_larguras)/len(faixa_larguras):.2f}pp")
    print(f"  largura mediana: {faixa_larguras[len(faixa_larguras)//2]:.2f}pp")
    print(f"  largura maxima: {max(faixa_larguras):.2f}pp")

    # --- indice de cobertura alternativo ---
    by_cand_cov = defaultdict(lambda: {"n_base": 0, "n_commit_no_base": 0, "nome": None, "n_ret_atual": 0})
    for r in records:
        key = (r["estado"], r["slug"])
        by_cand_cov[key]["nome"] = r["nome"]
        if r["com_base"]:
            by_cand_cov[key]["n_base"] += 1
        else:
            if r["retorica_sem_evidencia"]:
                by_cand_cov[key]["n_ret_atual"] += 1
            if PROPOSAL_RE.search(r["frase"]):
                by_cand_cov[key]["n_commit_no_base"] += 1

    cov_rows = []
    for key, d in by_cand_cov.items():
        n_cov = d["n_base"] + d["n_commit_no_base"]
        idx_cov = round(d["n_base"] / n_cov * 100, 2) if n_cov else 0.0
        idx_atual = baseline[key]
        cov_rows.append({
            "estado": key[0], "slug": key[1], "nome": d["nome"],
            "indice_atual_pct": idx_atual,
            "indice_cobertura_pct": idx_cov,
            "n_base": d["n_base"], "n_ret_atual": d["n_ret_atual"],
            "n_commit_no_base": d["n_commit_no_base"],
        })

    import csv
    out_csv = OUT_DIR / "indice_cobertura_alternativo.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cov_rows[0].keys())
        w.writeheader()
        w.writerows(cov_rows)
    print(f"\nSalvo: {out_csv}")

    from scipy import stats
    a = [r["indice_atual_pct"] for r in cov_rows]
    b = [r["indice_cobertura_pct"] for r in cov_rows]
    r_pearson, p_pearson = stats.pearsonr(a, b)
    r_spearman, p_spearman = stats.spearmanr(a, b)
    print(f"\nCorrelacao indice atual x indice de cobertura: Pearson r={r_pearson:.3f} (p={p_pearson:.4f}) | Spearman rho={r_spearman:.3f} (p={p_spearman:.4f})")
    print(f"Media indice atual: {sum(a)/len(a):.2f}%  |  Media indice cobertura: {sum(b)/len(b):.2f}%")
    n_commit_total = sum(r["n_commit_no_base"] for r in cov_rows)
    n_base_total = sum(r["n_base"] for r in cov_rows)
    print(f"Total frases de compromisso sem base empirica (n_commit_no_base): {n_commit_total}")
    print(f"Total frases com base empirica (n_base): {n_base_total}")
    print(f"Denominador do indice de cobertura eh {n_commit_total+n_base_total} frases, vs {n_base_total + sum(r['n_ret_atual'] for r in cov_rows)} do indice atual")


if __name__ == "__main__":
    main()
