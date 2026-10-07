#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Goiás 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver, por
exemplo, /home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py)
e nos estados já processados do Norte e do Centro-Oeste (ex.: Tocantins, Mato
Grosso): distribuição temática exaustiva por segmentação de marcadores de
seção reais (lidos e mapeados à mão) e Índice de Base Empírica (heurística
lexical/regex idêntica à usada em todos os outros estados, reaproveitada sem
alterações para manter comparabilidade entre estados e regiões).

Caso de Goiás: o governador titular, Ronaldo Caiado (União Brasil, depois
PSD), cumpria seu 2º mandato consecutivo — portanto inelegível para um 3º
mandato estadual — e, em 2026, RENUNCIOU ao cargo de governador para
concorrer à Presidência da República pelo PSD (fonte: Gazeta do Povo, "Ronaldo
Caiado será candidato a presidente pelo PSD"). Seu vice-governador, Daniel
Vilela (MDB), tomou posse como governador (fontes: Agência Brasil Central —
goias.gov.br/abc, "Daniel Vilela toma posse como governador de Goiás"; NSC
Total, "Daniel Vilela é o novo governador de Goiás após Caiado deixar
governo") e hoje concorre à reeleição como governador em exercício, com
discurso explícito de continuidade do governo Caiado (fonte: A Redação,
"Candidatura de Daniel Vilela à reeleição ao governo é oficializada com
discurso de continuidade") — classificado aqui como "incumbente por
sucessão", o mesmo padrão já identificado no Mato Grosso (Otaviano Pivetta).
O próprio plano de governo de Daniel Vilela relata em primeira pessoa: "Como
vice-governador de Ronaldo Caiado, compreendeu o impacto de decisões
baseadas em evidências". O outro candidato analisado, Marconi Perillo
(PSDB), é ex-governador de Goiás por múltiplos mandatos (1999-2014) e
disputa a eleição como opositor ao grupo político de Caiado/Vilela (fontes:
Portal 6, "PSDB oficializa Marconi Perillo como candidato ao Governo de
Goiás"; Gazeta do Povo, "Eleições 2026 opõe legados de governadores em
Goiás") — classificado aqui como "desafiante". Nenhum dos dois candidatos
deste projeto é o titular pleno buscando reeleição (Caiado não pôde
concorrer ao cargo estadual); essa é uma leitura eleitoral, baseada em fontes
jornalísticas e institucionais de 2026, e não influenciou nenhuma etapa da
extração ou classificação textual dos planos.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/centro-oeste/goias/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/centro-oeste/goias/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "daniel_vilela", "nome": "Daniel Vilela", "partido": "MDB",
     "categoria": "incumbente por sucessão — era vice-governador de Ronaldo Caiado (União "
                  "Brasil/PSD, 2º mandato consecutivo como governador, portanto inelegível "
                  "para um 3º mandato estadual) e assumiu o cargo de governador em 2026, "
                  "após a renúncia de Caiado para concorrer à Presidência da República; "
                  "hoje governador em exercício, candidato à reeleição com discurso "
                  "explícito de continuidade do governo Caiado — fontes: Agência Brasil "
                  "Central (goias.gov.br/abc), \"Daniel Vilela toma posse como governador "
                  "de Goiás\"; NSC Total, \"Daniel Vilela é o novo governador de Goiás após "
                  "Caiado deixar governo\"; Gazeta do Povo, \"Ronaldo Caiado será candidato "
                  "a presidente pelo PSD\"; A Redação, \"Candidatura de Daniel Vilela à "
                  "reeleição ao governo é oficializada com discurso de continuidade\""},
    {"slug": "marconi_perillo", "nome": "Marconi Perillo", "partido": "PSDB",
     "categoria": "desafiante — ex-governador de Goiás por múltiplos mandatos (1999-2014), "
                  "candidato do PSDB em oposição ao grupo político de Ronaldo Caiado e "
                  "Daniel Vilela — fontes: Portal 6, \"PSDB oficializa Marconi Perillo como "
                  "candidato ao Governo de Goiás\"; Gazeta do Povo, \"Eleições 2026 opõe "
                  "legados de governadores em Goiás\""},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os demais estados do
# projeto (Nordeste, Norte e Centro-Oeste), não adaptadas a Goiás, para
# preservar comparabilidade entre estados. Mantidas verbatim, inclusive
# termos estruturais específicos de outros estados (ex.: "maranhão").
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

# Daniel Vilela (MDB): documento muito bem estruturado em duas grandes
# partes. Uma primeira parte (páginas 01-04, "QUEM É DANIEL VILELA" /
# "MENSAGEM DO CANDIDATO" / "HORIZONTE 2030 — visão de futuro" / "LEGADO
# 2019-2026") narra a biografia do candidato e presta contas do governo
# Caiado/Vilela em blocos temáticos claros (SEGURANÇA PÚBLICA,
# DESENVOLVIMENTO SOCIAL, EDUCAÇÃO, SAÚDE, GESTÃO FISCAL, DESENVOLVIMENTO
# ECONÔMICO, INFRAESTRUTURA, CIÊNCIA/TECNOLOGIA/INOVAÇÃO, ESPORTE/LAZER/
# CULTURA, MEIO AMBIENTE); uma segunda parte ("05 O PRÓXIMO CICLO" e "06
# EIXOS ESTRATÉGICOS") apresenta desafios estruturais/oportunidades
# estratégicas e detalha 6 eixos numerados (I a VI), cada um subdividido em
# "Diretrizes Estratégicas" com título próprio ("| Nome da diretriz").
#
# ATENÇÃO — artefato de extração: o PDF de origem foi extraído com um forte
# artefato de colunas entrelaçadas — ao longo de quase todo o documento,
# cada linha física do .txt concatena, lado a lado com grandes blocos de
# espaço em branco, conteúdo de duas colunas adjacentes do PDF original (ex.:
# a abertura da seção "SEGURANÇA PÚBLICA" e o início de "DESENVOLVIMENTO
# SOCIAL" aparecem na mesma linha física; dentro do Eixo I, o título de uma
# diretriz de saúde aparece colado ao final de uma frase sobre educação da
# coluna vizinha). Mesmo tipo de limitação já documentada no Ceará (Eixo 01
# de Ciro Gomes) e, de forma mais extensa, no Mato Grosso (plano de Otaviano
# Pivetta). Os marcadores abaixo foram escolhidos e verificados (via busca de
# texto exato) como literais e únicos no arquivo, na ordem em que realmente
# aparecem no .txt (que não é necessariamente a ordem de leitura pretendida
# do PDF original) — a segmentação por posição de caractere segue essa ordem
# real do arquivo. Como consequência, algumas diretrizes cujo título temático
# é inequívoco (ex.: "Saúde Mental, TEA e Reabilitação", "Rede Estadual de
# Combate ao Câncer", "Saúde Inteligente", dentro do bloco de saúde do Eixo
# I; "Cultura Viva Goiás", dentro do bloco de assistência social do mesmo
# eixo; "UEG", "Goiás Inteligente" e "Goiás pelo Mundo", dentro do bloco de
# educação do Eixo II; "Turismo em Rede" e "Mineração e Minerais Críticos",
# dentro do bloco de economia do Eixo III; toda a Eixo V de Segurança
# Pública; e "Serviço Público de Excelência" e "Governo da Energia
# Inteligente", dentro do bloco de gestão pública do Eixo VI) não têm
# marcador próprio — o marcador do início do bloco temático mais amplo em
# que essas diretrizes se inserem já basta, porque cada uma dessas
# diretrizes pertence ao MESMO tema do bloco em que fisicamente aparece no
# arquivo (não havia necessidade de segmentação adicional). O único caso em
# que um bloco de "Oportunidades Estratégicas" mistura dois temas
# afins (Minerais Críticos e Inteligência Artificial, ambos tratados como
# "economia") também não exigiu marcador extra pelo mesmo motivo. Ver nota
# de metodologia para mais detalhes.
MARCADORES_DANIEL_VILELA = [
    # --- "04 LEGADO 2019-2026": balanço do governo Caiado/Vilela, por tema ---
    ("tranquilidade de caminhar por ruas seguras, dormir de portas abertas e", "seguranca"),
    ("garantia de que cada pessoa tenha condições reais de sonhar com o", "assistencia_social"),
    ("goiana transformou histórias e construiu uma base sólida para", "educacao"),
    ("precisava de atendimento médico especializado antes de 2019", "saude"),
    ("reflexo imediato de um Estado em colapso fiscal recaía sobre a rotina de", "gestao_publica"),
    ("prosperidade que entra pela porta de casa de cada trabalhador,", "economia"),
    ("Ligar o campo ao mercado e aproximar as pessoas das oportunidades é o", "infraestrutura"),
    # Ciência/Tecnologia/Inovação enquadrada, no balanço de legado, em torno
    # de competitividade estadual — tratada como "economia", diferente do
    # tratamento dado ao bloco de C&T do Eixo II (ver abaixo), que é
    # majoritariamente sobre formação/educação.
    ("Cada laboratório conectado, cada pesquisa financiada e cada nova", "economia"),
    ("Ver praças revitalizadas cheias de vida, festivais culturais movimentando", "assistencia_social"),
    ("eixo estratégico que conecta o crescimento econômico à conservação", "meio_ambiente"),
    # --- "05 O PRÓXIMO CICLO": desafios estruturais e oportunidades estratégicas ---
    ("O PRÓXIMO CICLO: DESAFIOS E OPORTUNIDADES", "outros"),
    ("Brasil vive a maior transformação da sua história. Com a Emenda", "economia"),
    ("Secas mais prolongadas, chuvas mais intensas e incêndios florestais", "meio_ambiente"),
    # Bloco "Geopolítica Internacional" seguido, no arquivo, pelos blocos
    # "Minerais Críticos" e "Inteligência Artificial" (ambos "economia") —
    # sem marcador próprio adicional, ver nota acima.
    ("conjuntura internacional tem passado por um período de", "economia"),
    # --- "06 EIXOS ESTRATÉGICOS" ---
    ("06 EIXOS ESTRATÉGICOS", "outros"),
    # Eixo I — Desenvolvimento Humano e Bem-Estar (educação, saúde, social,
    # habitação, esporte/cultura)
    ("| Educação Integral Goiás", "educacao"),
    ("| Regionalização da Saúde: Atendimento Mais Perto das Pessoas", "saude"),
    ("| Desenvolvimento Social: Proteção e Emancipação das Famílias", "assistencia_social"),
    ("| Habitação: Moradia Digna e Segurança para as Famílias", "infraestrutura"),
    ("| Esporte para Todos: Formação, Inclusão e Alto Rendimento", "assistencia_social"),
    # Eixo II — Conhecimento, Tecnologia e Inovação (Goiás Inova, voltado a
    # geração de valor econômico, tratado como "economia"; o restante do
    # eixo — Gestão Escolar, UEG, Goiás Inteligente, Goiás pelo Mundo — é
    # majoritariamente sobre formação/universidade/servidores da educação,
    # tratado como "educacao")
    ("| Goiás Inova: Ciência, Tecnologia e Empreendedorismo para", "economia"),
    ("Gestão           Escolar,        Valorização   e       Desenvolvimento        dos", "educacao"),
    # Eixo III — Desenvolvimento Econômico e Competitividade (agropecuária,
    # mineração, turismo = economia; autonomia fiscal municipal = gestão
    # pública)
    ("| Agropecuária Forte, Segura, Sustentável e Inovadora", "economia"),
    ("| Autonomia Fiscal e Modernização Tributária Municipal", "gestao_publica"),
    # Eixo IV — Infraestrutura, Território e Sustentabilidade (dev.
    # regional, saneamento, mobilidade = infraestrutura; adaptação
    # climática = meio ambiente)
    ("| Desenvolvimento Regional: Mais Oportunidades em Todas as", "infraestrutura"),
    ("| Goiás Resiliente e Verde: Adaptação Climática e Novos", "meio_ambiente"),
    # Eixo V — Segurança Pública (bloco inteiro)
    ("| Trânsito Seguro Goiás: Mais Prevenção, Menos Acidentes", "seguranca"),
    # Eixo VI — Capacidade Institucional e Governança (bloco inteiro,
    # incluindo previdência, energia e centro administrativo — todos
    # enquadrados pelo próprio texto como eficiência/gestão da máquina
    # pública)
    ("| Goiás Planejado: Gestão Estratégica, Avaliação de Políticas", "gestao_publica"),
    ("GOVERNANÇA E MONITORAMENTO DO PLANO DE", "gestao_publica"),
    # Carta de encerramento
    ("Nenhum governo transforma um", "outros"),
]

# Marconi Perillo (PSDB): documento com a estrutura mais limpa e explícita de
# todo o projeto — o próprio plano se autodenomina organizado em "4. Áreas
# Temáticas 2027-2030" (item 4 do sumário), com exatamente 10 áreas
# temáticas numeradas (4.1 a 4.10) que já vêm nomeadas de forma quase
# idêntica à taxonomia de 9 temas usada neste projeto, cobrindo 55
# "compromissos" numerados. Cada área é um bloco único e coerente,
# antecedida de um cabeçalho "4.N Nome da Área" que ocorre no arquivo uma
# única vez como cabeçalho real (a menção ao mesmo título no sumário/
# "Arquitetura do Plano", nas páginas 8-9, usa espaçamento de texto
# diferente do cabeçalho real e não colide com a busca literal usada aqui).
# Duas áreas (4.8 e 4.9) reúnem explicitamente mais de um tema sob o mesmo
# título e foram parcialmente segmentadas:
#   - 4.8 "Desenvolvimento Social, Habitação e Cidadania": o compromisso 43
#     ("Ampliar o acesso à moradia digna e à regularização fundiária") é
#     destacado como "infraestrutura" (precedente do projeto: habitação =
#     infraestrutura), mantendo o restante da área (proteção social,
#     cidadania, direitos) como "assistencia_social".
#   - 4.9 "Cultura, Esporte e Turismo": o compromisso 50 ("Fazer do turismo
#     um motor de desenvolvimento regional") é destacado como "economia"
#     (turismo tratado como vocação econômica, mesmo precedente do Ceará),
#     mantendo cultura e esporte como "assistencia_social" (precedente do
#     projeto).
# Após as 10 áreas temáticas, o plano tem uma seção "5. Pacto com os 246
# Municípios" (cooperação Estado-municípios, tratada como "gestao_publica",
# por ser essencialmente sobre o modelo de relação institucional do governo
# estadual com os municípios) e "6. Responsabilidade Fiscal, Resultados e
# Transparência" (gestão fiscal e monitoramento de resultados, também
# "gestao_publica"), encerrando com "7. Compromisso Final - Goiás 2030"
# (carta de encerramento, "outros"). Diferente do plano de Daniel Vilela,
# este documento NÃO apresenta o artefato de colunas entrelaçadas — foi
# extraído em coluna única e ordem de leitura correta.
MARCADORES_MARCONI_PERILLO = [
    ("4.1 Educação, Ciência e Tecnologia", "educacao"),
    ("4.2 Saúde", "saude"),
    ("4.3 Segurança Pública", "seguranca"),
    ("4.4 Desenvolvimento Econômico e Trabalho", "economia"),
    ("4.5 Agronegócio, Agricultura Familiar e", "economia"),
    ("4.6 Infraestrutura, Logística e Desenvolvimento", "infraestrutura"),
    ("4.7 Meio Ambiente", "meio_ambiente"),
    ("4.8 Desenvolvimento Social, Habitação e Cidadania", "assistencia_social"),
    ("43 Ampliar o acesso à moradia digna e à regularização fundiária", "infraestrutura"),
    ("4.9 Cultura, Esporte e Turismo", "assistencia_social"),
    ("50 Fazer do turismo um motor de desenvolvimento regional", "economia"),
    ("4.10 Governança e Gestão Pública", "gestao_publica"),
    ("5. Pacto com os 246 Municípios", "gestao_publica"),
    ("6. Responsabilidade Fiscal, Resultados e Transparência", "gestao_publica"),
    ("7. Compromisso Final - Goiás 2030", "outros"),
]

MARCADORES = {
    "daniel_vilela": MARCADORES_DANIEL_VILELA,
    "marconi_perillo": MARCADORES_MARCONI_PERILLO,
}

# Ponto de partida da análise de Base Empírica (Tarefa 2) para cada
# candidato: nenhum dos dois planos de Goiás tem um sumário/índice longo em
# texto corrido que pudesse distorcer a extração de frases (o plano de
# Marconi Perillo tem um sumário gráfico curto, com títulos e números de
# eixo, não frases completas), então a análise roda sobre o corpo inteiro do
# documento (posição 0) para os dois candidatos.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "daniel_vilela": 0,
    "marconi_perillo": 0,
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
            "comparabilidade metodológica entre estados — por isso 'Goiás' "
            "e 'goiano(s)/goiana(s)' NÃO são filtrados e aparecem "
            "naturalmente entre os termos mais frequentes de ambos os "
            "planos). Mostra os termos mais repetidos por candidato e o "
            "agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/área temática/ "
            "diretriz, ou, quando necessário, o início verbatim de uma frase "
            "de abertura de bloco). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando um trecho do documento "
            "original já reunia explicitamente múltiplos temas afins sob um "
            "único bloco (ex.: 'Cultura, Esporte e Turismo' no plano de "
            "Marconi Perillo), o compromisso ou diretriz claramente "
            "dedicado a um tema distinto (ex.: turismo como motor "
            "econômico) foi destacado com marcador próprio; quando não era "
            "possível separar com segurança, o bloco inteiro foi mantido "
            "sob um único tema predominante."
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
            "Nordeste e dos estados já processados do Norte e do "
            "Centro-Oeste, sem nenhum ajuste específico para Goiás, para "
            "manter comparabilidade entre estados e entre regiões."
        ),
        "metodologia_nota": (
            "Goiás tem uma particularidade sucessória relevante, do mesmo "
            "tipo já observado no Mato Grosso: o governador titular, "
            "Ronaldo Caiado (União Brasil, depois PSD), cumpria seu 2º "
            "mandato consecutivo — portanto inelegível para um 3º mandato "
            "estadual — e, em 2026, renunciou ao cargo de governador para "
            "concorrer à Presidência da República (fonte: Gazeta do Povo, "
            "'Ronaldo Caiado será candidato a presidente pelo PSD'). Seu "
            "vice-governador, Daniel Vilela (MDB), tomou posse como "
            "governador (fontes: Agência Brasil Central — goias.gov.br/abc, "
            "'Daniel Vilela toma posse como governador de Goiás'; NSC "
            "Total, 'Daniel Vilela é o novo governador de Goiás após "
            "Caiado deixar governo') e hoje concorre à reeleição como "
            "governador em exercício, com discurso explícito de "
            "continuidade do governo Caiado (fonte: A Redação, "
            "'Candidatura de Daniel Vilela à reeleição ao governo é "
            "oficializada com discurso de continuidade') — classificado "
            "neste projeto como 'incumbente por sucessão'. O próprio plano "
            "de governo de Daniel Vilela relata, em sua biografia, que ele "
            "foi 'vice-governador de Ronaldo Caiado'. O outro candidato "
            "analisado, Marconi Perillo (PSDB), é ex-governador de Goiás "
            "por múltiplos mandatos (1999-2014) e disputa a eleição como "
            "opositor ao grupo político de Caiado/Vilela (fontes: Portal 6, "
            "'PSDB oficializa Marconi Perillo como candidato ao Governo de "
            "Goiás'; Gazeta do Povo, 'Eleições 2026 opõe legados de "
            "governadores em Goiás') — classificado como 'desafiante'. "
            "Nenhum dos dois candidatos deste projeto é o titular pleno "
            "buscando reeleição, já que Caiado não pôde concorrer ao cargo "
            "estadual. Essa é uma leitura eleitoral, baseada em cobertura "
            "jornalística e fontes institucionais de 2026, e não "
            "influenciou nenhuma etapa da extração ou classificação "
            "textual dos planos. "
            "Ressalva sobre a extração do plano de Daniel Vilela: o PDF de "
            "origem foi extraído com um forte artefato de colunas "
            "entrelaçadas ao longo de quase todo o documento — cada linha "
            "física do .txt concatena, lado a lado com grandes blocos de "
            "espaço em branco, conteúdo de duas colunas adjacentes do PDF "
            "original (mesmo tipo de limitação já documentada no Ceará, "
            "para o Eixo 01 de Ciro Gomes, e de forma mais extensa no Mato "
            "Grosso, no plano de Otaviano Pivetta). Os marcadores de "
            "segmentação temática foram escolhidos e verificados como "
            "literais e únicos no arquivo, na ordem em que realmente "
            "aparecem no .txt (que não é necessariamente a ordem de "
            "leitura pretendida do PDF original); como a maior parte das "
            "diretrizes de cada bloco temático pertence ao mesmo tema do "
            "bloco em que fisicamente aparece no arquivo, isso não exigiu "
            "marcadores adicionais na maioria dos casos, mas pode adicionar "
            "um pequeno ruído às fronteiras exatas de alguns segmentos. Não "
            "corrigimos a extração para manter a metodologia idêntica "
            "entre estados; o efeito é sobre a precisão fina das fronteiras "
            "de segmento, não sobre a contagem total de palavras do "
            "documento nem sobre a detecção de frases para o Índice de "
            "Base Empírica (que operam sobre o texto inteiro, "
            "independentemente da ordem de colunas). O plano de Marconi "
            "Perillo não apresenta esse artefato — foi extraído em coluna "
            "única e ordem de leitura correta — e sua estrutura em 10 "
            "áreas temáticas numeradas (4.1 a 4.10) já corresponde de "
            "forma quase direta à taxonomia de 9 temas usada neste "
            "projeto, o que tornou sua segmentação a mais direta do "
            "projeto até aqui. "
            "Nota sobre a fonte de Marconi Perillo: o TSE disponibilizou "
            "dois arquivos PDF de proposta de governo para este candidato "
            "(sufixos '_01' e '_02'), mas os dois são byte a byte "
            "idênticos (md5sum confirmado igual) — não se trata de um "
            "documento genuinamente dividido em duas partes. Foi utilizado "
            "apenas o arquivo '_01' para a extração do texto analisado "
            "aqui."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
