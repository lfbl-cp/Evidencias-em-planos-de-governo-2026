#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Sergipe 2026.

Réplica exata da metodologia usada no Maranhão/Piauí/Ceará/Pernambuco: distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica,
reaproveitada sem alterações, para manter comparabilidade entre estados).

Tokenização, stopwords, TEMAS, distribuicao_tematica_exaustiva,
base_empirica_analise, JARGAO_TERMOS, NUM_ANY, DIAG_KEYWORDS_RE, EFEITO_RE,
EVIDENCIA_RE, split_sentences, looks_like_header — todos idênticos ao
Maranhão/Ceará, sem nenhum ajuste específico para Sergipe. Apenas MARCADORES_*
(a segmentação temática, que depende da estrutura real de cada plano) foi
escrita do zero para os dois planos de Sergipe.

IMPORTANTE — EVIDENCIA_RE: este regex NÃO inclui "plano lula" nem "plano
nacional" como gatilhos genéricos do pilar C (mantém apenas a referência
específica "plano nacional de logística", que é uma citação legítima a uma
política federal concreta, não um gatilho genérico). Isso é especialmente
relevante em Sergipe porque Fábio Mitidieri é o governador em exercício e
menciona a parceria com o Governo Federal / presidente Lula (PAC, Petrobras)
algumas vezes — essas menções não devem inflar artificialmente o pilar C.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/sergipe/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/sergipe/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "fabio-mitidieri", "nome": "Fábio Mitidieri", "partido": "PSD",
     "categoria": "incumbente pleno (governador em exercício, 1º mandato, concorrendo à reeleição)"},
    {"slug": "valmir-de-francisquinho", "nome": "Valmir de Francisquinho", "partido": "Republicanos",
     "categoria": "desafiante (ex-prefeito de Itabaiana)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Maranhão/Paraíba/Ceará/Pernambuco.
# Mantidas propositalmente SEM ajuste (inclusive termos estruturais de outro
# estado, como "maranhão"/"maranhense") para preservar comparabilidade
# metodológica entre estados — mesmo critério já documentado no Ceará.
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

# Fábio Mitidieri (PSD, incumbente): documento com SUMÁRIO no início repetindo
# (com pontos de preenchimento e número de página) os 26 títulos de seção
# usados como marcador — mesmo problema de duplicação já visto no Maranhão
# (Felipe Camarão) e no Ceará (Elmano de Freitas). Aqui a solução foi ainda
# mais direta: o primeiro marcador escolhido, "PERSPECTIVAS PARA O NOVO CICLO"
# (abertura do capítulo de diagnóstico econômico, logo após o SUMÁRIO), NÃO
# aparece no SUMÁRIO — só existe uma vez no documento, e sua única ocorrência
# já fica posicionada depois do SUMÁRIO. Como a busca de cada marcador
# seguinte começa a partir do fim do marcador anterior (cursor sempre
# avançando), a partir desse ponto os 26 títulos de seção (cada um com 2
# ocorrências: 1x no SUMÁRIO, 1x no corpo) resolvem automaticamente para a
# ocorrência do CORPO, porque o cursor já passou pelo SUMÁRIO. Verificado
# programaticamente: todas as 26 posições ficam em ordem estritamente
# crescente. Não foi necessário usar o parâmetro cursor_inicial (a proteção
# genérica contra duplicação de sumário, herdada do Maranhão, continua no
# código abaixo por segurança/paridade de método, mas seu efeito é nulo aqui
# porque o primeiro marcador não se repete).
#
# Decisões de classificação não óbvias:
#  - "PERSPECTIVAS PARA O NOVO CICLO ECONÔMICO DE SERGIPE": capítulo de
#    diagnóstico econômico (~1.500 palavras sobre PIB, emprego, retomada dos
#    investimentos da Petrobras, Fafen, transição energética) que antecede os
#    55 compromissos numerados. Como no precedente do Maranhão (introdução
#    diagnóstica de Felipe Camarão) e do Ceará ("CONTEXTOS E AVANÇOS" de
#    Elmano), um capítulo diagnóstico coerente e substantivo sobre um único
#    tema NÃO é tratado como "outros" genérico — foi classificado como
#    "economia", o tema que efetivamente organiza todo o capítulo.
#  - "CIÊNCIA, TECNOLOGIA E INOVAÇÃO" (item 5-6, sobre ecossistema de
#    inovação, PPPs em CT&I, Fapitec, startups, banco de projetos, P&D):
#    classificada como "economia" (ecossistema de inovação/negócios),
#    seguindo o precedente de Pernambuco (Raquel Lyra) para o mesmo tipo de
#    conteúdo — diferente do precedente do Ceará, que classificou C&T como
#    "educacao" por estar embutida dentro do objetivo de Educação; aqui a
#    seção de Sergipe é autônoma e seu conteúdo é sobre ecossistema
#    empresarial de inovação, não sobre currículo/ensino.
#  - "CULTURA E SERGIPANIDADE", "ESPORTE E LAZER", "JUVENTUDE", "MULHERES",
#    "PRIMEIRA INFÂNCIA", "PROTEÇÃO ANIMAL", "DIREITOS HUMANOS",
#    "SEGURANÇA ALIMENTAR E NUTRICIONAL": "assistencia_social", seguindo os
#    precedentes já consolidados nos demais estados do projeto para essas
#    mesmas áreas temáticas.
#  - "HABITAÇÃO" e "SEGURANÇA HÍDRICA E SANEAMENTO": "infraestrutura",
#    seguindo o precedente de todos os estados anteriores (habitação,
#    saneamento e segurança hídrica = infraestrutura).
#  - "TURISMO": "economia", seguindo o precedente consolidado do projeto.
#  - "SISTEMA DE JUSTIÇA" (item 51: sistema prisional, Polícia Penal, Plano
#    Pena Justa, reincidência, e — em menor medida — Procon/defesa do
#    consumidor): classificada como "seguranca". A taxonomia de 9 temas deste
#    projeto não tem uma categoria dedicada a "justiça"; o conteúdo do item é
#    predominantemente sobre sistema prisional e segurança pública em sentido
#    amplo, com o trecho de Procon sendo uma fração menor do texto do item.
#  - "TRANSPARÊNCIA E CONTROLE SOCIAL" e "VALORIZAÇÃO DE SERVIDORES(AS)
#    PÚBLICOS E PREVIDÊNCIA": "gestao_publica".
MARCADORES_MITIDIERI = [
    ("PERSPECTIVAS PARA O NOVO CICLO", "economia"),
    ("AGRICULTURA, PECUÁRIA E PESCA", "economia"),
    ("ASSISTÊNCIA SOCIAL E COMBATE À POBREZA", "assistencia_social"),
    ("CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "economia"),
    ("CULTURA E SERGIPANIDADE", "assistencia_social"),
    ("DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("DIREITOS HUMANOS", "assistencia_social"),
    ("EDUCAÇÃO", "educacao"),
    ("EMPREGO, RENDA E EMPREENDEDORISMO", "economia"),
    ("ESPORTE E LAZER", "assistencia_social"),
    ("GOVERNANÇA ESTRATÉGICA", "gestao_publica"),
    ("HABITAÇÃO", "infraestrutura"),
    ("INFRAESTRUTURA", "infraestrutura"),
    ("JUVENTUDE", "assistencia_social"),
    ("MEIO AMBIENTE, SUSTENTABILIDADE E CLIMA", "meio_ambiente"),
    ("MULHERES", "assistencia_social"),
    ("PRIMEIRA INFÂNCIA", "assistencia_social"),
    ("PROTEÇÃO ANIMAL", "assistencia_social"),
    ("SAÚDE", "saude"),
    ("SEGURANÇA ALIMENTAR E NUTRICIONAL", "assistencia_social"),
    ("SEGURANÇA HÍDRICA E SANEAMENTO", "infraestrutura"),
    ("SEGURANÇA PÚBLICA", "seguranca"),
    ("SISTEMA DE JUSTIÇA", "seguranca"),
    ("TRANSPARÊNCIA E CONTROLE SOCIAL", "gestao_publica"),
    ("TURISMO", "economia"),
    ("VALORIZAÇÃO DE SERVIDORES(AS)", "gestao_publica"),
]

# Valmir de Francisquinho (Republicanos, desafiante): documento sem SUMÁRIO
# com títulos repetidos (não há duplicação de marcador a resolver). Estrutura
# real: biografia + 2 mensagens de abertura (Valmir e a vice Priscila
# Felizola) + "1. INTRODUÇÃO" + "2 – PANORAMA DO ESTADO DE SERGIPE"
# (diagnóstico socioeconômico genérico, cruzando geografia, hidrografia,
# demografia, economia, minérios e turismo em um único texto corrido sem
# subtítulos — ao contrário do capítulo econômico de Mitidieri, aqui o
# conteúdo GENUINAMENTE mistura múltiplos temas sem predominância clara de
# um só, por isso, junto com "1. INTRODUÇÃO", foi tratado como front matter
# genérico ("outros"), e não recebeu marcador próprio) + "3. DIRETRIZES
# ESTRATÉGICAS PARA O DESENVOLVIMENTO DE SERGIPE" (parágrafo de abertura,
# também "outros") + as 10 Diretrizes Estratégicas propriamente ditas
# (3.1 a 3.10) + "4. CONSIDERAÇÕES FINAIS" (encerramento genérico, "outros").
#
# Diretriz 3.6 ("Infraestrutura, Desenvolvimento Regional e Transição
# Energética") é, de longe, a mais heterogênea do documento: sob um título
# guarda-chuva de infraestrutura, ela reúne 19 "Compromissos de Governo"
# numerados com subtítulo próprio, cobrindo também desenvolvimento industrial/
# mineral, turismo, transição energética, meio ambiente/conservação, recursos
# hídricos, saneamento, mudanças climáticas e educação ambiental — temas que,
# na taxonomia de 9 áreas deste projeto, pertencem a "economia" ou
# "meio_ambiente", não a "infraestrutura". Como cada um dos 19 itens tem
# subtítulo próprio e identificável, a seção foi segmentada item a item (o
# mesmo critério de granularidade fina já usado no Maranhão para blocos
# multitemáticos com subtítulos), em vez de classificar o bloco inteiro como
# "infraestrutura" só porque esse é o tema do título da diretriz.
#
# A Diretriz 3.10 ("Cultura, Turismo e Identidade Sergipana") tem o mesmo
# problema em menor escala: mistura deliberadamente cultura (assistencia_
# social, por precedente) e turismo (economia, por precedente) sob um único
# título, mas também tem "Eixos" numerados com subtítulo próprio (Eixo 1 a
# Eixo 5), permitindo a mesma segmentação item a item.
#
# Decisões de classificação não óbvias dentro da Diretriz 3.6:
#  - Itens 1-5 e 8-10 (planejamento territorial, logística, rodovias,
#    mobilidade metropolitana, infraestrutura urbana, infraestrutura hídrica/
#    produção rural, mobilidade/segurança viária, infraestrutura digital):
#    "infraestrutura".
#  - Item 6 ("Desenvolvimento Logístico, Industrial e Mineral") e item 7
#    ("Turismo e Desenvolvimento Territorial"): "economia" — desenvolvimento
#    industrial/mineral e turismo seguem o precedente consolidado do projeto
#    (turismo = economia), mesmo aparecendo dentro da diretriz "Infra-
#    estrutura...".
#  - Item 11 ("Desenvolvimento Econômico e Ambiente de Negócios") e item 12
#    ("Transição Energética"): "economia" — a transição energética é
#    apresentada no documento como oportunidade de atração de investimento
#    (energia solar/eólica/hidrogênio, eletromobilidade, incentivo fiscal
#    para veículos elétricos), o mesmo enquadramento econômico usado por
#    Mitidieri em "Capital da Energia" (DESENVOLVIMENTO ECONÔMICO ->
#    economia).
#  - Itens 13, 16 e 18 ("Meio Ambiente e Conservação", "Mudanças Climáticas",
#    "Educação Ambiental e Inovação"): "meio_ambiente".
#  - Itens 14-15 ("Recursos Hídricos e Segurança Hídrica", "Saneamento e
#    Economia Circular"): "infraestrutura", seguindo o precedente do projeto
#    (segurança hídrica e saneamento = infraestrutura, inclusive no outro
#    plano de Sergipe, o de Mitidieri).
#  - Item 17 ("Turismo Sustentável e Patrimônio Natural"): "economia"
#    (precedente turismo = economia), apesar do nome incluir "Patrimônio
#    Natural" — o conteúdo do item é sobre concessão de uso público, ecoturismo
#    e desenvolvimento regional via turismo, não sobre conservação ambiental
#    em si (que já tem itens próprios, 13 e 16).
#  - Item 19 ("Qualificação Profissional para a Nova Economia"): "economia".
#  - "Projetos Estruturantes Prioritários" (lista final de obras: BR-101,
#    BR-235, SE-240, corredor ferroviário, corredor logístico mineral etc.,
#    seguida do parágrafo de encerramento "Nosso Compromisso" da diretriz):
#    "infraestrutura" — a lista é dominada por obras de transporte/logística.
#
# Diretriz 3.7 ("Agricultura, Pecuária e Segurança Alimentar"): tem 6 "Eixos
# Estruturantes" descritos em prosa (I a VI, incluindo segurança alimentar e
# segurança hídrica), mas os "Programas, Ações e Compromissos" que seguem são
# uma ÚNICA lista de marcadores (bullets) não agrupada por eixo — ao
# contrário da Diretriz 3.6, aqui não há como segmentar por eixo com
# segurança, então a diretriz inteira foi classificada como "economia"
# (agricultura/pecuária/pesca, seguindo o precedente do projeto), mesmo
# critério do Maranhão para blocos indivisíveis: manter o tema dominante e
# anunciado pelo próprio título da seção, em vez de "outros".
#
# Diretriz 3.8 ("Mulheres, Juventude, Diversidade e Inclusão Social"): tem 4
# "Subeixos" (Mulheres; Diversidade/Direitos Humanos; Infância/Família;
# Juventude) — todos mapeiam para o mesmo tema ("assistencia_social") pelos
# precedentes já consolidados do projeto, por isso não há necessidade de
# segmentar item a item (não haveria diferença no resultado).
MARCADORES_VALMIR = [
    ("3.1 Gente: Desafios Econômicos, Geração de Emprego e Inserção Social", "economia"),
    ("3.2 Saúde Humanizada e Eficiente", "saude"),
    ("3.3 Educação para o Futuro e Inovação Tecnológica", "educacao"),
    ("3.3.1 Inovação Tecnológica", "educacao"),
    ("3.4 Segurança Pública e Cultura de Paz", "seguranca"),
    ("3.5 Responsabilidade Fiscal e Modernização da Gestão Pública", "gestao_publica"),
    ("3.6 Infraestrutura, Desenvolvimento Regional e Transição Energética", "infraestrutura"),
    ("1. Planejamento Territorial e Desenvolvimento Regional", "infraestrutura"),
    ("2. Logística e Infraestrutura Estratégica", "infraestrutura"),
    ("3. Rodovias e Mobilidade Regional", "infraestrutura"),
    ("4. Mobilidade Metropolitana e Transporte Público", "infraestrutura"),
    ("5. Infraestrutura Urbana e Qualidade de Vida", "infraestrutura"),
    ("6. Desenvolvimento Logístico, Industrial e Mineral", "economia"),
    ("7. Turismo e Desenvolvimento Territorial", "economia"),
    ("8. Infraestrutura Hídrica e Produção Rural", "infraestrutura"),
    ("9. Mobilidade Inteligente e Segurança Viária", "infraestrutura"),
    ("10. Infraestrutura Digital e Governo Inteligente", "infraestrutura"),
    ("11. Desenvolvimento Econômico e Ambiente de Negócios", "economia"),
    ("12. Transição Energética", "economia"),
    ("13. Meio Ambiente e Conservação", "meio_ambiente"),
    ("14. Recursos Hídricos e Segurança Hídrica", "infraestrutura"),
    ("15. Saneamento e Economia Circular", "infraestrutura"),
    ("16. Mudanças Climáticas", "meio_ambiente"),
    ("17. Turismo Sustentável e Patrimônio Natural", "economia"),
    ("18. Educação Ambiental e Inovação", "meio_ambiente"),
    ("19. Qualificação Profissional para a Nova Economia", "economia"),
    ("Projetos Estruturantes Prioritários", "infraestrutura"),
    ("3.7 Agricultura, Pecuária e Segurança Alimentar", "economia"),
    ("3.8 Mulheres, Juventude, Diversidade e Inclusão Social", "assistencia_social"),
    ("3.9 Sergipe Empreendedor e Inclusivo", "economia"),
    ("3.10 Cultura, Turismo e Identidade Sergipana", "outros"),
    ("Eixo 1 - Desenvolvimento do Turismo", "economia"),
    ("Eixo 2 - Cultura, Patrimônio e Identidade Sergipana", "assistencia_social"),
    ("Eixo 3 - Economia Criativa e Empreendedorismo Cultural", "assistencia_social"),
    ("Eixo 4 - Qualificação, Governança e Inovação", "economia"),
    ("Eixo 5 - Turismo Regional, Sustentabilidade e Inclusão", "economia"),
    ("4. CONSIDERAÇÕES FINAIS", "outros"),
]

MARCADORES = {
    "fabio-mitidieri": MARCADORES_MITIDIERI,
    "valmir-de-francisquinho": MARCADORES_VALMIR,
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
# TAREFA 3 — Nuvem de palavras (mesmos parâmetros usados no Maranhão/Ceará/
# Pernambuco/Piauí: width=800, height=500, background_color=None, mode="RGBA",
# colormap="viridis". max_words=120, não 20 — mantido em paridade com todos os
# outros estados já publicados neste projeto, para preservar comparabilidade
# visual entre os painéis dos 9 estados.)
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
    # preserva campos publicados fora do escopo deste script (ex.:
    # achado_texto_compartilhado/texto_compartilhado, escritos por um
    # script separado de deteccao de texto compartilhado; lista_jargao_
    # utilizada, metodologia_frequencia_palavras) -- corrige um defeito
    # em que rerodar este script apagava esses campos silenciosamente
    # (achado em 25/08/2026 durante o rollout do indice de cobertura).
    analise_anterior_path = ANALISE_DIR / "analise.json"
    analise_anterior = (
        json.loads(analise_anterior_path.read_text(encoding="utf-8"))
        if analise_anterior_path.exists() else {}
    )
    resultado_candidatos = []
    agregado_counter = Counter()

    for c in CANDIDATOS:
        slug = c["slug"]
        raw_text = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Proteção contra sumário/índice duplicando o 1º marcador (mesma
        # lógica do Maranhão/Ceará): se o 1º marcador aparecer mais de uma
        # vez, pula para a 2ª ocorrência. Em Sergipe isso não chega a ser
        # necessário para nenhum dos dois candidatos (ver notas acima de cada
        # lista de marcadores), mas o código é mantido por segurança e
        # paridade de método entre estados.
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

        print(f"{c['nome']:<26} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
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
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Sergipe' "
            "e 'sergipano/sergipana' NÃO são filtrados e podem aparecer nos "
            "termos mais frequentes). Mostra os termos mais repetidos por "
            "candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de capítulo/diretriz/"
            "eixo/item, verbatim). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando uma seção do documento "
            "original já reunia explicitamente múltiplos temas de forma "
            "heterogênea sob um único título (ex.: a Diretriz 'Infraestrutura, "
            "Desenvolvimento Regional e Transição Energética' de Valmir de "
            "Francisquinho, que reúne 19 itens numerados cobrindo também "
            "turismo, meio ambiente e transição energética), o segmento foi "
            "classificado item a item sempre que os itens individuais eram "
            "identificáveis por subtítulo próprio, ou como 'outros' quando "
            "não era possível separar com segurança."
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
            "Heurística idêntica à usada nas análises da Paraíba, do "
            "Maranhão, do Piauí, do Ceará e de Pernambuco, sem nenhum ajuste "
            "específico para Sergipe, para manter comparabilidade entre "
            "estados. O regex do pilar (c) NÃO trata menção genérica a "
            "'plano Lula' ou 'plano nacional' como evidência — apenas "
            "referências específicas e verificáveis (IBGE, IPEA, Datasus, "
            "OMS, Banco Mundial, BNDES, 'plano nacional de logística', "
            "citação de lei etc.) contam para o pilar (c). Isso é "
            "particularmente relevante em Sergipe: Fábio Mitidieri, "
            "governador em exercício, menciona parceria com o Governo "
            "Federal e o presidente Lula (PAC, Petrobras) na abertura "
            "diagnóstica do plano — essas menções políticas não inflam o "
            "índice, pois não são gatilhos do pilar (c)."
        ),
        "metodologia_nota": (
            "Os dois planos de Sergipe têm tamanhos e perfis de redação muito "
            "diferentes: o de Fábio Mitidieri (~7,9 mil palavras) é um "
            "documento enxuto de 55 compromissos numerados, um por seção "
            "temática, com um capítulo diagnóstico econômico introdutório; o "
            "de Valmir de Francisquinho (~17,9 mil palavras) é mais de duas "
            "vezes maior, estruturado em 10 'Diretrizes Estratégicas' "
            "detalhadas, cada uma com diagnóstico, objetivos estratégicos e "
            "dezenas de compromissos — inclusive uma diretriz de "
            "infraestrutura com 19 itens numerados que cruza deliberadamente "
            "vários temas (turismo, meio ambiente, transição energética) sob "
            "um único título guarda-chuva, exigindo segmentação item a item "
            "(ver comentários no código-fonte, build_analysis_se.py, para o "
            "detalhe de cada decisão). "
            "No plano de Fábio Mitidieri, o SUMÁRIO no início do documento "
            "repete os 26 títulos de seção usados como marcador — mesmo "
            "problema de duplicação já identificado no Maranhão (Felipe "
            "Camarão) e no Ceará (Elmano de Freitas). Neste caso, porém, o "
            "primeiro marcador escolhido ('PERSPECTIVAS PARA O NOVO CICLO') "
            "não está listado no sumário e só ocorre uma vez no documento, já "
            "posicionado depois do sumário — isso faz com que a segmentação "
            "resolva corretamente para as ocorrências do corpo do texto sem "
            "precisar da proteção de cursor_inicial (mantida no código por "
            "segurança e paridade de método, mas com efeito nulo neste caso). "
            "Verificado programaticamente antes da consolidação do resultado: "
            "todas as posições dos 26 marcadores ficam em ordem estritamente "
            "crescente."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    analise = {**analise_anterior, **analise}
    analise["gerado_em"] = "25 de agosto de 2026"  # rollout indice de cobertura

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
