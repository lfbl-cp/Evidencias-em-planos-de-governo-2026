#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Mato Grosso do Sul 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste e nos estados já
processados do Norte (ver, por exemplo,
/home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py e
/home/claude/brasil_2026/norte/tocantins/analise/build_analysis_to.py):
distribuição temática exaustiva por segmentação de marcadores de seção reais
(lidos e mapeados à mão) e Índice de Base Empírica (heurística lexical/regex
idêntica à usada em todos os outros estados, reaproveitada sem alterações
para manter comparabilidade entre estados e entre regiões).

Caso de Mato Grosso do Sul: os dois candidatos analisados são Eduardo Riedel
(PP) e Fábio Trad (PT).

Eduardo Riedel é o próprio GOVERNADOR EM EXERCÍCIO concorrendo à reeleição —
incumbente pleno. Foi eleito em 2022 pelo PSDB e migrou para o PP ainda no
mandato (fonte: Gazeta do Povo, "Riedel migra para o PP e PSDB perde último
governador eleito em 2022",
https://www.gazetadopovo.com.br/republica/riedel-migra-pp-psdb-perde-ultimo-governador-eleito-2022/).
O próprio plano de governo de Fábio Trad, registrado oficialmente no TSE
(fonte primária deste projeto), confirma o dado ao se referir a "o plano de
gestão do atual governador Eduardo Riedel (PP), candidato à reeleição"
(ver corpo do arquivo fabio_trad.txt, seção 10.1 Diagnóstico). A cobertura
eleitoral de pré-campanha também confirma a liderança de Riedel nas pesquisas
e Fábio Trad como principal opositor pelo PT (ND+, "Eleições em Mato Grosso
do Sul 2026: Riedel lidera e PT aposta em Fábio Trad",
https://ndmais.com.br/politica/eleicoes-em-mato-grosso-do-sul-pre-candidatos/).

Fábio Trad (PT) é desafiante: ex-vereador, ex-vice-prefeito e ex-prefeito de
Campo Grande, migrou para o PT e é o candidato oficializado pelo partido à
disputa do Governo de MS em oposição ao grupo político de Riedel — fonte:
Campo Grande News, "Oposição contesta modelo de Riedel em Mato Grosso do
Sul" / "Trad e Catan convergem contra Riedel, mas divergem sobre o Estado"
(https://www.campograndenews.com.br/politica/trad-e-catan-convergem-contra-riedel-mas-divergem-sobre-o-estado)
e Poder360, "PT oficializa candidatura de Fábio Trad ao governo de Mato
Grosso do Sul" (https://www.poder360.com.br/poder-eleicoes-2026/pt-oficializa-candidatura-de-fabio-trad-ao-governo-de-mato-grosso-do-sul/).
O próprio plano de governo de Fábio Trad é construído inteiramente como
crítica ao modelo de gestão do governo Riedel (diagnósticos que abrem cada um
dos 13 eixos temáticos contrastam sistematicamente com a gestão estadual
atual), reforçando textualmente o enquadramento de oposição.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/centro-oeste/mato-grosso-do-sul/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/centro-oeste/mato-grosso-do-sul/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "eduardo_riedel", "nome": "Eduardo Riedel", "partido": "PP",
     "categoria": "incumbente pleno — o próprio governador em exercício concorrendo à "
                  "reeleição; eleito em 2022 pelo PSDB, migrou para o PP ainda no mandato "
                  "— fontes: Gazeta do Povo, \"Riedel migra para o PP e PSDB perde último "
                  "governador eleito em 2022\" "
                  "(gazetadopovo.com.br/republica/riedel-migra-pp-psdb-perde-ultimo-governador-eleito-2022); "
                  "o próprio plano de governo de Fábio Trad (registro oficial no TSE) refere-se a "
                  "\"o plano de gestão do atual governador Eduardo Riedel (PP), candidato à "
                  "reeleição\"; e ND+, \"Eleições em Mato Grosso do Sul 2026: Riedel lidera e "
                  "PT aposta em Fábio Trad\" (ndmais.com.br/politica/eleicoes-em-mato-grosso-do-sul-pre-candidatos)"},
    {"slug": "fabio_trad", "nome": "Fábio Trad", "partido": "PT",
     "categoria": "desafiante — ex-vice-prefeito e ex-prefeito de Campo Grande, migrou para "
                  "o PT e foi oficializado pelo partido como opositor ao grupo político do "
                  "governador Eduardo Riedel — fontes: Campo Grande News, \"Trad e Catan "
                  "convergem contra Riedel, mas divergem sobre o Estado\" "
                  "(campograndenews.com.br/politica/trad-e-catan-convergem-contra-riedel-mas-divergem-sobre-o-estado) "
                  "e Poder360, \"PT oficializa candidatura de Fábio Trad ao governo de Mato "
                  "Grosso do Sul\" (poder360.com.br/poder-eleicoes-2026/pt-oficializa-candidatura-de-fabio-trad-ao-governo-de-mato-grosso-do-sul); "
                  "o próprio plano de governo do candidato é construído como crítica "
                  "sistemática ao modelo de gestão do governo Riedel em cada um dos 13 eixos "
                  "temáticos, reforçando textualmente o enquadramento de oposição"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os demais estados do
# projeto (Nordeste e Norte), não adaptadas ao Mato Grosso do Sul, para
# preservar comparabilidade entre estados. Mantidas verbatim, inclusive
# termos estruturais específicos de outros estados (ex.: "maranhão").
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

# Eduardo Riedel (PP): documento em 2 grandes blocos — (1) "O QUE FOI FEITO",
# um balanço da gestão 2023-2026 organizado em subseções temáticas próprias
# (Economia e Competitividade, Redução da Pobreza e Inclusão Social, Saúde
# Pública, Educação, Segurança Pública, Governança e Modernização do Estado,
# Infraestrutura e Logística, Meio Ambiente, MS Ativo Municipalismo,
# Saneamento e Sustentabilidade, Ensino Superior e Programas Sociais,
# Números que Resumem o Mandato); e (2) "DIMENSÕES ESTRATÉGICAS", com 4
# dimensões numeradas, cada uma subdividida em subseções numeradas (1.1, 1.2,
# ...) com título temático explícito e conteúdo coerente com o tema
# anunciado. Segue o mesmo critério já usado no Ceará (Elmano de Freitas)
# para o capítulo de balanço de mandato: como as subseções têm títulos
# temáticos claros e conteúdo coerente, são classificadas pelo próprio tema
# anunciado, em vez de tudo cair em "outros".
#
# Textos de transição/estrutura entre seções (páginas de abertura de
# dimensão com diagramas e parágrafos genéricos de apresentação, listagem-
# índice de subtemas de cada dimensão, "Números que Resumem o Mandato" em
# formato de infográfico que mistura múltiplos temas em poucas linhas cada,
# e o fechamento "O Compromisso que Organiza Tudo") são classificados como
# "outros" — mesmo critério usado em outros estados para conteúdo
# genuinamente estrutural/indivisível entre temas, sem se aprofundar em
# nenhuma política específica.
#
# "Ciência, Tecnologia e Ecossistemas de Inovação" (2.1) e "Turismo de
# Natureza, Cultural e de Negócios" (2.5) e "Bioeconomia, Economia Verde e
# Economia Circular" (2.6) foram classificados como "economia": o próprio
# documento os posiciona dentro da Dimensão 2 ("Desenvolvimento,
# Competitividade e Futuro"), tratando-os explicitamente como vetores de
# desenvolvimento econômico e ambiente de negócios, e não como política
# educacional, cultural/social ou ambiental autônoma — mesmo critério usado
# no Tocantins para C&T e turismo no plano de Professora Dorinha, quando a
# própria candidata os agrupa com a dimensão econômica. Já "Cultura,
# Patrimônio, Economia Criativa e Desenvolvimento Comunitário" (1.5) e
# "Esporte, Juventude e Desenvolvimento Humano" (1.6), dentro da Dimensão 1
# ("Pessoas, Proteção Social e Desenvolvimento Humano"), seguem o precedente
# do projeto (cultura e esporte = assistência social), pois o próprio
# documento os posiciona ao lado de proteção social e cidadania, não de
# desenvolvimento econômico.
#
# "Segurança Hídrica" (3.7) segue o precedente do projeto (Ceará/Tocantins)
# = infraestrutura, mesmo estando dentro da dimensão ambiental. "Clima,
# Energia e Transição Energética" (3.4), "Proteção e Valorização dos Ativos
# Ambientais, Conservação e Biodiversidade" (3.6) e "Licenciamento
# Ambiental, Gestão Territorial e Segurança Jurídica" (3.8) permanecem
# "meio_ambiente" — o conteúdo de licenciamento (3.8), apesar de mencionar
# segurança jurídica, é predominantemente sobre gestão e regulação
# ambiental. "MS Ativo Municipalismo" (parte do balanço de mandato) foi
# classificado como "infraestrutura": o programa descrito é, no corpo do
# texto, essencialmente uma carteira de obras municipais (pavimentação,
# recapeamento, drenagem), não um modelo de governança em si. "Ensino
# Superior e Programas Sociais" mistura, em poucas linhas, um dado
# diagnóstico de ensino superior (IBGE) com estatísticas de programas de
# assistência social (Mais Social, Bolsa Família) — como a maior parte do
# conteúdo é sobre proteção social, o bloco foi classificado como
# "assistencia_social".
MARCADORES_RIEDEL = [
    ("INTRODUÇÃO", "outros"),
    ("O QUE FOI FEITO", "outros"),
    ("Economia e Competitividade", "economia"),
    ("Redução da Pobreza e Inclusão Social", "assistencia_social"),
    ("Saúde Pública", "saude"),
    ("Educação", "educacao"),
    ("Segurança Pública", "seguranca"),
    ("Governança e Modernização do Estado", "gestao_publica"),
    ("Infraestrutura e Logística", "infraestrutura"),
    ("Meio Ambiente", "meio_ambiente"),
    ("MS Ativo Municipalismo", "infraestrutura"),
    ("Saneamento e Sustentabilidade", "infraestrutura"),
    ("Ensino Superior e Programas Sociais", "assistencia_social"),
    ("Números que Resumem o Mandato", "outros"),
    ("Mas a obra não está concluída", "outros"),
    ("sta dimensão reúne o conjunto de políticas", "outros"),
    ("1.1 SEGURANÇA PÚBLICA, JUSTIÇA E PREVENÇÃO DA VIOLÊNCIA", "seguranca"),
    ("1.2 PROTEÇÃO SOCIAL, CIDADANIA, EQUIDADE E INCLUSÃO PRODUTIVA", "assistencia_social"),
    ("1.3 SAÚDE PÚBLICA, REGIONALIZAÇÃO, SAÚDE DIGITAL E VIGILÂNCIA EM SAÚDE", "saude"),
    ("1.4 EDUCAÇÃO BÁSICA, TÉCNICA E PROFISSIONAL", "educacao"),
    ("1.5 CULTURA, PATRIMÔNIO, ECONOMIA CRIATIVA E DESENVOLVIMENTO COMUNITÁRIO", "assistencia_social"),
    ("1.6 ESPORTE, JUVENTUDE E DESENVOLVIMENTO HUMANO", "assistencia_social"),
    ("ato Grosso do Sul vive um novo ciclo de", "outros"),
    ("2.1 CIÊNCIA, TECNOLOGIA E ECOSSISTEMAS DE INOVAÇÃO", "economia"),
    ("2.2 EMPREGO, RENDA E QUALIFICAÇÃO PROFISSIONAL", "economia"),
    ("2.3 AGROPECUÁRIA, AGROINDÚSTRIA E AGRO 5.0", "economia"),
    ("2.4 INDÚSTRIA, COMÉRCIO E SERVIÇOS", "economia"),
    ("2.5 TURISMO DE NATUREZA, CULTURAL E DE NEGÓCIOS", "economia"),
    ("2.6 BIOECONOMIA, ECONOMIA VERDE E ECONOMIA CIRCULAR", "economia"),
    ("2.7 AMBIENTE DE NEGÓCIOS, COMPETITIVIDADE E TRANSFORMAÇÃO ECONÔMICA", "economia"),
    ("sta dimensão reúne as políticas responsáveis pela", "outros"),
    ("3.1 LOGÍSTICA E INTEGRAÇÃO TERRITORIAL", "infraestrutura"),
    ("3.2 CIDADES, HABITAÇÃO E DESENVOLVIMENTO URBANO", "infraestrutura"),
    ("3.3 SANEAMENTO BÁSICO E RESÍDUOS SÓLIDOS", "infraestrutura"),
    ("3.4 CLIMA, ENERGIA E TRANSIÇÃO ENERGÉTICA", "meio_ambiente"),
    ("3.5 CONECTIVIDADE DIGITAL E INFRAESTRUTURA TECNOLÓGICA", "infraestrutura"),
    ("3.6 PROTEÇÃO E VALORIZAÇÃO DOS ATIVOS AMBIENTAIS, CONSERVAÇÃO E BIODIVER-", "meio_ambiente"),
    ("3.7 RECURSOS HÍDRICOS E SEGURANÇA HÍDRICA", "infraestrutura"),
    ("3.8 LICENCIAMENTO AMBIENTAL, GESTÃO TERRITORIAL E SEGURANÇA JURÍDICA", "meio_ambiente"),
    ("sta dimensão é voltada ao fortalecimento", "outros"),
    ("4.1 GOVERNANÇA E GESTÃO PÚBLICA ORIENTADA A RESULTADOS", "gestao_publica"),
    ("4.2 TRANSFORMAÇÃO DIGITAL E EXPERIÊNCIA DO CIDADÃO", "gestao_publica"),
    ("4.3 DADOS, INTELIGÊNCIA E MONITORAMENTO", "gestao_publica"),
    ("4.4 GESTÃO FISCAL E EFICIÊNCIA DO GASTO PÚBLICO", "gestao_publica"),
    ("4.5 TRANSPARÊNCIA, INTEGRIDADE E CONTROLE", "gestao_publica"),
    ("4.6 GESTÃO DE PESSOAS E LIDERANÇA PÚBLICA", "gestao_publica"),
    ("4.7 COMPRAS PÚBLICAS E GESTÃO CONTRATUAL", "gestao_publica"),
    ("O Compromisso\nque Organiza Tudo", "outros"),
]

# Fábio Trad (PT): documento em formato de diagnóstico + propostas, com uma
# "SÍNTESE GERAL" (lista de prioridades) e um "DIAGNÓSTICO GERAL" (contexto
# demográfico/histórico do Estado e histórico do PT no governo estadual)
# como front matter, seguidos por 13 eixos numerados ("1 - ... " a "13 - ..."),
# cada um com sua própria subseção "N.1 - Diagnóstico" e "N.2 - Propostas"
# (ou "N.1 - Propostas" quando o eixo não tem subseção diagnóstica separada
# numerada como N.2). Os títulos dos 13 eixos já indicam um tema único e
# claro, confirmado pelo conteúdo de cada diagnóstico/proposta, e por isso
# cada eixo foi mantido como bloco único — não há, ao contrário de Ceará e
# Tocantins, eixos que cruzem explicitamente mais de um tema da taxonomia de
# 9 temas do projeto sob um único título.
#
# "3 - NOVA POLÍTICA ESTADUAL DE INCENTIVOS FISCAIS" foi classificado como
# "economia": o eixo trata de incentivos fiscais como instrumento de atração
# de investimento e desenvolvimento econômico (mesmo tratamento dado à seção
# equivalente "AMBIENTE DE NEGÓCIOS" do plano de Eduardo Riedel), não de
# gestão do gasto público em si. "6 - TRABALHO DIGNO E GERAÇÃO DE RENDA" e
# "11 - DESENVOLVIMENTO AGRÁRIO COM AGRICULTURA FAMILIAR..." foram
# classificados como "economia": são agendas explícitas de mercado de
# trabalho/renda e de desenvolvimento rural/agropecuário, e não apenas o
# nome de uma pasta de assistência social (mesmo critério do precedente do
# Tocantins, quando o conteúdo é genuinamente sobre emprego/produção, e não
# sobre proteção social). "9 - CULTURA, ESPORTE E LAZER..." segue o
# precedente do projeto (cultura/esporte = assistência social). "13 -
# TURISMO SUSTENTÁVEL E AGREGADOR DE VALOR" foi classificado como
# "economia", consistente com o tratamento dado ao eixo equivalente do
# plano de Eduardo Riedel.
MARCADORES_TRAD = [
    ("SÍNTESE GERAL", "outros"),
    ("DIAGNÓSTICO GERAL", "outros"),
    ("1 - GESTÃO PÚBLICA MODERNA COM TRANSPARÊNCIA E", "gestao_publica"),
    ("2 - DESENVOLVIMENTO ECÔNOMICO SUSTENTÁVEL", "economia"),
    ("3 - NOVA POLÍTICA ESTADUAL DE INCENTIVOS FISCAIS", "economia"),
    ("4 - SAÚDE PÚBLICA EFICIENTE E ACESSÍVEL", "saude"),
    ("5 - SEGURANÇA PÚBLICA CIDADÃ E TECNOLÓGICA", "seguranca"),
    ("6 - TRABALHO DIGNO E GERAÇÃO DE RENDA", "economia"),
    ("7 - EDUCAÇÃO PARA O FUTURO", "educacao"),
    ("8 - INFRAESTRUTURA                    PLANEJADA        E    INDUTORA          DE", "infraestrutura"),
    ("9 - CULTURA, ESPORTE E LAZER VALORIZADOS E COM AMPLO", "assistencia_social"),
    ("10 - ESTADO CUIDADOR E INOVADOR NA ASSISTÊNCIA", "assistencia_social"),
    ("11 - DESENVOLVIMENTO AGRÁRIO COM AGRICULTURA", "economia"),
    ("12 - MEIO AMBIENTE COM PANTANAL, SERRA DA", "meio_ambiente"),
    ("13 - TURISMO SUSTENTÁVEL E AGREGADOR DE VALOR", "economia"),
]

MARCADORES = {
    "eduardo_riedel": MARCADORES_RIEDEL,
    "fabio_trad": MARCADORES_TRAD,
}

# Ponto de partida da análise de Base Empírica (Tarefa 2) para cada
# candidato. O plano de Eduardo Riedel tem uma carta de abertura assinada
# ("COLIGAÇÃO: FAZENDO O FUTURO ACONTECER" + carta) antes da INTRODUÇÃO,
# mas é um texto curto (não um sumário paginado) e não distorce a extração
# de frases, então a análise roda sobre o corpo inteiro (posição 0). O plano
# de Fábio Trad já foi extraído começando em "SÍNTESE GERAL" (cursor_inicial
# já aplicado na extração do .txt, conforme especificado), então também
# roda sobre o corpo inteiro (posição 0).
CURSOR_INICIAL_BASE_EMPIRICA = {
    "eduardo_riedel": 0,
    "fabio_trad": 0,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica aos demais estados)
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

        cursor_be = CURSOR_INICIAL_BASE_EMPIRICA.get(slug, 0)
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
        "gerado_em": "24 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Mato "
            "Grosso do Sul' e 'sul-mato-grossense(s)' NÃO são filtrados e "
            "aparecem naturalmente entre os termos mais frequentes de ambos "
            "os planos). Mostra os termos mais repetidos por candidato e o "
            "agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de dimensão/eixo/"
            "subseção). Cada segmento de texto entre dois marcadores "
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
            "Heurística idêntica à usada nas análises dos 9 estados do "
            "Nordeste e dos estados já processados do Norte, sem nenhum "
            "ajuste específico para Mato Grosso do Sul, para manter "
            "comparabilidade entre estados e entre regiões."
        ),
        "metodologia_nota": (
            "Mato Grosso do Sul é o primeiro estado do Centro-Oeste incluído "
            "no projeto, com a mesma metodologia usada nos 9 estados do "
            "Nordeste e nos estados já processados do Norte. Eduardo Riedel "
            "(PP) é o próprio governador em exercício concorrendo à "
            "reeleição — foi eleito em 2022 pelo PSDB e migrou para o PP "
            "ainda no mandato (fonte: Gazeta do Povo, 'Riedel migra para o "
            "PP e PSDB perde último governador eleito em 2022'). O próprio "
            "plano de governo de Fábio Trad, registrado oficialmente no "
            "TSE, confirma o dado ao se referir a 'o plano de gestão do "
            "atual governador Eduardo Riedel (PP), candidato à reeleição'. "
            "Fábio Trad (PT), ex-vice-prefeito e ex-prefeito de Campo "
            "Grande, foi oficializado pelo PT como candidato de oposição ao "
            "grupo político de Riedel (fontes: Campo Grande News e "
            "Poder360, ver campo 'categoria'). Essa é uma leitura eleitoral, "
            "baseada em cobertura jornalística e no próprio conteúdo dos "
            "documentos oficiais registrados no TSE, e não influenciou "
            "nenhuma etapa da extração ou classificação textual dos planos. "
            "Estruturalmente, os dois planos de MS são organizados de forma "
            "muito similar entre si (ambos usam diagnóstico + propostas por "
            "eixo temático numerado), ao contrário do padrão mais comum de "
            "assimetria estrutural observado em outros estados do projeto "
            "entre incumbente e desafiante — o que facilitou a segmentação "
            "de ambos por títulos de seção quase inteiramente monotemáticos, "
            "sem a necessidade de segmentação item a item por proposta "
            "individual, como ocorreu em outros estados (ex.: Ceará, "
            "Tocantins). "
            "Nenhuma anomalia de extração de texto (ligaduras quebradas do "
            "tipo 'fi'/'fl'/'ti', texto fora de ordem de leitura, ou "
            "duplicação de sumário) foi identificada em nenhum dos dois "
            ".txt de Mato Grosso do Sul durante a leitura integral dos "
            "planos para curadoria dos marcadores — ao contrário do que já "
            "ocorreu em outros estados do projeto. Uma única observação "
            "menor: o .txt de Fábio Trad preserva o ligado tipográfico "
            "'ﬁ' e 'ﬂ' do PDF original em várias palavras (ex.: "
            "'ediﬁcações', 'ﬁnanceiras', 'inﬂuência'), um caractere Unicode "
            "de ligadura válido (não uma falha de extração de fonte "
            "incorporada como já visto em outros estados), que não afeta a "
            "tokenização porque o regex de palavras (WORD_RE) do projeto "
            "não inclui esse caractere como letra — nesses casos, a palavra "
            "é dividida em duas ao redor da ligadura (ex.: 'ediﬁcações' "
            "vira os tokens 'edi' e 'cações'), um efeito colateral pequeno "
            "e já esperado da tokenização padrão do projeto, não corrigido "
            "aqui para preservar a metodologia idêntica entre estados."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
