#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Pará 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver
/home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py e
/home/claude/brasil_2026/nordeste/replicacao/codigo/python/build_analysis_pb.py),
agora aplicada ao estado do Pará (região Norte): distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica à usada em
todos os outros estados do projeto, reaproveitada sem alterações para manter
comparabilidade entre estados/regiões).

Caso especial do Pará: Hana Ghassan (MDB) é a governadora em exercício —
assumiu o cargo depois que Helder Barbalho (MDB), governador eleito em 2022,
renunciou em 2026 para concorrer ao Senado. Hana era a vice-governadora de
Barbalho e é a candidata lançada pelo MDB à sucessão (mandato próprio) em
2026. É, portanto, uma INCUMBENTE POR SUCESSÃO, não uma governadora eleita
buscando reeleição em nome próprio. Dr. Daniel Santos (Podemos) é o
desafiante, sem vínculo com o governo estadual em exercício.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/para/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/para/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "hana-ghassan", "nome": "Hana Ghassan", "partido": "MDB",
     "categoria": "incumbente por sucessão — vice-governadora que assumiu o "
                  "Governo do Pará em 2026 após a renúncia do então "
                  "governador Helder Barbalho (MDB), que deixou o cargo para "
                  "concorrer ao Senado; Hana foi lançada pelo MDB como "
                  "candidata à sucessão, buscando mandato próprio (fontes: "
                  "Metropoles e O Liberal, agosto de 2026, que já a tratam "
                  "como 'a governadora' e Barbalho como 'ex-governador')"},
    {"slug": "dr-daniel-santos", "nome": "Dr. Daniel Santos", "partido": "Podemos",
     "categoria": "desafiante — médico e candidato pelo Podemos, sem vínculo "
                  "com o governo estadual em exercício (fonte: Diário do "
                  "Pará, agosto de 2026)"},
]

# cursor_inicial_base_empirica: ponto de caractere (no CORPO, após o
# cabeçalho padronizado) onde o corpo real de cada plano começa, pulando
# Sumário/Índice/TOC. Calculado à mão para cada candidato e aplicado SOMENTE
# à chamada de base_empirica_analise (não à distribuição temática, nem ao
# total_palavras/top_palavras), seguindo o padrão de build_analysis_al.py:
# `be = base_empirica_analise(corpo[cursor_inicial:], slug)`.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "hana-ghassan": 1078,       # início de "BORA AVANÇAR!", logo após o Sumário
    "dr-daniel-santos": 6762,   # 2ª ocorrência de "MENSAGEM INSTITUCIONAL"
}

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os estados do
# projeto (Nordeste e agora Norte), não adaptadas ao Pará, para preservar
# comparabilidade entre estados/regiões.
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

# Hana Ghassan (MDB): plano estruturado em 3 PILARES numerados, cada um com
# subseções numeradas no Sumário ("1. Saúde", "2. Segurança" ... "13.
# Governança e Gestão Inovadora"). Conforme instrução do projeto, essas
# subseções numeradas foram usadas como marcadores individuais, e não os
# pilares inteiros. No corpo do texto as subseções não têm um subtítulo
# repetido (ex.: não há um "1. SAÚDE" solto no meio da página) — cada
# subseção começa diretamente com o primeiro parágrafo de abertura da área
# (ex.: "A saúde será a principal prioridade do nosso governo."), que foi
# usado como marcador verbatim. Cada subseção inclui, em sequência, o texto
# de abertura, "PRINCIPAIS REALIZAÇÕES" (balanço do governo Barbalho/Hana) e
# "COMO VAMOS AVANÇAR" (propostas) — todos classificados pelo tema da
# subseção correspondente.
#
# Decisões de classificação não óbvias (mesmo precedente já usado nos
# estados do Nordeste):
#  - "Desenvolvimento Urbano e Qualidade de Vida" (subseção 6, Pilar 1):
#    habitação, saneamento, mobilidade, regularização fundiária urbana =
#    infraestrutura (precedente CE/MA/PB).
#  - "Turismo" (subseção 9, Pilar 2): tratado como economia (vocação
#    econômica/geração de renda), seguindo o precedente de Ciro Gomes (CE),
#    onde o turismo foi classificado dentro do eixo econômico.
#  - "Cultura e Economia Criativa" (subseção 10, Pilar 2): assistencia_social,
#    seguindo o precedente do projeto (cultura = assistencia_social em todos
#    os estados já analisados).
#  - "Ciência, Tecnologia e Inovação" (subseção 11, Pilar 3): educacao — a
#    taxonomia de 9 temas do projeto não tem eixo dedicado a C&T, e o
#    candidato a associa a formação/talentos/universidades, mais próximo de
#    educação do que de economia (mesmo precedente usado em Elmano/Ciro, CE).
#  - "Políticas para as Mulheres" (subseção 4, Pilar 1): seção transversal
#    (combate à violência, autonomia econômica, saúde da mulher, participação
#    política), sem um tema único da taxonomia de 9 que a esgote. Como o
#    conteúdo é dominado por proteção social/rede de acolhimento a um grupo
#    vulnerável (e a própria candidata cria estrutura de governo dedicada —
#    Secretaria de Estado das Mulheres), foi classificada como
#    assistencia_social, e não fatiada, replicando o tratamento dado a
#    seções de proteção social transversal em outros estados (ex.:
#    "AMPLIAÇÃO DA PROTEÇÃO SOCIAL", CE/Elmano).
#  - "Desenvolvimento Social" (subseção 5, Pilar 1): assistencia_social
#    (primeira infância, juventude, Usinas da Paz, povos indígenas,
#    vulnerabilidade social).
#  - As aberturas dos 3 PILARES (título + parágrafos de apresentação +
#    "ÁREAS QUE COMPÕEM ESTE PILAR") são texto de transição genérico, sem
#    conteúdo temático próprio — tratadas como "outros", mesmo padrão usado
#    para "APRESENTAÇÃO"/"CONTEXTOS E AVANÇOS" no plano de Elmano (CE).
MARCADORES_HANA = [
    ("BORA AVANÇAR!", "outros"),
    ("ESTRUTURA DO PLANO DE GOVERNO", "outros"),
    ("PILAR 1\nCUIDAR DAS PESSOAS", "outros"),
    ("A saúde será a principal prioridade do nosso governo.", "saude"),
    ("A segurança pública continuará sendo uma das principais prioridades",
     "seguranca"),
    ("A educação será uma das grandes prioridades do nosso governo",
     "educacao"),
    ("As mulheres estarão no centro das prioridades do nosso governo.",
     "assistencia_social"),
    ("O desenvolvimento social é o caminho para reduzir desigualdades",
     "assistencia_social"),
    ("Construir cidades mais humanas, inclusivas e sustentáveis é essencial",
     "infraestrutura"),
    ("PILAR 2\nDESENVOLVER O PARÁ", "outros"),
    ("O desenvolvimento econômico é o caminho para gerar oportunidades",
     "economia"),
    ("A infraestrutura é a base do desenvolvimento econômico e da integração regional.",
     "infraestrutura"),
    ("O turismo é uma das grandes oportunidades para impulsionar o desenvolvimento do",
     "economia"),
    ("A cultura é um dos maiores patrimônios do Pará", "assistencia_social"),
    ("PILAR 3\nPREPARAR O FUTURO", "outros"),
    ("A ciência, a tecnologia e a inovação serão pilares estratégicos",
     "educacao"),
    ("O futuro do Pará está diretamente ligado à sua capacidade de conciliar",
     "meio_ambiente"),
    ("Uma gestão pública moderna, eﬁciente e inovadora é a base",
     "gestao_publica"),
    ("UM COM PROMISSO\nCOM O FUTURO DO PARÁ", "outros"),
]

# Dr. Daniel Santos (Podemos): plano extenso (79 páginas) em 3 PARTES.
# PARTE I (Capítulos I-IV) é inteiramente visão/diagnóstico geral e
# princípios de governo, antes de qualquer proposta temática concreta —
# grande volume de "outros" front matter, maior que em qualquer outro plano
# já analisado no projeto (peculiaridade documentada na nota de
# metodologia). PARTE II ("AS GRANDES TRANSFORMAÇÕES DO PARÁ") é organizada
# em 8 EIXOS numerados com títulos temáticos claros — usados como marcador,
# igual ao padrão de Ciro Gomes (CE) e outros planos em "eixos". PARTE III
# ("GOVERNAR PARA TRANSFORMAR O PARÁ") tem 5 CAPÍTULOS: o Capítulo II
# ("AS GRANDES MISSÕES DO GOVERNO") resume os mesmos 8 eixos em 7 "Missões"
# numeradas — conforme instrução do projeto, essas subseções numeradas
# também foram usadas como marcadores individuais (mesmo tema do eixo
# correspondente), e não tratadas como "outros" só por serem redundantes com
# os eixos. O ANEXO I ("COMPROMISSOS DOS PRIMEIROS 100 DIAS DE GOVERNO") tem
# 10 itens numerados, um por área de governo — também usados como marcadores
# individuais.
#
# Decisões de classificação não óbvias:
#  - CAPÍTULO III da Parte I ("OS PRINCÍPIOS QUE ORIENTARÃO O GOVERNO") e
#    CAPÍTULO IV da Parte I ("UMA NOVA GOVERNANÇA PARA UM NOVO CICLO DE
#    DESENVOLVIMENTO"): tratam de 10 princípios de governo (planejamento,
#    responsabilidade fiscal, eficiência, valorização de servidores,
#    parceria com municípios, diálogo institucional, inovação,
#    desenvolvimento sustentável etc.) e do desenho da governança estadual
#    (sistema de governança estratégica, regionalização da gestão,
#    transformação digital, transparência). Ambos são, no conjunto,
#    inseparáveis de qualquer um dos 9 temas isoladamente — foram
#    classificados como gestao_publica, mesmo precedente usado para
#    "GESTÃO ESTRATÉGICA, GOVERNANÇA INTERFEDERATIVA" no plano de Elmano
#    (CE).
#  - EIXO I ("UM ESTADO MODERNO, EFICIENTE E PRESENTE"): modernização
#    administrativa, governo digital, transparência, valorização do
#    servidor = gestao_publica.
#  - EIXO VII ("DESENVOLVIMENTO HUMANO, CIDADANIA, CULTURA E QUALIDADE DE
#    VIDA"): seção transversal em prosa corrida (sem subtítulos internos)
#    cobrindo proteção social, juventude, mulheres, idosos, pessoas com
#    deficiência, cultura, esporte, habitação e povos tradicionais. Não há
#    como fatiar com segurança em sentenças isoladas sem prejudicar a
#    legibilidade dos parágrafos (mesma situação do EIXO 02 de Ciro Gomes,
#    CE, "Trabalho e Ação Social, Proteção Social, Cultura, Esporte e
#    Juventude") — todo o eixo foi classificado como assistencia_social,
#    replicando esse precedente, mesmo que um parágrafo trate de habitação
#    (que isoladamente seguiria o precedente infraestrutura).
#  - EIXO VIII ("A AMAZÔNIA COMO VANTAGEM ESTRATÉGICA PARA O DESENVOLVIMENTO
#    DO PARÁ"): bioeconomia, zoneamento ecológico-econômico, unidades de
#    conservação, mercado de carbono = meio_ambiente (mesmo quando o texto
#    também fala de "oportunidades econômicas" da bioeconomia — o eixo em
#    si é apresentado e organizado como agenda ambiental/climática).
#  - Missão 3 ("Integrar o território para desenvolver a economia"): apesar
#    do título mencionar "economia", o conteúdo é inteiramente sobre obras
#    de infraestrutura (rodovias, hidrovias, portos, conectividade digital,
#    saneamento, energia) — classificada como infraestrutura, consistente
#    com o Eixo VI (mesmo assunto, versão condensada).
#  - Missão 6 ("Liderar a nova economia da Amazônia"): bioeconomia/inovação
#    ambiental — classificada como meio_ambiente, consistente com o Eixo
#    VIII (mesmo assunto, versão condensada).
#  - Missão 7 ("Reduzir as desigualdades entre as regiões do Estado") e o
#    parágrafo de fechamento do Capítulo II: discurso de integração
#    territorial genérico, sem tema específico da taxonomia de 9 — "outros".
#  - Itens 1, 2 e 9 do Anexo I (reorganização administrativa, "Programa
#    Estado Presente", transparência/governo digital) = gestao_publica,
#    mesmo critério do Eixo I. Item 10 ("Diálogo Permanente com a
#    Sociedade") também tratado como gestao_publica (é sobre o método de
#    governar, não sobre uma política setorial).
MARCADORES_DANIEL = [
    ("MENSAGEM INSTITUCIONAL", "outros"),
    ("CARTA DO CANDIDATO", "outros"),
    ("CAPÍTULO I\n\nO PARÁ QUE SOMOS", "outros"),
    ("CAPÍTULO II\n\nO PARÁ QUE QUEREMOS CONSTRUIR", "outros"),
    ("CAPÍTULO III\n\nOS PRINCÍPIOS QUE ORIENTARÃO O GOVERNO", "gestao_publica"),
    ("CAPÍTULO IV\n\nUMA NOVA GOVERNANÇA", "gestao_publica"),
    ("PARTE II\n\nAS GRANDES TRANSFORMAÇÕES DO PARÁ", "outros"),
    ("EIXO I\n\nUM ESTADO MODERNO", "gestao_publica"),
    ("EIXO II\n\nDESENVOLVIMENTO ECONÔMICO, INDUSTRIALIZAÇÃO", "economia"),
    ("EIXO III\n\nEDUCAÇÃO: O CAMINHO", "educacao"),
    ("EIXO IV\n\nSAÚDE: CUIDAR DAS PESSOAS", "saude"),
    ("EIXO V\n\nSEGURANÇA PÚBLICA, JUSTIÇA E DEFESA DA VIDA", "seguranca"),
    ("EIXO VI\n\nINFRAESTRUTURA, LOGÍSTICA E INTEGRAÇÃO", "infraestrutura"),
    ("EIXO VII\n\nDESENVOLVIMENTO HUMANO, CIDADANIA, CULTURA", "assistencia_social"),
    ("EIXO VIII\n\nA AMAZÔNIA COMO VANTAGEM ESTRATÉGICA", "meio_ambiente"),
    ("PARTE III\n\nGOVERNAR PARA TRANSFORMAR O PARÁ", "outros"),
    ("CAPÍTULO I\n\nGOVERNAR COM AS PESSOAS", "gestao_publica"),
    ("CAPÍTULO II\n\nAS GRANDES MISSÕES DO GOVERNO", "outros"),
    ("Missão 1 – Fazer da educação", "educacao"),
    ("Missão 2 – Construir a maior rede regionalizada de saúde", "saude"),
    ("Missão 3 – Integrar o território para desenvolver a economia", "infraestrutura"),
    ("Missão 4 – Industrializar o Pará e gerar empregos", "economia"),
    ("Missão 5 – Restabelecer a autoridade do Estado", "seguranca"),
    ("Missão 6 – Liderar a nova economia da Amazônia", "meio_ambiente"),
    ("Missão 7 – Reduzir as desigualdades entre as regiões", "outros"),
    ("CAPÍTULO III\n\nUM GOVERNO MODERNO, INTELIGENTE", "gestao_publica"),
    ("CAPÍTULO IV\n\nPARÁ 2030", "outros"),
    ("CAPÍTULO V\n\nCOMPROMISSO COM O PARÁ", "outros"),
    ("ANEXO I\n\nCOMPROMISSOS DOS PRIMEIROS 100 DIAS", "outros"),
    ("1. Reorganização da Administração Pública", "gestao_publica"),
    ("2. Programa Estado Presente", "gestao_publica"),
    ("3. Plano Emergencial para Redução das Filas", "saude"),
    ("4. Educação com início imediato", "educacao"),
    ("5. Segurança Pública", "seguranca"),
    ("6. Desenvolvimento Econômico", "economia"),
    ("7. Infraestrutura", "infraestrutura"),
    ("8. Amazônia e Desenvolvimento Sustentável", "meio_ambiente"),
    ("9. Transparência e Governo Digital", "gestao_publica"),
    ("10. Diálogo Permanente com a Sociedade", "gestao_publica"),
]

MARCADORES = {
    "hana-ghassan": MARCADORES_HANA,
    "dr-daniel-santos": MARCADORES_DANIEL,
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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica a todos os estados)
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
        arquivo = slug.replace("-", "_")
        raw_text = (PLANOS_DIR / f"{arquivo}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Se o 1º marcador aparecer mais de uma vez (documento com sumário/
        # índice que repete os títulos das seções antes do corpo real),
        # pula para a 2ª ocorrência, para não segmentar dentro do índice.
        # Mesma lógica usada em todos os estados do projeto.
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        n_ocorrencias_1o_marcador = corpo.count(primeiro_marcador)
        cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
        print(f"{slug}: 1º marcador aparece {n_ocorrencias_1o_marcador}x no corpo "
              f"(cursor_inicial_distribuicao={cursor_inicial})")

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        # Índice de Base Empírica: usa um cursor PRÓPRIO (calculado à mão,
        # ver CURSOR_INICIAL_BASE_EMPIRICA), independente do cursor usado
        # acima para a distribuição temática. Aplicado SOMENTE aqui — não
        # afeta total_palavras nem distribuicao_tematica_pct. Padrão de
        # build_analysis_al.py.
        cursor_be = CURSOR_INICIAL_BASE_EMPIRICA[slug]
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
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto, inclusive nos 9 "
            "estados do Nordeste analisados anteriormente — inclui termos "
            "específicos de outro estado (ex.: 'maranhão'/'maranhense'), "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados/regiões — por isso "
            "'Pará' e 'paraense' NÃO são filtrados e podem aparecer nos "
            "termos mais frequentes. Mostra os termos mais repetidos por "
            "candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de pilar/eixo/capítulo/ "
            "subseção numerada, verbatim). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando um trecho do documento "
            "original já reunia explicitamente múltiplos temas de forma "
            "indivisível (prosa corrida sem subtítulos internos separando os "
            "temas), o segmento foi classificado item a item sempre que os "
            "itens individuais eram identificáveis, ou como 'outros'/pelo "
            "tema dominante quando não era possível separar com segurança."
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
            "Nordeste, sem nenhum ajuste específico para o Pará, para manter "
            "comparabilidade entre estados e entre regiões."
        ),
        "metodologia_nota": (
            "O Pará é o primeiro estado da região Norte analisado pelo "
            "projeto, replicando a mesma metodologia usada nos 9 estados do "
            "Nordeste (Ceará, Alagoas, Paraíba, Maranhão etc.). Caso "
            "especial do Pará: Hana Ghassan (MDB) é a governadora em "
            "exercício — vice-governadora que assumiu o Governo do Pará "
            "depois que Helder Barbalho (MDB), governador eleito em 2018 e "
            "reeleito em 2022, renunciou em 2026 para concorrer ao Senado. "
            "Hana foi lançada pelo MDB como candidata à sucessão, buscando "
            "mandato próprio em 2026 — uma incumbente por sucessão, não uma "
            "reeleição em nome próprio (fontes: Metropoles e O Liberal, "
            "agosto de 2026). Isso é uma leitura eleitoral, não textual: não "
            "influenciou nenhuma etapa da extração ou classificação dos "
            "planos, mas explica por que o plano de Hana Ghassan é "
            "estruturado em grande parte como um balanço de governo (seções "
            "'PRINCIPAIS REALIZAÇÕES' repetidas em cada subseção temática, "
            "citando obras e programas do governo Barbalho/Hana) intercalado "
            "com propostas ('COMO VAMOS AVANÇAR'), diferente do formato mais "
            "propositivo/prospectivo do plano de Dr. Daniel Santos "
            "(Podemos), o desafiante. "
            "No plano de Hana Ghassan, o SUMÁRIO no início do documento "
            "repete os mesmos títulos numerados ('1. Saúde, 9', '2. "
            "Segurança, 14' etc.) usados como referência para os marcadores "
            "de seção — mas como o corpo de cada subseção não repete esse "
            "título numerado (a subseção começa diretamente pelo parágrafo "
            "de abertura), o marcador de cada subseção é o texto verbatim "
            "desse primeiro parágrafo, não o título numerado do Sumário; o "
            "único marcador do Sumário reaproveitado ('BORA AVANÇAR!', "
            "carta de abertura) aparece uma única vez no documento, então "
            "não houve necessidade de pular para uma 2ª ocorrência. "
            "O plano de Dr. Daniel Santos é o mais extenso já processado no "
            "projeto (79 páginas): a estrutura reserva as primeiras ~23 "
            "páginas (Mensagem Institucional, Carta do Candidato, e os 4 "
            "capítulos da Parte I — diagnóstico geral, visão de futuro, "
            "princípios de governo e desenho de governança) inteiramente a "
            "conteúdo introdutório/transversal, classificado majoritariamente "
            "como 'outros' ou 'gestao_publica', antes de chegar aos 8 EIXOS "
            "temáticos da Parte II — isso é uma característica genuína do "
            "documento (proporção de front matter maior que nos planos dos "
            "estados do Nordeste), não um artefato de extração. O SUMÁRIO "
            "repete os títulos de 'MENSAGEM INSTITUCIONAL' e 'CARTA DO "
            "CANDIDATO' (cada um aparece 2x no corpo: 1x no Sumário, 1x no "
            "corpo real) — corrigido com a mesma lógica usada em todos os "
            "estados do projeto: o primeiro marcador usa sua 2ª ocorrência "
            "como ponto de partida da segmentação, pulando o Sumário. A "
            "Parte III do plano ('GOVERNAR PARA TRANSFORMAR O PARÁ') resume, "
            "no Capítulo II ('AS GRANDES MISSÕES DO GOVERNO'), os mesmos 8 "
            "eixos da Parte II em 7 'Missões' numeradas mais curtas — essas "
            "missões foram tratadas como marcadores/segmentos temáticos "
            "próprios (mesmo tema do eixo correspondente), e o Anexo I "
            "('COMPROMISSOS DOS PRIMEIROS 100 DIAS DE GOVERNO') tem 10 itens "
            "numerados, um por área de governo, também tratados como "
            "marcadores individuais — seguindo a instrução do projeto de "
            "usar subseções numeradas como marcadores sempre que existirem, "
            "em vez de tratar essas recapitulações como 'outros'. "
            "Cursor da Base Empírica: para os dois candidatos, o Índice de "
            "Base Empírica é calculado sobre o corpo do documento a partir "
            "de um ponto de corte específico (cursor_inicial_base_empirica: "
            "1078 para Hana Ghassan, posição de 'BORA AVANÇAR!'; 6762 para "
            "Dr. Daniel Santos, 2ª ocorrência de 'MENSAGEM INSTITUCIONAL'), "
            "que pula o Sumário/Índice de cada documento — mas esse corte é "
            "aplicado SOMENTE ao cálculo do índice de base empírica, nunca à "
            "contagem de palavras nem à distribuição temática, que cobrem "
            "100% do corpo de cada plano (o Sumário entra integralmente na "
            "categoria 'outros' da distribuição temática, como texto de "
            "front matter). Mesmo padrão usado em build_analysis_al.py "
            "(Alagoas, Nordeste). "
            "Decisões de classificação não óbvias específicas do Pará "
            "(turismo = economia; ciência/tecnologia/inovação = educação; "
            "cultura, esporte, proteção social transversal e políticas para "
            "mulheres = assistencia_social; bioeconomia/Amazônia/zoneamento "
            "ecológico-econômico = meio_ambiente mesmo quando o texto também "
            "menciona geração de renda) estão documentadas linha a linha nos "
            "comentários do script de análise, e seguem, sempre que possível, "
            "o precedente já estabelecido nos 9 estados do Nordeste."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
