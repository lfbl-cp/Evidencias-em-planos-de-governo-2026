#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Minas Gerais 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia do Maranhão/Paraíba: distribuição temática exaustiva
por segmentação de marcadores de seção reais (lidos e mapeados à mão) e
Índice de Base Empírica (heurística lexical/regex idêntica, reaproveitada sem
alterações para manter comparabilidade entre estados).

Caso especial de Minas Gerais: NENHUM dos 2 candidatos deste projeto é
incumbente ou candidato de continuidade do governo em exercício. O
governador Romeu Zema (Novo) não podia concorrer a um 3º mandato
consecutivo e renunciou em 22/03/2026 para concorrer à Presidência da
República; seu vice, Mateus Simões (PSD), assumiu o governo no mesmo dia e é
o candidato de continuidade — mas Mateus Simões aparece com apenas ~4% nas
pesquisas e NÃO é um dos 2 candidatos analisados neste projeto. Cleitinho
Azevedo (Republicanos) é senador da República, sem vínculo com o governo
Zema/Simões, e lidera disparado as pesquisas (~32%). Alexandre Kalil (PDT) é
ex-prefeito de Belo Horizonte, também oposição ao governo estadual em
exercício. Os dois candidatos analisados são, portanto, "desafiantes" em
relação ao Executivo estadual em exercício — um enquadramento distinto do
padrão mais comum no projeto (incumbente vs. desafiante).

Segundo caso especial: os dois planos de MG têm tamanhos EXTREMAMENTE
diferentes. Cleitinho Azevedo: ~3,6 mil palavras, 16 páginas — o MENOR
documento do projeto até agora (menor até que os menores planos do
Nordeste). Alexandre Kalil: ~53,4 mil palavras, 147 páginas — um dos MAIORES
documentos do projeto inteiro, comparável ao de ACM Neto (BA, ~75 mil
palavras). Ver metodologia_nota para a discussão completa e para os totais
exatos — este contraste é dado real do material de campanha, não um efeito
de processamento, e é relevante para a discussão pendente sobre sensibilidade
do Índice de Base Empírica ao tamanho do documento (ver
NOTAS_METODOLOGICAS_PENDENTES.md).
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sudeste/minas-gerais/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sudeste/minas-gerais/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "cleitinho_azevedo", "nome": "Cleitinho Azevedo", "partido": "Republicanos",
     "categoria": "desafiante — senador da República, SEM vínculo com o governo estadual "
                  "em exercício (Zema/Mateus Simões); líder disparado nas pesquisas de "
                  "intenção de voto (~32% em 21/08/2026), muito à frente do candidato de "
                  "continuidade do governo atual, o vice-governador Mateus Simões (PSD, que "
                  "assumiu o cargo em 22/03/2026 após a renúncia de Romeu Zema para "
                  "concorrer à Presidência), que aparece com apenas ~4% e não é um dos 2 "
                  "candidatos deste projeto. Fontes: Portal 38, 'Pesquisa Governador MG "
                  "2026: Cleitinho lidera com 32%' (21/08/2026, "
                  "https://portal38.com.br/2026/08/21/pesquisa-governador-mg-2026-cleitinho/); "
                  "Poder360, 'Zema deixa o governo de MG para disputar a presidência' "
                  "(https://www.poder360.com.br/poder-eleicoes/zema-deixa-o-governo-de-mg-para-disputar-a-presidencia/)."},
    {"slug": "alexandre_kalil", "nome": "Alexandre Kalil", "partido": "PDT",
     "categoria": "desafiante — ex-prefeito de Belo Horizonte (2017–2020 e 2021–2022), "
                  "candidato do PDT ao governo de Minas Gerais, sem vínculo com o governo "
                  "estadual em exercício (Zema/Mateus Simões); concorre na oposição ao "
                  "grupo político hoje no Palácio da Liberdade. Fonte: BHAZ, 'PDT oficializa "
                  "Alexandre Kalil como candidato ao Governo de Minas' "
                  "(https://bhaz.com.br/noticias/minas-gerais/pdt-oficializa-alexandre-kalil-como-candidato-ao-governo-de-minas/)."},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os estados do
# projeto (não adaptadas a Minas Gerais), para preservar comparabilidade.
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
# Cleitinho Azevedo: o MENOR documento do projeto até agora (~3,6 mil
# palavras, 16 páginas), mas ainda assim bem estruturado: capa, "CARTA AO
# MINEIRO" (carta de abertura), "PRINCÍPIOS" (princípios inegociáveis de
# governo), "METODOLOGIA DE PARTICIPAÇÃO SOCIAL E GOVERNANÇA TRANSPARENTE"
# (Fóruns Regionais, Sala de Monitoramento — conteúdo de gestão pública real,
# não apenas retórica de abertura, por isso tratado como marcador próprio em
# vez de ser absorvido no "outros" de front matter) e, por fim, um índice
# ("10 EIXOS ESTRATÉGICOS DE GOVERNO") que lista os títulos dos 10 eixos
# reais do documento, cada um com até 10 propostas numeradas.
#
# BUG DE ÍNDICE (mesmo já visto no Ceará/Maranhão): o índice repete
# verbatim os títulos dos 10 eixos (com número de página) logo antes do
# corpo real. Diferente do Ceará (onde só o 1º marcador se repetia e a
# correção via "2ª ocorrência" bastava), aqui TODOS os 10 títulos de eixo se
# repetem no índice — a lógica de "usar a 2ª ocorrência", que só é aplicada
# ao primeiro marcador da lista pelo motor de análise, não resolveria os
# eixos 2 a 10. Solução adotada: o marcador de cada eixo NÃO é o título do
# eixo (que colide com o índice), e sim o texto verbatim do primeiro item
# numerado ("1. ...") de cada eixo — texto que não aparece no índice (o
# índice lista apenas títulos de eixo, não os itens numerados dentro deles).
# Isso desloca o início de cada segmento em poucas palavras (o próprio
# título do eixo, que passa a contar no segmento anterior) — efeito
# estatisticamente desprezível dado o tamanho de cada eixo.
#
# Dois eixos exigiram segmentação em duas partes por misturarem temas da
# taxonomia de 9 categorias do projeto:
#   - Eixo 9 ("Desenvolver e garantir o futuro dos mineiros"): itens 1-3
#     (saneamento, regulação da Copasa, resíduos sólidos) = infraestrutura;
#     itens 4-10 (barragens de mineração, licenciamento ambiental, riscos
#     climáticos, recursos hídricos, economia verde) = meio_ambiente —
#     mesmo precedente do Ceará ("SEGURANÇA HÍDRICA E SANEAMENTO AMBIENTAL"
#     = infraestrutura; demais itens ambientais = meio_ambiente).
#   - Eixo 10 ("Valorizar a cultura, o turismo e a identidade mineira"):
#     itens 1-5 (cultura, patrimônio, artesanato) = assistencia_social
#     (precedente do projeto: cultura = assistencia_social); itens 6-10
#     (turismo social, roteiros turísticos, capacitação para o setor de
#     turismo) = economia (setor econômico de serviços).
#
# "O Agro forte para Minas crescer" (eixo 7) foi tratado como "economia"
# (desenvolvimento do agronegócio), não há eixo dedicado a agro na taxonomia
# de 9 temas do projeto. "Minas que acolhe e transforma vidas" (eixo 8,
# proteção social/CRAS-CREAS/segurança alimentar/Reurb/mulheres/PCD/
# dependência química) foi mantido como bloco único em assistencia_social —
# a Regularização Fundiária Urbana (Reurb, item 4) é o único item que, em
# outro contexto do projeto, seria classificado como infraestrutura, mas
# aqui está explicitamente enquadrada como instrumento de proteção a
# famílias de baixa renda dentro de um eixo de assistência social, e é
# apenas 1 de 11 itens do eixo — não justifica quebrar o bloco.
#
# NUMERAÇÃO DEFEITUOSA NO DOCUMENTO ORIGINAL: no eixo 8, a numeração dos
# itens pula do item 5 direto para o item 7 (não existe item "6." no
# texto-fonte) — defeito do próprio PDF de campanha, não da extração; a
# contagem de palavras não é afetada (o texto entre os itens 5 e 7 foi
# incluído normalmente no segmento).
MARCADORES_CLEITINHO = [
    ("PRINCÍPIOS", "gestao_publica"),
    ("METODOLOGIA DE", "gestao_publica"),
    ("10 EIXOS ESTRATÉGICOS DE GOVERNO", "outros"),
    ("1. Renegociação da Dívida com a União", "gestao_publica"),
    ("1. Tabela Mineira de Procedimentos Estratégicos", "saude"),
    ("1. Policiamento Ostensivo e Territorial", "seguranca"),
    ("1. Recomposição da Aprendizagem, Alfabetização e Educação Especial", "educacao"),
    ("1. Ambiente de Negócios Simples e Digital", "economia"),
    ("1. Priorização de Investimentos Públicos sem Novos Pedágios", "infraestrutura"),
    ("1. Simplificação e Digitalização dos Processos", "economia"),
    ("1. Índice Mineiro de Vulnerabilidade Familiar", "assistencia_social"),
    ("1. Aceleração das Metas do Marco Legal do Saneamento", "infraestrutura"),
    ("4. Fiscalização Transparente de Barragens de Mineração", "meio_ambiente"),
    ("1. Descentralização dos Recursos da Cultura", "assistencia_social"),
    ("6. Expansão do Turismo Social", "economia"),
]

# ---------------------------------------------------------------------------
# Alexandre Kalil: um dos MAIORES documentos do projeto inteiro (~53,4 mil
# palavras, 147 páginas — comparável a ACM Neto, BA, ~75 mil palavras).
# Estrutura extremamente regular e numerada: 6 "PARTES" (I a VI, algemadas
# ao Sumário do PDF original, já removido pelo cursor_inicial da extração),
# 15 "Capítulos" numerados (1 a 15) e ~190 subseções numeradas (X.Y) dentro
# deles. Diferente de Cleitinho, o texto extraído NÃO preserva um sumário
# repetindo os títulos de capítulo antes do corpo (o cursor de extração já
# pulou o sumário original do PDF), então os marcadores de capítulo puderam
# ser usados diretamente, sem risco de colisão com um índice.
#
# Dado o tamanho do documento, a segmentação foi feita no nível de
# CAPÍTULO (a unidade estrutural real e majoritariamente monotemática do
# documento — cada capítulo já é dedicado a uma política setorial
# específica, ex.: capítulo 3 = SAÚDE inteiro, capítulo 5 = SEGURANÇA
# PÚBLICA inteiro), e não subseção por subseção — subdividir abaixo do
# nível de capítulo só foi feito nos poucos pontos em que um único capítulo
# mistura explicitamente mais de um dos 9 temas do projeto:
#
#   - Capítulo 8 (DESENVOLVIMENTO REGIONAL): subseções 8.1-8.4 e 8.7-8.8
#     (planejamento regional, governança territorial, inteligência
#     territorial) = gestao_publica; subseções 8.5-8.6 (Desenvolvimento
#     Urbano, Regularização Fundiária Rural) = infraestrutura, seguindo o
#     mesmo precedente do Ceará para regularização fundiária/habitação.
#   - Capítulo 11 (MEIO AMBIENTE E DESENVOLVIMENTO SUSTENTÁVEL): subseção
#     11.4 ("Bem-estar e proteção animal") = assistencia_social — mesmo
#     precedente usado no Ceará (Elmano de Freitas) para a seção homônima;
#     o restante do capítulo (11.1-11.3 e 11.5-11.18: água, biodiversidade,
#     bioeconomia, barragens, clima, licenciamento, resíduos, unidades de
#     conservação) permanece meio_ambiente.
#
# Capítulo 1 (subseções 1.1-1.5, "Um novo ciclo de desenvolvimento para
# Minas Gerais") foi classificado como "outros": é uma seção de visão geral
# do Plano (diagnóstico amplo e objetivos gerais que atravessam todos os
# temas ao mesmo tempo, sem detalhar propostas de nenhuma política setorial
# específica) — mesmo tratamento dado a seções de abertura/apresentação
# genéricas em outros estados do projeto (ex.: "APRESENTAÇÃO" no Ceará).
# Pelo mesmo motivo, o Capítulo 14 ("MINAS 2040", subseções 14.1-14.26) foi
# classificado como "outros": é um capítulo de cenário/visão de longo prazo
# que reafirma, de forma sintética e não-propositiva, os mesmos 9 temas já
# tratados em detalhe nos capítulos anteriores (ex.: 14.14 "Saúde em uma
# sociedade diferente", 14.15 "Educação para uma vida de aprendizagem
# permanente") — decisão editorial para não contar as mesmas propostas
# textualmente duas vezes sob temas diferentes; ver nota de metodologia
# para a alternativa considerada e descartada (distribuir cada subseção de
# volta ao tema que ela reafirma). O Capítulo 15 ("CONCLUSÃO") também é
# "outros" pelo mesmo motivo (encerramento/síntese, não proposta nova).
#
# Capítulo 6 (DESENVOLVIMENTO SOCIAL, TRABALHO E INCLUSÃO, 24 subseções:
# combate à pobreza, SUAS, qualificação profissional, juventude, mulheres,
# igualdade racial, LGBTQIA+, povos indígenas/quilombolas, PCD, pessoa
# idosa, população em situação de rua, segurança alimentar, habitação como
# proteção social, esporte/lazer, direitos humanos) foi mantido como bloco
# único em assistencia_social, mesmo critério do Ceará e do plano de
# Cleitinho neste mesmo estado — inclusive a subseção 6.17 ("Habitação como
# instrumento de proteção social"), que em outro contexto seria
# infraestrutura, mas aqui está explicitamente enquadrada pelo próprio
# título como política de proteção social, não como obra pública.
# Capítulo 12 (CULTURA, PATRIMÔNIO E IDENTIDADE MINEIRA, inclui a subseção
# "Economia criativa e trabalho cultural") segue o mesmo precedente do
# Ceará: cultura = assistencia_social, mesmo quando o texto discute a
# dimensão econômica da cultura.
MARCADORES_KALIL = [
    ("1.1. Um novo ciclo de desenvolvimento para Minas Gerais", "outros"),
    ("2. FINANÇAS E CAPACIDADE DE INVESTIMENTO", "gestao_publica"),
    ("3. SAÚDE", "saude"),
    ("4. EDUCAÇÃO", "educacao"),
    ("5. SEGURANÇA PÚBLICA", "seguranca"),
    ("6. DESENVOLVIMENTO SOCIAL, TRABALHO E INCLUSÃO", "assistencia_social"),
    ("7. DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("8. DESENVOLVIMENTO REGIONAL", "gestao_publica"),
    ("Desenvolvimento Urbano", "infraestrutura"),
    ("Inteligência Territorial", "gestao_publica"),
    ("9. ESTADO PARCEIRO DOS MUNICÍPIOS", "gestao_publica"),
    ("10. INFRAESTRUTURA PARA O DESENVOLVIMENTO", "infraestrutura"),
    ("11. MEIO AMBIENTE E DESENVOLVIMENTO SUSTENTÁVEL", "meio_ambiente"),
    ("Bem-estar e proteção animal", "assistencia_social"),
    ("Produzir conservando", "meio_ambiente"),
    ("12. CULTURA, PATRIMÔNIO E IDENTIDADE MINEIRA", "assistencia_social"),
    ("13. GESTÃO PÚBLICA MODERNA", "gestao_publica"),
    ("14. MINAS 2040", "outros"),
    ("15. CONCLUSÃO", "outros"),
]

MARCADORES = {
    "cleitinho_azevedo": MARCADORES_CLEITINHO,
    "alexandre_kalil": MARCADORES_KALIL,
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
            "comparabilidade metodológica entre estados). Mostra os termos "
            "mais repetidos por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/capítulo/"
            "subseção, ou, quando o título de seção colidia com um índice "
            "repetido no início do documento, o início verbatim do primeiro "
            "item de conteúdo da seção). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando um trecho do documento "
            "original já reunia explicitamente múltiplos temas de forma "
            "indivisível, o segmento foi classificado item a item sempre que "
            "os itens individuais eram identificáveis, ou como 'outros' "
            "quando não era possível separar com segurança."
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
            "Heurística idêntica à usada nas análises de todos os demais "
            "estados do projeto, sem nenhum ajuste específico para Minas "
            "Gerais, para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "Minas Gerais é um caso especial dentro do projeto por dois "
            "motivos independentes. "
            "(1) Nenhum dos 2 candidatos analisados é incumbente ou "
            "candidato de continuidade do governo em exercício: o "
            "governador Romeu Zema (Novo) não podia concorrer a um 3º "
            "mandato consecutivo e renunciou em 22/03/2026 para concorrer à "
            "Presidência da República; seu vice, Mateus Simões (PSD), "
            "assumiu o governo no mesmo dia e é o candidato de continuidade "
            "— mas Mateus Simões aparece com apenas ~4% nas pesquisas e NÃO "
            "é um dos 2 candidatos deste projeto. Cleitinho Azevedo "
            "(Republicanos) é senador da República, sem vínculo com o "
            "governo Zema/Simões, e lidera disparado as pesquisas (~32%); "
            "Alexandre Kalil (PDT) é ex-prefeito de Belo Horizonte, também "
            "oposição ao governo estadual em exercício. Os dois candidatos "
            "analisados são, portanto, 'desafiantes' em relação ao Executivo "
            "estadual em exercício — categoria distinta do par incumbente "
            "vs. desafiante mais comum em outros estados do projeto; ver "
            "'categoria' de cada candidato para as fontes completas. Essa é "
            "uma leitura eleitoral, não textual: não influenciou nenhuma "
            "etapa da extração ou classificação dos planos. "
            "(2) Os dois planos de MG têm tamanhos EXTREMAMENTE diferentes — "
            "um dado real do material de campanha, não um efeito de "
            "processamento. O plano de Cleitinho Azevedo tem "
            f"{resultado_candidatos[0]['total_palavras']:,} palavras "
            "(16 páginas) — o MENOR documento do projeto até agora, menor "
            "até que os menores planos já vistos no Nordeste. O plano de "
            "Alexandre Kalil tem "
            f"{resultado_candidatos[1]['total_palavras']:,} palavras "
            "(147 páginas) — um dos MAIORES documentos do projeto inteiro, "
            "comparável ao de ACM Neto (BA, ~75 mil palavras). Essa "
            "assimetria é relevante para a discussão metodológica pendente "
            "sobre a sensibilidade do Índice de Base Empírica ao tamanho do "
            "documento (levantada a partir do caso de Omar Aziz, AM, e ainda "
            "não resolvida — ver NOTAS_METODOLOGICAS_PENDENTES.md); os "
            "números de MG são registrados aqui para alimentar essa análise "
            "futura, sem qualquer correção retroativa aplicada aos dados "
            "deste relatório. "
            "Consequência prática dessa assimetria para a metodologia de "
            "segmentação: o plano de Cleitinho, mesmo curto, é bem "
            "estruturado (capa, carta de abertura, princípios, seção de "
            "governança, e 10 'Eixos Estratégicos de Governo' numerados com "
            "até 10 propostas cada) e preserva o mesmo bug de índice já "
            "visto no Ceará e no Maranhão: um sumário no início do documento "
            "('10 EIXOS ESTRATÉGICOS DE GOVERNO') repete verbatim os "
            "títulos dos 10 eixos antes do corpo real. Diferente do Ceará "
            "(onde só o título do primeiro marcador se repetia, resolvido "
            "usando sua 2ª ocorrência no texto), aqui os 10 títulos de eixo "
            "se repetem no sumário, e a lógica de 2ª ocorrência do motor de "
            "análise só se aplica ao primeiro marcador da lista — por isso, "
            "em vez do título de cada eixo, o marcador usado para os eixos "
            "1-10 é o texto verbatim do primeiro item numerado de cada um "
            "('1. Renegociação da Dívida com a União...' etc.), texto que "
            "não é repetido no sumário (que lista apenas títulos de eixo, "
            "não itens numerados). O plano de Kalil, por ser tão maior, é "
            "organizado em 6 Partes, 15 Capítulos e cerca de 190 subseções "
            "numeradas (X.Y) — o cursor de extração já removeu o sumário "
            "original do PDF, então não há colisão de índice, e a "
            "segmentação foi feita majoritariamente no nível de capítulo "
            "(cada capítulo já é dedicado, na prática, a uma única política "
            "setorial), com subdivisão adicional apenas nos 2 capítulos que "
            "misturam explicitamente mais de um dos 9 temas do projeto "
            "(Capítulo 8, Desenvolvimento Regional: parte planejamento/"
            "governança territorial = gestao_publica, parte "
            "desenvolvimento urbano/regularização fundiária rural = "
            "infraestrutura; Capítulo 11, Meio Ambiente: a subseção "
            "'Bem-estar e proteção animal' = assistencia_social, seguindo o "
            "mesmo precedente já usado no Ceará, com o restante do capítulo "
            "em meio_ambiente). Os capítulos 1 (visão geral de abertura), 14 "
            "('Minas 2040', um capítulo de cenário de longo prazo que "
            "reafirma de forma sintética os mesmos 9 temas já detalhados "
            "nos capítulos anteriores) e 15 (conclusão) foram classificados "
            "como 'outros' — decisão editorial para não contar as mesmas "
            "propostas duas vezes sob temas diferentes; a alternativa "
            "considerada e descartada foi redistribuir cada subseção do "
            "capítulo 14 de volta ao tema que ela reafirma (ex.: '14.14 "
            "Saúde em uma sociedade diferente' -> saude), o que inflaria "
            "artificialmente o peso desses temas em relação aos capítulos "
            "dedicados que já os tratam em detalhe. Decisões de "
            "classificação não óbvias (cultura = assistencia_social; "
            "regularização fundiária/habitação = infraestrutura; proteção "
            "animal = assistencia_social; turismo = economia quando tratado "
            "como setor econômico, mas mantido junto de cultura quando o "
            "próprio candidato os trata como bloco único) estão documentadas "
            "linha a linha nos comentários do script de análise. "
            "Nenhuma anomalia de extração de texto (ligaduras fi/fl/ti "
            "quebradas, mojibake de acentuação, ou texto fora de ordem de "
            "leitura) foi identificada em nenhum dos dois .txt de Minas "
            "Gerais — extração limpa em ambos os casos, incluindo no "
            "documento de 147 páginas de Kalil. Uma observação menor sobre "
            "o próprio texto-fonte (não da extração): no Eixo 8 do plano de "
            "Cleitinho ('Minas que acolhe e transforma vidas'), a numeração "
            "dos itens pula do item 5 direto para o item 7 (não existe um "
            "item '6.' no PDF original) — defeito do documento de campanha "
            "em si, sem efeito sobre a contagem de palavras ou a "
            "classificação temática. "
            "Ressalva sobre a frequência de palavras no plano de Cleitinho: "
            "o rodapé 'PLANO DE GOVERNO | CLEITINHO E FALCÃO' (ou variação "
            "'PLANO DE GOVERNO| CLEITINHO E FALCÃO') se repete em 13 das 16 "
            "páginas do PDF e é preservado no .txt extraído, inflando "
            "artificialmente a contagem de 'cleitinho' (16 ocorrências) e "
            "'falcão' (16 ocorrências) no topo de palavras mais frequentes "
            "por um motivo estrutural do documento (rodapé de página "
            "repetido), não por ênfase textual do próprio candidato — o "
            "mesmo tipo de ruído de extração já documentado para outros "
            "planos do projeto (ex.: rodapé 'Elmano Governador 2027-2030' "
            "no Ceará). Como o documento de Cleitinho é muito curto (o menor "
            "do projeto), esse ruído tem peso proporcionalmente maior na "
            "lista de termos mais frequentes do que teria em um documento "
            "maior. Nenhum ruído equivalente foi identificado no plano de "
            "Kalil (o texto extraído não preserva um rodapé de página "
            "repetido)."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
