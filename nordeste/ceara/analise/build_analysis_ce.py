#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Ceará 2026.

Réplica da metodologia usada no Maranhão (build_analysis_ma.py), que por sua
vez replicou a metodologia da Paraíba (build_analysis_v3.py): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica
à do Maranhão e da Paraíba, reaproveitada sem alterações para manter
comparabilidade entre estados).

Caso especial do Ceará: Elmano de Freitas é o INCUMBENTE pleno (governador em
exercício, 1º mandato, concorrendo à reeleição) e, segundo institutos de peso
nacional, está ATRÁS do desafiante Ciro Gomes nas pesquisas — um incumbente
em desvantagem. Isso não muda a metodologia de análise textual (idêntica aos
demais estados), mas é relevante para o enquadramento editorial do achado.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/ceara/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/ceara/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "elmano-de-freitas", "nome": "Elmano de Freitas", "partido": "PT",
     "categoria": "incumbente pleno (governador em exercício, 1º mandato, concorrendo à "
                  "reeleição) — segundo institutos de peso nacional, aparece atrás do "
                  "desafiante nas pesquisas"},
    {"slug": "ciro-gomes", "nome": "Ciro Gomes", "partido": "PSDB",
     "categoria": "desafiante — líder nas pesquisas"},
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

# Elmano de Freitas: documento muito bem estruturado, com ÍNDICE completo no
# início repetindo (com pontos de preenchimento/página) os títulos de seção
# usados como marcador — MESMO BUG já encontrado no Maranhão (Felipe
# Camarão). Protegido pela mesma lógica de `cursor_inicial` (2ª ocorrência
# do primeiro marcador, "APRESENTAÇÃO", usada como ponto de partida).
#
# Estrutura real do documento:
#   - Capa + ÍNDICE (front matter, tratado como "outros" automaticamente)
#   - APRESENTAÇÃO (texto de abertura genérico)
#   - CONTEXTOS E AVANÇOS: capítulo de balanço do 1º mandato, com
#     subseções temáticas próprias (AMPLIAÇÃO DA PROTEÇÃO SOCIAL,
#     FORTALECIMENTO DAS INSTITUIÇÕES..., SEGURANÇA PÚBLICA, SAÚDE
#     PÚBLICA, EDUCAÇÃO..., CULTURA..., INVESTIMENTO EM INFRAESTRUTURAS).
#     Decisão editorial: como estas subseções têm títulos temáticos claros
#     e conteúdo coerente com o tema anunciado (não são apenas uma
#     introdução genérica), foram classificadas pelo próprio tema anunciado,
#     em vez de tudo cair em "outros". Isso é uma diferença em relação ao
#     tratamento dado a introduções genéricas de outros planos do projeto.
#   - Depois, "OBJETIVOS E PROPOSIÇÕES": 7 "Grandes Objetivos de
#     Desenvolvimento" numerados, cada um com uma ou mais subseções de
#     propostas.
#
# Dentro do Objetivo 5 (Resiliência Ambiental e Desenvolvimento Urbano e
# Rural), seguimos o precedente já usado no Maranhão/Paraíba: habitação,
# saneamento, mobilidade e regularização fundiária = "infraestrutura"
# (mesmo estando dentro de um objetivo nominalmente ambiental); as
# subseções estritamente ambientais (preservação, clima, ecossistemas
# costeiros) permanecem "meio_ambiente". "PROTEÇÃO E BEM-ESTAR ANIMAL" é
# tratado como "assistencia_social", replicando a classificação usada para
# a seção homônima de Orleans Brandão (PB/MA).
#
# Dentro do Objetivo 6 (Saúde), "SEGURANÇA ALIMENTAR E NUTRICIONAL", "BEM-
# ESTAR" (programa intersetorial de esporte/atividade física) e "ESPORTE"
# foram classificados como "assistencia_social", replicando o precedente de
# Orleans Brandão (esporte, combate à fome = assistência social), e não
# como "saude", ainda que estejam dentro do objetivo nominalmente de saúde.
# "SEGURANÇA VIÁRIA" foi tratado como "infraestrutura" (mobilidade/trânsito),
# consistente com o tratamento dado à seção de mobilidade do Objetivo 5.
#
# Dentro do Objetivo 7 (Educação), "CIÊNCIA, TECNOLOGIA E INOVAÇÃO" foi
# classificado como "educacao": a própria taxonomia de 9 temas usada neste
# projeto não tem um eixo dedicado a ciência/tecnologia, e o candidato
# agrupa esse conteúdo explicitamente dentro do objetivo "Educação
# Transformadora, Valorização da Cultura e Inovação" (universidades,
# formação de pesquisadores, ensino superior) — mais próximo de educação do
# que de "economia". "CULTURA E PATRIMÔNIO" segue o precedente do projeto
# (cultura = assistencia_social).
MARCADORES_ELMANO = [
    ("APRESENTAÇÃO", "outros"),
    ("CONTEXTOS E AVANÇOS", "outros"),
    ("AMPLIAÇÃO DA PROTEÇÃO SOCIAL", "assistencia_social"),
    ("FORTALECIMENTO DAS INSTITUIÇÕES PÚBLICAS E", "gestao_publica"),
    ("SEGURANÇA PÚBLICA", "seguranca"),
    ("SAÚDE PÚBLICA", "saude"),
    ("EDUCAÇÃO É A BASE PARA A SOCIEDADE DO CONHECIMENTO", "educacao"),
    ("CULTURA COMO VETOR ECONÔMICO E IDENTITÁRIO", "assistencia_social"),
    ("INVESTIMENTO EM INFRAESTRUTURAS", "infraestrutura"),
    # transição "Dos avanços à ação" / recapitulação dos 7 objetivos /
    # cabeçalho "OBJETIVOS E PROPOSIÇÕES" — trecho de ligação, sem conteúdo
    # temático próprio.
    ("Os avanços alcançados nos últimos anos constituem uma base sólida", "outros"),
    ("GESTÃO ESTRATÉGICA, GOVERNANÇA INTERFEDERA-", "gestao_publica"),
    ("ACOLHIMENTO, PROTEÇÃO SOCIAL E CUIDADOS", "assistencia_social"),
    ("SEGURANÇA PÚBLICA E PREVENÇÃO ÀS VIOLÊNCIAS", "seguranca"),
    ("DESENVOLVIMENTO ECONÔMICO E INCLUSÃO", "economia"),
    ("RESILIÊNCIA AMBIENTAL E", "meio_ambiente"),
    ("PROTEÇÃO E BEM-ESTAR ANIMAL", "assistencia_social"),
    ("SEGURANÇA HÍDRICA E SANEAMENTO AMBIENTAL", "infraestrutura"),
    ("GOVERNANÇA FUNDIÁRIA E TITULAÇÃO DE TERRAS", "infraestrutura"),
    ("HABITAÇÃO", "infraestrutura"),
    ("CIDADES SUSTENTÁVEIS", "infraestrutura"),
    ("MOBILIDADE, ACESSIBILIDADE, TRANSPORTE PÚBLICO E", "infraestrutura"),
    ("PROMOÇÃO DA SAÚDE, BEM-ESTAR E ENVELHECI-", "saude"),
    ("SEGURANÇA ALIMENTAR E NUTRICIONAL", "assistencia_social"),
    ("SEGURANÇA VIÁRIA", "infraestrutura"),
    ("BEM-ESTAR", "assistencia_social"),
    ("ESPORTE", "assistencia_social"),
    ("EDUCAÇÃO TRANSFORMADORA, VALORIZAÇÃO DA", "educacao"),
    ("CULTURA E PATRIMÔNIO", "assistencia_social"),
]

# Ciro Gomes: documento em prosa corrida, organizado em 6 "Eixos
# Estratégicos" numerados (EIXO 01 a EIXO 06), cada um cobrindo várias
# pastas/secretarias ao mesmo tempo (ex.: EIXO 01 = "Saúde – Educação –
# Ciência, Tecnologia e Educação Superior"), sem subtítulos internos que
# demarquem onde um tema termina e outro começa — a mudança de tema
# acontece apenas na prosa, parágrafo a parágrafo.
#
# Dois eixos (03 e 05) são inteiramente ou majoritariamente monotemáticos e
# foram tratados em bloco único: EIXO 04 (Infraestrutura e Desenvolvimento
# Urbano) = infraestrutura; EIXO 05 (Segurança Pública e Administração
# Penitenciária) = seguranca; EIXO 06 (Governança, Gestão e Eficiência
# Fiscal) = gestao_publica; EIXO 02 (Trabalho e Ação Social, Proteção
# Social, Cultura, Esporte e Juventude) = assistencia_social (o rótulo
# "Trabalho e Ação Social" aqui nomeia a pasta/secretaria responsável pela
# assistência social, não uma agenda de emprego/renda — não há, no corpo do
# texto, parágrafo autônomo sobre política de trabalho/emprego que
# justificasse separar para "economia"; cultura segue o precedente do
# projeto = assistencia_social).
#
# Os eixos 01 e 03 exigiram segmentação parágrafo a parágrago porque
# cruzam explicitamente temas que pertencem a categorias diferentes da
# nossa taxonomia de 9 (saúde x educação/ciência no Eixo 01; economia x
# meio ambiente x segurança hídrica no Eixo 03). O texto do Eixo 01 em
# particular apresenta trechos com ordem de parágrafos aparentemente fora
# de sequência lógica (ex.: uma frase sobre saúde é interrompida e só
# retomada páginas depois) — provável artefato de extração de um PDF em
# duas colunas fora de ordem de leitura; ver nota de metodologia. Como no
# Ceará não há subtítulos, os marcadores usados aqui são as primeiras
# palavras (verbatim) de cada parágrafo, não títulos de seção.
#
# "Ciência, Tecnologia e Educação Superior" (parte do título do Eixo 01) foi
# tratada como "educacao" (mesma razão usada para Elmano: não há tema
# dedicado a C&T na taxonomia, e o candidato agrupa esse conteúdo com
# educação/universidades, não com o Eixo 03 de desenvolvimento econômico).
# Parágrafos genuinamente indivisíveis entre saúde e educação (ex.: "estamos
# integrando saúde, educação, ciência, tecnologia e educação superior") =
# "outros". "Segurança hídrica" segue o precedente do Ceará/Elmano =
# infraestrutura; proteção animal, aqui embutida em um parágrafo que a
# define explicitamente como parte "da política ambiental do Estado" (e não
# como seção autônoma, ao contrário do plano de Elmano), permanece
# "meio_ambiente".
MARCADORES_CIRO = [
    ("EIXO 01", "outros"),
    ("O Ceará construiu, ao longo das últimas décadas, experiências", "saude"),
    ("Na educação, o Ceará tornou-se referência nacional ao construir", "educacao"),
    ("Embora os indicadores de aprendizagem permaneçam satisfatórios,", "educacao"),
    ("A ciência, a tecnologia e a inovação passaram a representar fatores", "educacao"),
    ("A educação superior também enfrenta novos desafios.", "educacao"),
    ("As transformações tecnológicas em curso", "outros"),
    ("Analisar a implantação de Centros de Ciências e Descobrimento,", "educacao"),
    ("Apesar desses avanços, observa-se um processo de perda inequívoca", "saude"),
    ("eletrônico estadual, inteligência de dados e monitoramento", "saude"),
    ("Na educação, iniciaremos uma nova geração de políticas", "educacao"),
    ("A ciência, a tecnologia e a inovação passarão a ocupar posição", "educacao"),
    ("Na saúde, fortaleceremos a regionalização do Sistema Único de", "saude"),
    ("desenvolvimento humano e econômico do Ceará.", "outros"),
    ("O Ceará que queremos é um Estado que cuida das pessoas desde", "outros"),
    ("As universidades estaduais serão valorizadas como patrimônio", "educacao"),
    ("Promoveremos uma ampla transformação digital dos sistemas de", "outros"),
    ("Nosso governo promoverá uma nova etapa de desenvolvimento", "outros"),
    ("EIXO 02", "assistencia_social"),
    ("EIXO 03", "economia"),
    ("No campo, os desafios permanecem igualmente significativos.", "economia"),
    ("O turismo, uma das principais vocações econômicas do Ceará,", "economia"),
    ("Nos últimos anos, a iniciativa privada cearense abriu caminhos", "economia"),
    ("Os desafios ambientais também se tornaram mais complexos.", "meio_ambiente"),
    ("A segurança hídrica continuará sendo uma das questões estratégicas", "infraestrutura"),
    ("As transformações econômicas em curso no mundo representam", "economia"),
    ("Consolidaremos o Complexo Industrial e Portuário do Pecém", "economia"),
    ("Fortaleceremos o desenvolvimento do interior do Estado,", "economia"),
    ("O desenvolvimento agrário será tratado como política estratégica de", "economia"),
    ("O turismo passará a ser desenvolvido como política permanente", "economia"),
    ("A política ambiental será orientada pelo princípio do desenvolvimento", "meio_ambiente"),
    ("A segurança hídrica continuará sendo prioridade estratégica", "infraestrutura"),
    ("O Ceará reúne todas as condições para voltar a liderar o", "outros"),
    ("EIXO 04", "infraestrutura"),
    ("EIXO 05", "seguranca"),
    ("EIXO 06", "gestao_publica"),
]

MARCADORES = {
    "elmano-de-freitas": MARCADORES_ELMANO,
    "ciro-gomes": MARCADORES_CIRO,
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
# TAREFA 4 — Detecção de texto compartilhado entre planos
# (adicionada na correção pós-auditoria de 25/08/2026: os campos
# achado_texto_compartilhado/texto_compartilhado nunca foram incorporados ao
# analise.json publicado do Ceará -- find_shared_text_ce.py existia e já
# tinha o resultado genuíno [0 blocos], mas o merge nunca foi feito, fazendo
# o dashboard cair num texto padrão enganoso. Lógica idêntica à do Maranhão,
# adaptada para o único par possível com 2 candidatos.)
# ---------------------------------------------------------------------------
_SHARED_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9][a-zA-ZÀ-ÖØ-öø-ÿ0-9\-]*")
_SHARED_N = 8
_SHARED_MIN_CHARS = 150


def _tokenize_with_pos(text):
    return [(m.group(0).lower(), m.start(), m.end()) for m in _SHARED_WORD_RE.finditer(text)]


def _find_shared_blocks(text_a, text_b, n=_SHARED_N, min_chars=_SHARED_MIN_CHARS):
    toks_a = _tokenize_with_pos(text_a)
    toks_b = _tokenize_with_pos(text_b)
    words_a = [t[0] for t in toks_a]
    words_b = [t[0] for t in toks_b]

    index_a = {}
    for i in range(len(words_a) - n + 1):
        gram = tuple(words_a[i:i + n])
        index_a.setdefault(gram, []).append(i)

    matches = []
    i = 0
    while i <= len(words_b) - n:
        gram = tuple(words_b[i:i + n])
        candidates = index_a.get(gram)
        if candidates:
            best_len = 0
            best_a = None
            for a_start in candidates:
                length = 0
                while (a_start + length < len(words_a) and i + length < len(words_b)
                       and words_a[a_start + length] == words_b[i + length]):
                    length += 1
                if length > best_len:
                    best_len = length
                    best_a = a_start
            matches.append((best_a, i, best_len))
            i += best_len
        else:
            i += 1

    blocks = []
    for a_start, b_start, length in matches:
        if length < n:
            continue
        a_char_start = toks_a[a_start][1]
        a_char_end = toks_a[a_start + length - 1][2]
        b_char_start = toks_b[b_start][1]
        b_char_end = toks_b[b_start + length - 1][2]
        size = a_char_end - a_char_start
        if size >= min_chars:
            blocks.append({
                "a_char_start": a_char_start, "a_char_end": a_char_end,
                "b_char_start": b_char_start, "b_char_end": b_char_end,
                "size_a": size, "size_b": b_char_end - b_char_start,
            })
    return blocks


def _merge_close_blocks(blocks, gap_tolerance=3):
    if not blocks:
        return blocks
    blocks = sorted(blocks, key=lambda x: x["a_char_start"])
    merged = [blocks[0]]
    for b in blocks[1:]:
        last = merged[-1]
        if (b["a_char_start"] - last["a_char_end"] <= gap_tolerance and
                b["b_char_start"] - last["b_char_end"] <= gap_tolerance and
                b["b_char_start"] >= last["b_char_end"] - gap_tolerance):
            last["a_char_end"] = max(last["a_char_end"], b["a_char_end"])
            last["b_char_end"] = max(last["b_char_end"], b["b_char_end"])
            last["size_a"] = last["a_char_end"] - last["a_char_start"]
            last["size_b"] = last["b_char_end"] - last["b_char_start"]
        else:
            merged.append(b)
    return merged


def detectar_texto_compartilhado(textos_por_slug, pares):
    """Retorna (achado_texto_compartilhado, texto_compartilhado), no mesmo
    formato usado no analise.json publicado do Maranhão."""
    resultado_por_par = {}
    total_blocos = 0
    for s1, s2 in pares:
        a, b = textos_por_slug[s1], textos_por_slug[s2]
        blocks = _find_shared_blocks(a, b)
        blocks = _merge_close_blocks(blocks)
        blocks = [x for x in blocks if x["size_a"] >= _SHARED_MIN_CHARS]
        blocks.sort(key=lambda x: -x["size_a"])
        total_blocos += len(blocks)
        if blocks:
            identicos = [
                {
                    "tamanho_caracteres": x["size_a"],
                    "trecho": a[x["a_char_start"]:x["a_char_start"] + 200].replace("\n", " ").strip(),
                }
                for x in blocks
            ]
            observacao = (
                f"{len(blocks)} bloco(s) de texto idêntico (mínimo 150 caracteres, "
                "8 palavras consecutivas) encontrado(s) entre os dois planos."
            )
        else:
            identicos = []
            observacao = (
                "Nenhum bloco de texto idêntico (mínimo 150 caracteres, 8 palavras "
                "consecutivas) encontrado entre os dois planos."
            )
        resultado_por_par[f"{s1}_x_{s2}"] = {
            "blocos_identicos": identicos,
            "observacao": observacao,
        }

    if total_blocos == 0:
        resumo = (
            "Assim como observado no Maranhão (mas ao contrário da Paraíba, onde "
            "dois planos rivais compartilhavam parágrafos idênticos, incluindo um "
            "trecho sobre política de segurança pública repetido em três planos), "
            "a checagem de blocos de texto idêntico ou quase idêntico entre os "
            "planos do Ceará não encontrou nenhum bloco compartilhado (mínimo de "
            "150 caracteres, 8 palavras consecutivas) entre o par de candidatos "
            "analisado."
        )
    else:
        resumo = (
            f"A checagem de blocos de texto idêntico ou quase idêntico entre os "
            f"planos do Ceará encontrou {total_blocos} bloco(s) compartilhado(s) "
            "(mínimo de 150 caracteres, 8 palavras consecutivas)."
        )

    achado = {
        "resumo": resumo,
        "pares_verificados": [f"{s1}_x_{s2}" for s1, s2 in pares],
        "blocos_encontrados": total_blocos,
    }
    texto_compartilhado = {
        "pares_comparados": [f"{s1}_x_{s2}" for s1, s2 in pares],
        "resultado_por_par": resultado_por_par,
        "metodologia": (
            "Detecção por n-gramas: janelas deslizantes de 8 palavras consecutivas "
            "comparadas entre cada par de planos; sequências de n-gramas idênticos "
            "consecutivos são unidas em blocos, e blocos com menos de 150 caracteres "
            "são descartados por serem coincidências triviais de linguagem comum."
        ),
        "observacao_editorial": (
            "A ausência de blocos de texto idêntico não prova que os planos foram "
            "escritos de forma totalmente independente (podem ter referenciado as "
            "mesmas fontes de dados oficiais, por exemplo), apenas que não houve "
            "cópia literal de trechos redigidos entre os planos analisados."
        ),
    }
    return achado, texto_compartilhado


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    resultado_candidatos = []
    agregado_counter = Counter()
    corpos_por_slug = {}

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)
        corpos_por_slug[slug] = corpo

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

    pares = [("elmano-de-freitas", "ciro-gomes")]
    achado_texto_compartilhado, texto_compartilhado = detectar_texto_compartilhado(
        corpos_por_slug, pares
    )

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "19 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Ceará' e "
            "'cearense' NÃO são filtrados e podem aparecer nos termos mais "
            "frequentes). Mostra os termos mais repetidos por candidato e o "
            "agregado dos dois planos."
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
            "Heurística idêntica à usada nas análises da Paraíba e do "
            "Maranhão, sem nenhum ajuste específico para o Ceará, para "
            "manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O Ceará é um caso especial dentro do projeto: Elmano de Freitas "
            "é o governador em exercício concorrendo à reeleição (1º "
            "mandato) e, segundo institutos de pesquisa de peso nacional, "
            "aparece atrás do desafiante Ciro Gomes — um incumbente em "
            "desvantagem eleitoral, ao contrário do padrão mais comum em "
            "outros estados do projeto. Essa é uma leitura eleitoral, não "
            "textual: não influenciou nenhuma etapa da extração ou "
            "classificação dos planos. "
            "No plano de Elmano de Freitas, o ÍNDICE no início do documento "
            "repete (com pontos de preenchimento e número de página) os "
            "mesmos títulos usados como marcador de seção — o mesmo "
            "problema já identificado no plano de Felipe Camarão, no "
            "Maranhão. Corrigido com a mesma lógica: o primeiro marcador "
            "('APRESENTAÇÃO') usa sua 2ª ocorrência no texto como ponto de "
            "partida da segmentação, pulando o índice. "
            "O plano de Ciro Gomes tem uma particularidade distinta: é "
            "redigido em prosa corrida, organizado em 6 'Eixos "
            "Estratégicos' que agrupam deliberadamente vários temas sob um "
            "único rótulo (ex.: Eixo 01 = 'Saúde – Educação – Ciência, "
            "Tecnologia e Educação Superior'), sem subtítulos internos. Dois "
            "desses eixos (01 e 03) tiveram que ser segmentados parágrafo a "
            "parágrafo (usando as primeiras palavras verbatim de cada "
            "parágrafo como marcador, na ausência de subtítulos) para "
            "separar os temas cruzados. O Eixo 01, em particular, apresenta "
            "trechos com sequência de parágrafos aparentemente fora de "
            "ordem lógica (uma frase sobre saúde é interrompida e só "
            "retomada páginas depois) — provável artefato da extração de um "
            "PDF em duas colunas fora da ordem de leitura; essas frases "
            "fragmentadas foram classificadas pelo conteúdo do trecho em "
            "que aparecem, e não pela posição no documento. Decisões de "
            "classificação não óbvias (ciência/tecnologia = educação; "
            "proteção animal ora como assistência social ora como meio "
            "ambiente, dependendo de como cada candidato a enquadra "
            "textualmente; segurança viária e segurança hídrica = "
            "infraestrutura) estão documentadas linha a linha nos "
            "comentários do script de análise. "
            "Ressalva sobre a frequência de palavras: os dois PDFs extraídos "
            "preservam cabeçalhos/rodapés de página repetidos ao longo de "
            "todo o corpo do texto ('Elmano Governador 2027-2030' / 'Elmano "
            "e Gabriella 2027-2030', 54 ocorrências; 'PROGRAMA DE GOVERNO "
            "CIRO GOMES -2026', 39 ocorrências). Isso infla artificialmente "
            "a contagem de 'elmano' (62 ocorrências) no plano de Elmano de "
            "Freitas e de 'programa', 'ciro' e 'gomes' (~42-46 ocorrências "
            "cada) no plano de Ciro Gomes, fazendo esses nomes aparecerem "
            "entre os termos mais frequentes por um motivo estrutural do "
            "documento (rodapé repetido), não por ênfase textual real do "
            "candidato — o mesmo tipo de ruído de extração já documentado "
            "para o plano de Felipe Camarão no Maranhão, embora de origem "
            "diferente (rodapé de página, não falha de fonte incorporada). "
            "Ressalva sobre as citações de exemplo (pilares a/b/c e "
            "retórica sem evidência): os dois .txt do Ceará preservam a "
            "quebra de linha visual do PDF original linha a linha (cada "
            "linha do PDF é uma linha própria no .txt, em vez de texto "
            "corrido por parágrafo). Como a função de divisão de frases "
            "('split_sentences', idêntica à do Maranhão/Paraíba) trata "
            "quebras de linha como fim de frase, isso produz mais "
            "fragmentos de frase cortados no meio (ex.: uma citação "
            "começando em letra minúscula) do que nos planos de outros "
            "estados cujo texto foi extraído já como parágrafos corridos. "
            "Não alteramos a função para não introduzir uma diferença de "
            "metodologia específica do Ceará; o efeito é apenas estético "
            "nas citações de exemplo, não na contagem de palavras nem na "
            "distribuição temática (que operam por posição de caractere, "
            "não por frase)."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
        "achado_texto_compartilhado": achado_texto_compartilhado,
        "texto_compartilhado": texto_compartilhado,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
