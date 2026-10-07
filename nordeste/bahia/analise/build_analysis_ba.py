#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Bahia 2026.

Réplica da metodologia usada nos demais estados do projeto (build_analysis_ma.py
como script canônico, já corrigido por um validador independente): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica à
usada em todos os outros estados, reaproveitada sem alterações para manter
comparabilidade). Também gera as nuvens de palavras (wordcloud) embutidas em
base64 em cada candidato.

NOTA METODOLÓGICA ESPECÍFICA DA BAHIA — DOIS DOCUMENTOS COM ESTRUTURAS MUITO
DIFERENTES:

O plano de Jerônimo Rodrigues (PT, incumbente pleno, 1º mandato, concorrendo à
reeleição) é um documento de ~15,6 mil palavras, organizado em 4 "eixos"
numerados (1. Temas Transversais Prioritários; 2. Desenvolvimento Econômico;
3. Desenvolvimento Social e Garantias de Direitos; 4. Governança Democrática),
cada um subdividido em seções "N.N TÍTULO" com marcadores de tabulação (\t)
entre o número e o título — extraídos do PDF original com um Sumário completo
no início que repete os mesmos títulos de seção (mesmo problema já visto no
Maranhão/Piauí/Ceará/Alagoas): corrigido usando a 2ª ocorrência do marcador
"APRESENTAÇÃO" como cursor inicial, pulando todo o Sumário. Além disso, cada
um dos 3 "eixos temáticos" (2, 3 e 4) abre com um parágrafo-diagnóstico
substancial (várias centenas a milhares de palavras), citando estatísticas de
gestão (crescimento do PIB, taxa de desemprego, Índice de Gini, número de
leitos hospitalares, taxa de alfabetização etc.) — típico de um plano de
governo de candidato À REELEIÇÃO, que usa o documento também para prestar
contas do mandato em curso. O intróito do eixo 3 (Desenvolvimento Social) é
particularmente extenso e multitemático (cobre saúde, educação, assistência
social, cultura, habitação, segurança pública em sequência) — foi segmentado
parágrafo a parágrafo, pelo início de cada frase temática ("Na saúde,...",
"Na educação,..." etc.), no mesmo espírito de granularidade fina já usado no
Bloco 1 de Felipe Camarão (Maranhão) e no item (d) do diagnóstico do mesmo
candidato.

O plano de ACM Neto (União Brasil, desafiante, ex-prefeito de Salvador) é um
documento MUITO mais longo (~75,2 mil palavras / 7.748 linhas), com diagramação
elaborada de campanha (títulos de capítulo em blocos gráficos grandes,
quebrados em várias linhas curtas, ex.: "SEGURANÇA\nPÚBLICA\nE DEFESA\nDO
CIDADÃO."). O documento também tem um Sumário no início, mas — ao contrário
dos demais estados — os títulos de capítulo no Sumário estão formatados em
uma única linha contínua (ex.: "PRIMEIRA TRINDADE - Página 09"), enquanto os
mesmos títulos no corpo do documento aparecem como blocos gráficos quebrados
em múltiplas linhas (ex.: "PRIMEIRA\nTRINDADE"). Como resultado, os marcadores
usados (que incluem a quebra de linha \n verbatim) são estruturalmente únicos
e não colidem com o Sumário — verificado programaticamente (cada marcador usado
tem exatamente 1 ocorrência no corpo do documento) — então NÃO foi necessário
o truque do cursor_inicial de 2ª ocorrência para este candidato. O documento é
organizado em "Três Trindades da Mudança" (Vida Digna: Segurança/Saúde/
Educação; Prosperidade Humana e Territorial: Economia/Infraestrutura/
Habitação/Promoção Social; Futuro Baiano: Cultura/Meio Ambiente/Inovação) mais
um capítulo final de Excelência na Gestão. Como cada um dos capítulos de 2ª
ordem (ex.: "Promoção Econômica do Desenvolvimento", que por si só reúne
Indústria, Comércio, Mineração, Agronegócio, Turismo e Trabalho) mapeia
inteiramente para um único tema do projeto (economia), não foi necessário
segmentar item a item os "pilares" numerados internos (ex.: "1. PLANO
ESTRATÉGICO INDUSTRIAL", "2. REFORMA DO DESENVOLVE" etc.) — a exceção é o
item "8. SAÚDE ANIMAL E BEM-ESTAR DOS PETS", dentro do capítulo de Saúde, que
foi destacado como seu próprio segmento e reclassificado para
assistencia_social (bem-estar animal), seguindo o mesmo precedente usado no
Maranhão (Orleans Brandão) e na Bahia (Jerônimo Rodrigues, seção 3.16) para
conteúdo de proteção/bem-estar animal.
"""
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/bahia/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/bahia/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "jeronimo-rodrigues", "nome": "Jerônimo Rodrigues", "partido": "PT",
     "categoria": ("incumbente pleno (governador em exercício, 1º mandato, "
                   "concorrendo à reeleição)")},
    {"slug": "acm-neto", "nome": "ACM Neto", "partido": "União Brasil",
     "categoria": "desafiante (ex-prefeito de Salvador)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os outros estados do
# projeto (WORD_RE e núcleo de STOPWORDS byte-idênticos; apenas
# EXTRA_STOPWORDS troca os termos estruturais específicos do estado).
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
plano governo bahia baiano baiana baianos baianas eleições 2026 partido
número coligação fonte fontes status texto seção seções eixo eixos parte
partes bloco blocos documento página páginas inclui incluem também estamos
propõe prevê abertura caminho proposto propostos principais desafios núcleo
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

# Jerônimo Rodrigues — 4 eixos numerados (1-4), subseções "N.N\tTÍTULO"
# (tabulação real entre número e título). O Sumário no início repete os
# mesmos títulos das subseções mas SEM a tabulação colada ao texto (título
# e número aparecem em linhas separadas no Sumário) — na prática, os
# marcadores "N.N\tTÍTULO" usados aqui só colidem com o Sumário em alguns
# casos (ex.: "3.12\t POPULAÇÃO IDOSA" aparece idêntico nos dois lugares);
# por isso, cursor_inicial pula todo o Sumário de uma vez (2ª ocorrência de
# "APRESENTAÇÃO"), e a partir daí a busca sequencial (cursor sempre avança)
# garante que cada marcador seja localizado apenas em sua ocorrência real no
# corpo do texto.
MARCADORES_JERONIMO = [
    ("APRESENTAÇÃO", "outros"),  # carta de abertura do governador + descrição do processo participativo (PGP)
    (" BAHIA DO CUIDADO", "assistencia_social"),  # seção com propostas concretas de política de cuidados (creches, idosos, PCD, trabalho doméstico)
    ("1\tTEMAS TRANSVERSAIS PRIORITÁRIOS", "outros"),  # parágrafo-preview dos 5 temas transversais (1.1-1.5), sem propostas próprias
    ("1.1\t SUSTENTABILIDADE AMBIENTAL", "meio_ambiente"),
    ("1.2\t TECNOLOGIA E INOVAÇÃO", "economia"),
    ("1.3\t IGUALDADE RACIAL", "assistencia_social"),
    ("1.4\t JUVENTUDE", "assistencia_social"),
    ("1.5\t MULHERES", "assistencia_social"),
    ("2\tDESENVOLVIMENTO ECONÔMICO", "economia"),  # intróito-diagnóstico do eixo 2 (PIB, emprego, Gini, BYD, Novo PAC etc.)
    ("2.1\t INDÚSTRIA, MINERAÇÃO, COMÉRCIO E SERVIÇOS", "economia"),
    ("2.2\t INFRAESTRUTURA, LOGÍSTICA E MOBILIDADE", "infraestrutura"),
    ("2.3\t INFRAESTRUTURA SOCIAL", "infraestrutura"),  # drenagem/contenção de encostas + Centros Sociais Urbanos
    ("2.4\t TRABALHO, GERAÇÃO DE EMPREGO E RENDA", "economia"),
    ("2.5\t SANEAMENTO E INFRAESTRUTURA HÍDRICA", "infraestrutura"),
    ("2.6\t DESENVOLVIMENTO DA PESCA", "economia"),
    ("2.7\t CONVIVÊNCIA COM O SEMIÁRIDO", "meio_ambiente"),  # adaptação climática/gestão hídrica em região semiárida
    ("2.8\t DESENVOLVIMENTO DO AGRONEGÓCIO", "economia"),
    ("2.9\t DESENVOLVIMENTO RURAL", "economia"),
    ("2.10\tTURISMO", "economia"),
    ("3\tDESENVOLVIMENTO SOCIAL E", "outros"),  # frase de abertura genérica do eixo 3, antes do parágrafo "Na saúde,"
    ("Na saúde, esse compromisso se traduz", "saude"),
    ("Na educação, a escola pública é entendida", "educacao"),
    ("A assistência social segue como uma das principais", "assistencia_social"),
    ("A promoção dos direitos segue como compromisso", "assistencia_social"),  # inclui frase sobre inclusão digital (Conecta Bahia)
    ("Na cultura, os investimentos das leis Paulo Gustavo", "assistencia_social"),
    ("Na habitação e na infraestrutura social, a parceria", "infraestrutura"),
    ("A segurança hídrica permanece como prioridade", "infraestrutura"),  # inclui dado sobre execução de rodovias (mesmo parágrafo)
    ("Na segurança pública, a modernização das forças", "seguranca"),
    ("A democracia participativa segue como uma marca", "gestao_publica"),
    ("Os avanços demonstram que o desenvolvimento social depende", "outros"),  # frase de fechamento do intróito do eixo 3
    ("3.1\t SAÚDE", "saude"),
    ("3.2\t EDUCAÇÃO", "educacao"),
    ("3.3\t ASSISTÊNCIA SOCIAL", "assistencia_social"),
    ("3.4\t ESPORTES", "assistencia_social"),
    ("3.5\t SEGURANÇA ALIMENTAR E NUTRICIONAL E", "assistencia_social"),
    ("3.6\t CULTURA", "assistencia_social"),
    ("3.7\t SEGURANÇA PÚBLICA E PREVENÇÃO À VIOLÊNCIA", "seguranca"),
    ("3.8\t HABITAÇÃO", "infraestrutura"),
    ("3.9\t CIDADANIA E DIREITOS HUMANOS", "assistencia_social"),
    ("3.10\tPOPULAÇÃO LGBTQIAPN+", "assistencia_social"),
    ("3.11\tCRIANÇA E ADOLESCENTE", "assistencia_social"),
    ("3.12\t POPULAÇÃO IDOSA", "assistencia_social"),
    ("3.13\tINDÍGENAS, POVOS E COMUNIDADES TRADICIONAIS", "assistencia_social"),
    ("3.14\tCUIDADO E REDUÇÃO DE DANOS", "assistencia_social"),
    ("3.15\tPOPULAÇÃO EM SITUAÇÃO DE RUA", "assistencia_social"),
    ("3.16\tDIREITOS DOS ANIMAIS", "assistencia_social"),  # bem-estar animal, mesmo precedente do Maranhão (Orleans Brandão)
    ("4\tGOVERNANÇA DEMOCRÁTICA,", "gestao_publica"),  # intróito-diagnóstico do eixo 4 (Territórios de Identidade, transformação digital)
    ("4.1\t TERRITORIALIDADE E DESENVOLVIMENTO", "gestao_publica"),
    ("4.2\t CAPACIDADE DE GOVERNO E GESTÃO DE PESSOAS", "gestao_publica"),
    ("4.3\t COMPRAS PÚBLICAS", "gestao_publica"),
    ("4.4\t RELAÇÕES INTERNACIONAIS", "economia"),  # internacionalização/atração de investimentos
]

# ACM Neto — documento longo (~75,2 mil palavras) organizado em "Três Trindades
# da Mudança" mais um capítulo final. Os títulos de capítulo no corpo são
# blocos gráficos quebrados em várias linhas (ex.: "SEGURANÇA\nPÚBLICA\nE
# DEFESA\nDO CIDADÃO."), estruturalmente distintos da mesma entrada no
# Sumário inicial (que aparece em uma única linha contínua, ex.: "Segurança
# Pública E Defesa Do Cidadão"). Cada marcador abaixo foi verificado
# programaticamente como tendo exatamente 1 ocorrência no corpo do
# documento — não há colisão com o Sumário, e por isso NÃO foi necessário o
# truque de cursor_inicial de 2ª ocorrência (diferente do Jerônimo e da
# maioria dos outros estados). Como os capítulos de 2ª ordem já mapeiam,
# quase todos, para um único tema do projeto, os "pilares" numerados
# internos (ex.: "1. PLANO ESTRATÉGICO INDUSTRIAL 2027–2035") não precisaram
# de marcador próprio — exceção: "8. SAÚDE ANIMAL E BEM-ESTAR DOS PETS",
# destacado do capítulo de Saúde e reclassificado para assistencia_social.
MARCADORES_ACM = [
    ("GOVERNANÇA\nPOR VOCAÇÃO\nREGIONAL\nDNA DA BAHIA.", "gestao_publica"),  # metodologia de planejamento territorial (27 Territórios de Identidade) + Sumário (título gráfico não colide com o Sumário)
    ("PRIMEIRA\nTRINDADE", "outros"),  # página divisória curta antes do capítulo de Segurança
    ("SEGURANÇA\nPÚBLICA\nE DEFESA\nDO CIDADÃO.", "seguranca"),
    ("VIDA NO\nTEMPO CERTO.", "saude"),
    ("8. SAÚDE ANIMAL E BEM-ESTAR DOS PETS", "assistencia_social"),
    ("EDUCAÇÃO.\nDE VERGONHA NACIONAL À\nREFERÊNCIA DO BRASIL.", "educacao"),
    ("SEGUNDA\nTRINDADE", "outros"),  # página divisória curta antes do capítulo econômico
    ("PROMOÇÃO\nECONÔMICA DO\nDESENVOLVIMENTO", "economia"),  # Indústria, Comércio/MPE, Mineração, Agronegócio, Turismo, Trabalho/Emprego
    ("INFRAESTRUTURA,\nTRANSPORTE\nE LOGÍSTICA.", "infraestrutura"),
    ("HABITAÇÃO.\nMORADIA DIGNA COMO\nPOLÍTICA DE ESTADO.", "infraestrutura"),
    ("PROMOÇÃO\nSOCIAL,\nCIDADANIA\nE COMBATE\nÀ POBREZA.", "assistencia_social"),  # inclui subseção de Esporte ("A Bahia que forma campeões")
    ("TERCEIRA\nTRINDADE", "outros"),  # página divisória curta antes do capítulo Futuro Baiano
    ("CULTURA.\nA BAHIA EXPORTA CULTURA HÁ", "assistencia_social"),
    ("MEIO AMBIENTE,\nSUSTENTABILIDADE\nE EMERGÊNCIA\nCLIMÁTICA.", "meio_ambiente"),
    ("INOVAÇÃO\nNA BAHIA.", "economia"),
    ("EXCELÊNCIA\nNA GESTÃO\nE RESPONSABILIDADE\nFISCAL.", "gestao_publica"),
    ("FONTES E\nREFERÊNCIAS.", "outros"),  # bibliografia final
]

MARCADORES = {
    "jeronimo-rodrigues": MARCADORES_JERONIMO,
    "acm-neto": MARCADORES_ACM,
}

# Candidatos cujo 1º marcador colide com uma cópia no Sumário (a busca deve
# começar a partir da 2ª ocorrência do 1º marcador, para não segmentar
# dentro do índice). Confirmado programaticamente: Jerônimo tem colisão
# (Sumário repete "APRESENTAÇÃO"); ACM Neto NÃO tem colisão (títulos
# gráficos multi-linha do corpo são estruturalmente distintos das entradas
# do Sumário, verificado com contagem de ocorrências == 1 para cada
# marcador usado).
CANDIDATOS_COM_SUMARIO_COLIDENTE = {"jeronimo-rodrigues"}


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
    segmentos_debug.append(("[FRONT MATTER: capa/carta de abertura/sumário]", "outros", n_intro))

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


# EVIDENCIA_RE — CORRIGIDO (herdado byte a byte de build_analysis_ma.py já
# corrigido). NÃO inclui "plano lula|plano nacional" como gatilhos genéricos
# de evidência: um validador independente encontrou que isso inflava
# artificialmente o pilar C quando um candidato apenas cita alinhamento
# político com o plano nacional do partido, sem citar evidência de fato. Isto
# é ESPECIALMENTE relevante na Bahia: Jerônimo Rodrigues é o incumbente do PT
# e cita o Governo Federal/presidente Lula com grande frequência ao longo do
# documento (parceria Bahia-União, Novo PAC, Minha Casa Minha Vida, BNDES,
# obras como a Ponte Salvador-Itaparica) — essas menções NÃO disparam
# is_evidencia por si só (verificado manualmente nos exemplos do pilar C
# gerados; ver metodologia_nota). "plano nacional de logística" é mantido:
# é uma referência específica e legítima a um documento técnico federal, não
# um gatilho genérico de alinhamento partidário.
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
# \x90 (documentado na correção pós-auditoria de 25/08/2026): caractere de
# controle usado como marcador de bullet no PDF original de Jerônimo
# Rodrigues (275 ocorrências no texto extraído) -- não é um erro de
# extração a corrigir, é o próprio glifo de marcador de lista do documento
# fonte, tratado aqui como qualquer outro caractere de bullet (-, •).
BULLET_RE = re.compile(r"^[\-••\x90]\s*")
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
                    colormap="viridis", prefer_horizontal=0.9, max_words=20)
    wc.generate_from_frequencies(freqs)
    png_path = WC_DIR / f"{slug}.png"
    wc.to_file(str(png_path))
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# TAREFA 4 — Texto compartilhado entre os 2 planos (achado pré-computado por
# find_shared_text_ba.py; resultado colado abaixo, mesmo padrão usado nos
# demais estados).
# ---------------------------------------------------------------------------
ACHADO_TEXTO_COMPARTILHADO = {
    "resumo": (
        "A checagem de blocos de texto idêntico ou quase idêntico entre os "
        "planos de Jerônimo Rodrigues e ACM Neto (mínimo de 150 caracteres, "
        "8 palavras consecutivas) não encontrou nenhum bloco compartilhado "
        "entre os dois documentos — resultado no mesmo sentido do observado "
        "no Maranhão, Piauí, Ceará, Pernambuco e Alagoas (0 blocos em todos "
        "os pares desses 5 estados), e diferente do observado na Paraíba "
        "(blocos de texto idênticos entre planos de candidatos rivais, "
        "incluindo um parágrafo repetido nos três planos)."
    ),
    "pares_verificados": ["jeronimo-rodrigues x acm-neto"],
    "blocos_encontrados": 0,
}

TEXTO_COMPARTILHADO = {
    "pares_comparados": ["jeronimo-rodrigues_x_acm-neto"],
    "resultado_por_par": {
        "jeronimo-rodrigues_x_acm-neto": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de 150+ caracteres idênticos (mínimo de 8 "
                "palavras consecutivas) encontrado entre estes dois planos. "
                "Os dois documentos têm perfis de redação e origem muito "
                "diferentes — o de Jerônimo Rodrigues é mais enxuto (~15,9 "
                "mil palavras) e estruturado como balanço de gestão mais "
                "propostas por eixo; o de ACM Neto é um dossiê de campanha "
                "muito mais extenso (~79,8 mil palavras), com diagnóstico "
                "comparativo detalhado por capítulo — o que por si só já "
                "torna reaproveitamento de texto literal entre as duas "
                "campanhas pouco provável."
            ),
        }
    },
    "metodologia": (
        "Mesmo método de detecção usado nas análises da Paraíba, Maranhão, "
        "Piauí, Ceará, Pernambuco e Alagoas: índice de n-gramas de 8 palavras "
        "consecutivas para localizar trechos idênticos ou quase idênticos "
        "entre os planos, com blocos adjacentes mesclados e um piso de 150 "
        "caracteres para descartar coincidências triviais (conectores, "
        "boilerplate curto). Como a Bahia tem apenas 2 candidatos com plano "
        "de governo coletado neste projeto, há um único par possível a "
        "comparar."
    ),
    "observacao_editorial": (
        "Nenhum bloco foi encontrado entre os dois planos da Bahia. Isso "
        "não prova ausência de uso de consultoria compartilhada ou de "
        "templates de propostas — apenas que não há trechos literalmente "
        "idênticos detectáveis por este método entre os dois documentos "
        "disponíveis."
    ),
}


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
        cursor_inicial = 0
        if slug in CANDIDATOS_COM_SUMARIO_COLIDENTE:
            # Se o 1º marcador aparecer mais de uma vez (documento com
            # sumário/índice que repete os títulos das seções antes do
            # corpo real), pula para a 2ª ocorrência, para não segmentar
            # dentro do índice.
            primeiro_marcador = marcadores[0][0]
            primeira_ocorrencia = corpo.find(primeiro_marcador)
            segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
            cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
        n_ocorrencias_1o_marcador = corpo.count(marcadores[0][0])
        print(f"{slug}: 1º marcador aparece {n_ocorrencias_1o_marcador}x no corpo "
              f"(cursor_inicial={cursor_inicial})")

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
                f.write(f"[{tema:20s}] {n:6d} palavras ({pct_seg:5.1f}%) :: {marcador[:80]!r}\n")

        print(f"{c['nome']:<28} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
              f"(a={be['n_pilar_a_diagnostico']} b={be['n_pilar_b_efeito']} c={be['n_pilar_c_evidencia_causal']} "
              f"/ retorica={be['n_retorica_sem_evidencia']})")
        soma_pct = round(sum(pct.values()), 1)
        print(f"  soma distribuicao_tematica_pct = {soma_pct}")

    top_agregado = agregado_counter.most_common(30)

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "19 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto, adaptada apenas no "
            "gentílico/nome do estado. Mostra os termos mais repetidos por "
            "candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "marcadores de seção reais (títulos de capítulo/eixo/pilar, "
            "verbatim, incluindo quebras de linha quando o título é um bloco "
            "gráfico quebrado em várias linhas no PDF original). Cada "
            "segmento de texto entre dois marcadores consecutivos foi "
            "contado (em número de palavras) e atribuído a UM dos 9 temas. "
            "No plano de Jerônimo Rodrigues, o Sumário no início do "
            "documento repete os títulos das seções (mesmo problema já visto "
            "em outros estados do projeto) — corrigido com cursor_inicial na "
            "2ª ocorrência do marcador 'APRESENTAÇÃO', pulando o Sumário "
            "inteiro. No plano de ACM Neto, os títulos de capítulo no corpo "
            "são blocos gráficos multi-linha estruturalmente distintos das "
            "entradas do Sumário (que estão em linha única) — verificado "
            "programaticamente que cada marcador usado tem exatamente 1 "
            "ocorrência no corpo do texto, então não foi necessário nenhum "
            "ajuste de cursor. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível "
            "(ex.: o intróito do eixo 'Desenvolvimento Social' de Jerônimo "
            "Rodrigues, que percorre saúde, educação, assistência social, "
            "cultura, habitação e segurança pública em sequência), o "
            "segmento foi classificado parágrafo a parágrafo sempre que os "
            "parágrafos individuais eram identificáveis, ou como 'outros' "
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
            "Heurística idêntica à usada nas análises da Paraíba, Maranhão, "
            "Piauí, Ceará, Pernambuco e Alagoas, sem nenhum ajuste "
            "específico para a Bahia, para manter comparabilidade entre "
            "estados. O regex de evidência (pilar C) NÃO trata menção a "
            "'plano nacional' ou alinhamento com o governo federal/Lula como "
            "evidência por si só — apenas referências específicas a "
            "estudos, dados institucionais (IBGE, IPEA, DATASUS etc.) ou "
            "modelos comprovadamente adotados contam (ver comentário no "
            "código-fonte sobre a correção do EVIDENCIA_RE). Isso é "
            "especialmente relevante aqui: Jerônimo Rodrigues, incumbente do "
            "PT concorrendo à reeleição, cita o Governo Federal/presidente "
            "Lula com grande frequência ao longo do documento (parceria "
            "Bahia-União, Novo PAC, Minha Casa Minha Vida, BNDES, Ponte "
            "Salvador-Itaparica) — nenhuma dessas menções, por si só, conta "
            "como evidência (pilar C); apenas quando o texto cita "
            "explicitamente uma fonte de dado/estudo (ex.: 'segundo a PNAD "
            "Contínua/IBGE', 'IBGE') é que o pilar A ou C é acionado. "
            "[Nota de correção metodológica (20/08/2026), aplicada "
            "uniformemente a todos os estados do projeto após auditoria "
            "independente: (1) o pilar C (evidência/mecanismo causal "
            "externo) tinha regex excessivamente genérico — os gatilhos "
            "'plano lula'/'plano nacional' (que capturavam mera menção de "
            "alinhamento político, não evidência) e os conectivos soltos "
            "'conforme o/a' e 'baseado em'/'com base em' sem exigir um "
            "substantivo evidencial próximo (ex.: 'baseado em gestão "
            "qualificada, inovação' disparava indevidamente) — foram "
            "removidos/restringidos para exigir termos evidenciais "
            "concretos (dados, estudos, indicadores, modelo, pesquisa "
            "etc.); (2) o cálculo do índice agora exclui a mesma região de "
            "capa/sumário/front-matter já excluída da distribuição "
            "temática, evitando que fragmentos de índice ou capa fossem "
            "contados como 'retórica sem evidência'. Os números e exemplos "
            "citados neste painel já refletem a versão corrigida.]"
        ),
        "metodologia_nota": (
            "Os dois planos da Bahia têm perfis muito diferentes de "
            "extensão e função. O de Jerônimo Rodrigues (incumbente, "
            "candidato à reeleição) é mais enxuto (~15,6 mil palavras) e "
            "usa boa parte do espaço para prestar contas do mandato em "
            "curso — os intróitos dos eixos 2, 3 e 4 são, na prática, "
            "capítulos de balanço de gestão, com dezenas de estatísticas "
            "oficiais (crescimento do PIB, taxa de desemprego, Índice de "
            "Gini, número de leitos hospitalares e escolas entregues, taxa "
            "de alfabetização, redução da pobreza extrema etc.), muitas "
            "delas citando explicitamente fontes como IBGE, PNAD Contínua e "
            "Instituto Jones dos Santos Neves. O de ACM Neto (desafiante, "
            "ex-prefeito de Salvador) é muito mais extenso (~75,2 mil "
            "palavras) e estruturado como um dossiê de campanha, com "
            "diagnósticos comparativos detalhados por capítulo (rankings "
            "estaduais, séries históricas, comparações com outros estados "
            "nordestinos) que citam fontes como FBSP, FJP, IPEA, DIEESE, "
            "INPI, CLP/Tendências, ABEP-TIC, entre outras, listadas "
            "integralmente em uma seção de 'Fontes e Referências' ao final "
            "do documento — um formato de dossiê investigativo bem mais "
            "denso em citação de fonte do que o observado nos planos de "
            "desafiantes de outros estados do projeto. Essa diferença de "
            "formato (balanço de gestão vs. dossiê de diagnóstico) é, em si, "
            "um achado editorial relevante para a leitura comparativa do "
            "Índice de Base Empírica entre os dois candidatos."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
        "achado_texto_compartilhado": ACHADO_TEXTO_COMPARTILHADO,
        "texto_compartilhado": TEXTO_COMPARTILHADO,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
