#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Piauí 2026.

Réplica exata da metodologia usada no Maranhão (build_analysis_ma.py), que por
sua vez replicou a metodologia da Paraíba: distribuição temática exaustiva por
segmentação de marcadores de seção reais (lidos e mapeados à mão) e Índice de
Base Empírica (heurística lexical/regex idêntica, reaproveitada sem
alterações, para manter comparabilidade entre estados).

Tokenização, stopwords, TEMAS, distribuicao_tematica_exaustiva,
base_empirica_analise, JARGAO_TERMOS, NUM_ANY, DIAG_KEYWORDS_RE, EFEITO_RE,
EVIDENCIA_RE, split_sentences, looks_like_header — todos idênticos ao
Maranhão, sem nenhum ajuste específico para o Piauí. Apenas MARCADORES_* (a
segmentação temática, que depende da estrutura real de cada plano) foi escrita
do zero para os dois planos do Piauí.
"""
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/piaui/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/piaui/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "rafael-fonteles", "nome": "Rafael Fonteles", "partido": "PT",
     "categoria": "incumbente pleno (governador em exercício, 1º mandato, concorrendo à reeleição)"},
    {"slug": "joel-rodrigues", "nome": "Joel Rodrigues", "partido": "PP",
     "categoria": "desafiante"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Maranhão/Paraíba
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
plano governo piauí piauiense piauienses eleições 2026 partido número
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
# Rafael Fonteles: documento em 8 "Eixos" (o eixo 1, "Pacto pela Economia", é
# descrito no próprio texto como "eixo global... que funciona como elemento
# integrador"; os outros 7 são "eixos estratégicos"), cada um subdividido em
# "Programa N – Título" (53 programas ao todo, numerados sequencialmente e
# sem repetição — não há sumário/índice no início do documento que repita os
# títulos dos eixos ou programas antes do corpo real, então o bug do
# Maranhão/sumário duplicado não se aplica aqui; confirmado por grep antes de
# escrever este script).
#
# Estratégia de segmentação: como os "Eixos" 2, 3, 4 e 8 reúnem
# explicitamente mais de um tema no título (ex.: Eixo 2 = "Saúde, Segurança e
# Trânsito"), a segmentação foi feita no nível de PROGRAMA (mais granular),
# não no nível de Eixo — cada um dos 53 programas tem título e conteúdo
# tematicamente identificável. O parágrafo de abertura de cada Eixo (a
# "conversa" antes do primeiro Programa daquele eixo) foi lido e classificado
# caso a caso: nos eixos cujo título já reúne mais de um tema (2, 3, 4, e o
# eixo 8 por conter o Programa 53 multitemático), a abertura também mistura
# temas em prosa corrida (ex.: a do Eixo 2 fala de saúde E segurança no mesmo
# parágrafo) e foi classificada como "outros"; nos eixos monotemáticos (1, 5,
# 6, 7 e a maior parte do 8), a abertura é, na leitura integral, inteiramente
# sobre aquele único tema (conferido trecho a trecho) e foi classificada
# junto com o tema do eixo, em vez de "outros" — mesmo critério do Maranhão
# (só vira "outros" o que não é seguramente atribuível a um único tema).
MARCADORES_FONTELES = [
    ("Eixo 1\n", "economia"),
    ("Programa 1 – Fortalecimento da cultura empreendedora", "economia"),
    ("Programa 2 – Mais Formação, Mais Renda", "economia"),
    ("Programa 3 – Trabalhar, Empreender e Prosperar", "economia"),
    ("Programa 4 – Crédito produtivo", "economia"),
    ("Programa 5 – Pro Piauí 10", "economia"),
    ("Programa 6 – Pro Piauí 100", "economia"),
    ("Programa 7 – Mais Rentabilidade no Campo", "economia"),
    ("Programa 8 – Casa Legal e Terra Legal", "economia"),  # regularização fundiária — precedente PB/MA: tratada junto do eixo econômico quando o próprio plano a enquadra como parte do "choque de desenvolvimento econômico" (é uma Meta do Programa 1); aqui é tratada como economia por estar no eixo econômico
    ("Programa 9 – Piauí Conectado ao Mundo", "economia"),
    ("Programa 10 – Piauí de Turismo e Economia Criativa", "economia"),

    ("Eixo 2\n", "outros"),
    ("Programa 11 – Saúde Digital e Acesso Universal", "saude"),
    ("Programa 12 – Hospitais mais Eficientes e Humanizados", "saude"),
    ("Programa 13 – Saúde Mental: Cuidado que Transforma Vidas", "saude"),
    ("Programa 14 – Vigilância e Resposta em Saúde", "saude"),
    ("Programa 15 – Pacto pela Ordem", "seguranca"),
    ("Programa 16 – Caminhos para a Ressocialização", "seguranca"),
    ("Programa 17 – Pacto contra o Feminicídio", "seguranca"),
    # Trânsito (mortalidade viária, fiscalização, CNH Social) classificado
    # como segurança pública — mesma lógica do resto do Eixo 2 ("A Vida em
    # Primeiro Lugar"), não como infraestrutura.
    ("Programa 18 – Pacto pela Vida no Trânsito", "seguranca"),

    ("Eixo 3\n", "outros"),
    ("Programa 19 – Escola que Educa, Transforma e Inclui", "educacao"),
    ("Programa 20 – Alfabetização das Crianças na Idade Certa", "educacao"),
    ("Programa 21 – Piauí Alfabetiza e Avança", "educacao"),
    # Cultura e Esporte, dentro do eixo de Educação: seguindo o precedente do
    # Maranhão (Orleans Brandão), cultura e esporte são classificados como
    # assistência social/direitos, não como educação nem como economia.
    ("Programa 22 – Piauí de Cultura Viva", "assistencia_social"),
    ("Programa 23 – Esporte que Transforma", "assistencia_social"),

    ("Eixo 4\n", "outros"),
    # Piauí Inovador: hubs de inovação e pesquisa aplicada vinculados às
    # cadeias produtivas do Estado — tratado como economia (mesmo critério
    # do Programa 27, abaixo).
    ("Programa 24 – Piauí Inovador", "economia"),
    # Zap do Cidadão e CapacitIA: portas de acesso digital a serviços
    # públicos e formação de "agentes comunitários digitais" — o conteúdo é
    # sobre a capacidade do próprio Estado de prestar serviço (governo
    # digital), não sobre desenvolvimento econômico ou assistência social;
    # tratados como gestão pública.
    ("Programa 25 – Zap do Cidadão", "gestao_publica"),
    ("Programa 26 – CapacitIA - Autonomia Digital", "gestao_publica"),
    # Ciência que Gera Resultados: financiamento à pesquisa aplicada (FAPEPI)
    # com foco explícito em "fortalecimento dos negócios locais" e
    # "desenvolvimento territorial" — tratado como economia.
    ("Programa 27 – Ciência que Gera Resultados", "economia"),

    ("Eixo 5\n", "assistencia_social"),
    ("Programa 28 – Pacto pela Assistência Social", "assistencia_social"),
    ("Programa 29 – Pacto pelas Crianças", "assistencia_social"),
    ("Programa 30 – Piauí da Igualdade Racial", "assistencia_social"),
    ("Programa 31 – Piauí Por Elas", "assistencia_social"),
    ("Programa 32 – Piauí Mais Inclusivo", "assistencia_social"),
    ("Programa 33 – Oportunidade Jovem", "assistencia_social"),
    ("Programa 34 – Pacto pela Pessoa Idosa", "assistencia_social"),
    ("Programa 35 – Caminhos para Recomeçar – Socioeducação com", "assistencia_social"),
    ("Programa 36 – Piauí de Todas as Cores", "assistencia_social"),

    ("Eixo 6\n", "infraestrutura"),
    ("Programa 37 – Estradas que Conectam o Piauí", "infraestrutura"),
    ("Programa 38 – Minha Rua, Minha Vida", "infraestrutura"),
    ("Programa 39 – Porto e Hidrovia: O Corredor Azul do Desenvolvimento", "infraestrutura"),
    ("Programa 40 – Água e Saneamento para Todos", "infraestrutura"),
    ("Programa 41 – Água e vida", "infraestrutura"),
    ("Programa 42 – Energia do Futuro, Riqueza do Presente", "infraestrutura"),

    ("Eixo 7\n", "meio_ambiente"),
    ("Programa 43 – Piauí que Preserva, Piauí que Cresce", "meio_ambiente"),
    ("Programa 44 – Pacto pela Revitalização da Bacia do Parnaíba", "meio_ambiente"),
    ("Programa 45 – Zero Lixões", "meio_ambiente"),
    ("Programa 46 – Pacto pelos Animais", "meio_ambiente"),
    # Gestão de riscos e desastres (defesa civil) classificada como meio
    # ambiente, por estar no eixo "Meio Ambiente, Clima, Recursos Hídricos,
    # Defesa Civil e Proteção Animal" e tratar de risco climático.
    ("Programa 47 – Piauí Preventivo: Gestão de Riscos e Desastres", "meio_ambiente"),

    ("Eixo 8\n", "gestao_publica"),
    ("Programa 48 – Valorizar Para Servir Melhor", "gestao_publica"),
    ("Programa 49 – Piauí Participativo, Decisões Compartilhadas", "gestao_publica"),
    ("Programa 50 – Equilíbrio para Investir", "gestao_publica"),
    ("Programa 51 – Piauí Transparente", "gestao_publica"),
    ("Programa 52 – Pactos pelo Piauí", "gestao_publica"),
    # Regiões Metropolitanas de Teresina e Parnaíba: o próprio texto define
    # o programa como multitemático e indivisível em um único parágrafo de
    # metas ("competitividade, infraestrutura urbana, segurança, turismo,
    # cultura") sem subtítulos por área — mesmo critério do Maranhão
    # (Felipe Camarão, Bloco 1) para blocos explicitamente multitemáticos:
    # classificado como "outros".
    ("Programa 53 – Desenvolvimento das Regiões Metropolitanas de", "outros"),
]

# ---------------------------------------------------------------------------
# Joel Rodrigues: documento em 11 "EIXO"s, cada um com uma "Apresentação do
# eixo" (visão geral + lista de "Frentes Estratégicas de Atuação") seguida de
# "Ações e orientações programáticas" (as Ações Programáticas numeradas por
# frente, ex. "2.1", "2.1.1"). Cada Eixo aparece DUAS VEZES no texto (uma
# como cabeçalho de abertura antes da "Apresentação do eixo", outra
# imediatamente antes de "Ações e orientações programáticas") — não é um
# sumário/índice (o sumário real, no início do documento, usa numeração
# "6.1 Governança Territorial..." e não repete o texto "EIXO N"), então o
# bug do Maranhão não se aplica; confirmado por grep antes de escrever este
# script. Usa-se a 1ª ocorrência de cada "EIXO N" como marcador (cobre
# apresentação + ações, o eixo inteiro).
#
# IMPORTANTE: os marcadores usam "EIXO 1\n" (com quebra de linha), não
# apenas "EIXO 1", porque "EIXO 1" é uma substring literal de "EIXO 10" e
# "EIXO 11" — sem o "\n" de proteção, a lógica de cursor_inicial (que busca a
# 2ª ocorrência do 1º marcador para pular sumários) encontraria por engano
# "EIXO 10"/"EIXO 11" como "2ª ocorrência" de "EIXO 1" e quebraria toda a
# segmentação. Com "\n", cada marcador só casa com o título de eixo real.
#
# A maioria dos eixos é tematicamente uniforme (todas as suas "frentes
# estratégicas" pertencem ao mesmo tema), então a segmentação foi feita no
# nível de EIXO (mais grosso que no plano de Fonteles, mas fiel à estrutura
# real deste documento — que não tem uma segunda camada de títulos "Programa
# N" como o de Fonteles, e sim frentes "N.M" cujo cabeçalho de conteúdo real
# tem formatação de quebra de linha inconsistente com o da lista-prévia da
# "Apresentação do eixo", o que tornaria marcadores por frente propensos ao
# mesmo tipo de bug de índice — por isso não foram usados).
MARCADORES_RODRIGUES = [
    ("EIXO 1\n", "gestao_publica"),  # Governança Territorial, Presença do Estado, Integridade e Capacidade de Entrega
    ("EIXO 2\n", "saude"),  # Saúde, Cuidado, Regionalização e Qualidade de Vida
    ("EIXO 3\n", "educacao"),  # Educação, Conhecimento, Juventude e Inclusão Educacional
    ("EIXO 4\n", "seguranca"),  # Segurança Pública, Trânsito Seguro e Justiça Integrada
    ("EIXO 5\n", "economia"),  # Desenvolvimento Econômico, Trabalho, Renda, Turismo e Inovação Produtiva
    ("EIXO 6\n", "economia"),  # Desenvolvimento Rural, Agricultura e Agronegócio
    ("EIXO 7\n", "infraestrutura"),  # Infraestrutura, Cidades, Habitação, Mobilidade e Integração Territorial
    # Cultura, Patrimônio, Identidade Territorial, Turismo Cultural e
    # Economia Criativa: das 7 "frentes estratégicas" deste eixo, 5 são
    # sobre cultura/patrimônio/identidade e só 2 (economia criativa, turismo
    # cultural) têm ênfase econômica; a "Apresentação do eixo" também
    # enquadra o eixo primeiro como "força do Piauí" cultural/identitária.
    # Classificado como assistência social (cultura), seguindo o precedente
    # de Orleans Brandão no Maranhão — nota: é uma decisão diferente da
    # tomada para o eixo combinado "Turismo, Cultura e Patrimônio" de
    # Eduardo Braide (também no Maranhão), que foi classificado como
    # economia por ênfase econômica predominante no texto daquele plano;
    # aqui a leitura do texto pesou para o lado cultural/identitário.
    ("EIXO 8\n", "assistencia_social"),
    ("EIXO 9\n", "meio_ambiente"),  # Meio Ambiente, Recursos Hídricos e Minerais, Transição Sustentável e Resiliência Territorial
    ("EIXO 10\n", "assistencia_social"),  # Proteção Social, Direitos, Equidade, Mulheres, Famílias, Juventude e Cidadania Transversal
    ("EIXO 11\n", "assistencia_social"),  # Esporte, Lazer, Inclusão e Desenvolvimento Humano — precedente Maranhão: esporte = assistência social
    # Seções de encerramento (metodologia de escuta popular + agradecimentos
    # nominais), sem conteúdo temático de política pública — "outros".
    ("7. O PIAUÍ QUE OUVIMOS:", "outros"),
]

MARCADORES = {
    "rafael-fonteles": MARCADORES_FONTELES,
    "joel-rodrigues": MARCADORES_RODRIGUES,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica à da Paraíba/Maranhão)
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
# TAREFA 4 — Nuvem de palavras
# ---------------------------------------------------------------------------
def gerar_wordcloud_png_b64(counts: Counter, slug: str) -> str:
    wc = WordCloud(
        width=800, height=500, background_color=None, mode="RGBA",
        colormap="viridis", prefer_horizontal=0.92, max_words=120,
    ).generate_from_frequencies(counts)
    png_path = WC_DIR / f"{slug}.png"
    wc.to_file(str(png_path))
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # preserva campos publicados fora do escopo deste script (ex.:
    # achado_texto_compartilhado/texto_compartilhado, escritos por um
    # script separado de deteccao de texto compartilhado; lista_jargao_
    # utilizada, metodologia_frequencia_palavras) -- corrige um defeito
    # em que rerodar este script apagava esses campos silenciosamente
    # (achado em 25/08/2026 durante o rollout do indice de cobertura).
    analise_anterior_path = ANALISE_DIR / "analise.json"
    analise_anterior = (
        json.loads(analise_anterior_path.read_text(encoding="utf-8"))
        if analise_anterior_path.exists() else {}
    )
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
        # índice que repete os títulos das seções antes do corpo real), pula
        # para a 2ª ocorrência, para não segmentar dentro do índice. Mesma
        # lógica de proteção usada no Maranhão. Nos dois planos do Piauí essa
        # proteção não chega a ser acionada (nenhum dos dois tem sumário que
        # repita os títulos usados como marcador — verificado por grep antes
        # de escrever os MARCADORES_* acima), mas o código é mantido idêntico
        # por robustez e para preservar a comparabilidade entre estados.
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
                f.write(f"[{tema:20s}] {n:6d} palavras :: {marcador[:80]!r}\n")

        print(f"{c['nome']:<20} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
              f"(a={be['n_pilar_a_diagnostico']} b={be['n_pilar_b_efeito']} c={be['n_pilar_c_evidencia_causal']} "
              f"/ retorica={be['n_retorica_sem_evidencia']})")
        soma_pct = round(sum(pct.values()), 1)
        print(f"  soma distribuicao_tematica_pct = {soma_pct}")

    top_agregado = agregado_counter.most_common(30)

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "19 de agosto de 2026",
        "lista_jargao_utilizada": JARGAO_TERMOS,
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'Piauí', 'eleições'). Mostra os termos mais repetidos "
            "por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/programa/frente, "
            "verbatim). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando uma seção do documento original já reunia "
            "explicitamente múltiplos temas de forma indivisível (ex.: um "
            "programa que o próprio candidato define como cruzando "
            "infraestrutura, segurança, turismo e cultura em uma única lista "
            "de metas, sem subtítulos por área), o segmento foi classificado "
            "como 'outros'. Parágrafos de abertura de eixo/seção que resumem "
            "resultados de forma genérica, sem se prender a um único tema, "
            "também foram classificados como 'outros' quando não era "
            "possível atribuí-los com segurança a uma única área."
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
            "Heurística idêntica à usada nas análises da Paraíba e do "
            "Maranhão, sem nenhum ajuste específico para o Piauí, para "
            "manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "Os dois planos do Piauí têm estruturas de seção bem diferentes "
            "entre si, e a granularidade da segmentação temática refletiu "
            "essa diferença: o plano de Rafael Fonteles organiza seus 8 "
            "'Eixos' em 53 'Programas' numerados, cada um com título e "
            "conteúdo tematicamente identificável, o que permitiu segmentar "
            "no nível de Programa (marcadores mais finos); o plano de Joel "
            "Rodrigues organiza seus 11 'Eixos' em 'Frentes Estratégicas' "
            "numeradas (ex. 2.1, 2.2...), mas o cabeçalho de cada frente "
            "aparece no texto com quebra de linha e hifenização diferentes "
            "entre a lista-prévia da 'Apresentação do eixo' e o início real "
            "do conteúdo em 'Ações e orientações programáticas' — usar essas "
            "frentes como marcador exigiria o mesmo tipo de proteção contra "
            "casar com a ocorrência errada (a lista-prévia, e não o "
            "conteúdo real) que o Maranhão precisou para sumários/índices, "
            "com risco de erro maior que o ganho de granularidade; por isso, "
            "no plano de Joel Rodrigues a segmentação foi feita no nível de "
            "Eixo (marcadores mais grossos). Nos dois planos, cada Eixo do "
            "Piauí aparece mais de uma vez no texto bruto (um cabeçalho de "
            "abertura de seção e, no caso de Joel Rodrigues, um segundo "
            "cabeçalho antes do bloco de ações), mas nenhum dos dois planos "
            "tem um sumário/índice no início do documento que repita os "
            "títulos usados como marcador antes do corpo real — o bug de "
            "sumário encontrado no Maranhão (onde o 1º marcador casava "
            "primeiro com a ocorrência do índice) foi checado explicitamente "
            "para os dois planos e não se aplica aqui; a lógica de proteção "
            "(cursor_inicial) foi mantida no código por robustez e "
            "comparabilidade. Uma armadilha específica do Piauí, porém, foi "
            "encontrada e corrigida: no plano de Joel Rodrigues, o texto "
            "'EIXO 1' é uma substring literal de 'EIXO 10' e 'EIXO 11' — os "
            "marcadores usam 'EIXO N\\n' (com quebra de linha) para casar "
            "apenas com o título de eixo real, e não com o início do número "
            "de um eixo de dois dígitos. Por fim, uma limitação da extração "
            "do texto-fonte (não do método de análise): o PDF de Joel "
            "Rodrigues tem diagramação justificada em que várias palavras "
            "foram hifenizadas na quebra de linha (ex.: 'pro-' numa linha, "
            "'gramática' na linha seguinte) e a extração de texto preservou "
            "esse hífen literal em vez de rejuntar a palavra; cerca de 6% "
            "dos tokens do plano de Joel Rodrigues são fragmentos desse tipo "
            "(ex.: 'pro-', 're-', 'es-'), o que ocasionalmente aparece na "
            "lista de palavras mais frequentes e na nuvem de palavras dele. "
            "Isso não afeta a segmentação temática (os marcadores usados são "
            "títulos de seção, não palavras do meio de parágrafos "
            "hifenizados), mas é uma característica do texto-fonte deste "
            "candidato especificamente, mantida sem correção manual — assim "
            "como o Maranhão manteve sem correção manual o ruído de OCR do "
            "plano de Felipe Camarão — para não introduzir edição "
            "discricionária no corpo analisado."
        ),
    }

    analise = {**analise_anterior, **analise}
    analise["gerado_em"] = "25 de agosto de 2026"  # rollout indice de cobertura

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
