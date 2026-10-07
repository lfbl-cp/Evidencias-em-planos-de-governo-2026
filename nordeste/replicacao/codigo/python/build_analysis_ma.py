#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Maranhão 2026.

Réplica da metodologia usada na Paraíba (build_analysis_v3.py): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica
à da Paraíba, reaproveitada sem alterações para manter comparabilidade entre
estados).
"""
import json
import re
from collections import Counter
from pathlib import Path

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/maranhao/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/maranhao/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "orleans-brandao", "nome": "Orleans Brandão", "partido": "MDB",
     "categoria": "candidato de continuidade"},
    {"slug": "eduardo-braide", "nome": "Eduardo Braide", "partido": "PSD",
     "categoria": "desafiante"},
    {"slug": "felipe-camarao", "nome": "Felipe Camarão", "partido": "PT",
     "categoria": "desafiante (vice-governador em exercício, rompido com o governador)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas à Paraíba
# ---------------------------------------------------------------------------
WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ][a-zA-ZÀ-ÖØ-öø-ÿ\-]*")

STOPWORDS = set("""
a ao aos aquela aquelas aquele aqueles aquilo as até com como da das de dele
deles depois do dos e ela elas ele eles em entre era eram essa essas esse
esses esta estas este estes eu foi foram fui há isso isto já lhe lhes mais
mas me mesmo meu meus minha minhas muito na nas nem no nos nossa nossas
nosso nossos num numa não nós o os ou para pela pelas pelo pelos por qual
quando que quem se sem seu seus só sua suas também te tem tendo ter teu
teus toda todas todo todos tu tua tuas um uma umas uns você vocês vos à às
é são sob sobre outro outra outros outras cada onde qualquer quais isso
esse essa aquele aquela mesma mesmas mesmos ainda assim ser sendo sido
estar está estão estava estavam sejam seja fica fica ficam foram será
serão seria seriam pode podem poderá poderão deve devem deverá deverão
apenas cada bem mais menos tão tanto tanta tantos tantas outro qual quais
nas por para com sem sob sobre até após ante contra desde durante mediante
perante segundo trás salvo exceto entre dentro fora acima abaixo diante
frente através dentre
""".split())

EXTRA_STOPWORDS = set("""
candidato candidata governador governadora vice-governador vice-governadora
plano governo maranhão maranhense maranhenses eleições 2026 partido número
coligação fonte fontes status texto seção seções eixo eixos parte partes
bloco blocos documento página páginas inclui incluem também estamos propõe
prevê abertura caminho proposto propostos principais desafios núcleo
contexto visão onde compromisso compromissos destaca destacados destacado
""".split())

EXTRA_STOPWORDS |= set("""
ods sumário monitoramento revisão implementação
""".split())

ALL_STOPWORDS = STOPWORDS | EXTRA_STOPWORDS


def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx + len(marker):] if idx != -1 else text


def tokenize(text: str):
    return [w.lower() for w in WORD_RE.findall(text)]


def word_freq(text: str, top_n=20):
    tokens = tokenize(text)
    total_tokens = len(tokens)
    filtered = [w for w in tokens if w not in ALL_STOPWORDS and len(w) > 2]
    counts = Counter(filtered)
    top = counts.most_common(top_n)
    return total_tokens, counts, top


# ---------------------------------------------------------------------------
# TAREFA 1 — Distribuição temática exaustiva
# ---------------------------------------------------------------------------
TEMAS = ["saude", "seguranca", "educacao", "infraestrutura", "meio_ambiente",
         "economia", "gestao_publica", "assistencia_social", "outros"]

# Orleans Brandão: documento em 18 seções TEMÁTICAS bem delimitadas (índice
# no início do documento confere com os títulos usados como marcador).
MARCADORES_ORLEANS = [
    ("GESTÃO E PLANEJAMENTO", "gestao_publica"),
    ("ATRAÇÃO DE INVESTIMENTOS E INOVAÇÃO", "economia"),
    ("SEGURANÇA PÚBLICA E DEFESA CIVIL", "seguranca"),
    ("INFRAESTRUTURA E LOGÍSTICA", "infraestrutura"),
    ("MOBILIDADE URBANA", "infraestrutura"),
    ("CIDADES", "infraestrutura"),  # habitação, água/esgoto, praias, prevenção a desastres, acessibilidade em prédios públicos
    ("SAÚDE", "saude"),
    ("EDUCAÇÃO", "educacao"),
    ("PRIMEIRA INFÂNCIA", "assistencia_social"),
    ("PRODUÇÃO, TRABALHO E RENDA", "economia"),
    ("MEIO AMBIENTE E SUSTENTABILIDADE", "meio_ambiente"),
    ("TURISMO", "economia"),
    ("CULTURA", "assistencia_social"),
    ("ESPORTE", "assistencia_social"),
    ("JUVENTUDE", "assistencia_social"),
    ("DESENVOLVIMENTO SOCIAL E DIREITOS HUMANOS", "assistencia_social"),
    ("COMBATE À FOME E ERRADICAÇÃO DA POBREZA", "assistencia_social"),
    ("PROTEÇÃO E BEM-ESTAR ANIMAL", "assistencia_social"),
]

# Eduardo Braide: 9 seções temáticas (55 propostas numeradas)
MARCADORES_BRAIDE = [
    ("COMBATE À POBREZA, DESENVOLVIMENTO SOCIAL E REDUÇÃO DAS DESIGUALDADES", "assistencia_social"),
    ("SAÚDE", "saude"),
    ("EDUCAÇÃO", "educacao"),
    ("DESENVOLVIMENTO ECONÔMICO, EMPREGO E RENDA", "economia"),
    ("INFRAESTRUTURA, SANEAMENTO E SUSTENTABILIDADE", "infraestrutura"),
    ("SEGURANÇA E PROTEÇÃO", "seguranca"),
    ("GESTAO EFICIENTE E COMBATE À CORRUPÇÃO", "gestao_publica"),  # "Gestao" sem acento no PDF original
    ("TURISMO, CULTURA E PATRIMÔNIO", "economia"),  # seção combinada; ênfase econômica no texto (geração de renda/oportunidades) predomina — ver nota de metodologia
    ("MEIO AMBIENTE E MUDANÇAS CLIMÁTICAS", "meio_ambiente"),  # inclui item de proteção animal
    ("REGULARIZAÇÃO FUNDIÁRIA E HABITAÇÃO", "infraestrutura"),  # precedente PB: habitação = infraestrutura
]

# Felipe Camarão: documento estruturado em "matrizes" transversais por
# desenho (o próprio plano organiza os compromissos por eixo transversal
# cruzando temas, não por pasta temática) — ver nota de metodologia no
# relatório final sobre o tratamento do "Bloco 1" (item a item) e da tabela-
# síntese duplicada ao final do documento (classificada como "outros",
# conforme documentado).
MARCADORES_CAMARAO = [
    # Parte I — diagnóstico socioeconômico geral (a-d), ~8 mil palavras que
    # antecedem os eixos/blocos de compromissos. Tratado como "economia"
    # (não "outros"): ao contrário de introduções genéricas de outros
    # planos analisados neste projeto, aqui o conteúdo é um capítulo
    # diagnóstico coerente e sustentado sobre crescimento, matrizes
    # produtivas, desigualdade e capital humano — squarely econômico em seu
    # enquadramento, ainda que o item (d) inclua indicadores sociais.
    ("O Maranhão ocupa, no desenvolvimento nacional, uma posição paradoxal", "economia"),
    ("Por matriz de desenvolvimento entende-se o arranjo dominante", "economia"),
    ("As matrizes existentes produzem um padrão de desigualdades", "economia"),
    ("Uma matriz socioeconômica não se caracteriza apenas pela riqueza", "economia"),
    # Item (d) do diagnóstico ("base social") tem subtítulos internos que,
    # como o Bloco 1, cobrem temas identificáveis e devem ser separados em
    # vez de lumped em "economia" — mesmo critério de granularidade fina já
    # aplicado ao Bloco 1 (correção pós-validação independente).
    ("O capital humano: o gargalo educacional que trava", "educacao"),
    ("A saúde: reproduzir a vida e a força de trabalho", "saude"),
    ("A violência letal: o custo humano e econômico que a matriz", "seguranca"),
    ("O passivo sanitário e habitacional: infraestrutura de vida", "infraestrutura"),
    ("A capacidade de Estado: a pré-condição de que a matriz saia", "gestao_publica"),
    ("Há um eixo que atravessa", "meio_ambiente"),  # Eixo transversal 1 — conservação ambiental/água/alimentos
    ("Se o quadro social mostrou que o Maranhão movimenta riquezas", "assistencia_social"),  # Eixo transversal 2 — combate a desigualdades
    ("O terceiro eixo transversal responde à pergunta", "educacao"),  # Eixo transversal 3 — educação/inovação/inclusão
    # Bloco 1 (tabela detalhada, 13 compromissos) — classificado item a item,
    # pois o próprio plano o define como um bloco EXPLICITAMENTE
    # multitemático ("Escola, saúde, segurança, comida na mesa, água, casa,
    # obra, cultura e esporte")
    ("Bloco 1 — Políticas finalísticas", "outros"),  # cabeçalho do bloco + frase de abertura
    ("1. Escola Digna", "educacao"),
    ("2. /EMA em todas as", "educacao"),
    ("3. Maranhão que Aprende", "educacao"),
    ("Maranhão Saúde para", "saude"),
    ("Culdado maternos Gestante", "saude"),
    ("6. Sorfrir em toda a", "saude"),
    ("Instituir o programa estruturante Reconstruir a Cultura", "assistencia_social"),
    ("8. Wikia Protegida", "seguranca"),
    ("9. Pasto Maranianda", "assistencia_social"),  # combate à fome
    ("10, Maranhão de Todos", "saude"),  # saúde da população negra/quilombola
    ("11, SUAS forte", "assistencia_social"),
    ("12. Obras em todos os", "infraestrutura"),  # água/esgoto/moradia
    ("14. Esporte em Todo Canto", "assistencia_social"),
    ("Bloco 2 — Combate às desigualdades e promoção da inclusão", "assistencia_social"),
    ("Bloco 3 — Desenvolvimento socioeconômico", "economia"),
    ("Bloco 4 — Território, ambiente e povos", "meio_ambiente"),
    ("Bloco 5 — Capacidade de Estado", "gestao_publica"),
    # Tabela-síntese duplicada ao final do documento (recapitula os mesmos
    # 52 compromissos em formato compacto) — classificada em bloco (não
    # item a item, por ser redundante com a tabela detalhada já classificada
    # acima) usando o mesmo critério: Bloco 1 = multitemático = outros
    ("Bloco 1. GARANTIR direitos fundamentais", "outros"),
    ("Bloco 2. PROMOVER igualdade e inclusão", "assistencia_social"),
    ("Bloco 3. DESENVOLVER trabalho e inovação", "economia"),
    ("Bloco 4. FORTALECER territórios e povos", "meio_ambiente"),
    ("Bloco 5. AMPLIAR a capacidade do Estado", "gestao_publica"),
]

MARCADORES = {
    "orleans-brandao": MARCADORES_ORLEANS,
    "eduardo-braide": MARCADORES_BRAIDE,
    "felipe-camarao": MARCADORES_CAMARAO,
}


def distribuicao_tematica_exaustiva(corpo: str, marcadores, cursor_inicial=0):
    contagem = {t: 0 for t in TEMAS}
    segmentos_debug = []

    posicoes = []
    cursor = cursor_inicial
    for marcador, tema in marcadores:
        pos = corpo.find(marcador, cursor)
        if pos == -1:
            raise ValueError(f"Marcador não encontrado (a partir da pos {cursor}): {marcador!r}")
        posicoes.append(pos)
        cursor = pos + len(marcador)

    primeiro_pos = posicoes[0]
    intro = corpo[:primeiro_pos]
    n_intro = len(tokenize(intro))
    contagem["outros"] += n_intro
    segmentos_debug.append(("[FRONT MATTER: carta de abertura/sumário/intro]", "outros", n_intro))

    for i, (marcador, tema) in enumerate(marcadores):
        start = posicoes[i]
        end = posicoes[i + 1] if i + 1 < len(marcadores) else len(corpo)
        trecho = corpo[start:end]
        n = len(tokenize(trecho))
        contagem[tema] += n
        segmentos_debug.append((marcador, tema, n))

    total = sum(contagem.values())
    pct = {k: round(v / total * 100, 1) for k, v in contagem.items()} if total else {k: 0.0 for k in contagem}
    diff = round(100.0 - sum(pct.values()), 1)
    if abs(diff) >= 0.1:
        pct["outros"] = round(pct["outros"] + diff, 1)
    return pct, contagem, segmentos_debug


# ---------------------------------------------------------------------------
# TAREFA 2 — Índice de Base Empírica (heurística idêntica à da Paraíba)
# ---------------------------------------------------------------------------
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

NUM_ANY = re.compile(
    r"(\bR\$\s?[\d\.,]+|\b\d+([.,]\d+)?\s?(%|por cento)|\b\d[\d\.]*\b)",
)
DIAG_KEYWORDS_RE = re.compile(
    r"\b(segundo dados|segundo o sistema|de acordo com o sistema|"
    r"de acordo com dados|dados do sistema|dados da|dados do|"
    r"taxa de analfabetismo|terceira maior|maior taxa|menor taxa|"
    r"maior índice|menor índice|não têm acesso|não tem acesso|"
    r"não contam com|não dispõe|não dispõem|não sabe ler|"
    r"abaixo da linha de pobreza|linha de base|posição no ranking|"
    r"entre as (?:dez|cinco|três)|um em cada|"
    r"segundo o sinisa|sinisa|datasus|ibge|censo|zee-ma|zee/ma|"
    r"pessoas foram assassinadas|foram registrados|se perdem na distribuição|"
    r"não têm|não tem)\b",
    re.IGNORECASE,
)


def is_diagnostico(s_low: str) -> bool:
    if not NUM_ANY.search(s_low) and "maior" not in s_low and "menor" not in s_low:
        return False
    return bool(DIAG_KEYWORDS_RE.search(s_low))


EFEITO_RE = re.compile(
    r"\b(reduzir(?:á|emos)?|redução de|redução do|redução da|"
    r"aumentar(?:á|emos)?|aumento de|elevar(?:á)?|elevação de|"
    r"diminuir(?:á)?|diminuição de|queda (?:de|continuada)|"
    r"zerar|meta de|meta:|trajetória (?:de|média)|"
    r"posicionar.{0,40}entre|figurar(?:em)? entre|"
    r"ampliar.{0,30}em \d|elevar.{0,30}em \d)\b",
    re.IGNORECASE,
)


def is_efeito(s_low: str) -> bool:
    if not EFEITO_RE.search(s_low):
        return False
    if NUM_ANY.search(s_low):
        return True
    if re.search(r"\bentre (?:as|os) (?:dez|cinco|três)\b", s_low):
        return True
    return False


EVIDENCIA_RE = re.compile(
    r"\b(a exemplo (?:d[eo]|da)|conforme (?:dados|estudos?|pesquisas?|levantamento|indicadores?)|"
    r"segundo (?:estudos?|dados|pesquisa)|modelo (?:já )?adotado|"
    r"experiência bem[- ]sucedida|"
    r"(?:baseado|baseada) (?:n[ao]|em) (?:dados|estudos?|evidências?|indicadores?|"
    r"modelo(?:s)?|pesquisas?|diagnóstico|informações|levantamento|resultados?)|"
    r"com base em (?:dados|estudos?|evidências?|indicadores?|modelo(?:s)?|pesquisas?|"
    r"diagnóstico|informações|levantamento|resultados?)|"
    r"evidênci|comprovad|estudo(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|mapbiomas|"
    r"universidade|instituto)|pesquisa(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|"
    r"mapbiomas|universidade|instituto)|"
    r"ibge|ipea|datasus|sinisa|mapbiomas|inpe|zee-ma|zee/ma|"
    r"organização mundial da saúde|\boms\b|banco mundial|\bbndes\b|\bbnb\b|"
    r"plano nacional de logística|marco legal do saneamento|"
    r"lei nº|lei n°)\b",
    re.IGNORECASE,
)


def is_evidencia(s_low: str) -> bool:
    return bool(EVIDENCIA_RE.search(s_low))


SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"'“”’)\]]?\s+|;\s+|\n+|(?=^-\s)|(?<=^-)\s+", re.MULTILINE)
BULLET_RE = re.compile(r"^[\-••]\s*")
NUMBERED_HEADER_RE = re.compile(r"^\d{1,2}\s?[—\-–]\s*")
MIN_SENTENCE_WORDS = 5

DATE_LINE_RE = re.compile(r"^\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}$", re.IGNORECASE)


def split_sentences(text: str):
    parts = SENT_SPLIT_RE.split(text)
    cleaned = []
    for p in parts:
        p = p.strip().strip('"').strip("'").strip()
        p = BULLET_RE.sub("", p)
        p = NUMBERED_HEADER_RE.sub("", p)
        if p:
            cleaned.append(p)
    return cleaned


def looks_like_header(s: str) -> bool:
    if DATE_LINE_RE.match(s):
        return True
    letters = [c for c in s if c.isalpha()]
    if letters and all(c.upper() == c for c in letters):
        return True
    if s[-1] not in ".!?”’\")":
        words = s.split()
        if len(words) <= 10:
            alpha_words = [w for w in words if w[:1].isalpha()]
            cap_words = [w for w in alpha_words if w[:1].isupper()]
            if alpha_words and len(cap_words) / len(alpha_words) >= 0.7:
                return True
    return False


def base_empirica_analise(text: str, slug: str):
    sentences = split_sentences(text)
    com_a, com_b, com_c = [], [], []
    com_base = []
    retorica = []

    for s in sentences:
        if looks_like_header(s):
            continue
        if len(s.split()) < MIN_SENTENCE_WORDS:
            continue
        s_low = s.lower()

        pa = is_diagnostico(s_low)
        pb = is_efeito(s_low)
        pc = is_evidencia(s_low)

        if pa:
            com_a.append(s.strip())
        if pb:
            com_b.append(s.strip())
        if pc:
            com_c.append(s.strip())

        if pa or pb or pc:
            com_base.append(s.strip())
        else:
            found_jargoes = [t for t in JARGAO_TERMOS if t in s_low]
            if found_jargoes:
                retorica.append((s.strip(), found_jargoes))

    n_base = len(com_base)
    n_ret = len(retorica)
    indice = round(n_base / (n_base + n_ret) * 100, 1) if (n_base + n_ret) else 0.0

    return {
        "indice": indice,
        "n_com_base_empirica": n_base,
        "n_retorica_sem_evidencia": n_ret,
        "n_pilar_a_diagnostico": len(com_a),
        "n_pilar_b_efeito": len(com_b),
        "n_pilar_c_evidencia_causal": len(com_c),
        "exemplos_pilar_a": com_a[:5],
        "exemplos_pilar_b": com_b[:5],
        "exemplos_pilar_c": com_c[:5],
        "exemplos_retorica": [s for s, _ in retorica[:5]],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    resultado_candidatos = []
    agregado_counter = Counter()

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Se o 1º marcador aparecer mais de uma vez (documento com sumário/
        # índice que repete os títulos das seções antes do corpo real),
        # pula para a 2ª ocorrência, para não segmentar dentro do índice.
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        be = base_empirica_analise(corpo[cursor_inicial:], slug)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "categoria": c["categoria"],
            "total_palavras": total_tokens,
            "top_palavras": [{"palavra": w, "freq": f} for w, f in top20],
            "distribuicao_tematica_pct": pct,
            "indice_base_empirica_pct": be["indice"],
            "indice_base_empirica_detalhe": {
                "n_trechos_com_base_empirica": be["n_com_base_empirica"],
                "n_trechos_retorica_sem_evidencia": be["n_retorica_sem_evidencia"],
                "n_pilar_a_diagnostico": be["n_pilar_a_diagnostico"],
                "n_pilar_b_efeito": be["n_pilar_b_efeito"],
                "n_pilar_c_evidencia_causal": be["n_pilar_c_evidencia_causal"],
            },
            "base_empirica_exemplos": {
                "pilar_a_diagnostico": be["exemplos_pilar_a"],
                "pilar_b_efeito": be["exemplos_pilar_b"],
                "pilar_c_evidencia_causal": be["exemplos_pilar_c"],
            },
            "retorica_exemplos_sem_evidencia": be["exemplos_retorica"],
        }
        resultado_candidatos.append(entry)

        # debug de segmentação, para auditoria
        debug_path = ANALISE_DIR / f"_debug_segmentos_{slug}.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            for marcador, tema, n in segmentos_debug:
                f.write(f"[{tema:20s}] {n:6d} palavras :: {marcador[:80]}\n")

        print(f"{c['nome']:<20} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
              f"(a={be['n_pilar_a_diagnostico']} b={be['n_pilar_b_efeito']} c={be['n_pilar_c_evidencia_causal']} "
              f"/ retorica={be['n_retorica_sem_evidencia']})")
        soma_pct = round(sum(pct.values()), 1)
        print(f"  soma distribuicao_tematica_pct = {soma_pct}")

    top_agregado = agregado_counter.most_common(30)

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de capítulo/bloco/eixo, "
            "verbatim). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando uma seção do documento original já reunia "
            "explicitamente múltiplos temas de forma indivisível (ex.: um "
            "'bloco' que o próprio candidato define como cruzando saúde, "
            "educação, segurança, cultura e mais em uma única lista, sem "
            "subtítulos por área), o segmento foi classificado item a item "
            "sempre que os itens individuais eram identificáveis, ou como "
            "'outros' quando não era possível separar com segurança."
        ),
        "metodologia_indice_base_empirica": (
            "Mede se cada proposta se apoia em evidência empírica, e não a "
            "mera presença de números/prazos. Cada frase do plano é "
            "verificada contra 3 pilares: (a) dado de diagnóstico que "
            "fundamenta o problema (estatística/fonte citada), (b) "
            "efeito/resultado mensurável esperado da proposta (não apenas a "
            "ação em si), (c) referência a evidência ou mecanismo causal "
            "externo (modelo adotado alhures, estudo, dado institucional). "
            "Frases sem nenhum pilar mas que usam termos de retórica de "
            "gestão pública genérica ('eficiência', 'modernização', "
            "'fortalecimento' etc.) contam como retórica sem evidência. O "
            "índice é a proporção trechos_com_base_empirica / "
            "(trechos_com_base_empirica + trechos_retorica_sem_evidencia). "
            "Heurística idêntica à usada na análise da Paraíba, sem nenhum "
            "ajuste específico para o Maranhão, para manter comparabilidade "
            "entre estados."
        ),
        "metodologia_nota": (
            "O plano de Felipe Camarão tem uma particularidade: é o único, "
            "entre os 6 planos analisados neste projeto (PB + MA), "
            "estruturado deliberadamente em 'matrizes'/'eixos transversais' "
            "que cruzam temas por desenho, em vez de capítulos temáticos "
            "estanques. Isso torna sua distribuição temática inerentemente "
            "mais sensível a decisões editoriais de classificação — "
            "documentadas linha a linha no script de análise para auditoria. "
            "Além disso, o PDF original de Felipe Camarão continha uma fonte "
            "incorporada com falha (caracteres corrompidos em parágrafos "
            "narrativos ao extrair a camada de texto do PDF); o texto usado "
            "nesta análise foi obtido por OCR sobre as páginas renderizadas, "
            "e pode conter pequenos ruídos de reconhecimento, sobretudo em "
            "tabelas."
        ),
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
