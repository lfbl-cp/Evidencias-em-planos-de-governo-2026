"""
Classificação ideológica dos partidos do painel pelo Brazilian Legislative
Survey (BLS) de Zucco & Power — onda mais recente disponível (BLS9, 56ª
legislatura, entrevistas em 2021).

Pedido do usuário (17/10/2026): "vamos verificar se a base empírica por área
varia conforme o partido. Use o BLS de Zucco e Power mais recente para
classificar as ideologias partidárias."

FONTE: Zucco, Cesar & Power, Timothy J. (2024). "The Ideology of Brazilian
Parties and Presidents: A Research Note on Coalitional Presidentialism Under
Stress." Latin American Politics and Society 66(1). Tabela C1 do material
suplementar (nove ondas do BLS, 1990–2021; 48ª a 56ª legislatura) —
https://static.cambridge.org/content/id/urn:cambridge.org:id:article:S1531426X23000249/resource/name/S1531426X23000249sup001.pdf

Escala: estimativa de posição esquerda-direita centrada em 0, aproximadamente
entre -1 (mais à esquerda) e +1 (mais à direita) — não é a escala 0-10 bruta
da pergunta de survey, é uma transformação dos autores (IRT/escala contínua).

IMPORTANTE -- limitações desta classificação, registradas aqui e no CLAUDE.md:

1. O BLS entrevista DEPUTADOS FEDERAIS eleitos. Partidos pequenos que nunca
   elegeram (ou raramente elegem) bancada federal não têm estimativa própria
   -- isso inclui boa parte da esquerda marginal que apareceu nos achados
   anteriores do projeto (PCO, PCB, UP não têm NENHUMA linha na Tabela C1;
   PSTU tem uma única observação, de uma única onda, com erro-padrão alto --
   tratar como muito incerta, não como medida confiável).
2. Partidos que mudaram de nome/sigla foram mapeados para a mesma linhagem
   quando a continuidade é bem documentada (número do partido no TSE mantido,
   fusão/renomeação oficial) -- ver dicionário `RENOMEACOES` abaixo. Quando a
   linhagem é incerta (ex. "DEMOCRATA" no painel 2026 -- não está claro se é a
   mesma linhagem do extinto DEM, que já havia se fundido ao União Brasil em
   2021), a sigla fica SEM pontuação em vez de arriscar um mapeamento errado.
3. A extração do PDF (via WebFetch, não há acesso a planilha bruta) não
   permitiu recuperar o ano exato de cada observação para partidos com série
   incompleta (linhas "esparsas"). Usei o ÚLTIMO valor dispon vel na tabela
   para cada partido (a estimativa mais recente que a extração conseguiu
   identificar com confiança) -- não necessariamente a onda de 2021 para
   todos. Isso é uma classificação ideológica ESTÁTICA (um valor por
   partido, aplicado a todos os 4 ciclos do painel), não uma correspondência
   onda-a-onda por ciclo eleitoral -- consistente com o pedido do usuário
   ("BLS mais recente", singular).
4. Esta tabela foi montada por extração assistida de PDF (WebFetch), não por
   acesso à planilha de replicação original (Harvard Dataverse,
   10.7910/DVN/6KVTUV, não acessível neste ambiente) -- plausível mas não
   100% garantido estar livre de erro de transcrição. Antes de publicar
   qualquer resultado baseado nisso, revisar os números abaixo contra o PDF
   original ou a planilha de replicação.

Uso: `from ideologia_partidaria_bls import ideologia_partido` ou rodar este
arquivo diretamente para ver a tabela completa + cobertura do painel.
"""

# Partidos com série completa (9 ondas, 1990-2021) na Tabela C1 -- valor usado
# é SEMPRE o de 2021 (coluna mais recente, mapeamento confiável por posição).
IDEOLOGIA_BLS_COMPLETA = {
    "PCDOB": -0.822,   # PC do B
    "PT": -0.691,
    "PSB": -0.427,
    "PDT": -0.356,
    "CID": -0.014,     # Cidadania (ex-PPS)
    "MDB": 0.137,      # ex-PMDB
    "PSDB": 0.157,
    "DEM": 0.431,      # ex-PFL; fundido ao União Brasil em 2021 (ver UNIAO)
    "PTB": 0.455,
    "PL": 0.493,       # linhagem PL(antigo)/PR/PL(atual) -- mesmo número TSE 22
    "PP": 0.510,
}

# Partidos com série esparsa -- uso o ÚLTIMO valor identificado na extração
# (ver limitação #3 acima: ano exato nem sempre determinável).
IDEOLOGIA_BLS_ESPARSA = {
    "PSOL": -0.874,
    "REDE": -0.555,
    "PSTU": -0.826,    # ÚNICA observação em toda a série -- tratar com cautela extrema
    "PV": -0.069,
    "PROS": 0.032,
    "SD": 0.190,       # Solidariedade
    "PSD": 0.296,      # PSD atual (Kassab, fundado 2011)
    "PODE": 0.386,     # Podemos -- linhagem PTN/PHS
    "REP": 0.550,      # Republicanos -- linhagem PRB
    "PSC": 0.596,
    "PSL": 0.803,
    "NOVO": 0.711,
}

# Combinação direta (sigla da Tabela C1 -> score)
_IDEOLOGIA_BLS = {**IDEOLOGIA_BLS_COMPLETA, **IDEOLOGIA_BLS_ESPARSA}

# Construção especial -- não é observação direta do survey, é a MÉDIA PONDERADA
# publicada pelos próprios autores para o União Brasil (fusão DEM+PSL, 2023),
# já que não há pesquisa com deputados eleitos pela sigla nova.
_IDEOLOGIA_BLS["UNIAO"] = 0.66  # Zucco & Power (2024): média ponderada DEM(0.431)+PSL(0.803) na fusão

# Mapa: sigla como aparece no painel brasil_multiciclo (SG_PARTIDO, por ciclo)
# -> sigla da Tabela C1 do BLS (linhagem equivalente). Documentado por que
# cada mapeamento foi feito (renomeação oficial confirmada via TSE/imprensa).
RENOMEACOES = {
    # --- mapeamentos diretos (mesma sigla) ---
    "PT": "PT", "PSB": "PSB", "PDT": "PDT", "PSDB": "PSDB", "DEM": "DEM",
    "PTB": "PTB", "PP": "PP", "PSOL": "PSOL", "REDE": "REDE", "PSTU": "PSTU",
    "PV": "PV", "PROS": "PROS", "PSD": "PSD", "PODE": "PODE", "PSC": "PSC",
    "PSL": "PSL", "NOVO": "NOVO",
    # --- renomeações/fusões confirmadas ---
    "PC do B": "PCDOB",          # grafia do TSE com espaço
    "PMDB": "MDB",                # renomeado 2017
    "PPS": "CID",                 # renomeado "Cidadania" 2019
    "CIDADANIA": "CID",
    "PR": "PL",                   # "Partido da República" renomeado PL 2022, mesmo nº TSE 22
    "PRB": "REP",                 # renomeado "Republicanos" 2019
    "REPUBLICANOS": "REP",
    "PTN": "PODE",                # PTN virou Podemos (2017); PHS fundido depois (2019)
    "PHS": "PODE",
    "SD": "SD", "SOLIDARIEDADE": "SD",
    "PTC": None,                  # renomeado "Agir" 2022 -- SEM score próprio no BLS (não eleito bancada federal)
    "AGIR": None,
    "UNIÃO": "UNIAO",
    # --- sem score BLS confiável (partido pequeno, nunca/raramente elegeu bancada federal,
    #     ou linhagem pós-fusão ambígua demais para mapear com segurança) ---
    "PCB": None, "PCO": None, "UP": None,
    "PATRIOTA": None, "PRTB": None, "PRP": None, "PPL": None, "PMN": None,
    "MOBILIZA": None,             # ex-PMN, mesma incerteza
    "PT do B": None, "AVANTE": None,   # PT do B virou Avante (2017) -- sem score
    "PSDC": None, "DC": None,     # PSDC virou Democracia Cristã -- sem score
    "PHS2": None,
    "PMB": None, "PTC2": None,
    "DEMOCRATA": None,            # linhagem incerta (ver limitação #2) -- NÃO mapeado para DEM
    "MISSÃO": None, "PRD": None,  # partidos muito novos (2026), sem histórico BLS
}


def ideologia_partido(sg_partido):
    """Retorna o score de ideologia BLS (-1 a +1, negativo=esquerda) para a
    sigla do painel, ou None se não houver classificação confiável."""
    alvo = RENOMEACOES.get(sg_partido, sg_partido if sg_partido in _IDEOLOGIA_BLS else None)
    if alvo is None:
        return None
    return _IDEOLOGIA_BLS.get(alvo)


if __name__ == "__main__":
    import json
    with open("/home/claude/brasil_multiciclo/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)

    partidos_painel = sorted({r["SG_PARTIDO"] for r in painel})
    print(f"{'partido (painel)':<18}{'score BLS':>12}  cobertura")
    com_score = sem_score = 0
    for p in partidos_painel:
        s = ideologia_partido(p)
        if s is None:
            sem_score += 1
            print(f"{p:<18}{'--':>12}  SEM classificação BLS")
        else:
            com_score += 1
            print(f"{p:<18}{s:>12.3f}  ok")

    n_candidaturas_com_score = sum(1 for r in painel if ideologia_partido(r["SG_PARTIDO"]) is not None)
    print(f"\n{com_score}/{len(partidos_painel)} siglas do painel com score BLS "
          f"({n_candidaturas_com_score}/{len(painel)} candidaturas, {sem_score} siglas sem cobertura)")
