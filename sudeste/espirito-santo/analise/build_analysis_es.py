#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Espírito Santo 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia do Maranhão e da Paraíba: distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica aos demais
estados do projeto, reaproveitada sem alterações para manter comparabilidade
entre estados).

Caso especial do Espírito Santo: o governador Renato Casagrande (PSB)
renunciou ao cargo em abril de 2026 para concorrer ao Senado — o mesmo padrão
já observado em três estados do Centro-Oeste do projeto (MT, GO, DF), em que
o governador titular renuncia em ano eleitoral para disputar outro cargo. Seu
vice, Ricardo Ferraço (MDB), tomou posse como governador em exercício e
concorre à reeleição — classificado aqui como "incumbente por sucessão", e
não como incumbente pleno (não foi eleito governador em 2022; assumiu o cargo
por sucessão em abril de 2026). Lorenzo Pazolini (Republicanos), ex-prefeito
de Vitória, concorre como candidato de oposição ao grupo governista —
classificado como "desafiante". Fontes: ver metodologia_nota abaixo.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sudeste/espirito-santo/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sudeste/espirito-santo/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "ricardo_ferraco", "nome": "Ricardo Ferraço", "partido": "MDB",
     "categoria": "incumbente por sucessão — o governador titular, Renato "
                  "Casagrande (PSB), renunciou em abril de 2026 para "
                  "concorrer ao Senado (mesmo padrão observado em MT, GO e "
                  "DF, no Centro-Oeste, no mesmo ciclo eleitoral); Ferraço, "
                  "então vice-governador, tomou posse como governador em "
                  "exercício e concorre à reeleição à frente da máquina "
                  "estadual, mas sem ter sido o titular eleito em 2022"},
    {"slug": "lorenzo_pazolini", "nome": "Lorenzo Pazolini", "partido": "Republicanos",
     "categoria": "desafiante — ex-prefeito de Vitória, candidato de "
                  "oposição ao grupo governista"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas aos demais estados do projeto (Ceará,
# Maranhão, Paraíba), não adaptadas ao Espírito Santo, para preservar
# comparabilidade entre estados.
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

# Ricardo Ferraço: documento estruturado em 3 EIXOS numerados (EIXO 1 —
# Espírito Santo que Cuida; EIXO 2 — Espírito Santo que Prospera; EIXO 3 —
# Espírito Santo que Transforma), cada um subdividido em seções "X.Y" com
# títulos temáticos claros, por sua vez subdivididas em subseções "X.Y.Z".
# Como as subseções quase sempre pertencem ao mesmo tema da seção-mãe
# (ex.: 1.1.1 "Ensino Básico" e 1.1.2 "Ensino Profissional" dentro de 1.1
# "Educação e Qualificação Profissional" = educacao), a segmentação usa como
# marcador o nível "X.Y" (não "X.Y.Z"), exceto quando uma subseção muda de
# tema em relação à seção-mãe — caso de 1.4.10 "Habitação de Interesse
# Social e Regularização Fundiária", destacada como marcador próprio
# (infraestrutura) dentro da seção 1.4 "Proteção Social..." (assistencia_
# social), seguindo o precedente do projeto de tratar habitação como
# infraestrutura mesmo quando embutida em um capítulo social.
#
# Cultura (1.6), Esporte (1.7) e Proteção e Bem-Estar Animal (1.8) seguem o
# precedente já usado em Ceará/Maranhão/Paraíba (Orleans Brandão): cultura,
# esporte e proteção animal = assistencia_social.
#
# 3.2 "Ciência, Tecnologia e Inovação" foi classificada como "economia": ao
# contrário do plano de Elmano de Freitas (CE), em que C&T aparecia dentro do
# capítulo de Educação e era tratada como tal, aqui a seção fica dentro do
# EIXO 3 (gestão/eficiência do Estado) e trata quase exclusivamente de
# ecossistema de inovação, startups, fomento a empresas e neoindustrialização
# — sem menção a universidades/ensino superior –, o que a aproxima mais de
# "economia" do que de "educacao" neste plano específico.
#
# Dentro do EIXO 2 ("Espírito Santo que Prospera"), 2.4 "Turismo" e 2.6
# "Economia Azul" foram tratados como "economia" (o próprio texto os enquadra
# como vetores de desenvolvimento econômico, emprego e renda, ainda que a
# Economia Azul mencione também proteção de ecossistemas marinhos). Já a
# seção 2.5 "Meio Ambiente e Desenvolvimento Sustentável" — incluindo suas
# subseções 2.5.1 (Adaptação Climática, Recursos e Segurança Hídrica), 2.5.2
# (Gestão de Riscos e Desastres) e 2.5.3 (Energia e Descarbonização) — foi
# mantida integralmente em "meio_ambiente": ao contrário do precedente do
# Ceará (em que "segurança hídrica" foi tratada como infraestrutura por
# aparecer isolada em um eixo de desenvolvimento agrário), aqui o próprio
# candidato agrupa explicitamente gestão hídrica, defesa civil/adaptação
# climática e transição energética dentro de um único capítulo ambiental
# nomeado, sem qualquer menção a obras de infraestrutura física como foco
# central — o que justifica manter o agrupamento temático do próprio
# documento em vez de fragmentar por precedente de outro estado.
#
# Os textos de abertura de cada EIXO (título + parágrafos de transição antes
# do primeiro "X.Y") e as seções de propósito geral (APRESENTAÇÃO,
# DIRETRIZES DO PROGRAMA, texto de abertura de EIXO 2) foram classificados
# como "outros", por não tratarem de um tema específico da taxonomia de 9
# eixos, replicando o tratamento dado a introduções genéricas de outros
# planos do projeto.
MARCADORES_FERRACO = [
    ("APRESENTAÇÃO", "outros"),
    ("DIRETRIZES DO PROGRAMA", "outros"),
    ("EIXO 1 —", "outros"),
    ("1.1 — EDUCAÇÃO E QUALIFICAÇÃO", "educacao"),
    ("1.2 — SAÚDE", "saude"),
    ("1.3 — SEGURANÇA PÚBLICA E DEFESA DA VIDA", "seguranca"),
    ("1.4 — PROTEÇÃO SOCIAL, DIREITOS", "assistencia_social"),
    ("1.4.10 — HABITAÇÃO DE INTERESSE SOCIAL E", "infraestrutura"),
    ("1.5 — MOBILIDADE E SEGURANÇA NO TRÂNSITO", "infraestrutura"),
    ("1.6 — CULTURA", "assistencia_social"),
    ("1.7 — ESPORTE", "assistencia_social"),
    ("1.8 — PROTEÇÃO E BEM-ESTAR ANIMAL", "assistencia_social"),
    ("EIXO 2.", "outros"),
    ("2.1 — COMPETITIVIDADE, AMBIENTE DE", "economia"),
    ("2.2 — AGROPECUÁRIA, INFRAESTRUTURA", "economia"),
    ("2.3 — INFRAESTRUTURA, MACRODRENAGEM", "infraestrutura"),
    ("2.4 — TURISMO", "economia"),
    ("2.5 — MEIO AMBIENTE E DESENVOLVIMENTO", "meio_ambiente"),
    ("2.6 — ECONOMIA AZUL", "economia"),
    ("EIXO 3 —", "outros"),
    ("3.1 — GESTÃO FISCAL COMO PLATAFORMA", "gestao_publica"),
    ("3.2 — CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "economia"),
    ("3.3 — GESTÃO DE PESSOAS", "gestao_publica"),
    ("3.4 — GOVERNO COMO PLATAFORMA", "gestao_publica"),
    ("3.5 — GOVERNANÇA, INTEGRIDADE", "gestao_publica"),
]

# Lorenzo Pazolini: documento mais curto (54 páginas), organizado em 4
# blocos temáticos numerados com algarismos romanos (I a IV), cada um com
# subseções "X.Y" com título e slogan próprios ("É TEMPO DE..."). Segmentação
# direta pelos marcadores "X.Y" (nível único de subseção neste documento).
#
# 1.4 "Assistência Social e Cidadania" e 1.5 "Esporte e Lazer" seguem o
# mesmo precedente do projeto (assistência social, esporte = assistencia_
# social). 2.3 "Turismo, Cultura e Economia Criativa" mistura turismo e
# cultura em uma única seção indivisível, mas o texto a enquadra
# explicitamente como agenda de "desenvolvimento econômico, emprego e
# renda" (diferente do tratamento dado a "cultura" isolada em outros planos
# do projeto) — por ser uma seção conjunta e explicitamente econômica,
# tratada aqui como "economia". 2.4 "Ciência, Tecnologia e Inovação" segue o
# mesmo raciocínio aplicado à seção 3.2 de Ricardo Ferraço: sem menção a
# ensino superior, tratando de inovação aplicada a cadeias produtivas,
# patentes e investimento privado — "economia".
#
# 3.2 "Meio Ambiente e Sustentabilidade" reúne recursos hídricos, defesa
# civil/resiliência climática, proteção da biodiversidade e bem-estar animal
# em um único capítulo ambiental (mesmo padrão do 2.5 de Ferraço) — mantido
# integralmente como "meio_ambiente", incluindo o item "Bem-Estar Animal e
# Controle de Zoonoses", que aqui aparece como uma diretriz dentro do
# capítulo ambiental (e não como seção autônoma, ao contrário do plano de
# Ferraço) e por isso não foi destacada em segmento à parte.
#
# Os títulos dos blocos I a IV (mais o texto de abertura "É TEMPO DE PAZ",
# a "Introdução" e os parágrafos de transição de cada bloco antes da
# primeira subseção "X.Y") foram classificados como "outros".
MARCADORES_PAZOLINI = [
    ("É TEMPO DE PAZ", "outros"),
    ("Introdução", "outros"),
    ("I - Espírito Santo das Pessoas", "outros"),
    ("1.1 Educação", "educacao"),
    ("1.2 Segurança Pública", "seguranca"),
    ("1.3 Saúde", "saude"),
    ("1.4 Assistência Social e Cidadania", "assistencia_social"),
    ("1.5 Esporte e Lazer", "assistencia_social"),
    ("II - Espírito Santo Competitivo", "outros"),
    ("2.1 Economia, Emprego e Renda", "economia"),
    ("2.2 Agricultura, Aquicultura e Pesca", "economia"),
    ("2.3 Turismo, Cultura e Economia Criativa", "economia"),
    ("2.4 Ciência, Tecnologia e Inovação", "economia"),
    ("2.5 Infraestrutura e Mobilidade", "infraestrutura"),
    ("III - Espírito Santo Sustentável", "outros"),
    ("3.1 Urbanismo, Saneamento e Habitação", "infraestrutura"),
    ("3.2 Meio Ambiente e Sustentabilidade", "meio_ambiente"),
    ("IV – Espírito Santo que entrega", "outros"),
    ("4.1 Governança, Gestão e Estratégia", "gestao_publica"),
    ("4.2 Tecnologia e Inovação na Gestão", "gestao_publica"),
]

MARCADORES = {
    "ricardo_ferraco": MARCADORES_FERRACO,
    "lorenzo_pazolini": MARCADORES_PAZOLINI,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica ao Ceará/Maranhão/Paraíba)
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
        # Nos dois planos do Espírito Santo os arquivos .txt já chegam com o
        # cursor inicial aplicado (sumário/índice já removido na extração),
        # e o 1º marcador ocorre uma única vez — este bloco é mantido apenas
        # por robustez/paridade com os demais scripts do projeto.
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        be = base_empirica_analise(corpo[cursor_inicial:], slug)

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
        "gerado_em": "24 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Espírito "
            "Santo' e 'capixaba(s)' NÃO são filtrados e podem aparecer nos "
            "termos mais frequentes). Mostra os termos mais repetidos por "
            "candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/bloco/seção "
            "numerada). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível, o "
            "segmento foi classificado pelo enquadramento dominante dado "
            "pelo próprio candidato, ou como 'outros' quando não era "
            "possível separar com segurança (títulos de eixo, cartas de "
            "abertura e parágrafos de transição genéricos)."
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
            "Heurística idêntica à usada nas análises do Ceará, do Maranhão "
            "e da Paraíba, sem nenhum ajuste específico para o Espírito "
            "Santo, para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O Espírito Santo tem um caso de sucessão análogo ao já visto em "
            "três estados do Centro-Oeste do projeto (Mato Grosso, Goiás e "
            "Distrito Federal): o governador titular, Renato Casagrande "
            "(PSB), renunciou ao cargo em abril de 2026 para concorrer ao "
            "Senado. Seu vice, Ricardo Ferraço (MDB), tomou posse como "
            "governador em exercício e concorre à reeleição — classificado "
            "neste projeto como 'incumbente por sucessão' (e não incumbente "
            "pleno, já que não foi o titular eleito em 2022). Lorenzo "
            "Pazolini (Republicanos), ex-prefeito de Vitória, concorre como "
            "candidato de oposição ao grupo governista — 'desafiante'. Essa "
            "é uma leitura eleitoral, não textual: não influenciou nenhuma "
            "etapa da extração ou classificação dos planos. Fontes da "
            "verificação: reportagens de Gazeta do Povo, Informe Capixaba e "
            "Tribuna Online sobre a renúncia de Casagrande e a posse de "
            "Ferraço (abril de 2026); reportagens de Metrópoles e do site "
            "oficial do Republicanos-ES sobre o lançamento da candidatura de "
            "Lorenzo Pazolini. "
            "Os dois planos são bem estruturados, com títulos de "
            "seção/subseção numerados e claros, sem o problema de sumário "
            "duplicado (índice com pontos de preenchimento repetindo os "
            "títulos de seção antes do corpo do texto) encontrado em outros "
            "estados do projeto (ex.: Felipe Camarão, no Maranhão; Elmano de "
            "Freitas, no Ceará) — os dois arquivos .txt já foram extraídos "
            "começando diretamente no corpo do programa de governo, sem "
            "sumário/índice inicial. Não foi identificado nenhum defeito de "
            "ligadura (fi/fl/ti) nem mojibake de acentuação em nenhum dos "
            "dois textos — extração limpa em ambos os casos. "
            "O plano de Ricardo Ferraço (152 páginas) é o mais extenso e "
            "detalhado dos dois, organizado em 3 EIXOS numerados, cada um "
            "com seções 'X.Y' e subseções 'X.Y.Z'; a segmentação temática "
            "usa o nível 'X.Y' como marcador (as subseções internas quase "
            "sempre compartilham o tema da seção-mãe), exceto para 1.4.10 "
            "'Habitação de Interesse Social e Regularização Fundiária', "
            "destacada à parte como 'infraestrutura' dentro da seção 1.4 de "
            "proteção social (assistência social). O plano de Lorenzo "
            "Pazolini (54 páginas) é mais enxuto, organizado em 4 blocos "
            "numerados em algarismos romanos (I a IV), cada um com seções "
            "'X.Y'; a segmentação usa diretamente o nível 'X.Y', único nível "
            "de subseção existente no documento. Decisões de classificação "
            "não óbvias e comuns aos dois planos — Ciência, Tecnologia e "
            "Inovação como 'economia' (e não 'educação', diferente do "
            "precedente do Ceará, pois nos dois planos capixabas a seção "
            "trata de ecossistema de inovação/startups/indústria, sem menção "
            "a ensino superior); Turismo e a seção conjunta 'Turismo, "
            "Cultura e Economia Criativa' (Pazolini) como 'economia', por "
            "serem enquadradas pelos próprios candidatos como agenda de "
            "emprego e renda; Cultura, Esporte e Proteção/Bem-Estar Animal "
            "como 'assistencia_social', replicando o precedente do projeto; "
            "e capítulos ambientais que agrupam explicitamente segurança "
            "hídrica, defesa civil/adaptação climática e transição "
            "energética sob um único título de Meio Ambiente (seção 2.5 de "
            "Ferraço; seção 3.2 de Pazolini) mantidos integralmente como "
            "'meio_ambiente', diferindo do precedente do Ceará (em que "
            "'segurança hídrica' era tratada como infraestrutura), porque "
            "nos planos do Espírito Santo esses temas aparecem "
            "explicitamente agrupados pelo próprio candidato dentro do "
            "capítulo ambiental, sem foco em obras físicas — estão "
            "documentadas linha a linha nos comentários do script de "
            "análise."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
