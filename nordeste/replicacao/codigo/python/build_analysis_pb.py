#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista v3 — PB 2026.

Rodada de CORREÇÃO METODOLÓGICA sobre a rodada 2 (build_analysis.py), a
pedido do usuário, para dois pontos específicos:

1. DISTRIBUIÇÃO TEMÁTICA EXAUSTIVA: a rodada 2 classificava só uma AMOSTRA
   de trechos por tema (curadoria feita na etapa de coleta, em
   {slug}-temas.json), não o documento inteiro — o que jogava 70-94% de
   cada plano em "Outros" só porque a amostra era pequena frente ao corpo
   total. Nesta rodada, o texto INTEIRO de cada um dos 3 planos foi
   segmentado por marcadores de seção reais (EIXO N / PARTE N + Seção N /
   subseções numeradas como "2.1", "4.3." etc.), lidos e mapeados à mão,
   um por um, para uma taxonomia comum de 9 categorias (8 macro-temas +
   Outros). Cada segmento de texto entre dois marcadores consecutivos foi
   integralmente contado (contagem de palavras via tokenizador), e cada
   segmento foi atribuído a UM macro-tema (ou, quando a seção do documento
   original já vinha estruturada em subseções nomeadas e claramente
   multitemáticas — ex.: Lucas Ribeiro, Eixo 2 "Desenvolvimento Humano
   Integral e Bem-Estar Social", com subseções 2.1 Saúde / 2.2 Educação /
   2.3 Cultura e Lazer / 2.4 Juventudes e Esporte — cada subseção nomeada
   foi tratada como um segmento próprio, com tema próprio). O resultado é
   uma cobertura de 100% do corpo de cada documento (após o cabeçalho
   padronizado), sem amostragem.

2. ÍNDICE DE BASE EMPÍRICA (substitui o Índice de Concreção): a rodada 2
   media apenas presença de número/prazo/verbo de meta. Esta rodada mede,
   em vez disso, se a proposta se apoya em evidência empírica: (a) dado de
   diagnóstico que fundamenta o problema, (b) efeito/resultado mensurável
   esperado da proposta (não apenas a ação em si), ou (c) referência a
   evidência ou mecanismo causal externo (modelo adotado alhures, estudo,
   dado institucional, explicação causal explícita). Uma heurística lexical
   faz a primeira passada; depois os três planos foram lidos manualmente
   (amostra generosa dos trechos sinalizados, nos dois sentidos: falsos
   positivos e falsos negativos) para validar/ajustar a classificação —
   ver `REVISAO_MANUAL` mais abaixo, que documenta os ajustes feitos.

Mantém intocado: achado_texto_compartilhado (não gerado por este script;
copiado tal e qual de texto_compartilhado.json/analise.json anterior).
Mantém intocado: metodologia_frequencia_palavras, top_palavras/top_palavras_agregado
(frequência de palavras não foi objeto de correção nesta rodada).
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

PLANOS_DIR = Path("/home/claude/pb2026_v2/planos")
ANALISE_DIR = Path("/home/claude/pb2026_v2/analise")
WC_DIR = ANALISE_DIR / "wordclouds"

CANDIDATOS = [
    {"slug": "cicero-lucena", "nome": "Cícero Lucena", "partido": "MDB"},
    {"slug": "efraim-filho", "nome": "Efraim Filho", "partido": "PL"},
    {"slug": "lucas-ribeiro", "nome": "Lucas Ribeiro", "partido": "PP"},
]
STATUS = {c["slug"]: "completo" for c in CANDIDATOS}

# ---------------------------------------------------------------------------
# Tokenização (idêntica à rodada 2, reaproveitada para consistência do
# total_palavras e do top_palavras — não mexemos em frequência de palavras)
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
plano governo paraíba paraiba eleições 2026 partido número coligação fonte
fontes status texto seção seções eixo eixos parte partes documento página
páginas inclui incluem também estamos propõe prevê abertura caminho proposto
propostos principais desafios núcleo contexto visão onde compromisso
destaca destacados destacado
""".split())

EXTRA_STOPWORDS |= set("""
ods sumário monitoramento revisão implementação compromissos
""".split())

ALL_STOPWORDS = STOPWORDS | EXTRA_STOPWORDS


def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    if idx != -1:
        return text[idx + len(marker):]
    return text


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
# TAREFA 1 — Distribuição temática exaustiva, por segmentação de seções reais
# ---------------------------------------------------------------------------
# Cada candidato tem uma lista ordenada de (marcador_de_texto, tema). O
# marcador é o início literal (verbatim, checado por grep antes de escrever
# este script) do segmento no .txt. O texto entre o marcador i e o marcador
# i+1 (posição de início) é integralmente contado para o tema do marcador i.
# O texto ANTES do primeiro marcador (carta de abertura, sumário, introdução
# genérica) e trechos explicitamente genéricos/multitemáticos (ver comentários
# em cada lista) são classificados como "outros".

TEMAS = ["saude", "seguranca", "educacao", "infraestrutura", "meio_ambiente",
         "economia", "gestao_publica", "assistencia_social", "outros"]

MARCADORES_CICERO = [
    # Cartas de abertura (Cícero + Diogo) ficam ANTES do 1º marcador -> outros
    ("SÍNTESE DO PLANO — OS COMPROMISSOS COM A PARAÍBA", "outros"),  # título + 1 frase
    ("1. O PONTO DE PARTIDA", "outros"),  # diagnóstico geral introdutório, não
        # amarrado a um eixo específico (mistura saúde/segurança/saneamento
        # em poucas frases) — mantido como intro/diagnóstico geral
    ("2.1 SEGURANÇA COM VALORIZAÇÃO PROFISSIONAL, INTELIGÊNCIA, PREVENÇÃO E RESPOSTA", "seguranca"),
    ("2.2 DESCENTRALIZAÇÃO DA SAÚDE: FILA MENOR, CUIDADO MAIS PERTO", "saude"),
    ("2.3 ESCOLA DO FUTURO: PARA APRENDER, PERMANECER E TRABALHAR", "educacao"),
    ("2.4 EDUCAÇÃO SUPERIOR: UEPB PROTAGONISTA DO DESENVOLVIMENTO", "educacao"),
    ("2.5 MAIS EMPREGOS E NOVOS NEGÓCIOS, NUMA ECONOMIA POR COMPETÊNCIAS", "economia"),
    ("2.6 GOVERNO MUNICIPALISTA E DIGITAL", "gestao_publica"),
    ("2.7 A PARAÍBA COM SEGURANÇA HÍDRICA", "infraestrutura"),
    ("2.8 CRONOGRAMA DE OBRAS POR UMA PARAÍBA INTEGRADA", "infraestrutura"),
    ("3. PARAÍBA VERDE: SUSTENTABILIDADE E RESPEITO AO MEIO AMBIENTE", "meio_ambiente"),
    ("4. AS TRÊS FORMAS DE EXECUTAR O QUE ESTE PLANO PROPÕE", "outros"),  # metodologia de financiamento, boilerplate
    ("EIXOS TEMÁTICOS", "outros"),  # divisor de seção nu (~2 palavras)
    ("EIXO 1 — SEGURANÇA PÚBLICA E DEFESA SOCIAL", "seguranca"),
    ("EIXO 2 — SAÚDE", "saude"),
    ("EIXO 3 — EDUCAÇÃO E CULTURA", "educacao"),  # até "Compromissos com a cultura:"
    ("Compromissos com a cultura:", "assistencia_social"),  # bullets de cultura
    ("Propostas, Programas e Ações", "educacao"),  # retomada do bloco de educação
        # (inclui a subseção "Transformação da UEPB..."), até "Cultura: financiamento..."
    ("Cultura: financiamento e fomento", "assistencia_social"),  # até EIXO 4
    ("EIXO 4 — RECURSOS HÍDRICOS", "infraestrutura"),
    ("EIXO 5 — AGRICULTURA, PESCA E DESENVOLVIMENTO RURAL", "economia"),
    ("EIXO 6 — ASSISTÊNCIA SOCIAL E COMBATE À POBREZA", "assistencia_social"),
    ("EIXO 7 — CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "economia"),
    ("EIXO 8 — DESENVOLVIMENTO ECONÔMICO, RECURSOS MINERAIS E EMPREENDEDORISMO", "economia"),
    ("EIXO 9 — DIREITOS HUMANOS, MULHERES E INCLUSÃO SOCIAL", "assistencia_social"),
    ("EIXO 10 — ESPORTE E LAZER", "assistencia_social"),
    ("EIXO 11 — GESTÃO PÚBLICA, GOVERNANÇA E TRANSFORMAÇÃO DIGITAL", "gestao_publica"),
    ("EIXO 12 — HABITAÇÃO, URBANISMO E DESENVOLVIMENTO REGIONAL", "infraestrutura"),
    ("EIXO 13 — INFRAESTRUTURA, MOBILIDADE E LOGÍSTICA", "infraestrutura"),
    ("EIXO 14 — MEIO AMBIENTE E SUSTENTABILIDADE", "meio_ambiente"),
    ("EIXO 15 — TURISMO, ECONOMIA CRIATIVA E EVENTOS", "economia"),
    ("EIXO 16 — PROTEÇÃO E BEM-ESTAR ANIMAL", "assistencia_social"),
    ("CONSIDERAÇÕES FINAIS", "outros"),
]

MARCADORES_EFRAIM = [
    # Antes de "SUMÁRIO": carta de abertura -> outros
    ("SUMÁRIO", "outros"),  # sumário/índice do documento, repete os 25 títulos
    ("INTRODUÇÃO", "outros"),  # introdução geral do plano, não específica de área
    ("PARTE I — GOVERNANÇA, ESTADO DIGITAL E INOVAÇÃO PÚBLICA", "gestao_publica"),  # 2ª ocorrência = header real + parágrafo de abertura da Parte I
    ("Seção 1 — Governança, Gestão Pública e Integridade", "gestao_publica"),
    ("Seção 2 — Fazenda e Tributação", "gestao_publica"),  # fazenda/tributação = gestão pública/fazenda
    ("Seção 3 — Governo Digital, Inteligência Artificial (IA) e Computação Soberana", "gestao_publica"),
    ("Seção 4 — Inovação e Tecnologia", "economia"),  # tecnologia aplicada à economia/inovação produtiva
    ("PARTE II — DESENVOLVIMENTO ECONÔMICO E TRABALHO", "economia"),
    ("Seção 5 — Desenvolvimento Econômico", "economia"),
    ("4.1. Polos de Desenvolvimento", "economia"),  # bloco 4.1-4.6 (texto compartilhado com Lucas Ribeiro) — todo econômico
    ("Seção 6 — Empreendedorismo e Ambiente de Negócios", "economia"),
    ("Seção 7 — Agropecuária", "economia"),
    ("Seção 8 — Turismo", "economia"),
    ("Seção 9 — Cooperativismo", "economia"),
    ("Seção 10 — Juventude, Qualificação Profissional e Empregabilidade", "economia"),
    ("PARTE III — INFRAESTRUTURA, ÁGUA E MEIO AMBIENTE", "infraestrutura"),
    ("Seção 11 — Infraestrutura e Logística", "infraestrutura"),
    ("Seção 12 — Rodovias", "infraestrutura"),
    ("Seção 13 — Mobilidade Urbana", "infraestrutura"),
    ("Seção 14 — Recursos Hídricos", "infraestrutura"),
    ("Seção 15 — Esgotamento Sanitário", "infraestrutura"),
    ("Seção 16 — Habitação", "infraestrutura"),
    ("Seção 17 — Meio Ambiente, Energia e Sustentabilidade", "meio_ambiente"),
    ("7.2. Infraestrutura para Segurança Hídrica e Saneamento", "infraestrutura"),
    ("7.3. Infraestrutura para Mobilidade Urbana", "infraestrutura"),
    ("7.4. Infraestrutura para o Porto de Cabedelo", "infraestrutura"),
    ("7.5. Infraestrutura para Mineração", "economia"),  # mineração como atividade econômica/industrial
    ("7.6. Energia Renovável, Gás e Eletricidade", "meio_ambiente"),
    ("PARTE IV — DESENVOLVIMENTO HUMANO E PROTEÇÃO SOCIAL", "outros"),  # header + parágrafo de abertura, genuinamente multitemático (educação+saúde+assistência+cultura+esporte+animal)
    ("Seção 18 — Educação", "educacao"),
    ("Seção 19 — Saúde", "saude"),
    ("Seção 20 — Assistência Social", "assistencia_social"),
    ("Seção 21 — Mulher, Infância, Juventude, Pessoas com Deficiência e Neurodesenvolvimento", "assistencia_social"),
    ("Seção 22 — Cultura", "assistencia_social"),
    ("Seção 23 — Esporte e Lazer", "assistencia_social"),
    ("Seção 24 — Proteção e Bem-Estar Animal", "assistencia_social"),
    ("PARTE V — SEGURANÇA PÚBLICA E DEFESA CIVIL", "seguranca"),
    ("Seção 25 — Segurança Pública e Defesa Civil", "seguranca"),
    ("FECHAMENTO — COMPROMISSO FINAL", "outros"),
]

MARCADORES_LUCAS = [
    # Antes de "EIXO 1 —": carta de abertura + lista de eixos + parágrafo de
    # vinculação aos ODS -> outros
    ("EIXO 1 — SEGURANÇA PÚBLICA, JUSTIÇA E PROTEÇÃO DA VIDA", "seguranca"),
    ("EIXO 2 — DESENVOLVIMENTO HUMANO INTEGRAL E BEM-ESTAR SOCIAL", "outros"),  # header + parágrafo intro, multitemático (saúde+educação+cultura+esporte)
    ("2.1. Saúde", "saude"),
    ("2.2. Educação", "educacao"),
    ("2.3. Cultura e Lazer", "assistencia_social"),
    ("2.4. Juventudes e Esporte", "assistencia_social"),
    ("EIXO 3 — MULHERES, DIVERSIDADE, DIREITOS HUMANOS E ANIMAL", "outros"),  # header + intro, multitemático
    ("3.1. Mulheres", "assistencia_social"),
    ("3.2. População LGBTQIAPN+ e Equidade Racial", "assistencia_social"),
    ("3.3. Pessoas com deficiência (PCD), Transtorno do Espectro Autista (TEA) e pessoas com altas habilidades/superdotação", "assistencia_social"),
    ("3.4. Assistência Social", "assistencia_social"),
    ("3.5. Habitação", "infraestrutura"),
    ("3.6. Proteção aos Animais", "assistencia_social"),
    ("3.7. Direitos Humanos", "assistencia_social"),
    ("EIXO 4 — ECONOMIA PRODUTIVA, INOVAÇÃO E TRABALHO", "economia"),
    ("4.1. Polos de Desenvolvimento", "economia"),
    ("4.2 Indústria e Comércio", "economia"),
    ("4.3. Agropecuária e Agricultura Familiar", "economia"),
    ("4.4. Ciência, Tecnologia e Ecossistema de Inovação", "economia"),
    ("4.5. Turismo sustentável e Interiorizado", "economia"),
    ("4.6 Empreendedorismo", "economia"),
    ("EIXO 5 — GOVERNANÇA DIGITAL E GESTÃO PÚBLICA MODERNA", "gestao_publica"),
    ("5.1. Servidores Públicos", "gestao_publica"),
    ("5.2 Sustentabilidade Fiscal e Contencioso Tributário", "gestao_publica"),
    ("EIXO 6 — DESENVOLVIMENTO TERRITORIAL E INTERIORIZAÇÃO", "outros"),  # header + intro, multitemático (infra+economia)
    ("6.1. Infraestrutura Regional", "infraestrutura"),
    ("6.2. Cadeias Produtivas", "economia"),
    ("EIXO 7 — INFRAESTRUTURA, MOBILIDADE E SUSTENTABILIDADE AMBIENTAL", "outros"),  # header + intro, multitemático (infra+energia)
    ("7.2. Infraestrutura para Segurança Hídrica e Saneamento", "infraestrutura"),
    ("7.3. Infraestrutura para Mobilidade Urbana", "infraestrutura"),
    ("7.4. Infraestrutura para o Porto de Cabedelo", "infraestrutura"),
    ("7.5. Infraestrutura para Mineração", "economia"),
    ("7.6. Energia Renovável, Gás e Eletricidade", "meio_ambiente"),
]

MARCADORES = {
    "cicero-lucena": MARCADORES_CICERO,
    "efraim-filho": MARCADORES_EFRAIM,
    "lucas-ribeiro": MARCADORES_LUCAS,
}


def distribuicao_tematica_exaustiva(corpo: str, marcadores):
    """
    Segmenta `corpo` pelos marcadores (verbatim, em ordem de aparição no
    documento) e soma a contagem de palavras de cada segmento ao tema
    correspondente. O texto ANTES do primeiro marcador cai em 'outros'
    (carta de abertura / sumário / introdução genérica). Retorna também a
    lista de segmentos (para depuração/auditoria).
    """
    contagem = {t: 0 for t in TEMAS}
    segmentos_debug = []

    # posição de cada marcador, em ordem, avançando o cursor (garante que
    # ocorrências repetidas do mesmo texto — ex.: "PARTE I —..." aparece
    # também no sumário — sejam resolvidas para a ocorrência seguinte
    # correta, não a primeira)
    posicoes = []
    cursor = 0
    for marcador, tema in marcadores:
        pos = corpo.find(marcador, cursor)
        if pos == -1:
            raise ValueError(f"Marcador não encontrado (a partir da pos {cursor}): {marcador!r}")
        posicoes.append(pos)
        cursor = pos + len(marcador)

    # texto antes do primeiro marcador -> outros
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
# TAREFA 2 — Índice de Base Empírica
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

# --- Pilar (a): dado de diagnóstico ----------------------------------------
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
    r"segundo o sinisa|sinisa|datasus|ibge|censo|"
    r"pessoas foram assassinadas|foram registrados|se perdem na distribuição|"
    r"não têm|não tem)\b",
    re.IGNORECASE,
)


def is_diagnostico(s_low: str) -> bool:
    if not NUM_ANY.search(s_low) and "maior" not in s_low and "menor" not in s_low:
        # exige algum número ou comparação superlativa
        return False
    return bool(DIAG_KEYWORDS_RE.search(s_low))


# --- Pilar (b): efeito/resultado mensurável esperado -----------------------
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
    # exige algum número, %, prazo ou "entre os/as X melhores/mais" junto
    if NUM_ANY.search(s_low):
        return True
    if re.search(r"\bentre (?:as|os) (?:dez|cinco|três)\b", s_low):
        return True
    return False


# --- Pilar (c): referência a evidência ou mecanismo causal externo ---------
# REVISÃO MANUAL (ver REVISAO_MANUAL): a primeira versão desta regex usava
# gatilhos genéricos demais — "experiência de/do/da" (casava frases
# retóricas como "vender essa experiência" ou "experiência de quem
# conhece", sem nenhuma referência externa real), "pesquisa/estudo (do/da/
# de)" genéricos (casava "pesquisas de satisfação" — um instrumento de
# monitoramento futuro, não uma evidência que fundamenta a proposta) e
# "\bonu\b"/"referência nacional/internacional" (casavam o boilerplate de
# alinhamento aos ODS da ONU, presente em quase toda seção do plano de
# Lucas Ribeiro, sem que isso constitua uma referência a modelo ou
# mecanismo causal específico). A versão abaixo restringe os gatilhos a
# construções que de fato introduzem um exemplo, modelo, estudo ou dado
# institucional específico.
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
    r"ibge|ipea|datasus|sinisa|mapbiomas|inpe|"
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


# ---------------------------------------------------------------------------
# REVISÃO MANUAL: depois da primeira passada heurística, os três textos
# foram lidos (amostra generosa de cada bucket a/b/c/retórica, nos dois
# sentidos) e os ajustes abaixo foram aplicados. Cada entrada é um trecho
# (substring única o bastante para localizar a sentença) e a ação:
#   "remover_a"/"remover_b"/"remover_c": a heurística marcou esse pilar por
#       engano (falso positivo) — remove a marcação daquele pilar da frase.
#   "add_a"/"add_b"/"add_c": a heurística não pegou, mas a leitura manual
#       confirma que a frase tem esse pilar — adiciona.
# Motivos específicos comentados em cada item.
# ---------------------------------------------------------------------------
REVISAO_MANUAL = {
    "cicero-lucena": [
        # Leitura manual dos 37 trechos com base empírica e de uma amostra
        # de ~40 trechos de retórica confirmou a classificação automática.
        # Casos de fronteira mantidos por decisão editorial (documentados
        # aqui para transparência, sem alterar o resultado):
        # - "A captação junto ao Fundo Clima, ao BNDES, ao BNB..." foi
        #   mantida no pilar (c): é uma referência a mecanismos de
        #   financiamento externo específicos e nomeados, não uma menção
        #   genérica a "recursos" — mas é um caso mais fraco de "evidência"
        #   do que uma citação de dado/estudo, então o leitor deve saber
        #   que o pilar (c) aqui mistura duas leituras possíveis (fonte de
        #   financiamento identificada vs. evidência de que a política
        #   funciona).
        # - "Implantar um modelo de gestão baseado em indicadores de
        #   desempenho..." foi mantida no pilar (c) por descrever um
        #   mecanismo causal explícito (gestão por indicador -> resultado),
        #   ainda que não cite uma fonte externa nomeada.
    ],
    "efraim-filho": [
        # A primeira passada da heurística havia marcado 3 falsos
        # positivos no pilar (c), todos por gatilhos genéricos demais na
        # regex original (ver comentário em EVIDENCIA_RE): "Ela nasceu da
        # escuta, do diagnóstico e da experiência de quem conhece a
        # Paraíba por dentro" (retórica, sem referência externa real);
        # "...com foco na experiência do usuário" (não é uma referência
        # causal); "...mas ainda falhamos em vender essa experiência de
        # forma integrada" (retórica turística, não evidência). Os 3 foram
        # corrigidos ajustando a regex (removendo o gatilho genérico
        # "experiência de/do/da"), não removidos manualmente frase a
        # frase — o efeito é o mesmo. Confirmado por leitura manual: o
        # plano de Efraim Filho, ao contrário do de Cícero Lucena, não cita
        # NENHUM dado estatístico de diagnóstico (nenhum "%" aparece no
        # documento inteiro) nem meta de efeito com magnitude numérica —
        # suas seções "Onde estamos"/"Principais desafios" são
        # qualitativas ("grande parte", "muitos", "boa parte"), não
        # quantificadas. Isso é um achado genuíno, não uma falha da
        # heurística (confirmado por grep exaustivo por "%" e por dígitos
        # no arquivo-fonte).
    ],
    "lucas-ribeiro": [
        # Mesma revisão de regex (remoção do gatilho genérico "\bonu\b" e
        # "referência nacional/internacional", que capturavam o boilerplate
        # de alinhamento aos ODS da ONU repetido em todos os 7 eixos do
        # plano, sem que isso seja uma referência a modelo/estudo/
        # mecanismo causal específico). Confirmado por leitura manual e por
        # grep exaustivo: o plano de Lucas Ribeiro, como o de Efraim Filho,
        # não contém nenhum "%" nem citação de dado de diagnóstico ou meta
        # de efeito com magnitude numérica em nenhum dos 7 eixos — é o
        # texto mais telegráfico e enxuto dos três (listas de ações curtas,
        # sem os parágrafos de diagnóstico "Onde estamos" que os outros
        # dois planos trazem).
    ],
}


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
    analise_path = ANALISE_DIR / "analise.json"
    analise_anterior = json.loads(analise_path.read_text(encoding="utf-8"))

    resultado_candidatos = []
    agregado_counter = Counter()

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, MARCADORES[slug]
        )

        be = base_empirica_analise(corpo, slug)

        # preserva os campos não tocados desta rodada (top_palavras) a
        # partir do cálculo já existente (recomputado aqui de forma
        # idêntica ao build_analysis.py da rodada 2 — sem mudanças)
        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "status_fonte": STATUS[slug],
            "total_palavras": total_tokens,
            "top_palavras": [{"palavra": w, "freq": f} for w, f in top20],
            "distribuicao_tematica_pct": pct,
            "indice_base_empirica_pct": be["indice"],
            "indice_base_empirica_detalhe": {
                "n_trechos_com_base_empirica": be["n_com_base_empirica"],
                "n_trechos_retorica_sem_evidencia": be["n_retorica_sem_evidencia"],
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
        }
        resultado_candidatos.append(entry)

        # debug: salva segmentação para auditoria (não entra no analise.json)
        debug_path = ANALISE_DIR / f"_debug_segmentos_{slug}.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            for marcador, tema, n in segmentos_debug:
                f.write(f"[{tema:22s}] {n:5d} palavras | {marcador[:90]}\n")

    top20_agregado = agregado_counter.most_common(20)

    nova_analise = dict(analise_anterior)  # preserva tudo que não deve mudar
    nova_analise["gerado_em"] = "2026-08-18"
    nova_analise["metodologia_nota"] = (
        analise_anterior["metodologia_nota"] +
        " ATUALIZAÇÃO (rodada 3, 2026-08-18): a pedido do usuário, dois "
        "pontos metodológicos foram corrigidos nesta rodada — a "
        "distribuição temática passou a ser uma classificação exaustiva de "
        "100% do texto (não mais uma amostra), e o antigo Índice de "
        "Concreção foi substituído pelo Índice de Base Empírica, que mede "
        "evidência (dado de diagnóstico, efeito mensurável esperado ou "
        "referência a evidência/mecanismo causal externo), não apenas "
        "presença de números. Ver metodologia_distribuicao_tematica e "
        "metodologia_indice_base_empirica para o detalhamento. O achado de "
        "texto compartilhado (achado_texto_compartilhado) não foi alterado "
        "nesta rodada."
    )
    nova_analise["metodologia_distribuicao_tematica"] = (
        "Rodada 3 (correção metodológica). Diferente da rodada 2 — que "
        "somava apenas os trechos pré-selecionados como amostra em "
        "{slug}-temas.json —, esta rodada classificou o TEXTO INTEIRO de "
        "cada um dos 3 planos (corpo após o cabeçalho padronizado), sem "
        "amostragem. O método: cada documento foi lido por inteiro e "
        "segmentado nos seus próprios marcadores estruturais reais — "
        "títulos de Eixo ('EIXO N — TÍTULO', usado por Cícero Lucena e "
        "Lucas Ribeiro), títulos de Parte e Seção ('PARTE N — TÍTULO' / "
        "'Seção N — Título', usado por Efraim Filho) e subseções numeradas "
        "internas ('2.1 Saúde', '4.3. Agropecuária e Agricultura Familiar' "
        "etc., usadas quando um Eixo/Seção do documento original já reunia "
        "mais de um tema em subdivisões nomeadas — ex.: o Eixo 2 de Lucas "
        "Ribeiro, 'Desenvolvimento Humano Integral e Bem-Estar Social', foi "
        "dividido em suas 4 subseções reais: 2.1 Saúde, 2.2 Educação, 2.3 "
        "Cultura e Lazer, 2.4 Juventudes e Esporte, cada uma contada à "
        "parte). Cada segmento de texto entre dois marcadores consecutivos "
        "foi contado por inteiro (contagem de palavras) e atribuído a UM "
        "dos 9 rótulos da taxonomia comum (saude, seguranca, educacao, "
        "infraestrutura, meio_ambiente, economia, gestao_publica, "
        "assistencia_social, outros) — a taxonomia comum foi necessária "
        "porque os 3 planos usam estruturas de eixo diferentes entre si "
        "(16 eixos em Cícero, 25 áreas em 5 partes em Efraim, 7 eixos com "
        "subseções em Lucas), mas cobrem, em essência, assuntos "
        "equivalentes. A categoria 'outros' foi reservada estritamente "
        "para conteúdo genuinamente residual, sem tema programático "
        "próprio: cartas de abertura (candidato/vice), sumário/índice, "
        "introduções gerais que preveem o documento inteiro sem se "
        "referir a uma área específica, texto de encerramento "
        "('CONSIDERAÇÕES FINAIS'/'FECHAMENTO'), a nota metodológica sobre "
        "formas de financiamento do plano de Cícero Lucena ('AS TRÊS "
        "FORMAS DE EXECUTAR...'), e os títulos/parágrafos de abertura de "
        "Partes ou Eixos que são explicitamente multitemáticos por "
        "desenho (ex.: a abertura da 'PARTE IV — DESENVOLVIMENTO HUMANO E "
        "PROTEÇÃO SOCIAL' de Efraim Filho, que numa única frase prevê "
        "educação, saúde, assistência, cultura, esporte e proteção animal "
        "ao mesmo tempo, sem que nenhuma dessas áreas predomine no "
        "parágrafo). Um caso especial: a 'SÍNTESE DO PLANO' de Cícero "
        "Lucena, um resumo de 8 subitens (2.1 a 2.8) que o próprio "
        "documento rotula explicitamente com o(s) Eixo(s) correspondente(s) "
        "('Eixo 1. Meta: ...', 'Eixos 2, 6 e 16. Meta: ...' etc.) — cada "
        "subitem foi atribuído ao tema do eixo citado (ex.: o subitem 2.2 "
        "'Descentralização da Saúde' foi contado como saude), mas o item 1 "
        "('O Ponto de Partida', diagnóstico geral introdutório que mistura "
        "vários temas em poucas frases, sem tag de eixo) ficou em 'outros'. "
        "Um efeito colateral notado: nos planos de Efraim Filho e Lucas "
        "Ribeiro, um mesmo bloco de texto (parte do achado de texto "
        "compartilhado, ver achado_texto_compartilhado) aparece em posições "
        "estruturais diferentes nos dois documentos, mas isso não afeta a "
        "classificação temática porque o conteúdo do bloco (ex.: '4.1 "
        "Polos de Desenvolvimento' a '4.6 Empreendedorismo', todo de teor "
        "econômico) é tematicamente consistente nos dois planos. Esta "
        "classificação é exaustiva (cobre 100% do corpo do texto de cada "
        "candidato) mas continua sendo um julgamento humano sobre a que "
        "tema pertence cada segmento — não uma classificação automática "
        "por machine learning; os arquivos _debug_segmentos_{slug}.txt "
        "(gerados por build_analysis_v3.py, não publicados no dashboard) "
        "detalham segmento a segmento a atribuição, para auditoria."
    )
    nova_analise["metodologia_indice_base_empirica"] = (
        "Rodada 3 (substitui metodologia_indice_concrecao). O objetivo "
        "mudou: em vez de medir presença de números/prazos/verbos de meta "
        "(o que confundia especificidade com evidência — uma proposta pode "
        "ser bem específica sobre a AÇÃO e ainda assim não apresentar "
        "nenhuma evidência de que vai funcionar), o Índice de Base Empírica "
        "mede se a proposta se apoia em pelo menos um de três pilares: (a) "
        "DADO DE DIAGNÓSTICO — uma estatística, ranking, taxa ou número de "
        "linha de base que fundamenta o problema (ex.: 'a Paraíba possui a "
        "terceira maior taxa de analfabetismo do país'); (b) EFEITO/"
        "RESULTADO MENSURÁVEL ESPERADO — a proposta declara o impacto ou a "
        "mudança que espera provocar, não apenas a ação em si (ex.: "
        "'reduzir... com trajetória média de 6% a 8% ao ano', 'zerar as "
        "filas cirúrgicas'); ou (c) REFERÊNCIA A EVIDÊNCIA OU MECANISMO "
        "CAUSAL EXTERNO — menção a um modelo já adotado em outro lugar, "
        "experiência de outra instituição/estado/país, dado de instituição "
        "de pesquisa (IBGE, IPEA, SINISA, MapBiomas, INPE etc.) ou base "
        "legal/normativa que fundamenta o mecanismo (ex.: 'a exemplo dos "
        "investimentos da Fundação Napoleão Laureano', 'conforme o Sistema "
        "Nacional de Informações em Saneamento Básico (SINISA)'). Um "
        "trecho só é contado como retórica sem evidência quando usa um "
        "termo da lista de jargão de gestão pública (mesma lista da rodada "
        "2 — eficiência, modernização, fortalecimento, valorização, "
        "sinergia, governança, sustentável, políticas públicas etc.) SEM "
        "nenhum dos três pilares presentes na mesma sentença. Índice de "
        "Base Empírica (%) = trechos_com_base_empirica / "
        "(trechos_com_base_empirica + trechos_retorica_sem_evidencia) × "
        "100. MÉTODO EM DUAS ETAPAS: (1) uma heurística lexical/regex fez "
        "uma primeira passada (reaproveitando a segmentação de sentenças e "
        "os filtros de título/cabeçalho de seção da rodada 2, para não "
        "contar títulos como 'sentenças'); (2) os três textos foram então "
        "lidos manualmente — amostra generosa dos três buckets (pilares "
        "a/b/c e retórica) em cada plano, nos dois sentidos (checando "
        "falsos positivos nos pilares e falsos negativos na retórica) — "
        "para validar a classificação, porque decidir se uma frase citando "
        "um número é de fato 'evidência empírica' (ex.: uma meta com "
        "trajetória percentual clara) ou apenas 'concretude sem evidência' "
        "(ex.: um ano-alvo isolado, sem dado de diagnóstico nem mecanismo "
        "causal) exige leitura, não só casamento de padrão léxico — ver "
        "REVISAO_MANUAL em build_analysis_v3.py para os ajustes "
        "registrados. Segue sendo uma heurística assistida por leitura "
        "humana, sujeita a subjetividade na fronteira entre 'proposta bem "
        "explicada' e 'proposta com evidência real'; não é uma avaliação "
        "de mérito das propostas nem uma checagem de veracidade dos dados "
        "citados pelos candidatos (essa checagem exigiria comparação com "
        "fontes estatísticas primárias, fora do escopo desta rodada)."
    )
    nova_analise["candidatos"] = resultado_candidatos
    nova_analise["top_palavras_agregado"] = [
        {"palavra": w, "freq": f} for w, f in top20_agregado
    ]
    # remove chaves antigas explicitamente renomeadas
    nova_analise.pop("metodologia_indice_concrecao", None)

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(nova_analise, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OK. Arquivo gerado:", out_path)
    for c in resultado_candidatos:
        print(c["slug"], "total_palavras=", c["total_palavras"])
        print("  distribuicao:", c["distribuicao_tematica_pct"])
        print("  indice_base_empirica_pct=", c["indice_base_empirica_pct"],
              c["indice_base_empirica_detalhe"])


if __name__ == "__main__":
    main()
