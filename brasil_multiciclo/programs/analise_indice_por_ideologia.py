"""
Testa se o Índice de Base Empírica (geral e por área de política pública)
varia conforme a ideologia do partido (BLS Zucco & Power, ver
ideologia_partidaria_bls.py).

Pedido do usuário (17/10/2026): "vamos verificar se a base empírica por área
varia conforme o partido. Use o BLS de Zucco e Power mais recente para
classificar as ideologias partidárias."

Unidade de análise: PARTIDO (não candidato) -- a ideologia é uma característica
do partido, não do candidato individual, então agregar por partido evita
pseudo-replicação (ex. PT com 61 candidaturas não deveria pesar 61x mais que
um partido com N=5 numa correlação ingênua a nível de candidato). Mesma
disciplina de corte por N já usada no projeto (dashboard "por partido":
n_efetivo >= 10; aqui, por ser uma amostra de partidos menor e mais exploratória,
uso n_candidaturas >= 5, com nota clara de quais ficam de fora).

Uso: python3 analise_indice_por_ideologia.py
Saída: analise/indice_por_ideologia_partidaria.json (tabela partido x ideologia
x índice geral x índice por área) + correlações impressas no console.
"""
import json
import sys
from collections import defaultdict

sys.path.insert(0, "/home/claude/brasil_multiciclo/programs")
from ideologia_partidaria_bls import ideologia_partido  # noqa: E402

BASE = "/home/claude/brasil_multiciclo"
N_MINIMO = 5


def media(vals):
    return round(sum(vals) / len(vals), 3) if vals else None


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return cov / (sx * sy)


def spearman(xs, ys):
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks
    return pearson(rank(xs), rank(ys))


def main():
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)
    with open(f"{BASE}/analise/indice_por_dominio.json", encoding="utf-8") as f:
        dominio_rows = json.load(f)

    # --- índice geral por partido ---
    por_partido_geral = defaultdict(list)
    for r in painel:
        if r.get("TEXTO_EXTRAIVEL") is False or r.get("INDICE_BASE_EMPIRICA") is None:
            continue
        por_partido_geral[r["SG_PARTIDO"]].append(r["INDICE_BASE_EMPIRICA"])

    # --- índice por área por partido ---
    DOMINIOS = ["saude", "educacao", "seguranca", "economia", "meio_ambiente"]
    por_partido_dominio = defaultdict(lambda: defaultdict(list))
    for row in dominio_rows:
        if row["indice_dominio"] is None:
            continue
        por_partido_dominio[row["partido"]][row["dominio"]].append(row["indice_dominio"])

    tabela = []
    for p in sorted(por_partido_geral):
        n = len(por_partido_geral[p])
        ideo = ideologia_partido(p)
        linha = {
            "partido": p, "n_candidaturas": n, "ideologia_bls": ideo,
            "indice_geral_medio": media(por_partido_geral[p]),
        }
        for d in DOMINIOS:
            linha[f"indice_{d}_medio"] = media(por_partido_dominio[p].get(d, []))
        tabela.append(linha)

    with open(f"{BASE}/analise/indice_por_ideologia_partidaria.json", "w", encoding="utf-8") as f:
        json.dump(tabela, f, ensure_ascii=False, indent=2)

    # --- filtro para correlação: N >= 5 e ideologia conhecida ---
    validos = [l for l in tabela if l["n_candidaturas"] >= N_MINIMO and l["ideologia_bls"] is not None]
    print(f"Partidos no painel: {len(tabela)} | com N>={N_MINIMO} e score BLS: {len(validos)}")
    print(f"Candidaturas cobertas nesses partidos: {sum(l['n_candidaturas'] for l in validos)} de {len(painel)}\n")

    print(f"{'partido':<14}{'N':>4}{'ideologia':>11}{'ind.geral':>11}"
          f"{'saude':>8}{'educ':>8}{'segur':>8}{'econ':>8}{'ambi':>8}")
    for l in sorted(validos, key=lambda x: x["ideologia_bls"]):
        print(f"{l['partido']:<14}{l['n_candidaturas']:>4}{l['ideologia_bls']:>11.3f}"
              f"{(l['indice_geral_medio'] or 0):>11.2f}"
              f"{(l['indice_saude_medio'] or 0):>8.2f}{(l['indice_educacao_medio'] or 0):>8.2f}"
              f"{(l['indice_seguranca_medio'] or 0):>8.2f}{(l['indice_economia_medio'] or 0):>8.2f}"
              f"{(l['indice_meio_ambiente_medio'] or 0):>8.2f}")

    print("\n=== Correlação (nível partido, N>=%d, score BLS disponível) ===" % N_MINIMO)
    xs = [l["ideologia_bls"] for l in validos]
    alvos = {"índice geral": "indice_geral_medio"}
    for d in DOMINIOS:
        alvos[f"área: {d}"] = f"indice_{d}_medio"

    resultado_corr = {}
    for nome, campo in alvos.items():
        pares = [(l["ideologia_bls"], l[campo]) for l in validos if l[campo] is not None]
        if len(pares) < 3:
            continue
        xs_, ys_ = zip(*pares)
        r_pearson = pearson(list(xs_), list(ys_))
        r_spearman = spearman(list(xs_), list(ys_))
        resultado_corr[nome] = {"n_partidos": len(pares), "pearson_r": round(r_pearson, 3) if r_pearson is not None else None,
                                 "spearman_rho": round(r_spearman, 3) if r_spearman is not None else None}
        print(f"{nome:<16} n={len(pares):>2}  Pearson r={r_pearson:+.3f}  Spearman ρ={r_spearman:+.3f}")

    with open(f"{BASE}/analise/correlacao_indice_ideologia.json", "w", encoding="utf-8") as f:
        json.dump(resultado_corr, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo em: {BASE}/analise/indice_por_ideologia_partidaria.json")
    print(f"Salvo em: {BASE}/analise/correlacao_indice_ideologia.json")


if __name__ == "__main__":
    main()
