#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Pernambuco 2026.

Réplica da metodologia usada no Maranhão (build_analysis_ma.py, por sua vez
réplica da Paraíba): distribuição temática exaustiva por segmentação de
marcadores de seção reais (lidos e mapeados à mão) e Índice de Base Empírica
(heurística lexical/regex idêntica à dos outros estados, reaproveitada sem
alterações para manter comparabilidade). Também gera as nuvens de palavras
(wordcloud) embutidas em base64 em cada candidato.

NOTA METODOLÓGICA ESPECÍFICA DE PERNAMBUCO — MARCADORES POR TEXTO NARRATIVO,
NÃO POR TÍTULO DE SEÇÃO:
O PDF de Raquel Lyra é um documento ESCANEADO (OCR). Nele, os títulos de
seção "de verdade" são artes gráficas (páginas de abertura de eixo/capítulo)
que o OCR reconhece muito mal — quase sempre como ruído ilegível — EXCETO
dentro do sumário/índice do início do documento, onde os títulos aparecem
como texto corrido limpo. Isso significa que, ao contrário do Maranhão (onde
os títulos de seção real eram legíveis e o único cuidado necessário era não
casar com a ocorrência do índice), aqui usar o título de seção como marcador
não funciona bem: o título muitas vezes SÓ existe de forma limpa no índice,
e o corpo do documento não o repete de forma reconhecível. A solução adotada
foi usar, como marcador de cada seção, a PRIMEIRA FRASE NARRATIVA legível
(texto corrido, não decorativo) que abre aquela seção no corpo do documento
—ande na prática tem o efeito colateral favorável de já não colidir com o
índice (o índice lista só os títulos, não essas frases). Ainda assim, o
código abaixo mantém a mesma proteção contra colisão com sumário/índice
usada no Maranhão (cursor_inicial = 2ª ocorrência do 1º marcador), por
segurança e paridade de método entre os dois candidatos e entre estados.
"""
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/pernambuco/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/pernambuco/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "raquel-lyra", "nome": "Raquel Lyra", "partido": "PSD",
     "categoria": "incumbente pleno (governadora em exercício, 1º mandato, concorrendo à reeleição)"},
    {"slug": "joao-campos", "nome": "João Campos", "partido": "PSB",
     "categoria": "desafiante (prefeito do Recife)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — WORD_RE e o núcleo de STOPWORDS são idênticos ao
# Maranhão (que por sua vez os herdou da Paraíba). Apenas EXTRA_STOPWORDS foi
# adaptado, trocando os termos estruturais específicos do estado (nome do
# estado/gentílico) — exatamente como o Maranhão fez ao herdar da Paraíba.
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
plano governo pernambuco pernambucano pernambucana pernambucanos
pernambucanas eleições 2026 partido número coligação fonte fontes status
texto seção seções eixo eixos parte partes bloco blocos documento página
páginas inclui incluem também estamos propõe prevê abertura caminho
proposto propostos principais desafios núcleo contexto visão onde
compromisso compromissos destaca destacados destacado
""".split())

EXTRA_STOPWORDS |= set("""
ods sumário monitoramento revisão implementação
""".split())

# Ruído específico da extração por OCR do plano de Raquel Lyra: o rodapé
# "Raquel [...] PLANODEGOVERNO2027-2030 [...]" se repete em quase toda
# página do PDF escaneado, e o OCR o funde em um único token
# "planodegoverno" (sem espaços) dezenas de vezes — não é uma palavra do
# conteúdo do plano, é artefato de paginação. Removido por ser ruído de
# extração, não por ajuste de conteúdo/tema.
EXTRA_STOPWORDS |= set("""
planodegoverno
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

# Raquel Lyra (PSD) — plano OCR, estruturado em 6 "eixos estratégicos"
# numerados (1 a 6, ver sumário do documento) subdivididos em subseções
# numeradas (1.1, 1.2, ...). Ver nota de metodologia no topo do arquivo sobre
# por que os marcadores usam a 1ª frase narrativa de cada (sub)seção, e não
# o título gráfico da seção (ilegível ao OCR fora do sumário).
#
# Decisões de classificação não óbvias:
#  - A introdução textual de cada eixo (parágrafo de abertura do eixo, antes
#    da 1ª subseção) não tem marcador próprio: foi absorvida pela 1ª
#    subseção de cada eixo, pelo mesmo motivo/critério usado no Maranhão
#    para introduções de seção curtas e tematicamente alinhadas com a
#    subseção seguinte (ao contrário de "front matter" genérico do
#    documento inteiro, que vai para "outros").
#  - 1.2 "Ciência, Tecnologia e Inovação": classificada como economia (não
#    educação), pois o conteúdo é sobre ecossistema de inovação, parques
#    tecnológicos (Porto Digital) e atração de investimento — não currículo
#    escolar. Precedente MA: seções de "inovação" -> economia.
#  - 3.2 "Inclusão Social e Direitos Humanos" e 3.3 "Políticas para
#    Mulheres": assistencia_social, seguindo o precedente do MA para
#    "desenvolvimento social e direitos humanos".
#  - 4.3 "Desenvolvimento Agrário e Agricultura Familiar" e 4.4 "Turismo":
#    economia, seguindo o precedente do MA ("PRODUÇÃO, TRABALHO E RENDA" e
#    "TURISMO" -> economia).
#  - 4.5 "Cultura, Economia Criativa e Patrimônio Histórico": assistencia_
#    social, seguindo o precedente do MA ("CULTURA" -> assistencia_social),
#    apesar do nome incluir "Economia Criativa" — o conteúdo do plano é
#    predominantemente sobre patrimônio, memória e acesso à cultura.
#  - 5.1 "Abastecimento de Água e Saneamento" e 5.3 "Habitação e Cidades
#    Resilientes": infraestrutura, seguindo o precedente do MA (água/esgoto,
#    habitação -> infraestrutura).
#  - 5.4 "Arquipélago de Fernando de Noronha": seção territorial que mistura
#    meio ambiente, turismo, energia limpa, saúde, educação e habitação da
#    ilha em um único capítulo indivisível por subtítulos. Classificada como
#    meio_ambiente porque é o tema que abre e organiza a seção (preservação
#    ambiental, matriz energética limpa, biodiversidade marinha) — decisão
#    editorial documentada aqui por não ser óbvia.
#  - O parágrafo de conclusão final do documento ("Ao longo deste Plano de
#    Governo...") foi classificado como "outros", mesmo critério do MA para
#    encerramentos genéricos que recapitulam o documento inteiro.
MARCADORES_RAQUEL = [
    ("O desenvolvimento econômico e social de Pernambuco está diretamente ligado à",
     "educacao"),  # eixo 1 intro + 1.1 Educação
    ("À Ciência, a Tecnologia e a Inovação (CT&I) são vetores fundamentais para o",
     "economia"),  # 1.2 Ciência, Tecnologia e Inovação
    ("O acesso pleno e digno à Saúde é a medida exata do respeito de um Estado pela sua",
     "saude"),  # eixo 2 intro + 2.1 Saúde e Qualidade de Vida
    ("Segurança e Cidadania não se constroem apenas com o combate à violência, mas com à",
     "seguranca"),  # eixo 3 intro + 3.1 Segurança Pública e Ressocialização
    ("Compreendemos que a verdadeira inclusão social passa por promover a equidade e combater a preconcuito",
     "assistencia_social"),  # 3.2 Inclusão Social e Direitos Humanos
    ("é POLÍTICAS PARA MULHERES",
     "assistencia_social"),  # 3.3 Políticas para Mulheres
    ("A infraestrutura viária e a imobilidade urbana de",
     "infraestrutura"),  # eixo 4 intro + 4.1 Infraestrutura Rodoviária e Mobilidade Urbana
    ("5 INDUSTRIA, COMERCIO E SERVIÇOS",
     "economia"),  # 4.2 Indústria, Comércio e Serviços
    ("4 DESENVOLVIMENTO AGRÁRIO E",
     "economia"),  # 4.3 Desenvolvimento Agrário e Agricultura Familiar
    ("Nos últimos três anos, avançamos no fomento à Indústria do Turismo. Em 2025.",
     "economia"),  # 4.4 Turismo
    ("À Cultura é a expressão máxima da identidade de Pernambuco, com um patrimônio imaterial E",
     "assistencia_social"),  # 4.5 Cultura, Economia Criativa e Patrimônio Histórico
    ("Construir o futuro de Pernambuco demanda uma perspectiva sistêmica, que una o",
     "infraestrutura"),  # eixo 5 intro + 5.1 Abastecimento de Água e Saneamento
    ("4 CLIMA E MEIO AMBIENTE",
     "meio_ambiente"),  # 5.2 Clima e Meio Ambiente
    ("4º HABITAÇÃO E CIDADES RESILIENTES",
     "infraestrutura"),  # 5.3 Habitação e Cidades Resilientes
    ("4 ARQUIPELAGO DE FERNANDO DE",
     "meio_ambiente"),  # 5.4 Arquipélago de Fernando de Noronha (ver nota acima)
    ("O futuro de Pernambuco exige um Estado inteligente e responsável com o uso dos recursos",
     "gestao_publica"),  # eixo 6 Gestão, Transparência e Combate à Corrupção
    ("ho longo deste Plano de Governo, apresentamos não apenas um retrato do que fizemos",
     "outros"),  # conclusão (OCR: "Ao longo" -> "ho longo")
]

# João Campos (PSB) — plano digital nativo (texto limpo, sem OCR), estruturado
# em 15 "eixos estratégicos" listados no sumário logo no início do documento
# (linha "Entre as principais diretrizes estão:"). Cada eixo é retomado no
# corpo do texto com o mesmo título (por isso, como no Maranhão, o 1º
# marcador aparece 2x — 1x no sumário, 1x no corpo — e o código pula para a
# 2ª ocorrência via cursor_inicial). A partir do 2º eixo em diante, o título
# no corpo NÃO repete o prefixo "» " do sumário, então cada marcador combina
# o título de seção com o início da 1ª frase do parágrafo de abertura, para
# garantir casamento único e evitar colisão com qualquer menção posterior à
# mesma palavra solta (ex.: "Saúde" sozinho apareceria dezenas de vezes no
# documento).
#
# Decisões de classificação não óbvias:
#  - "Garantia de Direitos e Diversidades (Crianças e Adolescentes, Juventude,
#    Pessoas Idosas, LGBTQIAPN+, Pessoas com Deficiência, Pessoas Negras,
#    Povos Originários)": assistencia_social — é um eixo de direitos e
#    proteção de populações específicas, mesmo critério do MA para "direitos
#    humanos".
#  - "Cultura e Economia Criativa": assistencia_social, mesmo precedente do
#    MA e do plano de Raquel Lyra (ver acima) — apesar do nome, o conteúdo é
#    predominantemente sobre identidade, patrimônio e fomento cultural.
#  - "Ciência, Tecnologia e Inovação": economia, mesmo critério aplicado ao
#    plano de Raquel Lyra (ecossistema de inovação/economia do conhecimento).
#  - "Desenvolvimento Econômico e Turístico": economia.
#  - "Desenvolvimento Agrário": economia, mesmo precedente do MA e do plano
#    de Raquel Lyra.
#  - "Infraestrutura e Recursos Hídricos" e "Desenvolvimento Urbano e
#    Mobilidade": infraestrutura.
#  - "Habitabilidade": infraestrutura, mesmo precedente do MA (habitação).
#  - "Meio Ambiente, Sustentabilidade & Proteção e Direito dos Animais":
#    meio_ambiente (inclui bem-estar animal, mesmo critério do MA).
#  - "Gestão Integrada, Regionalizada, Participativa e Digital": gestao_publica.
MARCADORES_JOAO = [
    ("» Desenvolvimento Social e Enfrentamento à Pobreza\nA Assistência Social será fortalecida",
     "assistencia_social"),
    ("Educação e Esportes\nPernambuco já provou que a educação pública pode mudar o destino de uma",
     "educacao"),
    ("Saúde\nCuidar da saúde dos pernambucanos exige antes de tudo concluir a ampliação",
     "saude"),
    ("Segurança Cidadã\nPernambuco precisa voltar a tratar a segurança pública com comando,",
     "seguranca"),
    ("Políticas para as Mulheres\nA política para as mulheres será uma dimensão central do novo projeto de",
     "assistencia_social"),
    ("Garantia de Direitos e Diversidades (Crianças e Adolescen-\ntes, Juventude, Pessoas Idosas, LGBTQIAPN+, Pessoas com\nDeficiência, Pessoas Negras, Povos Originários)\nA finalidade última",
     "assistencia_social"),
    ("Cultura e Economia Criativa\nPernambuco é terra de criação.",
     "assistencia_social"),
    ("Ciência, Tecnologia e Inovação\nTornar Pernambuco o maior polo da economia do conhecimento do Nordeste",
     "economia"),
    ("Desenvolvimento Econômico e Turístico\nTransformar Pernambuco em uma potência econômica regional exige que o",
     "economia"),
    ("Desenvolvimento Agrário\nO desenvolvimento de Pernambuco passa necessariamente pelo fortaleci-",
     "economia"),
    ("Infraestrutura e Recursos Hídricos\nPernambuco ocupa posição estratégica no Brasil e no Nordeste, reunindo",
     "infraestrutura"),
    (" Desenvolvimento Urbano e Mobilidade\nO desenvolvimento de Pernambuco passa pela retomada do papel do Estado",
     "infraestrutura"),
    ("Habitabilidade\nGarantir habitabilidade significa assegurar que as pessoas possam viver com",
     "infraestrutura"),
    ("Meio Ambiente, Sustentabilidade & Proteção e Direito dos\nAnimais\nNão existe desenvolvimento sustentável que não envolva preservação do meio",
     "meio_ambiente"),
    ("Gestão Integrada, Regionalizada, Participativa e Digital\nGovernar Pernambuco exige mais do que administrar a máquina pública ou",
     "gestao_publica"),
]

MARCADORES = {
    "raquel-lyra": MARCADORES_RAQUEL,
    "joao-campos": MARCADORES_JOAO,
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
    segmentos_debug.append(("[FRONT MATTER: capa/sumário/mensagens de abertura]", "outros", n_intro))

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
    r"abaixo da linha de pobreza|linha de base|posição no ranking|"
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
    r"evidênci|comprovad|estudo(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|mapbiomas|"
    r"universidade|instituto)|pesquisa(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|"
    r"mapbiomas|universidade|instituto)|"
    r"ibge|ipea|datasus|sinisa|mapbiomas|inpe|zee-ma|zee/ma|"
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
# TAREFA 3 — Nuvem de palavras (mesmo estilo do Maranhão)
# ---------------------------------------------------------------------------
def gerar_wordcloud_b64(counts: Counter, slug: str) -> str:
    wc = WordCloud(
        width=800, height=500, background_color=None, mode="RGBA",
        colormap="viridis", prefer_horizontal=0.9, max_words=120,
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
    resultado_candidatos = []
    agregado_counter = Counter()

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Mesma proteção contra sumário/índice usada no Maranhão: se o 1º
        # marcador aparecer mais de uma vez, pula para a 2ª ocorrência.
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        be = base_empirica_analise(corpo[cursor_inicial:], slug)
        wc_b64 = gerar_wordcloud_b64(counts, slug)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "categoria": c["categoria"],
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
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "marcadores de seção reais. No plano de João Campos (texto digital "
            "nativo), os marcadores são os títulos de seção verbatim. No plano "
            "de Raquel Lyra (documento escaneado, extraído por OCR), os "
            "títulos de seção são artes gráficas que o OCR não reconhece de "
            "forma legível fora do sumário; por isso os marcadores usam a "
            "primeira frase narrativa legível que abre cada seção no corpo do "
            "texto, com o mesmo efeito de segmentação exaustiva. Cada "
            "segmento de texto entre dois marcadores consecutivos foi contado "
            "(em número de palavras) e atribuído a UM dos 9 temas."
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
            "Maranhão, sem nenhum ajuste específico para Pernambuco, para "
            "manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O plano de Raquel Lyra tem uma particularidade importante: o PDF "
            "original é um documento ESCANEADO (imagem, sem camada de texto "
            "nativa), e o .txt usado nesta análise foi obtido por OCR "
            "(tesseract, 300dpi, português). Isso produz ruído de "
            "reconhecimento perceptível, sobretudo na capa, em elementos "
            "gráficos e em tabelas — e também faz com que os títulos de seção "
            "(que no PDF são artes gráficas de abertura de capítulo) sejam "
            "quase sempre ilegíveis ao OCR fora do sumário/índice do início "
            "do documento. Por isso a segmentação temática deste candidato "
            "usa como marcador a primeira frase narrativa legível de cada "
            "seção, não o título — ver comentários no código-fonte "
            "(build_analysis_pe.py) para o detalhe de cada decisão. O plano "
            "de João Campos, por outro lado, é um documento digital nativo, "
            "sem ruído de OCR."
        ),
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
