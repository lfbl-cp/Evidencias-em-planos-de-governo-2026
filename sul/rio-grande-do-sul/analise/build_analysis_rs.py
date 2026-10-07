#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Rio Grande do Sul 2026.

Réplica EXATA da metodologia usada no Ceará (build_analysis_ce.py), que por
sua vez replicou Maranhão/Paraíba: distribuição temática exaustiva por
segmentação de marcadores de seção reais (lidos e mapeados à mão) e Índice
de Base Empírica (heurística lexical/regex idêntica, reaproveitada sem
alterações para manter comparabilidade entre estados). Tokenização,
stopwords, `distribuicao_tematica_exaustiva`, `base_empirica_analise`,
`strip_header`, cálculo de `cursor_inicial` e geração de wordcloud são
copiados VERBATIM do motor canônico do Ceará.

Caso especial do Rio Grande do Sul: é uma disputa SEM INCUMBENTE. O atual
governador Eduardo Leite (PSDB) já cumpriu o limite constitucional de
reeleições e não é candidato ao Executivo estadual — concorre ao Senado.
Nem Luciano Zucco (PL) nem Juliana Brizola (PDT) jamais ocuparam o cargo de
governador ou vice-governador do RS; ambos estão em sua primeira
candidatura ao Executivo estadual, e por isso ambos são classificados como
"desafiante". Isso não muda a metodologia de análise textual (idêntica aos
demais estados), mas é relevante para o enquadramento editorial do achado.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sul/rio-grande-do-sul/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sul/rio-grande-do-sul/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "luciano_zucco", "nome": "Luciano Zucco", "partido": "PL",
     "categoria": "desafiante — corrida sem governador em exercício candidato à "
                  "reeleição (Eduardo Leite, PSDB, não concorre ao Executivo estadual "
                  "e disputa o Senado); deputado federal (2022–atual, o mais votado do "
                  "RS em 2022) e ex-deputado estadual (2018–2022), em sua primeira "
                  "candidatura ao Executivo estadual"},
    {"slug": "juliana_brizola", "nome": "Juliana Brizola", "partido": "PDT",
     "categoria": "desafiante — corrida sem governador em exercício candidato à "
                  "reeleição (Eduardo Leite, PSDB, não concorre ao Executivo estadual "
                  "e disputa o Senado); ex-deputada estadual (2011–2023) e "
                  "ex-vereadora de Porto Alegre, também candidata a prefeita de Porto "
                  "Alegre em 2020 (4º lugar), em sua primeira candidatura ao "
                  "Executivo estadual"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Maranhão/Paraíba (não adaptadas ao
# Ceará), para preservar comparabilidade entre estados.
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

# Luciano Zucco: documento muito bem estruturado, organizado em 5 grandes
# blocos ("UM ESTADO QUE PROTEGE" / "QUE CUIDA" / "QUE CRESCE" / "QUE
# CONECTA" / "QUE FUNCIONA" / "QUE LIDERA" — divisores de página, sem
# conteúdo temático próprio, absorvidos no segmento anterior) contendo 28
# seções temáticas com títulos de capítulo reais (em caixa alta, quebrados
# em 1-2 linhas por página). NÃO há sumário/índice repetindo os títulos no
# início do documento — o primeiro marcador ("SEGURANÇA PÚBLICA") aparece
# uma única vez no corpo inteiro, então `cursor_inicial` resolve para 0
# (nenhum salto necessário).
#
# "SISTEMA PRISIONAL E JUSTIÇA PENAL" = seguranca, seguindo o precedente do
# Mato Grosso (build_analysis_mt.py: "seguranca (policiamento e sistema
# prisional)").
#
# "DEFESA CIVIL E RESILIÊNCIA CLIMÁTICA" é uma seção autônoma (não bundlada
# com segurança pública, como no Maranhão) — classificada como
# "meio_ambiente", seguindo o precedente do Piauí (build_analysis_pi.py:
# "gestão de riscos e desastres (defesa civil) classificada como meio
# ambiente") e do Espírito Santo (defesa civil/resiliência climática =
# meio_ambiente).
#
# "DEFESA AGROPECUÁRIA, SANIDADE E BEM-ESTAR ANIMAL" mistura dois temas
# distintos e claramente separáveis por subtítulo de proposta: a vigilância
# zoo/fitossanitária que protege a competitividade do agronegócio (do
# início da seção até "QUALIFICAR OS SERVIÇOS DE INSPEÇÃO") = "economia",
# seguindo o precedente de Goiás ("Agropecuária Forte, Segura, Sustentável e
# Inovadora" = economia); a partir de "PROMOVER O BEM-ESTAR DOS ANIMAIS DE
# PRODUÇÃO" até o fim da seção (animais de produção + animais domésticos) =
# "assistencia_social", seguindo o precedente quase universal do projeto
# para bem-estar/proteção animal (Bahia, Ceará, Maranhão, RN, Tocantins,
# Espírito Santo, Minas Gerais).
#
# "PROTEÇÃO ÀS MULHERES, CRIANÇAS E PESSOAS VULNERÁVEIS" está posicionada
# dentro do bloco "UM ESTADO QUE PROTEGE" (junto de segurança pública,
# sistema prisional e defesa civil) e o conteúdo é dominado por mecanismos
# de proteção via aparato de segurança (delegacias, Patrulha Maria da
# Penha, monitoração eletrônica de agressores, medidas protetivas) —
# classificada como "seguranca", seguindo o precedente do Rio Grande do
# Norte ("Proteção às Mulheres e Enfrentamento ao Feminicídio" = seguranca)
# e do Piauí ("Pacto contra o Feminicídio" = seguranca), e não o precedente
# alternativo de Rondônia (mesmo conteúdo = assistencia_social) — mantida a
# mesma classificação para a seção equivalente de Juliana Brizola, para
# preservar comparabilidade entre os dois planos do RS.
#
# "PRIMEIRA INFÂNCIA" = assistencia_social, seguindo o precedente de
# Alagoas. "FAMÍLIA, DESENVOLVIMENTO SOCIAL E INCLUSÃO" e "ESPORTE, CULTURA
# E QUALIDADE DE VIDA" = assistencia_social (precedente do projeto para
# assistência social, esporte e cultura).
#
# "INOVAÇÃO, CIÊNCIA E TECNOLOGIA" foi classificada como "economia" (não
# "educacao"): o conteúdo é dominado por startups, ecossistemas regionais
# de inovação, financiamento de tecnologia e cadeias tecnológicas
# estratégicas — seguindo o precedente de Rondônia/Alagoas (inovação/C&T
# voltada a startups, incubadoras e investimento produtivo = economia), e
# não o precedente do Ceará (C&T bundlada com educação/universidades), pois
# aqui o eixo já tem seção própria de "EDUCAÇÃO" separada, sem menção a
# ciência/tecnologia. "TRABALHO, EMPREENDEDORISMO E QUALIFICAÇÃO
# PROFISSIONAL" = economia, seguindo o precedente amplo do projeto
# ("trabalho e renda" = economia: Maranhão, Distrito Federal, Mato Grosso
# do Sul).
#
# "CONCESSÕES, PPPs E GRANDES INVESTIMENTOS" = infraestrutura (financia
# obras de infraestrutura e serviços públicos via capital privado).
# "MUNICIPALISMO E DESENVOLVIMENTO REGIONAL" = gestao_publica (coordenação
# federativa Estado-municípios, regime de colaboração, arranjos
# institucionais regionais — não é sobre uma política setorial específica).
#
# O capítulo final "PROJETOS E PROGRAMAS ESTRATÉGICOS PARA O FUTURO DO RIO
# GRANDE" reúne projetos numerados explicitamente transversais, cada um
# vinculado a várias "Áreas" simultaneamente (ex.: projeto 1 vinculado a
# Gestão Pública, Planejamento Fiscal, Concessões, Municipalismo e
# Integridade ao mesmo tempo) — classificado como "outros", seguindo o
# precedente do Ceará para conteúdo genuinamente transversal não separável
# com segurança.
MARCADORES_ZUCCO = [
    ("SEGURANÇA PÚBLICA", "seguranca"),
    ("SISTEMA PRISIONAL", "seguranca"),
    ("DEFESA CIVIL E", "meio_ambiente"),
    ("DEFESA AGROPECUÁRIA,", "economia"),
    ("PROMOVER O BEM-ESTAR DOS ANIMAIS DE PRODUÇÃO", "assistencia_social"),
    ("PROTEÇÃO ÀS MULHERES,", "seguranca"),
    ("SAÚDE\n\nA saúde pública do Rio Grande do Sul enfrenta", "saude"),
    ("EDUCAÇÃO\n\nA educação pública gaúcha convive", "educacao"),
    ("PRIMEIRA INFÂNCIA\n\nOs primeiros anos de vida", "assistencia_social"),
    ("FAMÍLIA, DESENVOLVIMENTO SOCIAL", "assistencia_social"),
    ("ESPORTE, CULTURA", "assistencia_social"),
    ("DESENVOLVIMENTO ECONÔMICO\nE AMBIENTE DE NEGÓCIOS", "economia"),
    ("AGROPECUÁRIA\nE AGROINDÚSTRIA", "economia"),
    ("INOVAÇÃO, CIÊNCIA", "economia"),
    ("TURISMO E", "economia"),
    ("TRABALHO, EMPREENDEDORISMO", "economia"),
    ("INFRAESTRUTURA LOGÍSTICA", "infraestrutura"),
    ("MOBILIDADE E TRANSPORTE", "infraestrutura"),
    ("HABITAÇÃO E", "infraestrutura"),
    ("ENERGIA E INFRAESTRUTURA", "infraestrutura"),
    ("CONCESSÕES, PPPs", "infraestrutura"),
    ("GESTÃO PÚBLICA\nE GOVERNANÇA", "gestao_publica"),
    ("PLANEJAMENTO, FINANÇAS E", "gestao_publica"),
    ("TRANSFORMAÇÃO DIGITAL", "gestao_publica"),
    ("PESSOAS, MERITOCRACIA", "gestao_publica"),
    ("INTEGRIDADE, TRANSPARÊNCIA", "gestao_publica"),
    ("MUNICIPALISMO E", "gestao_publica"),
    ("RELAÇÕES INSTITUCIONAIS", "gestao_publica"),
    ("DESENVOLVIMENTO SUSTENTÁVEL\nE GESTÃO AMBIENTAL", "meio_ambiente"),
    ("POSICIONAMENTO INTERNACIONAL", "economia"),
    ("PROJETOS E PROGRAMAS ESTRATÉGICOS", "outros"),
]

# Juliana Brizola: documento com Sumário completo no início repetindo os
# títulos numerados (1.1, 1.2, ... 4.3) das 34 subseções — mesmo padrão já
# encontrado no Ceará (Elmano de Freitas) — protegido pela mesma lógica de
# `cursor_inicial` (2ª ocorrência do primeiro marcador, "1.1 - EDUCAÇÃO
# PÚBLICA, BÁSICA", usada como ponto de partida, pulando o Sumário).
#
# PARTICULARIDADE DE EXTRAÇÃO deste PDF (ver nota de metodologia): o corpo
# do documento foi extraído em DUAS COLUNAS INTERCALADAS LINHA A LINHA — a
# extração não segue a ordem de leitura (coluna esquerda inteira, depois
# coluna direita), e sim alterna uma linha da coluna esquerda com uma linha
# da coluna direita ao longo de toda a página, misturando o texto de
# "DIAGNÓSTICO SITUACIONAL" (coluna esquerda) com o de "DIRETRIZES E AÇÕES"
# (coluna direita) frase a frase. Isso não afeta a contagem total de
# palavras nem a segmentação temática por marcador (que operam por posição
# de caractere, contando o texto entre um título de seção e o próximo,
# independentemente da ordem interna das frases), mas fragmenta as frases
# usadas como exemplo no Índice de Base Empírica de forma mais acentuada
# que em planos extraídos como texto corrido — mesmo tipo de ressalva já
# documentada para o Eixo 01 de Ciro Gomes (Ceará), aqui com causa
# equivalente (colunas fora de ordem) mas presente ao longo de TODO o
# corpo do documento, não apenas em um trecho.
#
# 1.4 "POLÍTICAS PARA AS MULHERES E ENFRENTAMENTO ÀS VIOLÊNCIAS DE GÊNERO"
# = seguranca, mesma classificação usada para a seção equivalente de
# Luciano Zucco (ver comentário acima), para preservar comparabilidade
# entre os dois planos do RS: o conteúdo é dominado pelo Sistema Único de
# Proteção das Mulheres, Rede Lilás, DEAMs, Patrulha Maria da Penha e
# monitoração eletrônica de agressores.
#
# 1.7 "DIREITOS HUMANOS" = assistencia_social (proteção a defensores de
# direitos humanos, reintegração de egressos do sistema prisional,
# conselhos de direitos — sem foco predominante em aparato policial).
# 1.9 "CULTURA..." e 1.11 "ESPORTE..." = assistencia_social (precedente do
# projeto). 1.12 a 1.16 (igualdade racial, diversidade sexual, primeira
# infância, pessoa idosa, PCD) = assistencia_social (proteção a grupos
# vulneráveis, precedente do projeto). 1.18 "POLÍTICAS PÚBLICAS PARA AS
# JUVENTUDES E PRIMEIRO EMPREGO" = assistencia_social, seguindo o
# precedente do projeto para seções de juventude (Rondônia, Pará), mesmo
# contendo o Programa Primeiro Emprego Gaúcho, pois o diagnóstico da seção
# é dominado por vulnerabilidade social (desemprego, evasão escolar,
# violência), não por política de mercado de trabalho em geral.
#
# 1.17 "ECONOMIA SOLIDÁRIA, POPULAR E COOPERATIVISMO" = economia (geração
# de trabalho/renda via cooperativismo). 1.19 "DIREITOS, PROTEÇÃO E
# BEM-ESTAR ANIMAL" = assistencia_social (precedente quase universal do
# projeto). 2.6 "DEFESA CIVIL E GESTÃO PREDITIVA DE RISCOS CLIMÁTICOS" =
# meio_ambiente, mesma classificação usada para a seção equivalente de
# Zucco. 3.1 "AGRICULTURA FAMILIAR E ABASTECIMENTO ALIMENTAR" = economia
# (o "abastecimento" aqui é o Programa Estadual de Abastecimento —
# comercialização da produção familiar —, não um programa de combate à
# fome/segurança alimentar; dominante no diagnóstico é a economia rural:
# crédito, sucessão geracional, agroindustrialização).
#
# 4.2 "FINANÇAS PÚBLICAS" e 4.3 "BANCOS PÚBLICOS" — a seção 4.2 é sobre o
# equilíbrio fiscal do Estado (gestao_publica); a 4.3 é sobre bancos
# públicos (Banrisul/Badesul/BRDE) como instrumento de crédito para
# empresas, cooperativas e desenvolvimento produtivo — classificada como
# "economia". O capítulo final "CONCLUSÃO — UM NOVO CICLO DE
# DESENVOLVIMENTO" dá continuidade direta ao tema fiscal da seção 4.2
# (dívida com a União, FUNRIGS, Fundo Constitucional da Região Sul) —
# classificado como "gestao_publica".
MARCADORES_BRIZOLA = [
    ("1.1 - EDUCAÇÃO PÚBLICA, BÁSICA", "educacao"),
    ("1.2 - SAÚDE PÚBLICA, REGIONALIZAÇÃO DO", "saude"),
    ("1.3 - SEGURANÇA PÚBLICA, INTELIGÊNCIA", "seguranca"),
    ("1.4 - POLÍTICAS PARA AS MULHERES E", "seguranca"),
    ("1.5 - TRABALHO, EMPREGO, RENDA E", "economia"),
    ("1.6 - ASSISTÊNCIA SOCIAL, COMBATE À", "assistencia_social"),
    ("1.7 - DIREITOS HUMANOS", "assistencia_social"),
    ("1.8 - HABITAÇÃO DE INTERESSE SOCIAL", "infraestrutura"),
    ("1.9 - CULTURA, MEMÓRIA, PATRIMÔNIO", "assistencia_social"),
    ("1.10 - COMUNICAÇÃO SOCIAL PÚBLICA,", "gestao_publica"),
    ("1.11 - ESPORTE, PARADESPORTO, LAZER", "assistencia_social"),
    ("1.12 - IGUALDADE RACIAL E AÇÕES", "assistencia_social"),
    ("1.13 - DIVERSIDADE SEXUAL E CIDADANIA", "assistencia_social"),
    ("1.14 - PRIMEIRA INFÂNCIA E ADOLESCÊNCIA", "assistencia_social"),
    ("1.15 - DIREITOS E CUIDADO INTEGRAL", "assistencia_social"),
    ("1.16 - INCLUSÃO, ACESSIBILIDADE E DIREITOS", "assistencia_social"),
    ("1.17 - ECONOMIA SOLIDÁRIA, POPULAR E", "economia"),
    ("1.18 - POLÍTICAS PÚBLICAS PARA AS", "assistencia_social"),
    ("1.19 - DIREITOS, PROTEÇÃO", "assistencia_social"),
    ("2.1 - TRANSPORTES, LOGÍSTICA", "infraestrutura"),
    ("2.2 - ENERGIA, MATRIZ RENOVÁVEL E", "infraestrutura"),
    ("2.3 - MINERAÇÃO ESTRATÉGICA,", "economia"),
    ("2.4 - SANEAMENTO BÁSICO, RECURSOS", "infraestrutura"),
    ("2.5 - MEIO AMBIENTE, TRANSIÇÃO", "meio_ambiente"),
    ("2.6 - DEFESA CIVIL E GESTÃO PREDITIVA", "meio_ambiente"),
    ("2.7 - MOBILIDADE URBANA METROPOLITANA", "infraestrutura"),
    ("3.1 - AGRICULTURA FAMILIAR E", "economia"),
    ("3.2 - AGROPECUÁRIA SUSTENTÁVEL", "economia"),
    ("3.3 - COMÉRCIO, SERVIÇOS, ECONOMIA", "economia"),
    ("3.4 - CIÊNCIA, TECNOLOGIA, INOVAÇÃO", "economia"),
    ("3.5 - TURISMO SUSTENTÁVEL", "economia"),
    ("4.1 - GESTÃO PÚBLICA, VALORIZAÇÃO DO", "gestao_publica"),
    ("4.2 - FINANÇAS PÚBLICAS", "gestao_publica"),
    ("4.3 - BANCOS PÚBLICOS", "economia"),
    ("CONCLUSÃO", "gestao_publica"),
]

MARCADORES = {
    "luciano_zucco": MARCADORES_ZUCCO,
    "juliana_brizola": MARCADORES_BRIZOLA,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica ao Maranhão/Paraíba)
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
            "específicos de outros estados, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Rio "
            "Grande do Sul', 'gaúcho'/'gaúchos' e 'RS' NÃO são filtrados e "
            "podem aparecer nos termos mais frequentes). Mostra os termos "
            "mais repetidos por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de capítulo/eixo/bloco, "
            "ou, na ausência de subtítulos internos, o início verbatim de "
            "cada parágrafo). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível, o "
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
            "Heurística idêntica à usada nas análises da Paraíba, do "
            "Maranhão e do Ceará, sem nenhum ajuste específico para o Rio "
            "Grande do Sul, para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O Rio Grande do Sul é um caso especial dentro do projeto: é "
            "uma disputa SEM INCUMBENTE. O atual governador Eduardo Leite "
            "(PSDB) já cumpriu o limite constitucional de reeleições e não "
            "concorre ao Executivo estadual em 2026 — disputa uma vaga ao "
            "Senado. Nem Luciano Zucco (PL) nem Juliana Brizola (PDT) "
            "jamais ocuparam o cargo de governador ou vice-governador do "
            "RS; ambos estão em sua primeira candidatura ao Executivo "
            "estadual (Zucco como deputado federal em exercício, ex-"
            "deputado estadual; Brizola como ex-deputada estadual e "
            "ex-vereadora de Porto Alegre), e por isso ambos foram "
            "classificados como 'desafiante'. As pesquisas mais recentes "
            "de agosto/2026 mostram um empate técnico entre os dois "
            "(Paraná Pesquisas: Zucco 34,4% x Brizola 31,4%; Quaest: "
            "Brizola 24% x Zucco 22%). Essa é uma leitura eleitoral, não "
            "textual: não influenciou nenhuma etapa da extração ou "
            "classificação dos planos. "
            "O plano de Luciano Zucco é o mais longo do projeto até aqui "
            "entre planos de 2 candidatos por estado (107 páginas, ~29 mil "
            "palavras de corpo bruto), muito bem estruturado em 28 seções "
            "temáticas com títulos de capítulo reais, SEM sumário/índice "
            "repetindo os títulos no início — o primeiro marcador "
            "('SEGURANÇA PÚBLICA') aparece uma única vez no documento "
            "inteiro, então `cursor_inicial` resolve para 0 (não há índice "
            "a pular). A seção 'DEFESA AGROPECUÁRIA, SANIDADE E BEM-ESTAR "
            "ANIMAL' mistura dois temas claramente separáveis por "
            "subtítulo de proposta (defesa sanitária = economia; bem-estar "
            "animal = assistencia_social) e foi segmentada em dois "
            "marcadores, como já feito para casos análogos em outros "
            "estados do projeto. "
            "O plano de Juliana Brizola (38 páginas, ~16 mil palavras) tem "
            "um Sumário completo no início repetindo os 34 títulos "
            "numerados (1.1 a 4.3) das subseções — mesmo padrão já "
            "encontrado no Ceará (Elmano de Freitas) e no Maranhão (Felipe "
            "Camarão) — corrigido pela mesma lógica de `cursor_inicial` (2ª "
            "ocorrência do primeiro marcador, '1.1 - EDUCAÇÃO PÚBLICA, "
            "BÁSICA', como ponto de partida). "
            "DEFEITO DE EXTRAÇÃO relevante, específico do PDF de Juliana "
            "Brizola: o corpo do documento foi extraído em DUAS COLUNAS "
            "INTERCALADAS LINHA A LINHA ao longo de TODO o texto — cada "
            "linha física do .txt alterna uma linha da coluna esquerda "
            "('DIAGNÓSTICO SITUACIONAL') com uma linha da coluna direita "
            "('DIRETRIZES E AÇÕES') da mesma página, em vez de preservar a "
            "ordem de leitura (coluna inteira antes da próxima). Isso não "
            "afeta a contagem total de palavras nem a distribuição "
            "temática por marcador (que operam por posição de caractere, "
            "contando o texto entre um título de seção e o próximo, "
            "independentemente da ordem interna das frases), mas fragmenta "
            "de forma mais acentuada as frases usadas como exemplo no "
            "Índice de Base Empírica — problema da mesma natureza já "
            "documentado para o Eixo 01 de Ciro Gomes no Ceará (PDF em "
            "duas colunas fora de ordem de leitura), aqui presente ao "
            "longo de todo o corpo do documento, não apenas em um trecho "
            "isolado. Não foi feita nenhuma correção manual da ordem das "
            "colunas, para não introduzir uma etapa de processamento "
            "específica deste estado. "
            "Nenhum dos dois .txt do Rio Grande do Sul apresenta mojibake "
            "ou ligaduras fi/fl quebradas. "
            "Ressalva sobre a frequência de palavras: os dois PDFs "
            "extraídos preservam cabeçalhos/rodapés de página repetidos ao "
            "longo de todo o corpo do texto ('ZUCCO GOVERNADOR | SILVANA "
            "COVATTI VICE', 96 ocorrências no plano de Zucco; 'Plano de "
            "Governo Juliana Brizola - 2027-2030', 38 ocorrências no plano "
            "de Brizola — uma por página). Isso infla artificialmente a "
            "contagem de 'zucco' (100 ocorrências) no plano de Luciano "
            "Zucco e de 'brizola' (45 ocorrências) e 'coligação' (67 "
            "ocorrências, do rótulo recorrente 'A Coligação Com o Povo') "
            "no plano de Juliana Brizola, fazendo esses termos aparecerem "
            "entre os mais frequentes por um motivo estrutural do "
            "documento (cabeçalho/rodapé e rótulo de coligação repetidos), "
            "não por ênfase textual real do candidato — mesmo tipo de "
            "ruído de extração já documentado em outros estados do "
            "projeto (Ceará, Maranhão), embora de origem diferente."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
