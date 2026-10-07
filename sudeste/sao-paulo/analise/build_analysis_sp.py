#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — São Paulo 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia usada no Maranhão e na Paraíba: distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica, reaproveitada
sem alterações para manter comparabilidade entre estados).

Caso especial de São Paulo: é o duelo mais midiático do projeto até agora.
Tarcísio de Freitas (Republicanos) é o governador em exercício de SP (1º
mandato, eleito em 2022), buscando reeleição — classificado como "incumbente
pleno". Fernando Haddad (PT), ex-prefeito da capital paulista e ex-Ministro da
Fazenda (2023-2025), é o principal opositor, classificado como "desafiante".
Essa é uma leitura eleitoral, não textual, e não influenciou nenhuma etapa da
extração ou classificação dos planos.

Os dois planos têm tamanhos MUITO diferentes: o de Tarcísio de Freitas tem
cerca de 21,0 mil palavras (68 páginas, documento estruturado em 10
"Objetivos Estratégicos" com dezenas de subseções numeradas, no formato de
um relatório de gestão com resultados do primeiro mandato entremeados às
propostas), e o de Fernando Haddad tem cerca de 5,3 mil palavras (15 páginas,
carta-programa em prosa corrida, organizada em 7 capítulos). Isso é esperado
— reflete o formato real de cada documento registrado no TSE — e não é um
erro de extração.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sudeste/sao-paulo/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sudeste/sao-paulo/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "tarcisio_de_freitas", "nome": "Tarcísio de Freitas", "partido": "Republicanos",
     "categoria": "incumbente pleno (governador em exercício, 1º mandato, concorrendo à "
                  "reeleição)"},
    {"slug": "fernando_haddad", "nome": "Fernando Haddad", "partido": "PT",
     "categoria": "desafiante (ex-prefeito de São Paulo e ex-Ministro da Fazenda)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Ceará/Maranhão/Paraíba (não
# adaptadas a São Paulo), para preservar comparabilidade entre estados.
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

# Tarcísio de Freitas: documento longo (68 páginas) e muito bem estruturado,
# organizado em 10 "Objetivos Estratégicos" numerados (01. SEGURANÇA a 10.
# GOVERNANÇA), cada um com um parágrafo de propósito ("Nosso propósito: ...")
# seguido de subseções numeradas (ex.: 1.1, 1.2, ..., 8.1, 8.2, ...) com
# títulos de programa específicos. A segmentação usa dois níveis de
# marcador: (a) o parágrafo "Nosso propósito: ..." de cada capítulo (texto
# inicial exclusivo de cada capítulo, usado como divisor de capítulo — mais
# robusto que o título do capítulo em si, que se repete de forma truncada e
# com espaçamento tipográfico irregular no Sumário nas páginas 6-7); e (b)
# cada subseção numerada (X.Y), que é a unidade real de conteúdo.
#
# O pequeno trecho entre o título do capítulo (com fonte expandida/
# "letter-spaced", ex.: "I N T E G R A Ç Ã O D E I N T E L I G Ê N C I A S...")
# e o parágrafo "Nosso propósito" acaba contado dentro do último segmento do
# capítulo anterior (efeito estético, poucas dezenas de palavras no total,
# sem impacto relevante na distribuição percentual); ver nota de
# metodologia.
#
# Decisões de classificação não óbvias:
#  - 1.8 "DESENVOLVIMENTO URBANO E RURAL SEGURO": embora trate de
#    revitalização urbana/habitação, o texto enquadra explicitamente a
#    "ocupação qualificada do território" como "estratégia de prevenção
#    criminal" — mantido em "seguranca" pelo enquadramento textual do
#    próprio candidato, e não em "infraestrutura".
#  - Capítulo 4 (Desenvolvimento Social): seções de proteção social,
#    combate à pobreza, pessoa com deficiência, igualdade racial e
#    segurança alimentar = "assistencia_social"; mas "SP BAIRROS
#    CONECTADOS" (obras de saneamento/urbanização/habitação em periferias),
#    "UNIVERSALIZAÇÃO DO SANEAMENTO" e "CASA PAULISTA" (programa
#    habitacional) = "infraestrutura", replicando o precedente do
#    Ceará/Maranhão/Paraíba de que habitação/saneamento = infraestrutura
#    mesmo dentro de um objetivo nominalmente social.
#  - Capítulo 5 (Mulheres): tema transversal sem eixo próprio na taxonomia
#    de 9 temas do projeto. Segmentado subseção a subseção pelo conteúdo
#    real: 5.1 (plataforma/secretaria, apresentação institucional) =
#    "assistencia_social"; 5.2 a 5.6 (rede de proteção contra violência
#    doméstica, DDMs, tornozelamento, patrulha especializada) = "seguranca";
#    5.7 e 5.8 (crédito e capacitação para empreendedorismo feminino) =
#    "economia"; 5.9 (linha de cuidado em saúde da mulher) = "saude".
#  - Capítulo 6 (Sustentabilidade): tratado integralmente como
#    "meio_ambiente", incluindo 6.6 "Fauna Silvestre e Doméstica" (Centros
#    de Triagem de Animais Silvestres, Política Estadual de Fauna Silvestre
#    — enquadrado como manejo/conservação de fauna, não como assistência
#    social, diferente do precedente usado para seções de bem-estar animal
#    de estimação em outros estados) e 6.7-6.9 (economia de baixo carbono,
#    mineração sustentável, bioeconomia — mantidos em meio_ambiente por
#    estarem no capítulo de sustentabilidade e tratarem majoritariamente de
#    política ambiental/uso de recursos naturais, ainda que com uma faceta
#    econômica).
#  - 8.1 "NOVO CENTRO ADMINISTRATIVO": embora esteja no capítulo "Economia
#    do Conhecimento", o conteúdo é sobre a construção da nova sede do
#    governo e "modernização da gestão pública" — classificado como
#    "gestao_publica", não "economia".
#  - Demais subseções do capítulo 8 (hubs de inovação, supercomputador,
#    universidades/institutos de pesquisa, tecnologia para agronegócio/
#    esporte, minerais estratégicos) = "economia", consistente com o título
#    do capítulo ("Economia do Conhecimento").
#  - 9.6 "CULTURA, ECONOMIA E INDÚSTRIA CRIATIVAS": diferente do precedente
#    de outros estados (cultura = assistencia_social), aqui o texto enfatiza
#    explicitamente economia criativa, internacionalização e geração de
#    negócios, dentro do capítulo "Prosperidade" — classificado como
#    "economia".
MARCADORES_TARCISIO = [
    ("Nosso propósito: melhorar a sensação de segurança", "seguranca"),
    ("1.1   SP CIN - CENTRO DE INTELIGÊNCIA E INOVAÇÃO", "seguranca"),
    ("1.2   PROGRAMA MURALHA PAULISTA", "seguranca"),
    ("1.3   COMBATE ÀS ORGANIZAÇÕES CRIMINOSAS", "seguranca"),
    ("1.4   RECUPERA SP", "seguranca"),
    ("1.5   COMBATE AOS CRIMES CIBERNÉTICOS", "seguranca"),
    ("1.6   ADMINISTRAÇÃO PENITENCIÁRIA", "seguranca"),
    ("1.7   CAPACITAÇÃO E VALORIZAÇÃO POLICIAL", "seguranca"),
    ("1.8   DESENVOLVIMENTO URBANO", "seguranca"),

    ("Nosso propósito: inovar na saúde", "saude"),
    ("2.1   SP INOVA SAÚDE", "saude"),
    ("2.2   SUS PAULISTA", "saude"),
    ("2.3   ASSISTÊNCIA ÀS VÍTIMAS DE VIOLÊNCIA SEXUAL", "saude"),
    ("2.4   VACINAÇÃO", "saude"),
    ("2.5   + SAÚDE MENTAL", "saude"),
    ("2.6   HUBS REGIONALIZADOS", "saude"),
    ("2.7   POPULAÇÃO EM SITUAÇÃO DE RUA", "assistencia_social"),
    ("2.8   SP MOVIMENTA", "saude"),
    ("2.9   HOSPITAIS MUSICAIS", "saude"),

    ("Nosso propósito: preparar o cidadão", "educacao"),
    ("3.1   ALFABETIZA JUNTOS SP", "educacao"),
    ("3.2   BASE FORTE - RECOMPOSIÇÃO DE APRENDIZAGEM", "educacao"),
    ("3.3   PACTO PELA MATEMÁTICA", "educacao"),
    ("3.4   EDUCAÇÃO FINANCEIRA", "educacao"),
    ("3.5   EDUCAÇÃO PARA TECNOLOGIA", "educacao"),
    ("3.6   PROVÃO PAULISTA", "educacao"),
    ("3.7   DO ENSINO TÉCNICO E SUPERIOR", "educacao"),
    ("3.8   PROFISSÕES DO FUTURO", "educacao"),
    ("3.9   PROGRAMA BEEM", "educacao"),
    ("3.10   ENSINO INTEGRAL", "educacao"),
    ("3.11   CULTURA, ESPORTE E EDUCAÇÃO", "educacao"),
    ("3.12   ESCOLA DO FUTURO", "educacao"),
    ("3.13   ESCOLAS CÍVICO-MILITARES", "educacao"),
    ("3.14   PRONTOS PRO MUNDO", "educacao"),
    ("3.15   PORTAS SEMPRE ABERTAS", "educacao"),
    ("3.16   EDUCADORES PROTAGONISTAS", "educacao"),
    ("3.17   EDUCAÇÃO INTEGRADA", "educacao"),
    ("3.18   ESTUDANTES E FAMÍLIAS PRESENTES", "educacao"),

    ("Nosso propósito: superar a pobreza", "assistencia_social"),
    ("4.1   PROGRAMA CUIDAR PARA TODOS", "assistencia_social"),
    ("4.2   SUPERAÇÃO SP", "assistencia_social"),
    ("4.3   PESSOA COM DEFICIÊNCIA - UMA VIDA", "assistencia_social"),
    ("4.4   PREVENÇÃO E COMBATE À VIOLÊNCIA", "assistencia_social"),
    ("4.5   PROMOÇÃO À IGUALDADE RACIAL", "assistencia_social"),
    ("4.6   SP BAIRROS CONECTADOS", "infraestrutura"),
    ("4.7   UNIVERSALIZAÇÃO DO SANEAMENTO", "infraestrutura"),
    ("4.8   CASA PAULISTA", "infraestrutura"),
    ("4.9   SEGURANÇA ALIMENTAR E NUTRICIONAL", "assistencia_social"),

    ("Nosso propósito: promover uma vida livre de violência", "assistencia_social"),
    ("5.1   SP POR TODAS", "assistencia_social"),
    ("5.2   SEGURANÇA POR TODAS", "seguranca"),
    ("5.3   CADASTRO ESTADUAL DE CONDENADOS", "seguranca"),
    ("5.4   DDMS", "seguranca"),
    ("5.5   APP SP MULHER SEGURA", "seguranca"),
    ("5.6   PATRULHA SP MULHER SEGURA", "seguranca"),
    ("5.7   EMPREENDEDORAS SP", "economia"),
    ("5.8   MÃES EMPREENDEDORAS SP", "economia"),
    ("5.9   SAÚDE POR TODAS", "saude"),

    ("Nosso propósito: fortalecer São Paulo diante dos eventos climáticos", "meio_ambiente"),
    ("6.1   CIDADES SP DO FUTURO", "meio_ambiente"),
    ("6.2   PROGRAMA INTEGRATIETÊ", "meio_ambiente"),
    ("6.3   RESTAURAÇÃO ECOLÓGICA E RECUPERAÇÃO", "meio_ambiente"),
    ("6.4   UNIDADES DE CONSERVAÇÃO", "meio_ambiente"),
    ("6.5   PROGRAMA OCEANO SP", "meio_ambiente"),
    ("6.6   FAUNA SILVESTRE E DOMÉSTICA", "meio_ambiente"),
    ("6.7   ECONOMIA DE BAIXO CARBONO", "meio_ambiente"),
    ("6.8   MINERAÇÃO SUSTENTÁVEL", "meio_ambiente"),
    ("6.9   BIOECONOMIA", "meio_ambiente"),

    ("Nosso propósito: ampliar e fortalecer a infraestrutura", "infraestrutura"),
    ("7.1   SP PRA TODA OBRA 4.0", "infraestrutura"),

    ("Nosso propósito: desenvolver mais conhecimento", "economia"),
    ("8.1   NOVO CENTRO ADMINISTRATIVO", "gestao_publica"),
    ("8.2   HUBS DE INOVAÇÃO E TRILHAS TECNOLÓGICAS", "economia"),
    ("8.3   SUPERCOMPUTADOR PAULISTA", "economia"),
    ("8.4   UNIVERSIDADES E INSTITUTOS DE PESQUISA", "economia"),
    ("8.5   PESQUISA, INOVAÇÃO CIENTÍFICA E", "economia"),
    ("8.6   TECNOLOGIAS PARA O ESPORTE", "economia"),
    ("8.7   MINERAIS ESTRATÉGICOS", "economia"),

    ("Nosso propósito: promover a prosperidade", "economia"),
    ("9.1   HUB DA PROSPERIDADE", "economia"),
    ("9.2   FACILITA SP", "economia"),
    ("9.3   MAIS CRÉDITO PARA AS EMPRESAS", "economia"),
    ("9.4   AGRO PAULISTA E INSERÇÃO PRODUTIVA", "economia"),
    ("9.5   INDÚSTRIA 4.0", "economia"),
    ("9.6   CULTURA, ECONOMIA E INDÚSTRIA CRIATIVAS", "economia"),
    ("9.7   TURISMO E ECONOMIA DA EXPERIÊNCIA", "economia"),

    ("Nosso propósito: otimizar gastos e ampliar investimentos", "gestao_publica"),
    ("10.1   SP NA DIREÇÃO CERTA", "gestao_publica"),
    ("10.2   TRILHAS DA PROSPERIDADE -", "gestao_publica"),
    ("10.3   PARCERIA E APOIO ÀS PREFEITURAS", "gestao_publica"),
    ("10.4   COMPROMISSO FISCAL E COMBATE", "gestao_publica"),
]

# Fernando Haddad: documento curto (15 páginas, carta-programa em prosa
# corrida), organizado em 7 capítulos numerados. O capítulo 6 ("São Paulo
# por Inteiro") reúne 11 minitemas distintos (igualdade racial, moradia,
# mobilidade, saneamento, clima, cultura, esporte, turismo, proteção
# social/segurança alimentar, envelhecimento, acessibilidade), cada um
# introduzido por uma frase-título em negrito no PDF original — usadas aqui
# como marcador de subseção. O capítulo 4 ("Prosperidade para Todo Mundo")
# e o capítulo 7 ("Um Governo que Funciona") têm a mesma estrutura de
# frases-título e foram segmentados da mesma forma. Os capítulos 2 (SP
# Protege) e 5 (Saúde na Hora Certa), embora não usem frase-título em
# negrito no mesmo padrão, têm parágrafos temáticos claramente demarcados
# (ex.: "Nas ruas, a proposta é...", "Nas casas, o objetivo é...") e foram
# segmentados pelas primeiras palavras verbatim de cada parágrafo temático,
# replicando a técnica usada no plano de Ciro Gomes (Ceará) para prosa sem
# subtítulos internos.
MARCADORES_HADDAD = [
    ("2. PRIORIDADE Nº 1: SP PROTEGE COM IMPUNIDADE ZERO", "seguranca"),
    ("Nas ruas, a proposta é integrar", "seguranca"),
    ("Cada ocorrência será tratada", "seguranca"),
    ("Nas casas, o objetivo é proteger mulheres", "seguranca"),
    ("No andar de cima, o objetivo é combater", "seguranca"),
    ("Valorização de quem nos protege.", "seguranca"),
    ("Câmeras corporais com gravação contínua.", "seguranca"),
    ("O Meu Celular de Volta", "seguranca"),
    ("Golpe Zero.", "seguranca"),
    ("Segurança no campo.", "seguranca"),
    ("O estado inteiro nos territórios.", "seguranca"),
    ("A cadeia que corta o ciclo do crime.", "seguranca"),

    ("3. EDUCAÇÃO: A PORTA DA PROSPERIDADE", "educacao"),
    ("Ninguém para trás.", "educacao"),
    ("Escola completa, com profissão.", "educacao"),
    ("Universidade pública, patrimônio de São Paulo.", "educacao"),
    ("O professor no centro.", "educacao"),
    ("Educação com liderança.", "educacao"),

    ("4. PROSPERIDADE PARA TODO MUNDO", "economia"),
    ("O trabalho que rende.", "economia"),
    ("O pequeno que cresce.", "economia"),
    ("O campo que enriquece.", "economia"),
    ("A aposta na inteligência artificial.", "economia"),
    ("Atravessando os quatro compromissos", "economia"),

    ("5. SAÚDE NA HORA CERTA", "saude"),
    ("Consulta, exame e cirurgia com menor tempo de espera.", "saude"),
    ("O remédio e o socorro na hora certa.", "saude"),
    ("A sua saúde nas suas mãos.", "saude"),
    ("O cuidado que chega antes da doença.", "saude"),
    ("Uma rede só, com o estado de volta à coordenação.", "saude"),

    ("6. SÃO PAULO POR INTEIRO", "outros"),
    ("Igualdade e respeito.", "assistencia_social"),
    ("Moradia digna.", "infraestrutura"),
    ("Mobilidade que liberta tempo.", "infraestrutura"),
    ("Água e saneamento para todos.", "infraestrutura"),
    ("Preparo para o clima que mudou.", "meio_ambiente"),
    ("Cultura que pertence a todos.", "assistencia_social"),
    ("Esporte como política pública.", "assistencia_social"),
    ("Turismo que gera renda.", "economia"),
    ("Proteção social e segurança alimentar.", "assistencia_social"),
    ("Respeito a quem envelhece.", "assistencia_social"),
    ("Acessibilidade e inclusão.", "assistencia_social"),

    ("7. UM GOVERNO QUE FUNCIONA", "gestao_publica"),
    ("Gestão com liderança e instituições que ficam.", "gestao_publica"),
    ("O estado que funciona na vida das pessoas.", "gestao_publica"),
    ("Contrato vale, e vale para os dois lados.", "gestao_publica"),
    ("O estado no controle das tecnologias.", "gestao_publica"),
    ("Transparência, contas prestadas e escuta.", "gestao_publica"),
    ("Responsabilidade com o dinheiro do paulista.", "gestao_publica"),
]

MARCADORES = {
    "tarcisio_de_freitas": MARCADORES_TARCISIO,
    "fernando_haddad": MARCADORES_HADDAD,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica ao Ceará/Maranhão/
# Paraíba)
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
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'São "
            "Paulo'/'paulista' NÃO são filtrados e podem aparecer nos termos "
            "mais frequentes). Mostra os termos mais repetidos por candidato "
            "e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de capítulo/objetivo/"
            "subseção numerada, ou, na ausência de subtítulos internos, o "
            "início verbatim de cada parágrafo temático). Cada segmento de "
            "texto entre dois marcadores consecutivos foi contado (em "
            "número de palavras) e atribuído a UM dos 9 temas. Quando um "
            "trecho do documento original já reunia explicitamente "
            "múltiplos temas de forma indivisível, o segmento foi "
            "classificado item a item sempre que os itens individuais eram "
            "identificáveis, ou como 'outros' quando não era possível "
            "separar com segurança."
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
            "Heurística idêntica à usada nas análises do Ceará, da Paraíba "
            "e do Maranhão, sem nenhum ajuste específico para São Paulo, "
            "para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "São Paulo é o duelo mais midiático do projeto até este ponto: "
            "Tarcísio de Freitas (Republicanos) é o governador em exercício "
            "(1º mandato, eleito em 2022), buscando reeleição — classificado "
            "como incumbente pleno; Fernando Haddad (PT), ex-prefeito da "
            "capital paulista e ex-Ministro da Fazenda (2023-2025), é o "
            "principal opositor — classificado como desafiante. Essa é uma "
            "leitura eleitoral, não textual: não influenciou nenhuma etapa "
            "da extração ou classificação dos planos. "
            "Os dois planos têm extensão muito diferente por razões "
            "estruturais legítimas, não por falha de extração: o de "
            "Tarcísio de Freitas tem cerca de 21,0 mil palavras (68 "
            "páginas), no formato de um relatório de gestão do primeiro "
            "mandato entremeado a novas propostas, organizado em 10 "
            "'Objetivos Estratégicos' com dezenas de subseções numeradas "
            "(1.1, 1.2, ... 10.4); o de Fernando Haddad tem cerca de 5,3 mil "
            "palavras (15 páginas), uma carta-programa em prosa corrida "
            "organizada em 7 capítulos. Nenhum dos dois arquivos de texto "
            "apresentou defeito de ligadura (fi/fl/ti) ou mojibang de "
            "acentuação na extração; a checagem de qualidade de extração foi "
            "feita antes da análise. "
            "No plano de Tarcísio de Freitas, cada um dos 10 capítulos é "
            "aberto por um parágrafo padronizado iniciado por 'Nosso "
            "propósito:', usado aqui como marcador de transição de "
            "capítulo — mais robusto do que o título do capítulo em si, que "
            "aparece no Sumário (páginas 6-7) com espaçamento tipográfico "
            "diferente do usado no corpo do texto (títulos 'letter-spaced', "
            "com espaço entre cada letra) e por isso não colide com o texto "
            "usado como marcador. O pequeno subtítulo em fonte expandida de "
            "cada capítulo (entre o número do capítulo e o parágrafo "
            "'Nosso propósito') acaba contado dentro do último segmento do "
            "capítulo anterior — efeito estético de poucas dezenas de "
            "palavras no total, sem impacto relevante na distribuição "
            "percentual. Diversas decisões de classificação não óbvias "
            "(ex.: seção 1.8 'Desenvolvimento Urbano e Rural Seguro' = "
            "segurança, pelo enquadramento do próprio candidato; seções de "
            "habitação/saneamento dentro do capítulo de Desenvolvimento "
            "Social = infraestrutura; capítulo 5 'Mulheres', tema "
            "transversal sem eixo próprio na taxonomia do projeto, "
            "segmentado subseção a subseção entre segurança, saúde, "
            "economia e assistência social conforme o conteúdo real de "
            "cada subseção) estão documentadas linha a linha nos "
            "comentários do script de análise. "
            "No plano de Fernando Haddad, os capítulos 4, 6 e 7 usam "
            "frases-título curtas (ex.: 'Moradia digna.', 'Igualdade e "
            "respeito.') como marcador de cada minitema; os capítulos 2 e 5 "
            "não têm esse padrão e foram segmentados pelas primeiras "
            "palavras verbatim de cada parágrafo temático, técnica já usada "
            "no plano de Ciro Gomes (Ceará) para prosa corrida sem "
            "subtítulos internos."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
