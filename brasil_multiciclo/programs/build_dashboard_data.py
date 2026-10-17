"""
Gera data.json (uma linha por candidatura) e aggregates.json (trend/incumbência/
resultado/região/partido pré-computados) para o dashboard multiciclo, a partir do
painel final (analise/painel_governador_2014_2026.json).

NOTA (09/10/2026): casos com TEXTO_EXTRAIVEL==False (PDF entregue mas ilegível
mesmo após OCR -- ver CLAUDE.md item 10) entram em data.json com indice=null
(não 0.0), e são excluídos de toda média/mediana em aggregates.json -- tratar
como dado faltante, nunca como índice zero.

NOTA (15/10/2026): o agregado "por partido" agora é ciente de duplicação de
template (ver CLAUDE.md "duplicação de template infla N de alguns partidos" e
programs/detectar_duplicatas_texto.py). Cada partido aparece com `n` (candidaturas
nominais), `n_efetivo` (textos distintos -- um cluster de template repetido conta
1 vez) e `media` calculada por texto único (média das médias de cada cluster, não
das 42 linhas cruas no caso do PCO). O corte de inclusão no card usa n_efetivo>=10,
não mais n nominal>=15 -- isso tira o PCO do gráfico (n_efetivo=7) sem tirar
partidos genuinamente bem-representados.

Uso: python3 build_dashboard_data.py
Saída: ../../tmp .../scratchpad/dashboard/data.json e aggregates.json (caminho
fixo abaixo -- ajustar OUT_DIR se o diretório do dashboard mudar de sessão).
"""
import json
import statistics

PAINEL = "/home/claude/brasil_multiciclo/analise/painel_governador_2014_2026.json"
OUT_DIR = "/tmp/claude-0/-home-claude/0fc5a4d6-a5e8-5caf-b591-b610e5c5099f/scratchpad/dashboard"

REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def media(vals):
    return round(sum(vals) / len(vals), 2) if vals else None


def mediana(vals):
    return round(statistics.median(vals), 2) if vals else None


def main():
    with open(PAINEL, encoding="utf-8") as f:
        painel = json.load(f)

    data = []
    for r in painel:
        extraivel = r.get("TEXTO_EXTRAIVEL")
        indice = r.get("INDICE_BASE_EMPIRICA") if extraivel is not False else None
        data.append({
            "ano": r["ANO"],
            "uf": r["SG_UF"],
            "regiao": REGIAO.get(r["SG_UF"], "?"),
            "sq": r.get("SQ_CANDIDATO"),
            "nome": r.get("NM_URNA_CANDIDATO"),
            "partido": r.get("SG_PARTIDO"),
            "resultado": r.get("DS_SIT_TOT_TURNO"),
            "incumbente": r.get("INCUMBENTE"),
            "tem_proposta": r.get("TEM_PROPOSTA_DE_GOVERNO"),
            "n_palavras": r.get("N_PALAVRAS_PROPOSTA"),
            "indice": indice,
            "votos_t1": r.get("VOTOS_TURNO_1"),
            "cluster_id": r.get("CLUSTER_TEXTO_ID"),
        })

    com_indice = [r for r in data if r["indice"] is not None]

    # trend
    trend = []
    for ano in [2014, 2018, 2022, 2026]:
        vals = [r["indice"] for r in com_indice if r["ano"] == ano]
        trend.append({"ano": ano, "n": len(vals), "media": media(vals), "mediana": mediana(vals)})

    # incumbência (2014 não tem dado -- INCUMBENTE é None)
    incumbencia = []
    for ano in [2018, 2022, 2026]:
        inc = [r["indice"] for r in com_indice if r["ano"] == ano and r["incumbente"] is True]
        des = [r["indice"] for r in com_indice if r["ano"] == ano and r["incumbente"] is False]
        incumbencia.append({
            "ano": ano,
            "incumbente": {"n": len(inc), "media": media(inc)},
            "desafiante": {"n": len(des), "media": media(des)},
        })

    # resultado (2026 ainda não ocorreu -- sem ELEITO/NÃO ELEITO)
    resultado = []
    for ano in [2014, 2018, 2022]:
        eleito = [r["indice"] for r in com_indice if r["ano"] == ano and r["resultado"] == "ELEITO"]
        nao_eleito = [r["indice"] for r in com_indice if r["ano"] == ano and r["resultado"] == "NÃO ELEITO"]
        resultado.append({
            "ano": ano,
            "eleito": {"n": len(eleito), "media": media(eleito)},
            "nao_eleito": {"n": len(nao_eleito), "media": media(nao_eleito)},
        })

    # região
    regiao_agg = []
    for reg in sorted({r["regiao"] for r in com_indice}, key=lambda rg: -len([x for x in com_indice if x["regiao"] == rg])):
        vals = [r["indice"] for r in com_indice if r["regiao"] == reg]
        regiao_agg.append({"regiao": reg, "n": len(vals), "media": media(vals)})

    # partido -- ciente de duplicação de template (ver nota no topo do arquivo).
    # Agrupa por (partido, cluster_id): um template repetido em N estados conta como
    # 1 observação (n_efetivo), não N. Corte de inclusão no card: n_efetivo >= 10.
    partidos_clusters = {}
    for r in com_indice:
        p = r["partido"]
        cid = r["cluster_id"] or f"solo_{r['sq']}"
        partidos_clusters.setdefault(p, {}).setdefault(cid, []).append(r["indice"])

    partido_agg = []
    for p, clusters in partidos_clusters.items():
        n_nominal = sum(len(v) for v in clusters.values())
        n_efetivo = len(clusters)
        medias_por_cluster = [sum(v) / len(v) for v in clusters.values()]
        media_dedup = round(sum(medias_por_cluster) / len(medias_por_cluster), 2)
        media_nominal = media([x for v in clusters.values() for x in v])
        if n_efetivo >= 10:
            # "n" = n_efetivo (textos únicos) de propósito: é o que o tooltip do dashboard
            # mostra como "(n=X)", e o correto a mostrar é o N de observações independentes,
            # não a contagem nominal de candidaturas (que infla quando há template repetido).
            partido_agg.append({
                "partido": p, "n": n_efetivo, "n_nominal": n_nominal,
                "media": media_dedup, "media_nominal": media_nominal,
            })
    partido_agg.sort(key=lambda x: -x["n"])

    aggregates = {
        "trend": trend,
        "incumbencia": incumbencia,
        "resultado": resultado,
        "regiao": regiao_agg,
        "partido": partido_agg,
        "total_candidaturas": len(data),
        "total_com_proposta": sum(1 for r in data if r["tem_proposta"]),
        "ciclos": [2014, 2018, 2022, 2026],
    }

    with open(f"{OUT_DIR}/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    with open(f"{OUT_DIR}/aggregates.json", "w", encoding="utf-8") as f:
        json.dump(aggregates, f, ensure_ascii=False, indent=2)

    print(f"data.json: {len(data)} linhas ({len(com_indice)} com índice válido)")
    print(f"aggregates.json salvo em {OUT_DIR}")
    print(json.dumps(trend, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
