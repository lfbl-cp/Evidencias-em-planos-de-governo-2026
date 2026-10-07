#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Rio de Janeiro 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia do Maranhão e da Paraíba: distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica aos demais
estados, reaproveitada sem alterações para manter comparabilidade).

*** CASO ESPECIAL DO RIO DE JANEIRO: SÓ 1 CANDIDATO NESTA RODADA ***
Ao contrário de todos os demais estados do projeto (2 candidatos cada), o RJ
entra nesta rodada com um único candidato analisável: Douglas Ruas (PL).

Segundo pesquisas Datafolha de 18-21/08/2026, os 2 nomes mais competitivos ao
governo do RJ são Eduardo Paes (PSD, 41%, líder disparado) e Douglas Ruas
(PL, 19%, 2º lugar); um 3º nome, Anthony Garotinho (Republicanos), aparece
com 9%. Checagem no portal de dados abertos do TSE
(proposta_governo_2026_RJ.zip) mostrou que, na data de coleta, Eduardo Paes e
Anthony Garotinho AINDA NÃO haviam registrado proposta de governo em PDF
junto ao TSE — só Douglas Ruas tem documento disponível. Decisão editorial do
pesquisador responsável: analisar o RJ nesta rodada apenas com Douglas Ruas,
documentando a ausência dos outros dois com destaque (ver
"metodologia_nota"), e atualizar a análise quando Paes/Garotinho registrarem
suas propostas (o prazo eleitoral ainda permite o registro).

Sobre a categoria de Douglas Ruas: ele foi Secretário de Estado de Cidades no
governo de Cláudio Castro (2023–mar/2026) e, em março de 2026, foi eleito
presidente da Alerj. Cláudio Castro renunciou ao cargo de governador em
março/2026 e foi declarado inelegível até 2030 pelo TSE — não é candidato a
nada em 2026. Embora a linha sucessória constitucional apontasse inicialmente
para Douglas Ruas (presidente da Alerj) assumir o governo interinamente, o
STF, em abril/2026, negou pedido da Alerj nesse sentido e manteve o
desembargador presidente do Tribunal de Justiça do RJ como governador
interino — precisamente para evitar que um pré-candidato ao pleito de 2026
(Douglas Ruas) governasse o Estado durante a própria campanha. Ou seja:
Douglas Ruas NÃO é vice-governador, não é sucessor formal de Castro no cargo
e não está no Executivo estadual hoje — é candidato do PL/bolsonarismo, que
herdou o espaço político (e o eleitorado) de Castro, mas não o cargo. Por
isso foi classificado como "desafiante" (challenger), e não como incumbente
ou como parte de um "governo em exercício" — ver "categoria" abaixo, com
fontes.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sudeste/rio-de-janeiro/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sudeste/rio-de-janeiro/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {
        "slug": "douglas_ruas",
        "nome": "Douglas Ruas",
        "partido": "PL",
        "vice": "Fernanda Louback",
        "categoria": (
            "desafiante — não é o governador em exercício nem o sucessor formal "
            "de Cláudio Castro. Douglas Ruas foi Secretário de Estado de Cidades "
            "no governo Castro (2023–mar/2026) e, em março de 2026, foi eleito "
            "presidente da Alerj. Castro renunciou ao governo em março/2026 e foi "
            "declarado inelegível até 2030 pelo TSE (não concorre a nada em "
            "2026). Embora a linha sucessória constitucional apontasse "
            "inicialmente para o presidente da Alerj assumir o governo "
            "interinamente, o STF negou pedido da Alerj nesse sentido em "
            "abril/2026 e manteve o desembargador presidente do TJ-RJ como "
            "governador interino, justamente para que um pré-candidato ao "
            "pleito de 2026 não governasse o Estado durante a própria campanha. "
            "Douglas Ruas herdou o espaço político e o eleitorado bolsonarista "
            "de Castro, mas não o cargo — concorre como desafiante em um "
            "Executivo estadual hoje sob interinidade judicial, não político-"
            "partidária. Fontes: Agência Brasil "
            "(https://agenciabrasil.ebc.com.br/politica/noticia/2026-03/entenda-o-que-acontece-no-rio-com-renuncia-de-claudio-castro , "
            "https://agenciabrasil.ebc.com.br/justica/noticia/2026-04/tse-publica-acordao-que-condenou-castro-inelegibilidade-ate-2030); "
            "TSE (https://www.tse.jus.br/comunicacao/noticias/2026/Marco/tse-torna-inelegivel-ex-governador-do-rio-claudio-castro); "
            "STF (https://noticias.stf.jus.br/postsnoticias/stf-nega-pedido-da-alerj-e-mantem-desembargador-como-governador-interino-do-rio-de-janeiro/); "
            "Congresso em Foco "
            "(https://www.congressoemfoco.com.br/noticia/117604/douglas-ruas-e-eleito-presidente-da-alerj-e-deve-assumir-governo-do-rj , "
            "https://www.congressoemfoco.com.br/noticia/118343/tse-reconhece-renuncia-de-castro-e-deixa-eleicao-no-rj-nas-maos-do-stf)."
        ),
    },
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Ceará/Maranhão/Paraíba (não
# adaptadas ao Rio de Janeiro), para preservar comparabilidade entre estados.
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

# Douglas Ruas ("Plano do Rio Real 2027-2030"): documento em PDF de 51
# páginas, com Sumário próprio (página 3-4) que NÃO repete os títulos reais
# usados como marcador (usa numeração/grafia levemente diferente: "Eixo 01"
# em vez de "Eixo 1", "Rio seguro" minúsculo em vez de "Rio\nSeguro", e a
# página "Apresentação dos Eixos" usa "EIXO 1" em versalete dentro de um
# diagrama, também distinto do marcador real "Eixo 1"). Verificado
# programaticamente que cada marcador usado abaixo ocorre exatamente o
# número de vezes esperado no arquivo (1x para a maioria; 2x para as seções
# "Compromissos" que se estendem por duas páginas sob o mesmo título) — não
# houve colisão com o Sumário nem com a página de diagrama dos eixos, então,
# ao contrário do Ceará/Maranhão, NÃO foi necessário nenhum cursor_inicial
# de correção (usa-se 0, ponto de partida real do corpo do documento).
#
# Estrutura real do documento: Capa → Carta de Compromisso (carta de
# abertura) → Sumário → Introdução → Apresentação dos Eixos (diagrama) →
# Eixo 1 "Rio Seguro" → Eixo 2 "Rio que Cuida" → Eixo 3 "Rio Próspero" →
# Eixo 4 "Rio que Avança" → Considerações Finais.
#
# Front matter (capa) fica automaticamente em "outros" (texto antes do 1º
# marcador). O 1º marcador, "Carta de\nCompromisso", também foi classificado
# como "outros": ele abre um segmento que inclui a própria carta de
# compromisso, o Sumário e a Introdução, e a página de Apresentação dos
# Eixos — nenhum desses tem conteúdo temático próprio atribuível a um único
# tema da taxonomia de 9 (a carta de abertura fala de segurança, saúde,
# educação e economia na mesma respiração; a Introdução resume os 4 eixos em
# bloco).
#
# Eixo 1 "Rio Seguro" é inteiramente monotemático (o próprio eixo já é
# "segurança pública") — por isso um único marcador ("Eixo 1") cobre o
# divisor + texto de diagnóstico + todas as 8 subseções de "Compromissos"
# (Escudo Fluminense, Cerco Financeiro, Linha Dura, Retomada do Estado, Mapa
# Único de Manchas Criminais, Rio por Elas: Segurança e Respeito, Gestão
# Integrada por Resultados, Polícia Forte/Policial Valorizado), todas
# classificadas como "seguranca".
#
# Eixo 2 "Rio que Cuida" cruza saúde, educação, habitação e assistência
# social sob um único rótulo — precisou de segmentação por subseção
# "Compromissos": o divisor + texto de diagnóstico introdutório (que mistura
# explicitamente saúde, educação e habitação num único parágrafo
# indivisível) foi classificado como "outros"; "Fila Curta, Cirurgia
# Rápida", "Saúde Perto de Casa" e "Saúde Integral da Mulher" = "saude";
# "Atenção à Pessoa com Espectro Autista" mistura diagnóstico/terapia em
# saúde com inclusão escolar, mas o núcleo da seção é cuidado e rede de
# apoio a uma população vulnerável (moldes semelhantes à seção "proteção e
# bem-estar animal"/"segurança alimentar" tratadas como assistência social
# em outros estados do projeto) — classificada como "assistencia_social";
# "Aprendizagem Nota 10" (2 páginas) e "Escola Protegida" = "educacao";
# "Propriedade Garantida e Segura" (política habitacional) = "infraestrutura",
# seguindo o precedente do Ceará/Maranhão/Paraíba de tratar habitação como
# infraestrutura; "Políticas Sociais e Autonomia" = "assistencia_social".
#
# Eixo 3 "Rio Próspero" é majoritariamente "economia": o divisor + texto de
# diagnóstico e as subseções "Investe Aqui", "Todo o Rio Crescendo", "Da
# Serra ao Mar" (2 páginas — turismo, economia do mar, bioeconomia), "Rio
# Criativo" (economia criativa/audiovisual — aqui tratada como "economia",
# não como "assistencia_social"/cultura genérica, porque a seção é
# explicitamente enquadrada como setor econômico gerador de emprego e renda,
# ao contrário de seções de cultura de outros planos do projeto que tratam
# cultura como política de acesso/identidade), "Empreende RJ" (2 páginas) e
# "Agro Grande" = "economia". Uma subseção, "RJ Integrado" (2 páginas), trata
# de infraestrutura econômica (rodovias, ferrovias, portos, energia,
# conectividade digital) e foi classificada como "infraestrutura", seguindo
# o mesmo precedente usado no Ceará de tratar conteúdo de infraestrutura
# física como "infraestrutura" mesmo quando aparece dentro de um eixo
# nominalmente econômico.
#
# Eixo 4 "Rio que Avança" cruza infraestrutura, mobilidade e meio ambiente —
# o próprio texto de abertura do eixo anuncia essa mistura explicitamente
# ("Reunimos aqui as políticas de infraestrutura, mobilidade e meio
# ambiente"), por isso o divisor + diagnóstico introdutório foi classificado
# como "outros" (indivisível). As subseções de infraestrutura/mobilidade
# ("Estado Parceiro das Cidades" [2 páginas], "Novos Corredores de
# Mobilidade", "Bilhete Único", "Rodovias RJ", "Concessões: Serviços que
# Funcionam" [2 páginas, inclui saneamento]) = "infraestrutura"; as
# subseções ambientais ("Proteção Contra Tragédias" — prevenção de
# desastres/eventos climáticos, e "RJ Verde Produtivo" [2 páginas] —
# resíduos, proteção animal, energia renovável) = "meio_ambiente".
MARCADORES_DOUGLAS_RUAS = [
    ("Carta de\nCompromisso", "outros"),
    ("Eixo 1", "seguranca"),
    ("Eixo 2", "outros"),
    ("Compromissos\nFILA CURTA, CIRURGIA RÁPIDA", "saude"),
    ("Compromissos\nSAÚDE PERTO DE CASA", "saude"),
    ("Compromissos\nSAÚDE INTEGRAL DA MULHER", "saude"),
    ("Compromissos\nATENÇÃO À PESSOA COM", "assistencia_social"),
    ("Compromissos\nAPRENDIZAGEM NOTA 10", "educacao"),
    ("Compromissos\nAPRENDIZAGEM NOTA 10", "educacao"),
    ("Compromissos\nESCOLA PROTEGIDA", "educacao"),
    ("Compromissos\nPROPRIEDADE GARANTIDA E SEGURA", "infraestrutura"),
    ("Compromissos\nPOLÍTICAS SOCIAIS E AUTONOMIA", "assistencia_social"),
    ("Eixo 3", "economia"),
    ("Compromissos\nINVESTE AQUI", "economia"),
    ("Compromissos\nTODO O RIO CRESCENDO", "economia"),
    ("Compromissos\nRJ INTEGRADO", "infraestrutura"),
    ("Compromissos\nRJ INTEGRADO", "infraestrutura"),
    ("Compromissos\nDA SERRA AO MAR", "economia"),
    ("Compromissos\nDA SERRA AO MAR", "economia"),
    ("Compromissos\nRIO CRIATIVO", "economia"),
    ("Compromissos\nEMPREENDE RJ", "economia"),
    ("Compromissos\nEMPREENDE RJ", "economia"),
    ("Compromissos\nAGRO GRANDE", "economia"),
    ("Eixo 4", "outros"),
    ("Compromissos\nESTADO PARCEIRO DAS CIDADES", "infraestrutura"),
    ("Compromissos\nESTADO PARCEIRO DAS CIDADES", "infraestrutura"),
    ("Compromissos\nNOVOS CORREDORES DE MOBILIDADE", "infraestrutura"),
    ("Compromissos\nBILHETE ÚNICO", "infraestrutura"),
    ("Compromissos\nRODOVIAS RJ", "infraestrutura"),
    ("Compromissos\nCONCESSÕES: SERVIÇOS", "infraestrutura"),
    ("Compromissos\nCONCESSÕES: SERVIÇOS", "infraestrutura"),
    ("Compromissos\nPROTEÇÃO CONTRA TRAGÉDIAS", "meio_ambiente"),
    ("Compromissos\nRJ VERDE PRODUTIVO", "meio_ambiente"),
    ("Compromissos\nRJ VERDE PRODUTIVO", "meio_ambiente"),
    ("Considerações\nFinais", "outros"),
]

MARCADORES = {
    "douglas_ruas": MARCADORES_DOUGLAS_RUAS,
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
    segmentos_debug.append(("[FRONT MATTER: capa]", "outros", n_intro))

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
        # Diferente do Ceará/Maranhão, o plano de Douglas Ruas não repete o
        # 1º marcador num sumário (verificado: 'Carta de\nCompromisso'
        # ocorre exatamente 1 vez no documento), então cursor_inicial = 0.
        cursor_inicial = 0

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        be = base_empirica_analise(corpo[cursor_inicial:], slug)

        wc_b64 = gerar_wordcloud_png_b64(counts, slug)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "vice": c["vice"],
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
            "Contagem de todas as palavras do corpo do plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados). Mostra os termos "
            "mais repetidos no plano; como esta rodada do RJ tem apenas 1 "
            "candidato, o 'top_palavras_agregado' é idêntico ao "
            "'top_palavras' do único candidato."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo do documento, sem "
            "amostragem): o plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/bloco de "
            "'Compromissos'). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível "
            "(ex.: os textos de abertura dos Eixos 2 e 4, que anunciam a "
            "mistura de saúde/educação/habitação ou infraestrutura/meio "
            "ambiente em um único parágrafo), o segmento foi classificado "
            "como 'outros'."
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
            "Heurística idêntica à usada nas análises do Ceará, Maranhão e "
            "Paraíba, sem nenhum ajuste específico para o Rio de Janeiro, "
            "para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "*** ATENÇÃO — CASO ESPECIAL: RODADA COM APENAS 1 CANDIDATO. *** "
            "Ao contrário de todos os demais estados do projeto, esta análise "
            "do Rio de Janeiro cobre um ÚNICO candidato — Douglas Ruas (PL). "
            "Isso NÃO é uma escolha de amostragem, é um reflexo do estágio "
            "do registro de propostas de governo no TSE nesta data de coleta "
            "(24/08/2026). "
            "Segundo pesquisas Datafolha de 18 a 21/08/2026, os 2 candidatos "
            "mais competitivos ao governo do RJ em 2026 são Eduardo Paes "
            "(PSD), líder disparado com 41% das intenções de voto, e Douglas "
            "Ruas (PL), em 2º lugar com 19%; um 3º nome, Anthony Garotinho "
            "(Republicanos), aparece com 9%. Ao verificar o portal de dados "
            "abertos do TSE (arquivo proposta_governo_2026_RJ.zip, "
            "cdn.tse.jus.br), constatou-se que, nesta data, Eduardo Paes e "
            "Anthony Garotinho AINDA NÃO haviam registrado proposta de "
            "governo em PDF junto ao TSE — apenas Douglas Ruas possui "
            "documento oficial disponível (2026RJ190002542887_01.pdf, 51 "
            "páginas). Sem o documento-fonte primário, não há como aplicar a "
            "mesma metodologia de análise textual a Paes ou a Garotinho nesta "
            "rodada. "
            "Decisão do pesquisador responsável pelo projeto: publicar a "
            "análise do RJ apenas com Douglas Ruas nesta rodada, documentando "
            "essa ausência com destaque (inclusive no dashboard do estado), e "
            "atualizar a análise assim que Eduardo Paes e/ou Anthony "
            "Garotinho registrarem suas propostas de governo — o prazo "
            "eleitoral para esse registro ainda não se encerrou. Até lá, "
            "qualquer leitura comparativa envolvendo o RJ (ex.: rankings "
            "entre estados por índice de base empírica) deve ter em mente "
            "que o candidato líder nas pesquisas para o cargo NÃO está "
            "representado nesta análise. "
            "Sobre a categoria de Douglas Ruas: ver o campo 'categoria' do "
            "candidato, com fontes — em resumo, ele não é o governador em "
            "exercício nem o sucessor formal de Cláudio Castro (que renunciou "
            "em março/2026 e foi declarado inelegível até 2030 pelo TSE); o "
            "STF manteve um desembargador (presidente do TJ-RJ) como "
            "governador interino, negando pedido para que o presidente da "
            "Alerj (cargo ocupado por Douglas Ruas desde março/2026) "
            "assumisse o Executivo durante a campanha. Douglas Ruas concorre, "
            "portanto, como desafiante. "
            "Sobre a segmentação temática: o plano de Douglas Ruas é "
            "organizado em 4 'Eixos' com subseções tituladas 'Compromissos', "
            "sem o problema de sumário duplicado encontrado no Ceará/"
            "Maranhão — os marcadores usados aqui foram verificados "
            "programaticamente contra o texto extraído para confirmar que "
            "cada um ocorre exatamente o número de vezes esperado antes de "
            "compor a lista final (ver comentários no script). Decisões de "
            "classificação não óbvias — 'Atenção à Pessoa com Espectro "
            "Autista' como assistência social (não saúde nem educação, "
            "apesar de cruzar as duas); 'Rio Criativo' (economia criativa) "
            "como economia (não como cultura/assistência social, diferente "
            "do tratamento dado a seções de cultura genérica em outros "
            "planos do projeto, porque aqui a seção é enquadrada "
            "explicitamente como setor econômico gerador de emprego e "
            "renda); habitação ('Propriedade Garantida e Segura') como "
            "infraestrutura, seguindo o precedente do Ceará/Maranhão/"
            "Paraíba — estão documentadas linha a linha nos comentários do "
            "script de análise. "
            "ADENDO (verificação posterior): o PDF de Douglas Ruas (51 "
            "páginas) tem diagramação em duas colunas com um artefato de "
            "extração que intercala trechos de colunas adjacentes linha a "
            "linha no .txt — mesmo tipo de defeito já documentado no Ceará "
            "(Ciro Gomes) e no Centro-Oeste (Otaviano Pivetta/MT, Daniel "
            "Vilela/GO). Isso fragmenta bastante as frases na etapa de "
            "split_sentences (código canônico, idêntico em todo o "
            "projeto), o que pode contribuir para o Índice de Base "
            "Empírica particularmente baixo deste candidato (1,0%: apenas "
            "1 trecho com base empírica contra 96 de retórica sem "
            "evidência) — não corrigido, para manter a metodologia "
            "idêntica entre estados, mas registrado aqui como limitação "
            "conhecida da extração, não uma característica do conteúdo do "
            "plano em si. "
            "[Reverificação (25/08/2026): checagem direta do arquivo "
            "proposta_governo_2026_RJ.zip no CDN do TSE (regenerado pelo "
            "TSE em 24/08/2026, 07:02) confirma que a situação permanece "
            "inalterada — o zip contém 8 documentos de propostas de "
            "governo para o RJ (André Marinho/Novo, Coronel Busnello/"
            "Missão, Cyro Garcia/PSTU, Douglas Ruas/PL, Juliete/UP, Luan "
            "Monteiro/PCO, William Siri/PSOL, mais um arquivo aparentemente "
            "mal classificado como proposta de Deputada Estadual), mas "
            "NENHUM de Eduardo Paes (PSD) nem de Anthony Garotinho "
            "(Republicanos) — apesar de ambos aparecerem como candidatos a "
            "GOVERNADOR oficialmente registrados no cadastro do TSE após o "
            "encerramento do prazo de registro (15/08/2026). Ou seja, "
            "registro de candidatura e envio de proposta de governo em PDF "
            "são etapas distintas no TSE, e a segunda ainda está pendente "
            "para os dois nomes mais competitivos da corrida. Esta análise "
            "continua cobrindo apenas Douglas Ruas até que isso mude.]"
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
