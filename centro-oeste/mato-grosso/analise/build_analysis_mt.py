#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Mato Grosso 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver, por
exemplo, /home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py)
e nos estados já processados do Norte (ex.: Tocantins, Rondônia):
distribuição temática exaustiva por segmentação de marcadores de seção reais
(lidos e mapeados à mão) e Índice de Base Empírica (heurística lexical/regex
idêntica à usada em todos os outros estados, reaproveitada sem alterações
para manter comparabilidade entre estados e regiões).

Caso do Mato Grosso: o governador titular, Mauro Mendes (União Brasil, 2º
mandato), é inelegível para um 3º mandato consecutivo. Em julho de 2026,
Mendes RENUNCIOU ao cargo para disputar uma vaga ao Senado, e seu vice,
Otaviano Pivetta (Republicanos), tomou posse como governador (fonte: ALMT,
"ALMT dá posse a Otaviano Pivetta como governador ... após renúncia de Mauro
Mendes", al.mt.gov.br). Pivetta é hoje o governador EM EXERCÍCIO e oficializou
candidatura à reeleição pelo Republicanos (fonte: CircuitoMT, "Otaviano
Pivetta oficializa candidatura à reeleição ao Governo de MT pelo
Republicanos") — classificado aqui como "incumbente por sucessão": não foi
originalmente eleito para o cargo máximo, mas o ocupa por sucessão do
titular (era o vice) e concorre a um mandato próprio com todas as vantagens
de incumbência.
O outro candidato analisado, Wellington Fagundes (PL), é senador da
República e, segundo pesquisas divulgadas por CNN Brasil/Real Time Big Data,
lidera as intenções de voto; mantém disputa pública e crítica aberta com
Mauro Mendes e o governo estadual (fonte: HiperNotícias, "Wellington
Fagundes nega recuo de candidatura e critica 'incoerências' do governo de
Mauro Mendes"; Só Notícias, trocas de farpas entre Mauro Mendes e Wellington
Fagundes) — classificado aqui como "desafiante".
Essa é uma leitura eleitoral, baseada em cobertura jornalística e fonte
institucional (ALMT) de 2026, e não influenciou nenhuma etapa da extração ou
classificação textual dos planos.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/centro-oeste/mato-grosso/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/centro-oeste/mato-grosso/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "otaviano-pivetta", "nome": "Otaviano Pivetta", "partido": "Republicanos",
     "categoria": "incumbente por sucessão — era vice-governador de Mauro Mendes (União "
                  "Brasil, inelegível para 3º mandato consecutivo) e assumiu o cargo de "
                  "governador em julho de 2026, após a renúncia de Mendes para disputar o "
                  "Senado; hoje governador em exercício, oficializou candidatura à "
                  "reeleição pelo Republicanos — fontes: Assembleia Legislativa de Mato "
                  "Grosso (ALMT), \"ALMT dá posse a Otaviano Pivetta como governador ... "
                  "após renúncia de Mauro Mendes\" (al.mt.gov.br); CircuitoMT, \"Otaviano "
                  "Pivetta oficializa candidatura à reeleição ao Governo de MT pelo "
                  "Republicanos\""},
    {"slug": "wellington-fagundes", "nome": "Wellington Fagundes", "partido": "PL",
     "categoria": "desafiante — senador da República, líder nas pesquisas de intenção de "
                  "voto (Real Time Big Data) e em disputa pública e crítica aberta com o "
                  "governador Mauro Mendes e o governo estadual — fontes: CNN Brasil, "
                  "\"Real Time Big Data: Wellington Fagundes lidera disputa ao governo de "
                  "MT\"; HiperNotícias, \"Wellington Fagundes nega recuo de candidatura e "
                  "critica 'incoerências' do governo de Mauro Mendes\""},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os demais estados do
# projeto (Nordeste e Norte), não adaptadas ao Mato Grosso, para preservar
# comparabilidade entre estados. Mantidas verbatim, inclusive termos
# estruturais específicos de outros estados (ex.: "maranhão").
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

# Otaviano Pivetta (Republicanos): documento em prosa, com uma Carta ao
# Cidadão, uma seção de contexto/histórico ("De onde viemos e para onde
# vamos"), uma seção de metodologia de governo ("Fazimento" e "Lucro
# Social") e uma seção de justificativa cruzada dos "5 Pilares" (que
# descreve, em prosa corrida, a função de cada um dos 5 pilares antes de
# detalhá-los) — todo esse bloco inicial é tratado como "outros": é
# metodologia/diagnóstico/rationale que atravessa múltiplos temas ao mesmo
# tempo, sem subtítulos que permitam segmentação temática segura (mesmo
# critério usado para blocos de abertura/metodologia genéricos em outros
# estados do projeto, ex. "APRESENTAÇÃO" no Ceará e "METODOLOGIA DO PLANO"
# no Tocantins).
#
# ATENÇÃO — artefato de extração: o PDF de origem foi extraído com colunas
# de página entrelaçadas linha a linha (aparentemente conteúdo de duas
# páginas adjacentes do PDF, ou duas colunas da mesma página, concatenado
# lado a lado em cada linha física do .txt, com grandes espaços em branco no
# meio da linha separando os dois blocos). Isso é visível, por exemplo, nas
# ocorrências de "Pilar 1:", "Pilar 2:" etc. e dos marcadores "N.N. Eixo de
# Entrega:", que aparecem no meio de uma linha, coladas ao final de uma
# frase de conteúdo não relacionado (da "outra coluna"). Os marcadores
# abaixo foram escolhidos e verificados (via grep) como literais e únicos no
# arquivo, e a segmentação por posição de caractere funciona corretamente
# para determinar o INÍCIO de cada seção temática — mas o texto imediatamente
# anterior a um marcador pode conter cauda de conteúdo de uma coluna vizinha
# não relacionada ao tema seguinte, o que pode adicionar um pequeno ruído às
# fronteiras exatas dos segmentos (mesmo tipo de limitação já documentada no
# Ceará para o Eixo 01 de Ciro Gomes, aqui mais frequente). Não corrigimos a
# extração para manter a metodologia idêntica entre estados; ver nota de
# metodologia.
#
# A partir de "1.1. Eixo de Entrega", o plano é dividido em 5 "Pilares"
# numerados, cada um com 1 a 4 "Eixos de Entrega" (N.N), cada eixo com texto
# de diagnóstico/track-record seguido de uma lista de "Propostas". Como cada
# eixo já tem um tema único e claro no próprio título (ex.: "O estado onde a
# educação forma cidadãos"), cada eixo (diagnóstico + propostas) foi
# classificado em bloco único pelo tema anunciado.
# Pilar 1 (Saúde Próxima, Educação Libertadora, Apoio Social e
# Desenvolvimento Humano/Habitação): eixo 1.1 = educação; 1.2 = saúde; 1.3 =
# esporte e cultura = assistencia_social (precedente do projeto); 1.4 =
# vulneráveis/assistência social = assistencia_social; 1.5 = habitação =
# infraestrutura (precedente do projeto: habitação/moradia = infraestrutura,
# mesmo quando emoldurada como "apoio social").
# Pilar 2 (Segurança Firme, Tolerância Zero e Ordem Pública): eixos 2.1 e 2.2
# = seguranca (policiamento e sistema prisional).
# Pilar 3 (Proteção à Mulher, Apoio à Maternidade e Autonomia Financeira):
# eixo 3.1 = assistencia_social — não há eixo temático dedicado a políticas
# de gênero na taxonomia de 9 temas do projeto; segue o mesmo critério usado
# em outros estados para pautas de proteção/autonomia de grupos específicos.
# Pilar 4 (Produção Sustentável, Industrialização, Emprego e Logística
# Estruturante): eixo 4.1 (produção sustentável, licenciamento ambiental,
# combate a incêndios/desmatamento) = meio_ambiente; eixo 4.2 (emprego,
# qualificação profissional, agricultura familiar, ciência/inovação
# vinculada ao agronegócio) = economia; eixo 4.3 (industrialização,
# incentivos fiscais, PRODEIC, etanol de milho) = economia; eixo 4.4
# (ferrovia, rodovias, BR-163, pontes) = infraestrutura.
# Pilar 5 (O Estado Parceiro: Gestão Eficiente, Valorização do Servidor,
# Desburocratização e Pacto Municipalista): eixo 5.1 (desburocratização,
# ambiente de negócios, governo digital) = gestao_publica; eixo 5.2
# (responsabilidade fiscal, tributação, compras públicas) = gestao_publica;
# eixo 5.3 (valorização do servidor público) = gestao_publica; eixo 5.4
# (parceria com municípios: pavimentação urbana, iluminação, saneamento,
# conectividade) = infraestrutura, por ser predominantemente sobre obras e
# serviços de infraestrutura municipal, mesmo emoldurado como
# "municipalismo" (mesmo critério usado no Ceará para "GESTÃO ESTRATÉGICA,
# GOVERNANÇA INTERFEDERA-" vs. seções de infraestrutura específicas — aqui a
# ênfase do próprio texto do eixo 5.4 é overwhelmingly de obras/serviços de
# infraestrutura urbana, o que o distingue do 5.1/5.2/5.3, que são
# genuinamente sobre a máquina administrativa em si).
# O encerramento ("5. Compromisso de Transparência e Prestação de Contas")
# = gestao_publica (transparência/prestação de contas, fechamento do plano).
MARCADORES_PIVETTA = [
    ("Carta ao Cidadão Matogrossense", "outros"),
    ("De onde viemos e para onde vamos", "outros"),
    ("Metodologia e visão de futuro: gestão por", "outros"),
    ("Eixos estratégicos (5 pilares do governo)", "outros"),
    ("1.1. Eixo de Entrega: O estado onde a educação forma cidadãos.", "educacao"),
    ("1.2. Eixo de Entrega: O Estado onde a saúde pública funciona e", "saude"),
    ("1.3. Eixo de Entrega: O Estado onde o esporte e a cultura formam", "assistencia_social"),
    ("1.4. Eixo de Entrega: O Estado onde os vulneráveis encontram", "assistencia_social"),
    ("1.5. O Estado onde a moradia digna e o título do seu imóvel são uma", "infraestrutura"),
    ("2.1. Eixo de Entrega: O Estado onde o cidadão tem paz e o crime é", "seguranca"),
    ("2.2. Eixo de Entrega: O Estado onde o presídio não é", "seguranca"),
    ("3.1. Eixo de Entrega: O Estado onde as mulheres são respeitadas", "assistencia_social"),
    ("4.1. Eixo de Entrega: O Estado onde se produz de forma sustentável", "meio_ambiente"),
    ("4.2. Eixo de Entrega: O estado onde as pessoas encontram", "economia"),
    ("4.3. Eixo de Entrega: O Estado que transforma a produção do", "economia"),
    ("4.4. Eixo de Entrega: O Estado que conecta regiões por meio da", "infraestrutura"),
    ("5.1. Eixo de Entrega: O Estado que não atrapalha e que é parceiro", "gestao_publica"),
    ("5.2. Eixo de Entrega: O Estado onde o governo respeita o dinheiro", "gestao_publica"),
    ("5.3. Eixo de Entrega: O Estado onde os funcionários públicos são", "gestao_publica"),
    ("5.4. Eixo de Entrega: O Estado parceiro dos municípios para", "infraestrutura"),
    ("5. Compromisso de Transparência e Prestação de Contas", "gestao_publica"),
]

# Wellington Fagundes (PL): documento com estrutura de manual de governo,
# muito bem organizado — Carta ao Cidadão, um ÍNDICE completo (que repete os
# títulos dos 16 capítulos e de suas subseções, com número de página),
# seguido por 16 capítulos temáticos claros, cada um com um parágrafo de
# diagnóstico/compromisso e uma lista de subseções com propostas. Documento
# extraído em coluna única, em ordem de leitura correta (sem o artefato de
# colunas entrelaçadas visto no plano de Pivetta).
#
# Protegido contra o ÍNDICE (ver "Mesmo padrão de índice duplicado" já usado
# em outros estados do projeto) pela lógica padrão de cursor_inicial: como o
# primeiro marcador escolhido (a frase de abertura do capítulo 1, que NÃO
# aparece no índice, apenas o título do capítulo aparece lá) já é única no
# documento, a segmentação começa a partir da posição 0 (todo o front
# matter — Carta ao Cidadão + Índice — cai em "outros" antes do primeiro
# marcador).
#
# Os 16 capítulos (título entre parênteses) e a classificação temática
# usada, cada um mantido como bloco único (capítulo inteiro, incluindo suas
# subseções com marcador "•"), pois cada capítulo já tem um tema único e
# claro anunciado no próprio título e confirmado pelo conteúdo:
#   GESTÃO PÚBLICA E GOVERNANÇA = gestao_publica
#   PLANEJAMENTO, ORÇAMENTO E GESTÃO = gestao_publica
#   FAZENDA = gestao_publica (política fiscal/tributária)
#   SEGURANÇA PÚBLICA E JUSTIÇA = seguranca
#   PROTEÇÃO À MULHER = assistencia_social (sem eixo dedicado a políticas de
#     gênero na taxonomia de 9 temas do projeto; mesmo critério do plano de
#     Pivetta e de outros estados)
#   SAÚDE = saude
#   EDUCAÇÃO = educacao
#   ESPORTE E LAZER = assistencia_social (precedente do projeto)
#   INFRAESTRUTURA = infraestrutura (rodovias, ferrovias, hidrovias,
#     aeroportos, energia, conectividade)
#   CIÊNCIA E TECNOLOGIA = economia — não há eixo dedicado a C&T na
#     taxonomia; o capítulo é emoldurado como "Conhecimento que Gera
#     Oportunidades e Desenvolvimento" e mistura inovação empresarial,
#     competitividade e governança digital; seguimos aqui o precedente do
#     Tocantins (Professora Dorinha), que também agrupou C&T ao
#     desenvolvimento econômico, e não ao capítulo de Educação (que já é
#     um capítulo autônomo e distinto neste documento).
#   ECONOMIA = economia
#   TURISMO = economia (precedente: turismo tratado como vocação econômica,
#     mesmo critério do Ceará)
#   CULTURA = assistencia_social (precedente do projeto)
#   CIDADES E DESENVOLVIMENTO URBANO = infraestrutura (planejamento urbano,
#     habitação, saneamento, mobilidade — predominantemente obras/serviços
#     de infraestrutura municipal)
#   BEM-ESTAR SOCIAL = assistencia_social
#   MEIO AMBIENTE = meio_ambiente
MARCADORES_WELLINGTON = [
    ("Mato Grosso precisa de uma administração pública que transforme orçamento, estrutura e tecnologia", "gestao_publica"),
    ("O planejamento estadual precisa deixar de ser uma etapa formal e assumir o papel de orientar decisões,", "gestao_publica"),
    ("Uma política fiscal competente e responsável deve proteger o equilíbrio das contas públicas", "gestao_publica"),
    ("Mato Grosso enfrenta o avanço das facções, crimes de fronteira, violência urbana e rural", "seguranca"),
    ("Mato Grosso convive com índices inaceitáveis de violência contra a mulher e feminicídio.", "assistencia_social"),
    ("A saúde pública precisa funcionar para o paciente, com atendimento oportuno, cuidado humano", "saude"),
    ("A educação é ambiente de formação e o caminho mais seguro para ampliar oportunidades,", "educacao"),
    ("O esporte e o lazer são instrumentos de saúde, convivência, disciplina e desenvolvimento humano.", "assistencia_social"),
    ("Mato Grosso produz em grande escala, mas ainda enfrenta distâncias, custos logísticos e desigualdades", "infraestrutura"),
    ("Ciência, tecnologia e inovação são essenciais para gerar conhecimento, aumentar as oportunidades,", "economia"),
    ("Mato Grosso possui uma das economias mais dinâmicas do país, mas precisa transformar sua indústria primária", "economia"),
    ("Mato Grosso reúne Pantanal, Cerrado, Amazônia, rios, cultura, gastronomia e paisagens capazes de consolidar", "economia"),
    ("A cultura de Mato Grosso expressa a história, a diversidade regional e o modo de vida de seu povo.", "assistencia_social"),
    ("Mato Grosso precisa transformar crescimento econômico e populacional em cidades mais organizadas,", "infraestrutura"),
    ("O desenvolvimento de Mato Grosso precisa alcançar a vida concreta das famílias. A política social deve", "assistencia_social"),
    ("Mato Grosso precisa conciliar produção, conservação ambiental e segurança jurídica com equilíbrio e eficiência.", "meio_ambiente"),
]

MARCADORES = {
    "otaviano-pivetta": MARCADORES_PIVETTA,
    "wellington-fagundes": MARCADORES_WELLINGTON,
}

# Ponto de partida da análise de Base Empírica (Tarefa 2) para cada
# candidato: nenhum dos dois planos do Mato Grosso tem um sumário/índice
# longo o bastante em texto corrido (o de Wellington Fagundes é uma lista
# curta de títulos e números de página, não frases completas) que pudesse
# distorcer a extração de frases, então a análise roda sobre o corpo inteiro
# do documento (posição 0) para os dois candidatos.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "otaviano-pivetta": 0,
    "wellington-fagundes": 0,
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
        arquivo = slug.replace("-", "_") + ".txt"
        raw_text = (PLANOS_DIR / arquivo).read_text(encoding="utf-8")
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
            "Grosso' e 'mato-grossense(s)' NÃO são filtrados e aparecem "
            "naturalmente entre os termos mais frequentes de ambos os "
            "planos). Mostra os termos mais repetidos por candidato e o "
            "agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de pilar/eixo/capítulo, "
            "ou, quando necessário, o início verbatim de uma frase de "
            "abertura de capítulo). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando um trecho do documento "
            "original já reunia explicitamente múltiplos temas de forma "
            "indivisível (ex.: a seção de justificativa cruzada dos '5 "
            "pilares' do plano de Otaviano Pivetta, ou capítulos de "
            "diagnóstico geral), o segmento foi classificado como 'outros'."
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
            "ajuste específico para o Mato Grosso, para manter "
            "comparabilidade entre estados e entre regiões."
        ),
        "metodologia_nota": (
            "O Mato Grosso tem uma particularidade sucessória relevante: o "
            "governador titular, Mauro Mendes (União Brasil, 2º mandato), é "
            "inelegível para um 3º mandato consecutivo e, em julho de 2026, "
            "renunciou ao cargo para disputar uma vaga ao Senado. Seu vice, "
            "Otaviano Pivetta (Republicanos), tomou posse como governador "
            "(fonte: Assembleia Legislativa de Mato Grosso — ALMT, 'ALMT dá "
            "posse a Otaviano Pivetta como governador ... após renúncia de "
            "Mauro Mendes', al.mt.gov.br) e hoje concorre à reeleição como "
            "governador em exercício, oficializada pelo Republicanos "
            "(fonte: CircuitoMT, 'Otaviano Pivetta oficializa candidatura à "
            "reeleição ao Governo de MT pelo Republicanos') — classificado "
            "neste projeto como 'incumbente por sucessão'. O outro "
            "candidato analisado, Wellington Fagundes (PL), é senador da "
            "República e lidera pesquisas de intenção de voto segundo "
            "levantamento Real Time Big Data divulgado pela CNN Brasil, "
            "mantendo disputa pública e crítica aberta com Mauro Mendes e o "
            "governo estadual (fonte: HiperNotícias, 'Wellington Fagundes "
            "nega recuo de candidatura e critica incoerências do governo de "
            "Mauro Mendes') — classificado como 'desafiante'. Essa é uma "
            "leitura eleitoral, baseada em fonte institucional (ALMT) e "
            "cobertura jornalística de 2026, e não influenciou nenhuma etapa "
            "da extração ou classificação textual dos planos. "
            "Ressalva sobre a extração do plano de Otaviano Pivetta: o PDF "
            "de origem foi extraído com um artefato de colunas "
            "entrelaçadas — cada linha física do .txt parece concatenar, "
            "lado a lado com grandes espaços em branco no meio, conteúdo de "
            "duas colunas/páginas adjacentes do documento original. Isso é "
            "visível, por exemplo, nas ocorrências dos marcadores 'Pilar N:' "
            "e 'N.N. Eixo de Entrega:', que aparecem coladas ao final de "
            "frases de conteúdo não relacionado (da 'coluna vizinha'). Os "
            "marcadores de segmentação temática foram escolhidos e "
            "verificados como literais e únicos no arquivo (via busca de "
            "texto exato), e a segmentação por posição de caractere segue "
            "corretamente a ordem de aparição de cada marcador no arquivo — "
            "mas o texto imediatamente anterior a cada marcador pode conter "
            "cauda de conteúdo de uma coluna vizinha não relacionada ao tema "
            "seguinte, o que pode adicionar um pequeno ruído às fronteiras "
            "exatas dos segmentos (mesmo tipo de limitação já documentada "
            "no Ceará, para o Eixo 01 do plano de Ciro Gomes, aqui mais "
            "frequente ao longo de todo o documento). Não corrigimos a "
            "extração para manter a metodologia idêntica entre estados; o "
            "efeito é sobre a precisão fina das fronteiras de segmento, não "
            "sobre a contagem total de palavras do documento (que opera "
            "sobre o texto inteiro, independente de ordem de colunas) nem "
            "sobre a detecção de frases para o Índice de Base Empírica "
            "(que também opera sobre o texto inteiro). O plano de Wellington "
            "Fagundes não apresenta esse artefato — foi extraído em coluna "
            "única e ordem de leitura correta — e tem um ÍNDICE inicial que "
            "lista os 16 capítulos e suas subseções com número de página; "
            "como o primeiro marcador de segmentação usado para esse plano "
            "é a frase de abertura do primeiro capítulo (que não consta do "
            "índice, apenas o título do capítulo), a segmentação já parte "
            "corretamente do corpo real do documento, sem necessidade de "
            "pular uma 2ª ocorrência. Nenhum dos dois planos apresentou "
            "problemas de ligadura tipográfica quebrada (ex.: 'fi'/'fl'/'ti' "
            "convertidos em espaço), diferentemente do que foi observado em "
            "outros estados do projeto. "
            "Decisões de classificação não óbvias (proteção à mulher e "
            "cultura/esporte = assistência social por ausência de eixo "
            "dedicado na taxonomia de 9 temas; habitação e obras urbanas "
            "municipais = infraestrutura; ciência e tecnologia agrupada com "
            "economia, e não com educação, no plano de Wellington Fagundes, "
            "seguindo o precedente do Tocantins) estão documentadas linha a "
            "linha nos comentários do script de análise."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
