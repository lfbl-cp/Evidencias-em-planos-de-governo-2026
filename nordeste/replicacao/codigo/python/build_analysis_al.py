#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Alagoas 2026.

Réplica da metodologia usada nos demais estados do projeto (build_analysis_ma.py
como script canônico, já corrigido por um validador independente): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica à
usada em todos os outros estados, reaproveitada sem alterações para manter
comparabilidade). Também gera as nuvens de palavras (wordcloud) embutidas em
base64 em cada candidato.

NOTA METODOLÓGICA ESPECÍFICA DE ALAGOAS — DOIS DOCUMENTOS COM ESTRUTURAS MUITO
DIFERENTES:
O plano de João Henrique Caldas (JHC) é um documento de campanha longo e em
prosa corrida (~13,7 mil palavras), organizado em 7 "Eixos" (A a G) com
seções "Propostas" internas por área. O PDF original tem diagramação em caixas
de texto (títulos de seção em caixas laterais/de abertura de página), o que faz
com que, na extração para texto, alguns títulos de seção apareçam ENCAIXADOS NO
MEIO de uma frase do parágrafo principal, fora da ordem de leitura visual (ex.:
"...O Remédio em Casa garantirá a entrega de medicamentos de" [caixa "PROPOSTAS
SAÚDE / EIXO A / ALAGOAS QUE CUIDA"] "uso continuado e ampliará os pontos de
retirada..."). Como esses títulos encaixados sempre caem DENTRO do mesmo tema
do parágrafo que os cerca (nunca marcam uma mudança real de tema), eles não
foram usados como marcador de transição — os marcadores usados são sempre a
primeira frase narrativa legível que efetivamente abre um novo tema no corpo
do texto (mesmo critério adotado em Pernambuco para o plano OCR de Raquel
Lyra, por razão de extração diferente mas com o mesmo efeito prático).

O plano de Renan Filho é radicalmente mais curto e estruturalmente diferente:
não há prosa narrativa alguma. São 53 propostas numeradas (1 a 53) agrupadas em
5 "Missões" com tags de ODS, sem nenhum parágrafo de diagnóstico, contexto ou
justificativa. Isso already é, em si, um achado editorial relevante (ver
metodologia_nota) — e também torna a classificação temática deste candidato
necessariamente item a item (cada proposta numerada é seu próprio marcador),
em vez de por seção, já que o documento não tem seções textuais further do que
os títulos de Missão.
"""
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/alagoas/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/alagoas/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "jhc", "nome": "João Henrique Caldas (JHC)", "partido": "PSDB",
     "categoria": "desafiante (ex-prefeito de Maceió)"},
    {"slug": "renan-filho", "nome": "Renan Filho", "partido": "MDB",
     "categoria": ("candidato de continuidade (ex-governador; apoiado pelo "
                   "governador em exercício Paulo Dantas, que não concorre)")},
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
plano governo alagoas alagoano alagoana alagoanos alagoanas eleições 2026
partido número coligação fonte fontes status texto seção seções eixo eixos
parte partes bloco blocos documento página páginas inclui incluem também
estamos propõe prevê abertura caminho proposto propostos principais desafios
núcleo contexto visão onde compromisso compromissos destaca destacados
destacado
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

# João Henrique Caldas (JHC) — plano digital nativo, longo, em prosa corrida,
# organizado em 7 Eixos (A-G) com seções "Propostas" internas. O SUMÁRIO no
# início do documento repete os títulos de seção usados como marcador (mesmo
# problema já visto no Maranhão/Ceará/Piauí) — corrigido com a mesma lógica
# (cursor_inicial = 2ª ocorrência do 1º marcador).
#
# Decisões de classificação não óbvias:
#  - O "Diagnóstico" geral (dados sobre saúde/economia/educação/segurança/
#    saneamento/meio ambiente/inovação, todos misturados em um único capítulo
#    corrido) e a lista-síntese das "19 principais propostas" que o antecede
#    a leitura por Eixo (item 1 a 19, cruzando todos os temas em formato de
#    prévia) foram tratados como "outros" (front matter), pelo mesmo critério
#    usado em outros estados para material introdutório/sintético que
#    antecede e duplica o conteúdo detalhado apresentado depois por seção —
#    mesmo precedente do "Bloco 1"/tabela-síntese duplicada de Felipe Camarão
#    (Maranhão).
#  - A seção combinada "Cultura, Esporte e Turismo": como no plano de Eduardo
#    Braide (Maranhão), turismo é tratado como economia (ênfase em renda e
#    fluxo de visitantes) enquanto cultura e esporte são tratados como
#    assistencia_social (precedente Orleans Brandão, Maranhão), e "Alagoas
#    Lab" (ciência, tecnologia e inovação, dentro dessa mesma seção) como
#    economia (precedente: seções de inovação -> economia em todos os
#    estados). Cada um desses 4 programas foi segmentado item a item pelo
#    nome do programa, e não pelo título de seção combinado, exatamente para
#    poder separá-los.
#  - "Energia" (Eixo D): sem tema próprio nos 9 temas do projeto; classificado
#    como infraestrutura (energia é tratada aqui como infraestrutura
#    produtiva/rede pública, não como meio ambiente — o programa "Energia
#    para Crescer" tem foco explícito em competitividade industrial).
#  - Água/Saneamento e Habitação/Cidades (Eixo E): infraestrutura, mesmo
#    precedente usado no Maranhão (água/esgoto, habitação -> infraestrutura).
#  - Eixo G ("Alagoas para Todos" — Juventude, Mulheres, Igualdade Racial,
#    PCD, 60+, Povos Tradicionais): assistencia_social, mesmo precedente do
#    Maranhão para seções de direitos humanos/populações específicas.
#  - A lista de "Fontes" ao final (bibliografia/referências de dados) foi
#    classificada como "outros".
MARCADORES_JHC = [
    ("Este eixo trata do que acompanha a pessoa: nascer com segurança",
     "saude"),  # Eixo A: intro geral + Propostas Saúde (itens 1-10)
    ("PROPOSTAS\nEDUCAÇÃO",
     "educacao"),  # Propostas Educação (itens 11-17)
    ("PROPOSTAS\nPRIMEIRA INFÂNCIA",
     "assistencia_social"),  # Propostas Primeira Infância, Assistência e Proteção Social (itens 18-20)
    ("PROPOSTAS\nSEGURANÇA",
     "seguranca"),  # Eixo B: intro + Propostas Segurança (itens 1-5)
    ("PROPOSTAS\nTRABALHO, EMPREENDEDORISMO",
     "economia"),  # Eixo C: intro + Propostas Trabalho/Empreendedorismo/Desenv. Produtivo (itens 1-9, incl. Ponta a Ponta/turismo, Internacionalização, Alagoas Mais Competitiva)
    ("Cultura, esporte e turismo não podem mais ser oportunidades",
     "economia"),  # intro combinada + resumo dos 4 programas (predomínio de enquadramento econômico/renda, precedente Braide-MA)
    ("Programa Cultura por Todo Canto. Política estadual para descentralizar",
     "assistencia_social"),
    ("Parques-Biblioteca. Implantação de uma rede estadual de bibliotecas",
     "assistencia_social"),
    ("Alagoas Lab. Estratégia estadual para transformar o investimento",
     "economia"),
    ("Areninhas Alagoas. Implantação de uma rede estadual de espaços",
     "assistencia_social"),
    ("Este eixo trata das condições que permitem ao Estado transformar",
     "infraestrutura"),  # Eixo D intro + Propostas Infraestrutura, Transporte e Logística (itens 1-8)
    ("PROPOSTAS\nENERGIA",
     "infraestrutura"),  # Energia para Crescer
    ("Governar melhor também significa permitir que a população saiba",
     "gestao_publica"),  # Painel Alagoas Gigante, Gabinete do Povo, Gente que Faz
    ("Este eixo trata das condições básicas que fazem uma cidade",
     "infraestrutura"),  # Eixo E intro geral (água/habitação, diagnóstico misto)
    ("PROPOSTAS\nMEIO AMBIENTE",
     "meio_ambiente"),  # Alagoas Verde, Alagoas Clima, Alagoas Tem Parque
    ("Garantir água para todos exige enfrentar dois problemas diferentes",
     "infraestrutura"),  # Propostas Água e Saneamento
    ("Morar bem não é apenas ter uma casa",
     "infraestrutura"),  # Propostas Habitação e Cidade
    ("Criação da Controladoria Estadual Anticorrupção. Criação de uma",
     "gestao_publica"),  # Eixo F: Alagoas Transparente (Controladoria, Contas Abertas)
    ("Este eixo reúne políticas que não cabem dentro de uma única secretaria",
     "assistencia_social"),  # Eixo G: Alagoas para Todos (Juventude, Mulheres, Igualdade Racial, Inclusiva, 60+, Povos Tradicionais)
    ("IBGE (Censo 2022, PNAD Contínua",
     "outros"),  # lista de Fontes/bibliografia final
]

# Renan Filho — plano radicalmente mais curto: 53 propostas numeradas (1-53)
# agrupadas em 5 "Missões" com tags de ODS, sem nenhuma prosa de diagnóstico
# ou justificativa. Não há títulos de seção textual além dos cabeçalhos de
# Missão, então a classificação temática é necessariamente item a item —
# cada proposta numerada é seu próprio marcador. Os cabeçalhos de Missão 2-5
# (que aparecem entre duas propostas de temas diferentes) também recebem
# marcador próprio, mapeado para "outros", para não vazar nem para o tema da
# proposta anterior nem para o da seguinte.
MARCADORES_RENAN = [
    ("1. Ampliar a rede hospitalar do Estado", "saude"),
    ("2. Criar uma frota de ambulâncias", "saude"),
    ("3. Ampliar a integração de operações de órgãos de segurança pública",
     "seguranca"),
    ("4. Implantar Delegacias 24h da Mulher", "seguranca"),
    ("5. Criar programa de valorização profissional para os integrantes da segurança",
     "seguranca"),
    ("6. Ampliar a cobertura aérea de combate ao crime", "seguranca"),
    ("7. Expandir o cofinanciamento estadual de municípios", "assistencia_social"),
    ("8. Implantar Centro de Referência de Assistência Social", "assistencia_social"),
    ("9. Expandir a interiorização da Rede de Restaurantes Populares",
     "assistencia_social"),
    ("10. Desenvolver um sistema interoperacional para percurso da rota crítica",
     "seguranca"),
    ("11. Apoiar os municípios na criação ou no fortalecimento de seus organismos",
     "assistencia_social"),
    ("12. Desenvolver ações de prevenção e enfrentamento à misoginia",
     "seguranca"),
    ("13. Criar academias públicas ao ar livre", "assistencia_social"),
    ("14. Criar Centros Regionais de Desenvolvimento Esportivo",
     "assistencia_social"),
    ("MISSÃO 2: ECONOMIA INOVADORA", "outros"),
    ("15. Criar o Programa Educação IA", "educacao"),
    ("16. Implantar o programa Escola da Hora Tech", "educacao"),
    ("17. Instituir o Programa Mãe Estudante", "educacao"),
    ("18. Combater o analfabetismo na idade adulta", "educacao"),
    ("19. Transformar o Jaraguá no bairro de inovação", "economia"),
    ("20. Criar um programa de residência tecnológica", "economia"),
    ("21. Criar um programa estruturante e de longo prazo para o turismo",
     "economia"),
    ("22. Criar uma política de desenvolvimento da economia criativa",
     "economia"),
    ("23. Implantar Polo de Comércio e Serviços Corporativos", "economia"),
    ("24. Fomentar o empreendedorismo de mães e famílias atípicas", "economia"),
    ("25. Criar um amplo programa de qualificação profissional", "economia"),
    ("26. Eliminar barreiras burocráticas", "economia"),
    ("27. Fortalecer a agricultura familiar alagoana", "economia"),
    ("28. Estimular a produção de alimentos orgânicos", "economia"),
    ("29. Ampliar programas que fomentem a produção e comercialização de alimentos",
     "economia"),
    ("30. Ampliar acesso a sistemas simplificados de irrigação", "economia"),
    ("31. Fomentar a ampliação da área de cultivo de grãos", "economia"),
    ("32. Fortalecer a cadeia produtiva da fruticultura", "economia"),
    ("33. Apoiar a cadeia produtiva do leite", "economia"),
    ("34. Expandir programas de melhoramento genético", "economia"),
    ("35. Estruturar programa estadual de fomento à pesca e aquicultura",
     "economia"),
    ("36. Fomentar a consolidação e expansão da cadeia produtiva da carcinicultura",
     "economia"),
    ("37. Desenvolver uma política de modernização do setor sucroenergético",
     "economia"),
    ("MISSÃO 3: TRANSFORMAÇÃO ECOLÓGICA", "outros"),
    ("38. Criar a “Agenda 21 de Alagoas”", "meio_ambiente"),
    ("39. Criar o Programa de Restauração Florestal", "meio_ambiente"),
    ("40. Incentivar a Pesquisa, desenvolvimento e inovação (PD&I)",
     "meio_ambiente"),
    ("41. Fomentar a produção dos Planos de Manejo de Unidades de Conservação",
     "meio_ambiente"),
    ("42. Criar o Plano “Passagem silvestre”", "meio_ambiente"),
    ("43. Investir em energias renováveis (solar) na rede pública",
     "meio_ambiente"),
    ("44. Criar o Sistema Estadual de Gestão Ambiental Integrada",
     "meio_ambiente"),
    ("MISSÃO 4: INFRAESTRUTURA REGIONALIZADA", "outros"),
    ("45. Ampliar rodovias duplicadas", "infraestrutura"),
    ("46. Realizar estudo para implantar um terminal rodoviário",
     "infraestrutura"),
    ("47. Criar um programa de construção e recuperação de pontes",
     "infraestrutura"),
    ("48. Incluir os povoados no programa Minha Cidade Linda",
     "infraestrutura"),
    ("49. Implantar Programa de Endereçamento Postal", "infraestrutura"),
    ("50. Articular junto ao Governo Federal a construção de 5 mil casas",
     "infraestrutura"),
    ("MISSÃO 5: ESTADO DIGITAL E EFICIENTE", "outros"),
    ("51. Intensificar a transformação digital no Poder Executivo",
     "gestao_publica"),
    ("52. Criar uma política estruturada de Governança de Dados",
     "gestao_publica"),
    ("53. Implementar uma Política de Cidadania Digital", "gestao_publica"),
]

MARCADORES = {
    "jhc": MARCADORES_JHC,
    "renan-filho": MARCADORES_RENAN,
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
    segmentos_debug.append(("[FRONT MATTER: carta de abertura/sumário/diagnóstico/síntese]", "outros", n_intro))

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


# EVIDENCIA_RE — CORRIGIDO (herdado byte a byte de build_analysis_ma.py já
# corrigido). NÃO inclui "plano lula|plano nacional" como gatilhos genéricos
# de evidência: um validador independente encontrou que isso inflava
# artificialmente o pilar C quando um candidato apenas cita alinhamento
# político com o plano nacional do partido, sem citar evidência de fato. Isto
# é especialmente relevante em Alagoas: Renan Filho é candidato de
# continuidade e cita o Governo Federal com frequência (ver metodologia_nota
# — confirmado que essas menções não disparam is_evidencia por si só).
# "plano nacional de logística" é mantido: é uma referência específica e
# legítima a um documento técnico federal, não um gatilho genérico de
# alinhamento partidário.
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
# find_shared_text_al.py; resultado colado abaixo em achado_texto_compartilhado
# / texto_compartilhado, mesmo padrão usado no Ceará/Piauí/Pernambuco).
# ---------------------------------------------------------------------------
ACHADO_TEXTO_COMPARTILHADO = {
    "resumo": (
        "A checagem de blocos de texto idêntico ou quase idêntico entre os "
        "planos de João Henrique Caldas (JHC) e Renan Filho (mínimo de 150 "
        "caracteres, 8 palavras consecutivas) não encontrou nenhum bloco "
        "compartilhado entre os dois documentos — resultado no mesmo sentido "
        "do observado no Maranhão, Piauí, Ceará e Pernambuco (0 blocos em "
        "todos), e diferente do observado na Paraíba (blocos de texto "
        "idênticos entre planos de candidatos rivais, incluindo um parágrafo "
        "repetido nos três planos)."
    ),
    "pares_verificados": ["jhc x renan-filho"],
    "blocos_encontrados": 0,
}

TEXTO_COMPARTILHADO = {
    "pares_comparados": ["jhc_x_renan-filho"],
    "resultado_por_par": {
        "jhc_x_renan-filho": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de 150+ caracteres idênticos (mínimo de 8 "
                "palavras consecutivas) encontrado entre estes dois planos. "
                "Os dois documentos têm perfis de redação radicalmente "
                "diferentes — o de JHC é um documento de campanha longo em "
                "prosa corrida (~13,7 mil palavras), com diagnóstico "
                "detalhado e nomes de programa próprios ('Alagoas Gigante', "
                "'Saúde da Gente Alagoana' etc.); o de Renan Filho é uma "
                "lista enxuta de 53 propostas numeradas sem prosa "
                "(tipicamente uma frase por proposta) — o que por si só já "
                "torna reaproveitamento de texto literal entre as duas "
                "campanhas pouco provável."
            ),
        }
    },
    "metodologia": (
        "Mesmo método de detecção usado nas análises da Paraíba, Maranhão, "
        "Piauí, Ceará e Pernambuco: índice de n-gramas de 8 palavras "
        "consecutivas para localizar trechos idênticos ou quase idênticos "
        "entre os planos, com blocos adjacentes mesclados e um piso de 150 "
        "caracteres para descartar coincidências triviais (conectores, "
        "boilerplate curto). Como Alagoas tem apenas 2 candidatos com plano "
        "de governo coletado neste projeto, há um único par possível a "
        "comparar."
    ),
    "observacao_editorial": (
        "Nenhum bloco foi encontrado entre os dois planos de Alagoas. Isso "
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
        # Se o 1º marcador aparecer mais de uma vez (documento com sumário/
        # índice que repete os títulos das seções antes do corpo real), pula
        # para a 2ª ocorrência, para não segmentar dentro do índice.
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        n_ocorrencias_1o_marcador = corpo.count(primeiro_marcador)
        cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
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
            "marcadores de seção reais. No plano de JHC, os marcadores são a "
            "primeira frase narrativa legível que abre cada seção temática "
            "(e não o título gráfico de seção, que no PDF original aparece em "
            "caixas de texto lateral e, na extração, pode cair encaixado no "
            "meio de uma frase do parágrafo principal — ver nota de "
            "metodologia). No plano de Renan Filho, que não tem prosa "
            "narrativa alguma (apenas 53 propostas numeradas agrupadas em 5 "
            "Missões), cada proposta numerada foi tratada como seu próprio "
            "marcador/segmento. Cada segmento de texto entre dois marcadores "
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
            "Heurística idêntica à usada nas análises da Paraíba, Maranhão, "
            "Piauí, Ceará e Pernambuco, sem nenhum ajuste específico para "
            "Alagoas, para manter comparabilidade entre estados. O regex de "
            "evidência (pilar C) NÃO trata menção a 'plano nacional' ou "
            "alinhamento com o governo federal/Lula como evidência por si só "
            "— apenas referências específicas a estudos, dados "
            "institucionais (IBGE, IPEA, DATASUS etc.) ou modelos "
            "comprovadamente adotados contam (ver comentário no código-fonte "
            "sobre a correção do EVIDENCIA_RE)."
        ),
        "metodologia_nota": (
            "Os dois planos de Alagoas têm perfis quase opostos de "
            "extensão e formato, o que é, em si, um achado editorial. O de "
            "JHC (desafiante, ex-prefeito de Maceió) é um documento de "
            "campanha longo (~13,7 mil palavras), com diagnóstico "
            "quantitativo extenso (dezenas de estatísticas por município, "
            "citando IBGE, DATASUS, INEP, SINISA, Atlas da Violência, INPI "
            "etc.) e nomes de programa específicos por proposta. O de Renan "
            "Filho (candidato de continuidade, ex-governador apoiado pelo "
            "governador em exercício) é uma lista enxuta de 53 propostas "
            "numeradas — tipicamente uma única frase de ação por proposta, "
            "sem parágrafo de diagnóstico, contexto, meta numérica ou "
            "citação de fonte para nenhuma delas. Isso reduz estruturalmente "
            "o número de frases elegíveis para qualquer um dos 3 pilares do "
            "Índice de Base Empírica no plano de Renan Filho (não há "
            "sequer jargão de gestão pública suficiente para compor o "
            "denominador da métrica em muitos casos — ver "
            "indice_base_empirica_detalhe) — o que é consistente com o "
            "padrão de baixa base empírica em candidatos de continuidade já "
            "observado neste projeto na Paraíba e no Maranhão, embora aqui "
            "o mecanismo seja distinto (ausência quase total de prosa "
            "textual, não apenas prevalência de retórica genérica dentro de "
            "uma prosa extensa). Verificamos especificamente se Renan Filho "
            "cita o Governo Federal/Lula com frequência (esperável em um "
            "candidato de continuidade que já articula ações federais, ex.: "
            "item 29 'PAA... executados diretamente pelo governo do estado "
            "ou em parceria com o Governo Federal' e item 50 'Articular "
            "junto ao Governo Federal a construção de 5 mil casas do "
            "programa Minha Casa Minha Vida') — essas menções NÃO disparam "
            "o pilar C (evidência/mecanismo causal externo) do índice, "
            "porque o EVIDENCIA_RE usado neste projeto foi deliberadamente "
            "corrigido para não tratar alinhamento político/administrativo "
            "com o governo federal como evidência empírica (ver "
            "metodologia_indice_base_empirica)."
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
