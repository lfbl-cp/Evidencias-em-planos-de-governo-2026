#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Acre 2026 (região Norte).

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver, por
exemplo, /home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py):
distribuição temática exaustiva por segmentação de marcadores de seção reais
(lidos e mapeados à mão) e Índice de Base Empírica (heurística lexical/regex
idêntica à usada em todos os estados anteriores, reaproveitada sem nenhuma
alteração para manter comparabilidade entre estados/regiões).

Caso do Acre: 2 candidatos.
  - Mailza Assis (PP): foi eleita vice-governadora em 2022 na chapa de
    Gladson Cameli (PP) e assumiu o cargo de governadora em 2026, quando
    Cameli renunciou para concorrer ao Senado; concorre em 2026 buscando
    mandato próprio, com apoio declarado do ex-governador — INCUMBENTE POR
    SUCESSÃO.
  - Alan Rick (Republicanos): senador da República (eleito em 2022), deixa o
    mandato no Senado para concorrer ao governo do Acre; embora situado no
    mesmo campo político conservador de Gladson Cameli, é tratado pela
    imprensa como opositor à candidatura de continuidade de Mailza Assis, não
    como aliado do governo estadual atual — DESAFIANTE.
  (Fontes na string de categoria de cada candidato, abaixo.)
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/acre/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/acre/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {
        "slug": "mailza-assis", "nome": "Mailza Assis", "partido": "PP",
        "arquivo": "mailza_assis",
        "categoria": (
            "incumbente por sucessão — eleita vice-governadora em 2022 na "
            "chapa de Gladson Cameli (PP) e empossada governadora em 2026, "
            "quando Cameli renunciou ao cargo para concorrer ao Senado; "
            "concorre a mandato próprio em 2026 com apoio declarado do "
            "ex-governador (fontes: InfoMoney, 'Candidatos a governador do "
            "Acre em 2026'; AcreNews, 'Gladson entrega a faixa e Mailza é a "
            "nova governadora do Acre'; NEPOL, 'Poder, Herança e Disputa: as "
            "peças em movimento nas eleições de 2026 no Acre')"
        ),
        "cursor_inicial_base_empirica": 0,
    },
    {
        "slug": "alan-rick", "nome": "Alan Rick", "partido": "Republicanos",
        "arquivo": "alan_rick",
        "categoria": (
            "desafiante — senador da República (Republicanos), eleito em "
            "2022, deixa o mandato no Senado para concorrer ao governo do "
            "Acre; apesar de situado no mesmo campo político conservador de "
            "Gladson Cameli, é descrito pela imprensa como opositor à "
            "candidatura de continuidade de Mailza Assis (disputa interna "
            "no campo de direita), não como aliado do governo estadual "
            "atual — pesquisa AtlasIntel (jun/2026) mostrava os dois "
            "candidatos empatados na disputa (fontes: NEPOL, 'Poder, "
            "Herança e Disputa: as peças em movimento nas eleições de 2026 "
            "no Acre'; Poder360, 'Mailza Assis e Alan Rick empatam para o "
            "governo do Acre, diz AtlasIntel'; InfoMoney, 'Candidatos a "
            "governador do Acre em 2026')"
        ),
        "cursor_inicial_base_empirica": 986,
    },
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — IDÊNTICAS às usadas em todos os estados do
# Nordeste (não adaptadas ao Acre), para preservar comparabilidade entre
# estados/regiões. Copiadas verbatim de build_analysis_ce.py.
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

# ---------------------------------------------------------------------------
# MAILZA ASSIS (PP) — documento de 68 páginas organizado em Dez Eixos
# Estratégicos ("EIXO 1" a "EIXO 10"), cada um majoritariamente monotemático
# e subdividido internamente em "PROGRAMA N – <título>". Sem sumário/índice
# de página no início repetindo os títulos (diferente do Alan Rick — abaixo),
# então não há problema de "2ª ocorrência do marcador" aqui: a única
# ambiguidade textual é que a substring "EIXO 1" aparece dentro de "EIXO 10"
# (10 = "1" + "0"), mas como os marcadores avançam o cursor em ordem
# crescente (EIXO 1 é buscado antes de EIXO 10 no texto), isso não causa
# nenhum problema de segmentação (confirmado por auditoria de posições).
#
# Todo o texto ANTES do primeiro marcador ("EIXO 1") — mensagem de abertura,
# "O Acre que queremos construir", valores do governo, "Como vamos governar"
# e "Como este Plano está organizado" — cai automaticamente em "outros"
# (front matter), pela lógica padrão do projeto.
#
# Decisões de classificação não óbvias:
#  - Dentro do EIXO 1 (Educação), o "PROGRAMA 5 – Cultura, Conhecimento e
#    Desenvolvimento" foi destacado como "assistencia_social", replicando o
#    precedente do projeto (cultura = assistencia_social, usado em todos os
#    estados do Nordeste). O "PROGRAMA 6 – Governança, Gestão e Cooperação"
#    que o sucede permanece "educacao": trata especificamente da governança
#    da própria Secretaria de Educação e Cultura (SEE) e das instituições de
#    ciência do Estado (FAPAC, FUNTAC, IEPTEC), não de gestão pública geral.
#  - "Ciência, Tecnologia e Inovação" (Programa 3 do Eixo 1) permanece
#    "educacao": a taxonomia de 9 temas do projeto não tem eixo dedicado a
#    C&T, e a candidata agrupa esse conteúdo explicitamente dentro do próprio
#    Eixo de Educação — mesmo precedente usado no Ceará (Elmano de Freitas e
#    Ciro Gomes).
#  - O EIXO 4 ("Proteção, Inclusão e Qualidade de Vida") reúne SUAS,
#    proteção à mulher, autonomia econômica feminina, esporte, juventude e
#    defesa civil sob um único eixo de proteção social — tratado
#    integralmente como "assistencia_social", incluindo os programas de
#    "Mulher que Trabalha, Mulher que Cresce" (qualificação/empreendedorismo
#    para mulheres, mas enquadrado pela candidata como política de inclusão
#    social, não de desenvolvimento econômico) e "Proteção e Defesa Civil"
#    (resposta a desastres climáticos, mas agrupado neste eixo social, e não
#    no eixo ambiental).
#  - O EIXO 9 ("Meio Ambiente, Sustentabilidade e Resiliência Climática")
#    inclui programas como "Floresta que gera renda" (créditos de carbono,
#    bioeconomia) e "Cuidado e Respeito aos Povos Indígenas" (gestão
#    territorial e ambiental de terras indígenas) — mantidos como
#    "meio_ambiente" porque a própria candidata os enquadra dentro do eixo
#    ambiental (não do eixo econômico), e o conteúdo é predominantemente de
#    política de conservação/serviços ambientais, não de desenvolvimento
#    industrial ou agropecuário tradicional (que estão nos Eixos 5 e 6).
#  - Após o EIXO 10 (Gestão), o documento tem um encerramento em prosa ("O
#    ACRE QUE VAMOS CONSTRUIR JUNTOS") seguido de ficha técnica — marcado à
#    parte como "outros" para não inflar artificialmente o peso de
#    "gestao_publica".
MARCADORES_MAILZA = [
    ("EIXO 1", "educacao"),
    ("PROGRAMA 5 – Cultura, Conhecimento e Desenvolvimento", "assistencia_social"),
    ("PROGRAMA 6 – Governança, Gestão e Cooperação", "educacao"),
    ("EIXO 2", "saude"),
    ("EIXO 3", "seguranca"),
    ("EIXO 4", "assistencia_social"),
    ("EIXO 5", "economia"),
    ("EIXO 6", "economia"),
    ("EIXO 7", "infraestrutura"),
    ("EIXO 8", "infraestrutura"),
    ("EIXO 9", "meio_ambiente"),
    ("EIXO 10", "gestao_publica"),
    ("O ACRE QUE VAMOS CONSTRUIR JUNTOS", "outros"),
]

# ---------------------------------------------------------------------------
# ALAN RICK (Republicanos) — documento de 41 páginas organizado em Sete
# Eixos ("EIXO 1" a "EIXO 7"), cada um estritamente monotemático: todo eixo
# segue o mesmo roteiro interno "O DESAFIO QUE TEMOS PELA FRENTE" (diagnóstico)
# → "O CAMINHO QUE VAMOS SEGUIR" (subseções de propostas, sem títulos que
# cruzem para outro tema da taxonomia) → "O QUE MUDA NA VIDA DAS PESSOAS"
# (síntese). Por isso, ao contrário do plano de Mailza Assis, NENHUM eixo
# precisou de sub-marcador: cada EIXO N corresponde integralmente a um único
# tema dos 9 usados no projeto.
#
# O documento tem um SUMÁRIO no início que repete os títulos "EIXO 1" a
# "EIXO 7" (com número de página) — o mesmo problema já visto em vários
# outros estados do Nordeste (Maranhão, Ceará, Piauí, Alagoas etc.).
# Corrigido com a mesma lógica de sempre: o primeiro marcador ("EIXO 1") usa
# sua 2ª ocorrência no texto como ponto de partida da segmentação temática,
# pulando o sumário (função distribuicao_tematica_exaustiva abaixo).
#
# IMPORTANTE — dois cursores DIFERENTES neste plano, por instrução do
# projeto: o cursor que pula o sumário (2ª ocorrência de "EIXO 1") é usado
# SOMENTE na segmentação temática; o Índice de Base Empírica usa um cursor
# fixo diferente (986 caracteres, ponto exato em que "CARTA DE COMPROMISSO"
# começa após o sumário) para excluir o sumário do cálculo de base empírica
# sem depender da lógica de 2ª ocorrência — replicando o padrão adotado em
# build_analysis_al.py (Alagoas).
#
# Decisão de classificação não óbvia: dentro do EIXO 6 (Segurança), a
# subseção final "Proteção Ambiental e Defesa Civil" (Coordenadorias
# Municipais de Defesa Civil, brigadas de incêndio florestal, monitoramento
# de queimadas) permanece "seguranca": o próprio candidato a posiciona
# dentro do eixo de segurança pública (não em um eixo ambiental/social
# separado, como fez Mailza Assis com sua "Proteção e Defesa Civil", mantida
# em "assistencia_social" no plano dela) — a classificação segue a estrutura
# que cada candidato escolheu para o próprio texto.
MARCADORES_ALAN = [
    ("EIXO 1", "economia"),
    ("EIXO 2", "infraestrutura"),
    ("EIXO 3", "educacao"),
    ("EIXO 4", "assistencia_social"),
    ("EIXO 5", "saude"),
    ("EIXO 6", "seguranca"),
    ("EIXO 7", "gestao_publica"),
]

MARCADORES = {
    "mailza-assis": MARCADORES_MAILZA,
    "alan-rick": MARCADORES_ALAN,
}

# Só o plano de Alan Rick tem SUMÁRIO/índice de página que repete o texto do
# 1º marcador antes do corpo real (ver nota acima) — por isso só ele usa a
# lógica de "pular para a 2ª ocorrência". O plano de Mailza Assis não tem
# sumário desse tipo; nele, "EIXO 1" aparece 2x no corpo por um motivo
# puramente ortográfico (é também uma substring literal de "EIXO 10"), o que
# tornaria a lógica de "2ª ocorrência" incorreta se aplicada às cegas — daí
# esta flag explícita por candidato, em vez de detecção automática única.
POSSUI_SUMARIO_REPETIDO = {
    "mailza-assis": False,
    "alan-rick": True,
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
# TAREFA 2 — Índice de Base Empírica (heurística IDÊNTICA à usada em todos os
# estados do Nordeste — copiada verbatim de build_analysis_ce.py)
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
    r"abaixo da linha de pobreza|posição no ranking|"
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
    r"estudo(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|mapbiomas|"
    r"universidade|instituto)|pesquisa(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|"
    r"mapbiomas|universidade|instituto)|"
    r"ibge|ipea|datasus|sinisa|mapbiomas|inpe|zee-ma|zee/ma|"
    r"organização mundial da saúde|\boms\b|banco mundial|\bbndes\b|\bbnb\b|"
    r"plano nacional de logística|marco legal do saneamento|"
    r"lei nº|lei n°)\b",
    re.IGNORECASE,
)

# CORRIGIDO (25/08/2026, validacao Fase 1/2): a versao anterior tinha
# gatilhos genericos "evidênci"/"comprovad" isolados (sem exigir nenhum
# qualificador), que geravam falso positivo em uso tecnico nao-politico
# (ex.: "evidências indiretas (geofísicas...)" em prospeccao mineral). Alem
# disso, adiciona um padrao de citacao academica ("Estudo/Pesquisa NOME
# (FONTE, ANO)") para cobrir referencias a estudos especificos que nao
# citam nenhuma das instituicoes hard-coded acima (falso negativo
# identificado na validacao).
CITACAO_RE = re.compile(
    r"(?:estudo|pesquisa|levantamento|relatório)\s+[A-ZÀ-Ý][\wÀ-ÿ\s]{3,70}?"
    r"\(\s*[A-ZÀ-Ý]{2,15}(?:[\s,][A-ZÀ-Ý][\wÀ-ÿ]*)*,?\s*\d{4}\s*\)",
)


def is_evidencia(s_orig: str, s_low: str) -> bool:
    if EVIDENCIA_RE.search(s_low):
        return True
    if CITACAO_RE.search(s_orig):
        return True
    return False


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


# ADICIONADO (25/08/2026, validacao Fase 1/2): verbos/expressoes de
# compromisso programatico -- usado como o novo denominador do indice
# (substitui "frases com jargao" por "frases de compromisso/proposta", com
# ou sem jargao). E uma escolha de constructo alternativa, testada e
# validada contra a amostra de 265 frases (Spearman rho=0.92 com o indice
# legado) -- ver nota de metodologia.
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

def base_empirica_analise(text: str, slug: str):
    sentences = split_sentences(text)
    com_a, com_b, com_c = [], [], []
    com_base = []
    retorica = []
    compromisso_sem_base = []

    for s in sentences:
        if looks_like_header(s):
            continue
        if len(s.split()) < MIN_SENTENCE_WORDS:
            continue
        s_low = s.lower()

        pa = is_diagnostico(s_low)
        pb = is_efeito(s_low)
        pc = is_evidencia(s.strip(), s_low)

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
            if PROPOSAL_RE.search(s):
                compromisso_sem_base.append(s.strip())

    n_base = len(com_base)
    n_ret = len(retorica)
    n_compromisso = len(compromisso_sem_base)
    # indice_legado: formula original (rodada 1-3), preservada para trilha de
    # auditoria -- denominador = frases-com-jargao.
    indice_legado = round(n_base / (n_base + n_ret) * 100, 1) if (n_base + n_ret) else 0.0
    # indice: CORRIGIDO em 25/08/2026 (validacao Fase 1/2) -- denominador
    # passa a ser "frases de compromisso/proposta sem nenhum pilar", nao so
    # frases-com-jargao. Correlacao de Spearman 0.92 com o indice_legado no
    # projeto inteiro, mas cobre uma fatia mais representativa do texto (ver
    # metodologia/indice_base_empirica/RESULTADOS_FASE1_FASE2_25082026.md).
    indice = round(n_base / (n_base + n_compromisso) * 100, 1) if (n_base + n_compromisso) else 0.0

    return {
        "indice": indice,
        "indice_legado": indice_legado,
        "n_com_base_empirica": n_base,
        "n_retorica_sem_evidencia": n_ret,
        "n_compromisso_sem_base": n_compromisso,
        "n_pilar_a_diagnostico": len(com_a),
        "n_pilar_b_efeito": len(com_b),
        "n_pilar_c_evidencia_causal": len(com_c),
        "exemplos_pilar_a": com_a[:5],
        "exemplos_pilar_b": com_b[:5],
        "exemplos_pilar_c": com_c[:5],
        "exemplos_retorica": [s for s, _ in retorica[:5]],
    }


# ---------------------------------------------------------------------------
# TAREFA 3 — Nuvem de palavras
# ---------------------------------------------------------------------------
def gerar_wordcloud_png_b64(counts: Counter, slug: str) -> str:
    freqs = {w: f for w, f in counts.items() if w not in ALL_STOPWORDS and len(w) > 2}
    wc = WordCloud(width=800, height=500, background_color=None, mode="RGBA",
                   colormap="viridis", prefer_horizontal=0.9, max_words=120)
    wc.generate_from_frequencies(freqs)
    png_path = WC_DIR / f"{slug}.png"
    wc.to_file(str(png_path))
    buf = BytesIO()
    wc.to_image().save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# TAREFA 4 — Texto compartilhado entre os dois planos (n-gramas de 8
# palavras, mesma técnica usada em todos os estados do Nordeste — ver
# find_shared_text_ac.py, executado separadamente; resultado colado abaixo).
# ---------------------------------------------------------------------------
TEXTO_COMPARTILHADO = {
    "pares_comparados": ["mailza-assis_x_alan-rick"],
    "resultado_por_par": {
        "mailza-assis_x_alan-rick": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de texto idêntico (mínimo 150 caracteres, 8 "
                "palavras consecutivas) encontrado entre os dois planos."
            ),
        }
    },
    "metodologia": (
        "Detecção por n-gramas: janelas deslizantes de 8 palavras "
        "consecutivas comparadas entre os dois planos; sequências de "
        "n-gramas idênticos consecutivos são unidas em blocos, e blocos com "
        "menos de 150 caracteres são descartados por serem coincidências "
        "triviais de linguagem comum."
    ),
    "observacao_editorial": (
        "A ausência de blocos de texto idêntico não prova que os planos "
        "foram escritos de forma totalmente independente (podem ter "
        "referenciado as mesmas fontes de dados oficiais, por exemplo), "
        "apenas que não houve cópia literal de trechos redigidos entre os "
        "planos analisados."
    ),
}

ACHADO_TEXTO_COMPARTILHADO = {
    "resumo": (
        "A checagem de blocos de texto idêntico ou quase idêntico entre os "
        "planos não encontrou nenhum bloco compartilhado (mínimo de 150 "
        "caracteres, 8 palavras consecutivas) entre Mailza Assis e Alan "
        "Rick — mesmo padrão observado na maioria dos estados do Nordeste "
        "(Maranhão, Piauí, Ceará, Pernambuco etc.), diferente do que foi "
        "encontrado na Paraíba (onde planos rivais compartilhavam "
        "parágrafos idênticos)."
    ),
    "pares_verificados": ["mailza-assis_x_alan-rick"],
    "blocos_encontrados": 0,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    resultado_candidatos = []
    agregado_counter = Counter()

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{c['arquivo']}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Se o documento tem sumário/índice que repete os títulos das seções
        # antes do corpo real (só o caso do Alan Rick — ver
        # POSSUI_SUMARIO_REPETIDO acima), pula para a 2ª ocorrência do 1º
        # marcador, para não segmentar dentro do índice. (Usado apenas para
        # a DISTRIBUIÇÃO TEMÁTICA — o Índice de Base Empírica usa, para o
        # Alan Rick, um cursor fixo diferente, dado no dicionário
        # CANDIDATOS, seguindo o padrão de build_analysis_al.py.)
        primeiro_marcador = marcadores[0][0]
        n_ocorrencias_1o_marcador = corpo.count(primeiro_marcador)
        if POSSUI_SUMARIO_REPETIDO[slug]:
            primeira_ocorrencia = corpo.find(primeiro_marcador)
            segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
            cursor_inicial_tema = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
        else:
            cursor_inicial_tema = corpo.find(primeiro_marcador)
        print(f"{slug}: 1º marcador ({primeiro_marcador!r}) aparece "
              f"{n_ocorrencias_1o_marcador}x no corpo "
              f"(cursor_inicial_tema={cursor_inicial_tema})")

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial_tema
        )

        cursor_be = c["cursor_inicial_base_empirica"]
        be = base_empirica_analise(corpo[cursor_be:], slug)

        wc_b64 = gerar_wordcloud_png_b64(counts, slug)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "categoria": c["categoria"],
            "total_palavras": total_tokens,
            "top_palavras": [{"palavra": w, "freq": f} for w, f in top20],
            "distribuicao_tematica_pct": pct,
            "indice_base_empirica_pct": be["indice"],
            "indice_base_empirica_legado_pct": be["indice_legado"],
            "indice_base_empirica_detalhe": {
                "n_trechos_com_base_empirica": be["n_com_base_empirica"],
                "n_trechos_retorica_sem_evidencia": be["n_retorica_sem_evidencia"],
                "n_trechos_compromisso_sem_base": be["n_compromisso_sem_base"],
                "n_pilar_a_diagnostico": be["n_pilar_a_diagnostico"],
                "n_pilar_b_efeito_mensuravel": be["n_pilar_b_efeito"],
                "n_pilar_c_evidencia_causal_externa": be["n_pilar_c_evidencia_causal"],
            },
            "base_empirica_exemplos": {
                "pilar_a_dado_diagnostico": be["exemplos_pilar_a"],
                "pilar_b_efeito_mensuravel": be["exemplos_pilar_b"],
                "pilar_c_evidencia_ou_mecanismo_causal": be["exemplos_pilar_c"],
            },
            "retorica_exemplos_sem_evidencia": be["exemplos_retorica"],
            "wordcloud_png_b64": wc_b64,
        }
        resultado_candidatos.append(entry)

        # debug de segmentação, para auditoria
        debug_path = ANALISE_DIR / f"_debug_segmentos_{slug}.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            for marcador, tema, n in segmentos_debug:
                pct_seg = round(n / total_tokens * 100, 1) if total_tokens else 0.0
                f.write(f"[{tema:20s}] {n:6d} palavras ({pct_seg:5.1f}%) :: {marcador[:80]}\n")

        print(f"{c['nome']:<20} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
              f"(a={be['n_pilar_a_diagnostico']} b={be['n_pilar_b_efeito']} c={be['n_pilar_c_evidencia_causal']} "
              f"/ retorica={be['n_retorica_sem_evidencia']})")
        soma_pct = round(sum(pct.values()), 1)
        print(f"  soma distribuicao_tematica_pct = {soma_pct}")

    top_agregado = agregado_counter.most_common(30)

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "23 de agosto de 2026",
        "achado_texto_compartilhado": ACHADO_TEXTO_COMPARTILHADO,
        "texto_compartilhado": TEXTO_COMPARTILHADO,
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto, incluindo termos "
            "específicos de outros estados do Nordeste (como "
            "'maranhão'/'maranhense'), mantidos propositalmente sem ajuste "
            "para preservar comparabilidade metodológica entre estados e "
            "regiões — por isso 'Acre' e 'acreano(a)' NÃO são filtrados e "
            "podem aparecer nos termos mais frequentes. Mostra os termos "
            "mais repetidos por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de Eixo/Programa). Cada "
            "segmento de texto entre dois marcadores consecutivos foi "
            "contado (em número de palavras) e atribuído a UM dos 9 temas. "
            "Quando um trecho do documento original já reunia "
            "explicitamente múltiplos temas de forma indivisível, o "
            "segmento foi classificado item a item sempre que os itens "
            "individuais eram identificáveis, ou como 'outros' quando não "
            "era possível separar com segurança."
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
            "Heurística idêntica à usada em todas as análises anteriores do "
            "projeto (9 estados do Nordeste), sem nenhum ajuste específico "
            "para o Acre, para manter comparabilidade entre estados e "
            "regiões."
        ),
        "metodologia_nota": (
            "O Acre é o primeiro estado analisado fora da região Nordeste "
            "neste projeto (região Norte), com a mesma metodologia aplicada "
            "sem alterações. Contexto eleitoral: Gladson Cameli (PP) "
            "encerrou o mandato de governador em 2026 para concorrer ao "
            "Senado; Mailza Assis, sua vice desde 2022, assumiu o governo e "
            "concorre a mandato próprio (incumbente por sucessão, com apoio "
            "do ex-governador); Alan Rick, senador da República "
            "(Republicanos), deixa o mandato no Senado para concorrer ao "
            "governo como opositor à candidatura de continuidade, apesar de "
            "situado no mesmo campo político conservador — uma disputa "
            "interna ao campo de direita do estado, e não um confronto "
            "clássico entre situação e oposição de campos opostos. Essa é "
            "uma leitura eleitoral, não textual: não influenciou nenhuma "
            "etapa da extração ou classificação dos planos. "
            "Os dois planos têm estruturas muito parecidas — ambos "
            "organizados em Eixos Estratégicos numerados, cada um com "
            "diagnóstico, propostas e síntese de entregas — o que facilitou "
            "a segmentação temática por marcador de seção em ambos os "
            "casos (ao contrário de outros estados do Nordeste, nenhum dos "
            "dois planos do Acre exigiu segmentação parágrafo a parágrafo "
            "dentro de um eixo para separar temas cruzados; a única exceção "
            "é o Eixo 1 do plano de Mailza Assis, onde o Programa 5 "
            "'Cultura, Conhecimento e Desenvolvimento', embutido dentro do "
            "eixo de Educação, foi destacado como sub-marcador próprio para "
            "ser classificado como assistência social, seguindo o precedente "
            "do projeto para conteúdo de cultura). "
            "O plano de Alan Rick tem um SUMÁRIO no início que repete (com "
            "número de página) os mesmos títulos usados como marcador de "
            "seção — o mesmo problema já visto em vários outros estados do "
            "Nordeste (Maranhão, Ceará, Piauí, Alagoas). Corrigido com a "
            "mesma lógica de sempre: o primeiro marcador ('EIXO 1') usa sua "
            "2ª ocorrência no texto como ponto de partida da segmentação "
            "temática, pulando o sumário. Já o cursor usado para o Índice "
            "de Base Empírica do Alan Rick é um valor diferente e fixo (986 "
            "caracteres, o ponto exato em que a 'CARTA DE COMPROMISSO' "
            "começa após o sumário) — replicando o padrão adotado no "
            "Alagoas (build_analysis_al.py), em que os dois cursores "
            "(distribuição temática e base empírica) podem divergir. O "
            "plano de Mailza Assis não tem sumário/índice de página "
            "repetindo títulos, então o cursor de base empírica é 0 "
            "(nenhum corte necessário). "
            "Ressalva importante sobre as citações de exemplo do Alan Rick "
            "(pilares a/b/c e retórica sem evidência): o PDF original usa "
            "layout de duas colunas lado a lado ('O DESAFIO QUE TEMOS PELA "
            "FRENTE' à esquerda, 'O CAMINHO QUE VAMOS SEGUIR' à direita, em "
            "todos os eixos), e a extração para .txt preserva essa "
            "geometria: cada linha física do arquivo contém o fim de uma "
            "linha da coluna esquerda seguido do início da linha "
            "correspondente da coluna direita, unidos por espaços em "
            "branco. Como a função de divisão de frases ('split_sentences', "
            "idêntica à usada em todos os outros estados) trata quebras de "
            "linha como fim de frase, isso produz fragmentos de citação que "
            "misturam texto de diagnóstico com texto de proposta (ex.: uma "
            "frase sobre o Censo do IBGE emenda, na mesma linha do .txt, em "
            "um fragmento não relacionado sobre evasão escolar). Esse "
            "problema é mais acentuado no plano de Alan Rick do que no de "
            "Mailza Assis (que não usa layout de duas colunas lado a lado "
            "do mesmo tipo) e afeta apenas a legibilidade das citações de "
            "exemplo (pilares a/b/c e retórica) — não afeta a contagem de "
            "palavras nem a distribuição temática, que operam por posição "
            "de caractere no texto corrido, não por frase. Não alteramos a "
            "função de divisão de frases para não introduzir uma diferença "
            "de metodologia específica do Acre; é o mesmo tipo de "
            "compromisso já assumido no Ceará (onde a quebra de linha "
            "visual do PDF também produzia mais fragmentos cortados que em "
            "outros estados)."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
