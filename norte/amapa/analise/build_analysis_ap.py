#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Amapá 2026.

Réplica da metodologia usada nos 9 estados do Nordeste (build_analysis_ce.py,
build_analysis_al.py etc.): distribuição temática exaustiva por segmentação
de marcadores de seção reais (lidos e mapeados à mão) e Índice de Base
Empírica (heurística lexical/regex idêntica em todos os estados do projeto,
reaproveitada sem alterações para manter comparabilidade).

Caso do Amapá: 2 candidatos.
- Clécio Luís (União): GOVERNADOR EM EXERCÍCIO (1º mandato, 2023-2026),
  concorrendo à reeleição — incumbente pleno.
- Dr. Furlan (PSD, coligação PSD/PL/PODEMOS/NOVO): ex-prefeito de Macapá,
  afastado do cargo e depois renunciou para concorrer ao governo do Estado —
  desafiante/oposição ao governo estadual atual.
(Verificação feita por busca na Web em 23/08/2026 — ver campo "categoria" de
cada candidato e a nota de metodologia para as fontes exatas.)

DESVIO METODOLÓGICO DELIBERADO EM RELAÇÃO AO CEARÁ/ALAGOAS: nos dois planos
do Amapá, o corte de "cursor_inicial" (usado para pular a Capa/Sumário, que
repete os títulos de seção usados como marcador) é aplicado SOMENTE na
chamada de base_empirica_analise — não na distribuição temática exaustiva,
nem na contagem de total_palavras. Para a distribuição temática, o problema
de duplicação de marcadores no Sumário foi resolvido de outra forma: os
marcadores de cada seção foram escolhidos como texto de PROSA verbatim único
no documento (a 1ª frase do corpo de cada seção, e não o título da seção,
que em geral se repete no Sumário e/ou como cabeçalho de página repetido ao
longo de todo o eixo) — cada marcador foi conferido com grep para garantir
ocorrência única. Isso permite que a distribuição temática rode com
cursor_inicial=0 (padrão) e ainda assim classifique corretamente 100% do
corpo, com a Capa+Sumário caindo automaticamacaonte em "outros" (texto antes do
1º marcador).
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/amapa/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/amapa/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "clecio-luis", "nome": "Clécio Luís", "partido": "União",
     "categoria": (
         "incumbente pleno (governador em exercício do Amapá, 1º mandato "
         "2023-2026, concorrendo à reeleição) — confirmado pelo próprio "
         "texto do plano ('Desde o início da gestão do governador Clécio "
         "Luís...'; 'no segundo governo Clécio') e por cobertura eleitoral "
         "de 2026 ('O Amapá. O Clécio Luís. A Candidatura à Reeleição', "
         "blogoantagonico.com.br, jul/2026)"
     ),
     "cursor_inicial_base_empirica": 6003},
    {"slug": "dr-furlan", "nome": "Dr. Furlan", "partido": "PSD",
     "categoria": (
         "desafiante — ex-prefeito de Macapá (capital do Estado), afastado "
         "do cargo e depois renunciou à prefeitura em 2026 para disputar o "
         "governo do Amapá pela coligação PSD/PL/PODEMOS/NOVO, em oposição "
         "ao governo estadual de Clécio Luís (fonte: 'Prefeito afastado de "
         "Macapá renuncia para disputar o governo do Amapá', CNN Brasil, "
         "2026)"
     ),
     "cursor_inicial_base_empirica": 1994},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas a todos os estados do projeto (não
# adaptadas ao Amapá), para preservar comparabilidade.
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
# Clécio Luís — "Programa de Governo Estado do Amapá 2027-2030".
#
# Estrutura real do documento: Capa + Sumário (front matter, cai em "outros"
# automaticamente por ser texto antes do 1º marcador) + ensaio de balanço do
# 1º mandato ("O AMAPÁ AVANÇOU") + 6 EIXOS numerados com subseções.
#
# Como o Sumário reproduz literalmente os títulos de EIXO/subseção usados
# como cabeçalho no corpo (ex.: "EIXO 1: DESENVOLVIMENTO ECONÔMICO" aparece
# 2x no documento — 1x no Sumário, 1x como cabeçalho real), os marcadores
# abaixo evitam os títulos ambíguos e usam, nesses casos, a 1ª frase de
# prosa do corpo da seção (texto que não existe no Sumário) — cada marcador
# foi conferido com grep para garantir ocorrência única no documento
# inteiro. Os títulos de subseção (1.1, 1.2, ... 6.1) que NÃO se repetem no
# Sumário (por causa de pequenas diferenças de espaçamento/quebra de linha
# entre a entrada do Sumário e o cabeçalho real) foram usados diretamente,
# também conferidos via grep.
#
# Decisões de classificação não óbvias:
# - 1.5 "Ciência, Tecnologia e Inovação": classificado como "economia" (e
#   não "educacao"), porque no plano de Clécio esta subseção está dentro do
#   EIXO 1 (Desenvolvimento Econômico) e o conteúdo é sobre ecossistema de
#   inovação/startups/parque tecnológico voltado a negócios, não sobre
#   formação escolar/universitária.
# - 1.10 "Regularização Fundiária": "infraestrutura" (precedente do
#   projeto: titulação de terras = infraestrutura, não economia).
# - 1.11 "Cultura, turismo, eventos e economia criativa": trecho genuinamente
#   multitemático (mistura, de forma indivisível, dados econômicos de
#   turismo/eventos com listagem de festas populares e um projeto de
#   corredor histórico-cultural-turístico) — classificado como "outros",
#   conforme a regra do projeto para trechos que cruzam temas sem
#   possibilidade de separação segura.
# - 1.12 "Cultura e economia criativa": aqui o texto é predominantemente
#   sobre política cultural (Sistema Estadual de Cultura, Conselho, Fundo,
#   agentes culturais) — classificado como "assistencia_social", replicando
#   o precedente do projeto (cultura = assistência social) usado em todos
#   os outros estados.
# - 1.13 "Turismo": seção dedicada e monotemática, com argumento
#   explicitamente econômico ("vetor de desenvolvimento econômico") —
#   "economia".
# - 3.3 "Proteção Social" inclui um bullet de infraestrutura (Ponte Firme,
#   passarelas) e um de proteção animal (precedente = assistência social);
#   como o título da seção e a maior parte do conteúdo são de proteção
#   social, o segmento inteiro foi mantido em "assistencia_social".
# - EIXO 6 "Interiorização do Desenvolvimento": o parágrafo de abertura é
#   genericamente multitemático (menciona educação, saúde, segurança), mas
#   todas as "Propostas" listadas são obras físicas (rodovias, hospitais,
#   pavimentação, habitação, terminais hidroviários) — classificado como
#   "infraestrutura" no conjunto.
MARCADORES_CLECIO = [
    ("A partir de 2023, o Amapá iniciou um novo ciclo de desenvolvimento", "outros"),
    ("EIXOS ESTRATÉGICOS PARA O DESENVOLVIMENTO DO", "outros"),
    ("Eram conhecidos alguns gargalos para a atividade econômica", "economia"),
    ("1.2    Atração de investimentos para a promoção do desenvolvimento", "economia"),
    ("1.3     Preparar o Estado para a Economia do óleo e gás", "economia"),
    ("1.4     Economia da Floresta e Produção de Alimentos", "economia"),
    ("1.5     Ciência, Tecnologia e Inovação", "economia"),
    ("1.6   Pecuária", "economia"),
    ("1.7   Agricultura", "economia"),
    ("1.8   Pesca e aquicultura", "economia"),
    ("1.9   Desenvolvimento mineral", "economia"),
    ("1.10 Regularização Fundiária - Emissão de Títulos de Propriedade", "infraestrutura"),
    ("1.11 Cultura, turismo, eventos e economia criativa", "outros"),
    ("1.12 Cultura e economia criativa", "assistencia_social"),
    ("1.13 Turismo", "economia"),
    ("2.1    Infraestrutura e mobilidade", "infraestrutura"),
    ("3.1   Educação para o Futuro", "educacao"),
    ("3.2    Saúde da Gente", "saude"),
    ("3.3       Proteção Social", "assistencia_social"),
    ("3.4     Direitos humanos", "assistencia_social"),
    ("4.1    Segurança Pública: ações consistentes gerando resultados", "seguranca"),
    ("5.1    Concursos públicos e transposição de servidores", "gestao_publica"),
    ("6.1    Interiorização do Desenvolvimento do Amapá", "infraestrutura"),
    ("O Programa de Governo Clécio Luís Governador 2027–2030 é um documento", "outros"),
]

# ---------------------------------------------------------------------------
# Dr. Furlan — "Plano de Governo Amapá 2027-2030" (coligação PSD/PL/PODEMOS/
# NOVO), documento bem mais longo (78 páginas) e com estrutura mais
# elaborada: Capa + Sumário; Carta aberta ao povo; poema de abertura;
# "Apresentação" (repetida 3x como cabeçalho de página antes do texto real);
# "Três Pilares para um Novo Ciclo" (visão geral, sem conteúdo temático
# próprio); "Diretrizes Gerais da Gestão" (6 diretrizes numeradas, todas
# sobre COMO o governo vai operar — planejamento, transformação digital,
# regionalização, valorização de servidores, responsabilidade fiscal,
# participação social — classificado em bloco como "gestao_publica", e não
# "outros", porque, ao contrário da carta/poema/apresentação, tem conteúdo
# temático coerente e não é apenas retórica de abertura); depois 12 EIXOS
# temáticos numerados (cada um com diagnóstico em prosa + lista de
# propostas) e, por fim, um "Plano de Ação dos 100 Primeiros Dias" e um
# "COMPROMISSO FINAL" de encerramento.
#
# Como o título de cada EIXO se repete dezenas de vezes como cabeçalho de
# página ao longo de toda a seção (ex.: "Segurança Pública" aparece como
# cabeçalho em quase todas as páginas do Eixo 1, não apenas na abertura),
# os títulos de EIXO NÃO servem como marcador único. Cada marcador abaixo é,
# portanto, a 1ª frase de prosa do diagnóstico de cada eixo (texto que
# ocorre uma única vez no documento inteiro, conferido via grep) — e não o
# título do eixo.
#
# Decisões de classificação não óbvias:
# - "Petróleo e Energia": classificado como "economia" (cadeia produtiva de
#   óleo/gás/energia, atração de investimento, geração de emprego e renda),
#   mesmo critério usado no plano de Clécio Luís para o mesmo assunto
#   (subseção 1.3).
# - "Turismo e Economia Criativa": classificado como "economia" (o próprio
#   texto define o turismo como "vetor estratégico de transformação
#   econômica e social").
# - "Cultura, Patrimônio e Identidade Amapaense" e "Esporte e Lazer":
#   classificados como "assistencia_social", replicando o precedente do
#   projeto usado em todos os demais estados (cultura e esporte =
#   assistência social), mesmo quando o texto do candidato os descreve com
#   argumentos econômicos (geração de emprego/renda via eventos) — o
#   critério do projeto é o TEMA DE POLÍTICA PÚBLICA (cultura/esporte como
#   política setorial), não o argumento retórico usado para justificá-lo.
# - "Cidadania, Assistência e Proteção Social": "assistencia_social".
# - "Plano de Ação dos 100 Primeiros Dias": classificado como
#   "gestao_publica" (diagnóstico fiscal/administrativo e reforma
#   administrativa), não "outros", pelo mesmo critério usado para
#   "Diretrizes Gerais da Gestão".
# - "COMPROMISSO FINAL" (encerramento/carta final ao eleitor): "outros".
MARCADORES_FURLAN = [
    ("Carta erta", "outros"),
    ("Diretrizes Gerais da Gestão", "gestao_publica"),
    ("A segurança pública é condição essencial para garantir a liberdade", "seguranca"),
    ("A saúde é uma das principais políticas públicas para a promoção da qualidade de vida", "saude"),
    ("A educação é o principal instrumento para promover desenvolvimento humano", "educacao"),
    ("Entretanto, grande parte desses investimentos enfrenta obstáculos ainda na fase inicial de", "infraestrutura"),
    ("O Amapá inicia um novo momento de sua história.", "economia"),
    ("É necessário mapear as principais cadeias da sociobioeconomia", "meio_ambiente"),
    ("Cadeia produtiva de óleo, gás e energia: O Amapá produz mais energia do que consome.", "economia"),
    ("A assistência social constitui uma das principais políticas públicas de garantia cidadania.", "assistencia_social"),
    ("A cultura é uma das maiores riquezas do Amapá e um dos principais elementos de", "assistencia_social"),
    ("O turismo amapaense reúne ativos que nenhum outro estado brasileiro pode replicar", "economia"),
    ("O esporte e o lazer constituem políticas públicas essenciais para o desenvolvimento", "assistencia_social"),
    ("A transformar o Amapá num Estado moderno, eﬁciente, inovador e orientado por", "gestao_publica"),
    ("Plano de Ação dos 100 Primeiros Dias\n\n      O Governo do Estado executará", "gestao_publica"),
    ("COMPROMISSO FINAL", "outros"),
]

MARCADORES = {
    "clecio-luis": MARCADORES_CLECIO,
    "dr-furlan": MARCADORES_FURLAN,
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
    segmentos_debug.append(("[FRONT MATTER: capa/sumário]", "outros", n_intro))

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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica a todos os
# estados do projeto)
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
        # Nomes de arquivo em snake_case (clecio_luis.txt, dr_furlan.txt),
        # diferente do slug em kebab-case usado no resto do projeto.
        arquivo = slug.replace("-", "_") + ".txt"
        raw_text = (PLANOS_DIR / arquivo).read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]

        # Distribuição temática: SEM corte de cursor_inicial (marcadores já
        # são texto de prosa único no documento — ver nota de metodologia no
        # topo do arquivo).
        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=0
        )

        # Base empírica: corte de cursor_inicial (pula Capa/Sumário) É
        # aplicado aqui, para não contaminar os exemplos com fragmentos de
        # linhas de índice.
        cursor_inicial_be = c["cursor_inicial_base_empirica"]
        be = base_empirica_analise(corpo[cursor_inicial_be:], slug)

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
                f.write(f"[{tema:20s}] {n:6d} palavras ({pct_seg:5.1f}%) :: {marcador[:80]!r}\n")

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
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados). Mostra os termos "
            "mais repetidos por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "marcadores de texto verbatim (a 1ª frase de prosa de cada "
            "seção, e não seu título — ver nota de metodologia sobre o "
            "porquê). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível, o "
            "segmento foi classificado como 'outros', documentado nos "
            "comentários do script."
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
            "estados do projeto, sem nenhum ajuste específico para o "
            "Amapá, para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O Amapá é o primeiro estado da região Norte incluído no "
            "projeto (os 9 estados anteriores eram do Nordeste); a "
            "metodologia de análise textual é idêntica, sem nenhum ajuste "
            "regional. Os 2 planos são as propostas de governo oficiais "
            "registradas no TSE (proposta_governo_2026_AP.zip, "
            "cdn.tse.jus.br): Clécio Luís (2026AP30002536311_01.pdf, 37 "
            "páginas) e Dr. Furlan (2026AP30002530014_01.pdf, 78 páginas). "
            "Clécio Luís é o governador do Amapá em exercício (1º mandato, "
            "2023-2026), concorrendo à reeleição; Dr. Furlan é ex-prefeito "
            "de Macapá, afastado do cargo e depois renunciante em 2026 para "
            "concorrer ao governo, na oposição. "
            "DESVIO METODOLÓGICO EM RELAÇÃO AOS DEMAIS ESTADOS: nos planos "
            "anteriores do projeto (ex.: Ceará, Maranhão), quando a Capa/"
            "Sumário do PDF repetia os títulos usados como marcador de "
            "seção, a solução foi pular para a 2ª ocorrência do 1º "
            "marcador (cursor_inicial), e esse mesmo corte era aplicado "
            "tanto à distribuição temática quanto ao Índice de Base "
            "Empírica. No Amapá, os dois planos têm esse mesmo problema de "
            "Sumário duplicando títulos de seção — mas a solução adotada "
            "foi diferente: para a DISTRIBUIÇÃO TEMÁTICA, cada marcador foi "
            "trocado pelo início verbatim da 1ª frase de prosa de cada "
            "seção (texto que não existe no Sumário, conferido com grep "
            "para garantir ocorrência única), permitindo rodar a "
            "segmentação inteira a partir da posição 0 do documento, com a "
            "Capa/Sumário caindo automaticamente em 'outros' (texto antes "
            "do 1º marcador). Já para o ÍNDICE DE BASE EMPÍRICA, mantivemos "
            "o padrão de cortar um cursor_inicial fixo, calculado à mão "
            "para cada candidato (posição do início do corpo real, pulando "
            "Capa/Sumário): 6003 caracteres para Clécio Luís (2ª ocorrência "
            "de 'O AMAPÁ AVANÇOU', o cabeçalho real do ensaio de abertura) "
            "e 1994 caracteres para Dr. Furlan (início de 'Carta aberta ao "
            "Povo do Amapá'). Esse corte NÃO é aplicado à distribuição "
            "temática nem à contagem de total_palavras (que sempre operam "
            "sobre o corpo completo, incluindo Capa/Sumário) — apenas à "
            "extração de frases para os pilares a/b/c e para os exemplos de "
            "retórica sem evidência, para não contaminar essas citações com "
            "fragmentos de linhas de índice (título de seção seguido de "
            "pontos de preenchimento e número de página). "
            "Resíduo de extração de PDF conhecido, no plano de Dr. Furlan: "
            "o PDF original usa a ligadura tipográfica 'fi' com um glifo "
            "que, em ~19 ocorrências ao longo de todo o documento, foi "
            "extraído como caractere Unicode de Área de Uso Privado (U+F001 "
            "em 18 casos, U+E183 em 1 caso) em vez do texto 'fi' original — "
            "ex.: a 'Carta aberta ao Povo do Amapá' (título de seção) foi "
            "extraída como 'Carta \\ue183erta'; palavras comuns como "
            "'filho', 'desafios' e 'eficiente' aparecem, nesses ~19 pontos "
            "específicos, com o caractere de área privada no lugar do 'fi' "
            "(ex.: '\\uf001lho', 'desa\\uf001os'). Não corrigimos esse "
            "resíduo (mesmo espírito de transparência metodológica adotado "
            "para outros defeitos de extração já documentados no projeto, "
            "como o de ACM Neto na Bahia): ele é raro (~19 ocorrências em "
            "78 páginas), não afeta a segmentação temática (que opera por "
            "posição de caractere, não por palavra), e tem efeito mínimo na "
            "contagem de frequência de palavras (nesses poucos pontos, o "
            "tokenizador separa a palavra em dois fragmentos ao redor do "
            "caractere de área privada, já que ele não pertence à faixa "
            "Unicode de letras reconhecida por WORD_RE — nenhum desses "
            "fragmentos aparece entre os termos mais frequentes de cada "
            "candidato)."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
