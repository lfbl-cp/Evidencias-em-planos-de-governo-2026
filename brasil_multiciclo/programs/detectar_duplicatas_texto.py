"""
Detecta candidaturas que reaproveitam o MESMO texto de proposta de governo
(template nacional de partido, ou qualquer outra duplicação) em todo o painel
-- não só os 4 partidos checados manualmente em 14/10/2026 (ver CLAUDE.md,
"duplicação de template infla N de alguns partidos").

Método: shingles de 12 palavras, similaridade de Jaccard, agrupamento por
componente conexo (limiar 0.85) -- mesmo método da checagem original, agora
aplicado a TODO o painel (não só partidos com n>=5), para que qualquer partido
com esse problema seja pego, não só os já conhecidos.

Agrupa por partido (candidatos do mesmo partido em ciclos diferentes também
entram na mesma comparação -- template nacional pode se repetir entre ciclos,
não só dentro de um ciclo).

Uso: python3 detectar_duplicatas_texto.py
Saída: analise/clusters_texto.json -- {"<ano>_<sq>": "<cluster_id>", ...} +
analise/resumo_duplicatas_por_partido.json (N nominal vs. N efetivo por partido)
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from itertools import combinations

sys.path.insert(0, "/home/claude/brasil_multiciclo/programs")
from motor_indice_base_empirica import tokenize  # noqa: E402

BASE = "/home/claude/brasil_multiciclo"
OCR_CACHE = f"{BASE}/ocr_cache"
LIMIAR = 0.85


def extrair_texto(ano, uf, sq, arquivo):
    cache_path = f"{OCR_CACHE}/{ano}_{uf}_{sq}.txt"
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()
    caminho = f"{BASE}/propostas/{ano}/{uf}/{arquivo}"
    try:
        r = subprocess.run(["pdftotext", "-layout", caminho, "-"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60)
        return r.stdout
    except Exception:
        return ""


def shingles(texto, k=12):
    palavras = [w.lower() for w in tokenize(texto)]
    if len(palavras) < k:
        return set()
    return {" ".join(palavras[i:i + k]) for i in range(len(palavras) - k + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def main():
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)
    partido_por_ano_sq = {(str(r["ANO"]), r["SQ_CANDIDATO"]): r.get("SG_PARTIDO") for r in painel}

    todos = []
    for ano in [2014, 2018, 2022, 2026]:
        with open(f"{BASE}/codificacao/indice_base_empirica_{ano}.json", encoding="utf-8") as f:
            regs = json.load(f)
        for r in regs:
            if r["N_PALAVRAS"] > 0:
                r["_partido"] = partido_por_ano_sq.get((r["ANO"], r["SQ_CANDIDATO"]))
                todos.append(r)

    por_partido = defaultdict(list)
    for r in todos:
        if r["_partido"]:
            por_partido[r["_partido"]].append(r)

    print(f"Extraindo texto para {len(todos)} candidaturas em {len(por_partido)} partidos...", flush=True)
    for r in todos:
        r["_sh"] = shingles(extrair_texto(r["ANO"], r["SG_UF"], r["SQ_CANDIDATO"], r["ARQUIVO_PDF"]))

    cluster_por_chave = {}
    resumo = []
    proximo_cluster_id = 0

    for partido, regs in por_partido.items():
        n = len(regs)
        parent = {i: i for i in range(n)}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for i, j in combinations(range(n), 2):
            if jaccard(regs[i]["_sh"], regs[j]["_sh"]) >= LIMIAR:
                union(i, j)

        grupos = defaultdict(list)
        for i in range(n):
            grupos[find(i)].append(i)

        for membros in grupos.values():
            cid = f"c{proximo_cluster_id}"
            proximo_cluster_id += 1
            for i in membros:
                r = regs[i]
                chave = f"{r['ANO']}_{r['SQ_CANDIDATO']}"
                cluster_por_chave[chave] = cid

        maior = max(len(m) for m in grupos.values())
        resumo.append({
            "partido": partido, "n_nominal": n, "n_efetivo": len(grupos), "maior_cluster": maior,
            "reducao_pct": round(100 * (n - len(grupos)) / n, 1) if n else 0,
        })

    resumo.sort(key=lambda x: -(x["n_nominal"] - x["n_efetivo"]))

    with open(f"{BASE}/analise/clusters_texto.json", "w", encoding="utf-8") as f:
        json.dump(cluster_por_chave, f, ensure_ascii=False, indent=2)
    with open(f"{BASE}/analise/resumo_duplicatas_por_partido.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print(f"\n{'partido':<14}{'n nominal':>10}{'n efetivo':>11}{'maior cluster':>15}{'reducao':>10}")
    for r in resumo:
        if r["n_nominal"] != r["n_efetivo"]:
            print(f"{r['partido']:<14}{r['n_nominal']:>10}{r['n_efetivo']:>11}{r['maior_cluster']:>15}{r['reducao_pct']:>9}%")
    print(f"\n{sum(1 for r in resumo if r['n_nominal']!=r['n_efetivo'])} partidos com alguma duplicação "
          f"de {len(resumo)} partidos no total.")
    print(f"\nSalvo em: {BASE}/analise/clusters_texto.json")
    print(f"Salvo em: {BASE}/analise/resumo_duplicatas_por_partido.json")


if __name__ == "__main__":
    main()
