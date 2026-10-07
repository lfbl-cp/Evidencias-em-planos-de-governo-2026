#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Santa Catarina 2026.

Réplica EXATA da metodologia usada nos demais estados do projeto (Nordeste,
Norte, Centro-Oeste, Sudeste), a partir do motor canônico do Ceará
(build_analysis_ce.py): distribuição temática exaustiva por segmentação de
marcadores de seção reais (lidos e mapeados à mão) e Índice de Base Empírica
(heurística lexical/regex idêntica em todos os estados, reaproveitada sem
alterações para manter comparabilidade). Tokenização, stopwords,
distribuicao_tematica_exaustiva, base_empirica_analise (heurística de 3
pilares via regex: EVIDENCIA_RE, DIAG_KEYWORDS_RE, EFEITO_RE), strip_header,
cálculo de cursor_inicial e geração de wordcloud são código idêntico ao
motor canônico — apenas paths, CANDIDATOS e MARCADORES são específicos de SC.

Caso de Santa Catarina: Jorginho Mello (PL) é o INCUMBENTE pleno (governador
em exercício, eleito em 2022 — 1º mandato, sem mandato anterior
não-consecutivo confirmado por busca na Web — concorrendo à reeleição) e
está isolado na liderança das pesquisas (52,8% na Neokemp/OCP, jul/2026).
João Rodrigues (PSD) é desafiante: ex-prefeito de Chapecó, renunciou ao
cargo em abril/2026 para concorrer ao governo, nunca ocupou o Governo do
Estado, 2º colocado isolado nas pesquisas (20,3% na mesma pesquisa, sem
empate técnico com o 3º colocado). Ver campo "categoria" de cada candidato
para fontes completas.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sul/santa-catarina/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sul/santa-catarina/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "jorginho-mello", "nome": "Jorginho Mello", "partido": "PL",
     "categoria": "incumbente pleno — o próprio governador em exercício concorrendo à "
                  "reeleição; eleito em 2022 (1º mandato como governador; antes disso foi "
                  "deputado federal e senador da República, sem mandato anterior de "
                  "governador não-consecutivo) — isolado na liderança das pesquisas "
                  "(52,8% na Neokemp/OCP, jul/2026) — fontes: TSE, \"Jorginho Mello (PL) é "
                  "eleito governador de Santa Catarina\" "
                  "(tse.jus.br/comunicacao/noticias/2022/Outubro/jorginho-mello-pl-e-eleito-governador-de-santa-catarina); "
                  "Assembleia Legislativa de SC, \"Senador Jorginho Mello é eleito governador "
                  "de Santa Catarina\" (alesc.sc.gov.br/agencia/noticia/senador-jorginho-mello-e-eleito-governador-de-santa-catarina); "
                  "Câmara dos Deputados, biografia do Deputado Federal Jorginho Mello "
                  "(camara.leg.br/deputados/160509/biografia)"},
    {"slug": "joao-rodrigues", "nome": "João Rodrigues", "partido": "PSD",
     "categoria": "desafiante — ex-prefeito de Chapecó, renunciou ao cargo em abril/2026 "
                  "para concorrer ao governo; nunca ocupou o Governo do Estado; 2º colocado "
                  "isolado nas pesquisas (20,3% na mesma pesquisa Neokemp/OCP, jul/2026, sem "
                  "empate técnico com o 3º colocado)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os estados do
# projeto (não adaptadas a Santa Catarina), para preservar comparabilidade.
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

# Jorginho Mello: documento curto (22 páginas), sem sumário/índice duplicado.
# Estrutura real: (1) capa; (2) "RESULTADOS QUE PREPARAM O FUTURO" — carta de
# abertura genérica sobre o ciclo de governo encerrado; (3) "UM ESTADO QUE
# RECUPEROU A CAPACIDADE DE REALIZAR" — narrativa de balanço, seguida por
# UMA LISTA NUMERADA DE 21 REALIZAÇÕES do mandato atual (sem subtítulos,
# apenas números). Cada item da lista tem conteúdo tematicamente
# identificável (ex.: item 1 = Universidade Gratuita = educação; item 5 =
# recorde de cirurgias eletivas = saúde) e foi classificado item a item pelo
# seu próprio conteúdo, replicando o precedente já usado no Ceará (Elmano de
# Freitas) para o capítulo "CONTEXTOS E AVANÇOS", que também tem conteúdo
# temático reconhecível dentro de um capítulo nominalmente de balanço de
# mandato, em vez de classificar o bloco inteiro como "outros". Diferença em
# relação ao Ceará: lá as subseções tinham subtítulo próprio; aqui os itens
# são apenas números, então os marcadores usados são a primeira linha
# verbatim de cada item (mesma técnica usada no Eixo 01/03 de Ciro Gomes, no
# Ceará, para blocos de prosa sem subtítulo interno). O item 14 ("Maior
# investimento já realizado por um Governo do Estado em 200 anos... em
# Segurança Pública, Infraestrutura, Educação, Saúde e todas as demais
# áreas") agrega explicitamente múltiplos temas de forma indivisível e foi
# classificado como "outros", replicando o precedente do projeto para
# trechos que reúnem vários temas ao mesmo tempo sem que seja possível
# separar com segurança. Depois da lista, o documento tem DUAS seções
# chamadas "INTRODUÇÃO" (uma emenda textual da outra, mesmo título repetido)
# — um ensaio genérico sobre planejamento e gestão pública sem conteúdo
# temático específico, classificado como "outros" nas duas ocorrências. Só
# depois começa a segunda parte do plano, com 7 seções numeradas
# ("1. INFRAESTRUTURA..." a "7. CULTURA, TURISMO E ESPORTE"), cada uma com
# "Diretriz Central" + lista de "Compromissos e ações de continuidade".
#
# Dentro da seção 2 (Segurança Pública), o bullet "Proteção e Defesa Civil"
# (barragens, desassoreamento de rios) foi separado como "infraestrutura",
# replicando o precedente do Ceará de que obras de prevenção a enchentes/
# segurança hídrica = infraestrutura, mesmo dentro de uma seção nominalmente
# de segurança pública. Dentro da seção 3 (Saúde e Bem-Estar), "Programa
# Casa Catarina" (habitação) = infraestrutura e "Manutenção do
# cofinanciamento estadual... Assistência Social" = assistencia_social,
# ambos replicando precedentes já estabelecidos no projeto (habitação e
# assistência social nunca contam como saúde só por estarem dentro de uma
# seção de saúde). Dentro da seção 5 (Agro, Pesca, Meio Ambiente e o
# Crescimento do Campo), a diretriz central e a maior parte dos compromissos
# tratam de desenvolvimento econômico rural (= economia, replicando o
# precedente do Ceará de que agronegócio/pesca = economia), exceto o bullet
# de pavimentação de estradas rurais (= infraestrutura) e o bullet do
# programa "Mais Verde" de pagamento por serviços ambientais (=
# meio_ambiente). Dentro da seção 6 (Liberdade Econômica, Gestão Eficiente e
# Municipalismo), o primeiro bullet (Pronampe SC, crédito subsidiado) =
# economia, e os bullets seguintes sobre municipalismo/desburocratização =
# gestao_publica. Dentro da seção 7 (Cultura, Turismo e Esporte), cultura e
# esporte = assistencia_social (precedente do projeto), turismo = economia
# (precedente do Ceará) e "Conexões aéreas" (voos internacionais) =
# infraestrutura.
MARCADORES_JORGINHO = [
    ("RESULTADOS QUE PREPARAM O FUTURO", "outros"),
    ("UM ESTADO QUE RECUPEROU A CAPACIDADE DE REALIZAR", "outros"),
    ("Mais de 71 mil estudantes no curso da universidade que", "educacao"),
    ("Aumento em mais de 300% no número de alunos no", "educacao"),
    ("Maior programa de qualificação tecnológica do Estado,", "educacao"),
    ("Primeiro Estado do País a garantir que 100% das 14.100", "educacao"),
    ("Santa Catarina bateu recorde histórico e tornou-se o", "saude"),
    ("Maior expansão de leitos de UTI de sua história, abrindo", "saude"),
    ("Pioneirismo na criação de habilitações estaduais de alta", "saude"),
    ("Maior iniciativa nacional de castração e proteção", "assistencia_social"),
    ("Avanço aéreo inédito ao abrir rotas internacionais diretas", "infraestrutura"),
    ("Mais de 1.000 quilômetros de estradas rurais produtivas", "infraestrutura"),
    ("Maior investimento rodoviário da história catarinense,", "infraestrutura"),
    ("Estado Mais Seguro do País: menores níveis históricos", "seguranca"),
    ("Investimento histórico na modernização com o", "seguranca"),
    ("Maior investimento já realizado por um Governo do Estado", "outros"),
    ("Maior obra de dragagem portuária em execução no País,", "infraestrutura"),
    ("Maior programa de desassoreamento de rios do Brasil,", "infraestrutura"),
    ("Setor pesqueiro recebeu o maior pacote de investimentos", "economia"),
    ("Incentivo a novas fontes de energia destravou R$ 3,5", "economia"),
    ("Construção de 5.740 moradias, alcançando a adesão", "infraestrutura"),
    ("Primeira redução de custos do Governo do Estado em", "gestao_publica"),
    ("Pronampe SC: maior programa de crédito subsidiado da", "economia"),
    ("Quatro anos de gestão", "gestao_publica"),
    ("INTRODUÇÃO", "outros"),
    ("INTRODUÇÃO", "outros"),
    ("PLANO DE GOVERNO “FÉ NO TRABALHO E PÉ NA TÁBUA” - 2027-2030", "outros"),
    ("1. INFRAESTRUTURA, LOGÍSTICA E MOBILIDADE", "infraestrutura"),
    ("2. SEGURANÇA PÚBLICA, GESTÃO PENAL, PROTEÇÃO E DEFESA CIVIL", "seguranca"),
    ("•Proteção e Defesa Civil:", "infraestrutura"),
    ("3. SAÚDE E BEM-ESTAR", "saude"),
    ("•Programa Casa Catarina +22", "infraestrutura"),
    ("•Manutenção do cofinanciamento estadual", "assistencia_social"),
    ("4. EDUCAÇÃO, QUALIFICAÇÃO PROFISSIONAL E TECNOLOGIA", "educacao"),
    ("5. AGRO, PESCA, MEIO AMBIENTE E O CRESCIMENTO DO CAMPO", "economia"),
    ("•Estrada Boa Rural e infraestrutura no campo:", "infraestrutura"),
    ("•Fortalecimento do Financia Agro SC e Água no Campo:", "economia"),
    ("•Manter e ampliar o programa Mais Verde", "meio_ambiente"),
    ("6. LIBERDADE ECONÔMICA, GESTÃO EFICIENTE E MUNICIPALISMO", "economia"),
    ("•Municipalismo \"Pé na Tábua\":", "gestao_publica"),
    ("7. CULTURA, TURISMO E ESPORTE", "assistencia_social"),
    ("•Fortalecer a movimentação turística orgânica", "economia"),
    ("•Conexões aéreas:", "infraestrutura"),
]

# João Rodrigues: documento com SUMÁRIO/ÍNDICE completo no início (10 seções
# numeradas + "Compromisso Final", com pontos de preenchimento e número de
# página). Os títulos de seção no SUMÁRIO estão em Title Case ("1.
# Fundamentos do Plano de Governo 2027–2030"), enquanto os mesmos títulos no
# CORPO do documento aparecem em CAIXA ALTA ("1. FUNDAMENTOS DO PLANO DE
# GOVERNO 2027–2030") — por isso os marcadores de nível 1 usados aqui (em
# caixa alta) já são inerentemente únicos no documento (aparecem só no
# corpo, não colidem com o sumário), o que resolve automaticamente o
# problema do sumário sem precisar da lógica de "2ª ocorrência" (a busca
# sequencial de cada marcador subsequente, a partir da posição do anterior,
# nunca retrocede ao sumário). Os subtítulos internos (ex.: "5.1", "5.4")
# SÃO idênticos em maiúsculas/minúsculas no sumário e no corpo — mas, como a
# busca por eles só começa depois que o cursor já avançou para dentro do
# corpo (via os marcadores de nível 1, únicos), a 2ª ocorrência de cada um
# (a do corpo) é sempre a encontrada.
#
# Dentro da seção 5 (Educação e Desenvolvimento Humano), as subseções 5.1
# (Educação Básica), 5.2 (Ensino Superior) e 5.3 (Educação Especial) =
# educacao; 5.4 (Esporte e Lazer) e 5.5 (Cultura) = assistencia_social
# (precedente do projeto). O parágrafo de fechamento que amarra educação +
# esporte + cultura de forma indivisível foi classificado como "outros"; o
# parágrafo seguinte, especificamente sobre o resgate da UDESC (ensino
# superior), volta a ser "educacao".
#
# Dentro da seção 6 (Agricultura e Desenvolvimento Econômico), a subseção
# 6.3 ("Pesquisa, Extensão, Defesa e Infraestrutura Rural") mistura
# pesquisa/extensão agropecuária (economia) com um parágrafo explicitamente
# sobre infraestrutura física rural (energia trifásica, estradas, pontes,
# internet, habitações rurais = infraestrutura, replicando o precedente do
# projeto de que habitação/estradas contam como infraestrutura
# independentemente da seção em que aparecem) e um parágrafo sobre
# captação/armazenagem de água para a agricultura (também classificado como
# infraestrutura, por ser obra física de captação hídrica), retornando a
# "economia" no parágrafo seguinte sobre o produtor rural.
#
# Dentro da seção 8 (Desenvolvimento e Reinserção Social), o texto alterna
# explicitamente entre desenvolvimento econômico (empreendedorismo, atração
# de investimentos = economia) e proteção/reinserção social (idosos,
# população em situação de rua, egressos do sistema prisional =
# assistencia_social), inclusive repetindo os mesmos dois eixos na lista
# "Principais eixos" ao final — segmentado parágrafo a parágrafo e item a
# item, replicando a técnica usada no Ceará para o Eixo 02 (que já reunia
# "Trabalho e Ação Social" sob um rótulo só) sempre que os itens individuais
# eram identificáveis. O parágrafo "O desenvolvimento econômico e a
# inclusão social não são agendas opostas..." funde os dois temas de forma
# indivisível e foi classificado como "outros".
MARCADORES_JOAO = [
    ("1. FUNDAMENTOS DO PLANO DE GOVERNO 2027", "gestao_publica"),
    ("2. PLANO ESTRUTURAL DE GOVERNO", "gestao_publica"),
    ("3. SEGURANÇA PÚBLICA", "seguranca"),
    ("4. SAÚDE", "saude"),
    ("5. EDUCAÇÃO E DESENVOLVIMENTO HUMANO", "educacao"),
    ("5.4 Esporte e Lazer", "assistencia_social"),
    ("5.5 Cultura", "assistencia_social"),
    ("A educação, o esporte, o lazer e a cultura formam um conjunto indissociável", "outros"),
    ("O resgate da UDESC como instituição oficial de ensino superior do Estado", "educacao"),
    ("6. AGRICULTURA E DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("e implementadas parcerias para financiar investimentos e infraestrutura pública no meio rural,", "infraestrutura"),
    ("Um robusto programa de captação, armazenagem e uso de água na agricultura", "infraestrutura"),
    ("O produtor rural catarinense é um dos pilares", "economia"),
    ("7. INFRAESTRUTURA, MOBILIDADE, LOGÍSTICA E", "infraestrutura"),
    ("8. DESENVOLVIMENTO E REINSERÇÃO SOCIAL", "assistencia_social"),
    ("O empreendedorismo, a pequena e a microempresa e os polos", "economia"),
    ("A reinserção social de pessoas em situação de rua", "assistencia_social"),
    ("O desenvolvimento econômico e a inclusão social não são agendas opostas", "outros"),
    ("Os idosos e as pessoas em situação de maior vulnerabilidade receberão atenção especial", "assistencia_social"),
    ("Principais eixos:", "outros"),
    ("Fortalecer o empreendedorismo, a pequena e microempresa", "economia"),
    ("Atrair investimentos estratégicos para geração de empregos", "economia"),
    ("Ampliar e fortalecer a rede de assistência e promoção social, com atenção", "assistencia_social"),
    ("Desenvolver programas de reinserção social integrados", "assistencia_social"),
    ("9. GESTÃO INTEGRADA E INOVADORA", "gestao_publica"),
    ("10. DESENVOLVIMENTO REGIONAL E CIDADES", "gestao_publica"),
    ("COMPROMISSO FINAL", "outros"),
]

MARCADORES = {
    "jorginho-mello": MARCADORES_JORGINHO,
    "joao-rodrigues": MARCADORES_JOAO,
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
        raw_text = (PLANOS_DIR / f"{slug.replace('-', '_')}.txt").read_text(encoding="utf-8")
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
            "comparabilidade metodológica entre estados — por isso "
            "'catarinense'/'catarinenses' e 'Santa Catarina' NÃO são "
            "filtrados e podem aparecer nos termos mais frequentes). Mostra "
            "os termos mais repetidos por candidato e o agregado dos dois "
            "planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de capítulo/seção, "
            "subtítulos internos, itens numerados de listas de realizações "
            "ou, na ausência de subtítulo, o início verbatim de cada "
            "parágrafo/item). Cada segmento de texto entre dois marcadores "
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
            "Heurística idêntica à usada nas análises dos demais estados do "
            "projeto, sem nenhum ajuste específico para Santa Catarina, "
            "para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "Os dois planos de Santa Catarina foram extraídos diretamente "
            "dos PDFs oficiais de proposta de governo registrados no TSE, "
            "sem falhas de fonte incorporada, texto fora de ordem de "
            "leitura ou ligaduras tipográficas quebradas ('ﬁ'/'ﬂ') — os "
            "problemas de extração mais comuns em outros estados do "
            "projeto não foram encontrados aqui. Duas ressalvas menores, "
            "ambas de natureza estrutural do documento e não de falha de "
            "extração: "
            "(1) o .txt de Jorginho Mello preserva o rodapé de página "
            "repetido 'COLIGAÇÃO FÉ NO TRABALHO E PÉ NA TÁBUA' (23 "
            "ocorrências ao longo do texto), inflando artificialmente a "
            "contagem de 'coligação', 'trabalho' e 'tábua' nos termos mais "
            "frequentes por um motivo estrutural do documento (rodapé "
            "repetido em quase toda página), não por ênfase textual real "
            "do candidato — o mesmo tipo de ruído já documentado em outros "
            "estados do projeto (ex.: rodapé 'Elmano Governador 2027-2030' "
            "no Ceará); "
            "(2) o .txt de João Rodrigues preserva o rodapé de página "
            "repetido 'Página X de 25' (25 ocorrências), inflando a "
            "contagem de 'página' nos termos frequentes pelo mesmo motivo "
            "estrutural (os números da paginação em si não são contados, "
            "pois o regex de tokenização do projeto não reconhece dígitos "
            "como parte de palavra). "
            "Nenhuma das duas ressalvas foi corrigida, para preservar a "
            "metodologia idêntica entre estados (a lista de stopwords "
            "estruturais do projeto não é ajustada por estado). "
            "Sobre a distribuição temática: o plano de Jorginho Mello "
            "(candidato à reeleição) dedica uma fração grande do texto "
            "(cerca de 48%) a um bloco de abertura não-temático — uma carta "
            "de resultados do mandato atual, seguida por DUAS seções "
            "idênticas chamadas 'INTRODUÇÃO' (um ensaio genérico sobre "
            "planejamento e gestão pública, sem conteúdo temático "
            "específico, repetido) — antes de chegar às 7 seções de "
            "propostas propriamente ditas. Dentro do próprio bloco de "
            "abertura, uma lista numerada de 21 realizações do mandato "
            "(sem subtítulos, apenas números) TEM conteúdo tematicamente "
            "identificável item a item e foi segmentada dessa forma "
            "(replicando o precedente já usado no Ceará para o capítulo "
            "'Contextos e Avanços' de Elmano de Freitas), em vez de ser "
            "classificada inteira como 'outros'. Já o plano de João "
            "Rodrigues (desafiante) é organizado de forma mais convencional "
            "— sumário completo + 10 seções numeradas com subtítulos "
            "internos —, com apenas ~2,6% do corpo classificado como front "
            "matter puro (capa + sumário), o que por si só é um achado "
            "editorial: o desafiante estrutura o plano de forma mais "
            "sistemática/programática, enquanto o incumbente dedica quase "
            "metade do documento a defender o histórico do mandato atual "
            "antes de apresentar novas propostas."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
