#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Rio Grande do Norte 2026.

Réplica da metodologia usada nos demais estados do projeto
(build_analysis_ma.py como script canônico, já corrigido por um validador
independente): distribuição temática exaustiva por segmentação de
marcadores de seção reais (lidos e mapeados à mão) e Índice de Base
Empírica (heurística lexical/regex idêntica à usada em todos os outros
estados, reaproveitada sem alterações para manter comparabilidade). Também
gera as nuvens de palavras (wordcloud) embutidas em base64 em cada
candidato.

O RN não tem incumbente concorrendo (cadeira aberta) — os 3 candidatos
analisados (Allyson Bezerra, Álvaro Dias, Cadu Xavier) estão todos
classificados como "desafiante" no cabeçalho dos planos fornecidos.

NOTA METODOLÓGICA ESPECÍFICA DO RN — TRÊS DOCUMENTOS COM ESTRUTURAS MUITO
DIFERENTES:

1) Allyson Bezerra: o PDF original tem um defeito sistemático de extração
   de fonte — a letra "r" antes de determinadas consoantes/vogais (t, v, i,
   í, n, m, f, ç) foi extraída como um caractere combinador solto (U+0335,
   "combining short stroke overlay") seguido de um espaço espúrio, com a
   letra "r" em si sendo perdida (ex.: "No̵ te" em vez de "Norte", "fo̵ mam"
   em vez de "formam", "gove̵ no" em vez de "governo" — 416 ocorrências no
   documento). Esse padrão foi identificado, mapeado e corrigido
   deterministicamente por regex ANTES de qualquer tokenização ou
   segmentação (função `reparar_glifo_r_allyson`), reconstruindo a palavra
   original em praticamente todos os casos (validado por amostragem manual
   e por contagem de palavras-teste conhecidas como "Norte", "governo",
   "criar" antes/depois do reparo). Um único caso residual
   ("comunidadesr\nurais" -> "comunidades rurais") exigia tratamento
   especial por quebra de linha e foi corrigido à parte. O arquivo-fonte
   original (`planos/allyson-bezerra.txt`) NÃO foi alterado — o reparo é
   aplicado em memória neste script, de forma auditável.
   O plano de Allyson é organizado em 11 capítulos temáticos com 157
   propostas numeradas (011 a 167, cada uma com título e parágrafo próprio),
   sem prosa narrativa densa entre elas — por isso a classificação temática
   foi feita item a item (cada número de proposta é seu próprio marcador),
   e não por capítulo. Um defeito de diagramação em duas colunas fez o
   número "017" aparecer no texto antes do "016", e o corpo da proposta
   "106" aparecer fisicamente deslocado para depois do corpo da "107" — em
   nenhum dos dois casos isso afeta o resultado temático, pois os itens
   envolvidos pertencem ao mesmo tema (gestao_publica e infraestrutura,
   respectivamente).

2) Álvaro Dias: documento extenso (~30,5 mil palavras) em 5 "Eixos"
   temáticos, com um capítulo diagnóstico inicial ("O RN de Hoje") dividido
   em 5 subseções tituladas e um sumário no início que duplica todos os
   títulos de seção/subseção antes do corpo real (mesmo problema já visto
   no Maranhão/Piauí/Ceará/Alagoas). Os títulos de subseção do corpo do
   texto (ex.: "Modernização, Governança e Gestão por Resultados")
   aparecem, no PDF original, como uma legenda lateral/selo de ODS
   ENCAIXADA dentro do fluxo de texto em um ponto arbitrário do bloco que
   descrevem — nunca no início real do trecho (mesmo fenômeno de
   diagramação em caixas já visto no plano de JHC em Alagoas). Por isso,
   os marcadores usados para dividir temas DENTRO de um Eixo multitemático
   (Eixo II: Turismo/Cultura/Indústria; Eixo IV: Saúde/Educação/
   Segurança/Assistência Social; Eixo V: Meio Ambiente/Causa Animal) não
   são esses títulos-legenda, e sim a primeira frase narrativa que
   efetivamente abre cada novo tema no corpo do texto (mesmo critério do
   Alagoas). Eixos internamente monotemáticos (I, III) foram tratados como
   um único segmento, sem necessidade de dividir por subseção. O capítulo
   diagnóstico inicial foi dividido pelas 5 subseções tituladas do próprio
   sumário, e a subseção "Educação, saúde e segurança em situação
   preocupante" foi ainda subdividida pelas 3 frases narrativas que abrem,
   respectivamente, o diagnóstico de educação, saúde e segurança dentro
   dela — em vez de tratar o capítulo inteiro como "outros", reduzindo
   artificialmente essa categoria de ~29% para ~18,5% do texto.

3) Cadu Xavier: documento em 13 "Eixos", cada um com uma introdução geral
   (visão política, diagnóstico) seguida de exatamente 4 "Diretrizes
   Estratégicas" numeradas com título próprio. Ao contrário do plano de
   Álvaro Dias, aqui os títulos de subseção são cabeçalhos reais no início
   de cada bloco (sem legenda deslocada), o que tornou a segmentação mais
   direta. Eixos inteiramente monotemáticos (1, 2, 3, 4, 5, 11, 12, 13)
   foram tratados como um único segmento; Eixos dedicados a um público
   específico mas com diretrizes cruzando vários temas (6- Mulheres, 7-
   Juventude, 8- Igualdade Racial, 9- LGBTQIA+, 10- Cultura/Esporte) tiveram
   cada uma das 4 diretrizes classificada individualmente (ex.: a diretriz
   de autonomia econômica de cada público-alvo foi classificada como
   "economia", a de enfrentamento à violência como "seguranca", a de saúde
   como "saude", mantendo o restante como "assistencia_social"). O texto
   de introdução de cada um desses 5 Eixos (visão política, diagnóstico,
   "onde queremos chegar") foi mantido como "assistencia_social" — o tema
   dominante do Eixo como um todo — e não como "outros", por não se tratar
   de um capítulo diagnóstico multitemático genérico como o de Álvaro
   Dias, e sim da introdução de um Eixo já dedicado a um público/tema
   específico do projeto.
"""
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/rio-grande-do-norte/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/rio-grande-do-norte/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "allyson-bezerra", "nome": "Allyson Bezerra", "partido": "União Brasil",
     "categoria": "desafiante"},
    {"slug": "alvaro-dias", "nome": "Álvaro Dias", "partido": "PL",
     "categoria": "desafiante"},
    {"slug": "cadu-xavier", "nome": "Cadu Xavier", "partido": "PT",
     "categoria": "desafiante"},
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
plano governo potiguar potiguares rio grande norte eleições 2026 partido
número coligação fonte fontes status texto seção seções eixo eixos parte
partes bloco blocos documento página páginas inclui incluem também estamos
propõe prevê abertura caminho proposto propostos principais desafios
núcleo contexto visão onde compromisso compromissos destaca destacados
destacado
""".split())

EXTRA_STOPWORDS |= set("""
ods sumário monitoramento revisão implementação
""".split())

# Boilerplate de cabeçalho/rodapé repetido por página do PDF de Cadu Xavier
# ("PLANO DE GOVERNO CADU XAVIER" / slogan "RN QUE CRESCE CUIDANDO DE GENTE"
# em quase toda página) — removido por ser artefato de diagramação, não
# conteúdo temático (achado do auditor independente, 20/08/2026).
EXTRA_STOPWORDS |= set("""
cadu xavier cresce cuidando
""".split())

ALL_STOPWORDS = STOPWORDS | EXTRA_STOPWORDS


def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx + len(marker):] if idx != -1 else text


# ---------------------------------------------------------------------------
# Reparo determinístico do defeito de extração de fonte no plano de Allyson
# Bezerra (ver nota de metodologia no topo do arquivo). Aplicado em memória,
# nunca ao arquivo-fonte.
# ---------------------------------------------------------------------------
def reparar_glifo_r_allyson(text: str) -> str:
    # U+0335 (combining short stroke overlay) substitui a letra "r" perdida;
    # quando seguido de espaço, o espaço também é consumido (o "r" volta a
    # colar na sílaba seguinte, ex.: "No" + [combinador] + " " + "te" ->
    # "Norte"). Quando dois combinadores aparecem em sequência (ex. "rr" de
    # "território"), cada um vira um "r" independente.
    fixed = re.sub("̵ ?", "r", text)
    # Único caso residual: quebra de linha entre duas palavras onde o "r"
    # perdido era a primeira letra da palavra seguinte ("comunidades" +
    # combinador + quebra de linha + "urais" -> "comunidades\nrurais").
    fixed = fixed.replace("comunidadesr\nurais", "comunidades\nrurais")
    return fixed


# ---------------------------------------------------------------------------
# TAREFA 1 — Distribuição temática exaustiva
# ---------------------------------------------------------------------------
TEMAS = ["saude", "seguranca", "educacao", "infraestrutura", "meio_ambiente",
         "economia", "gestao_publica", "assistencia_social", "outros"]

# --- Allyson Bezerra ---------------------------------------------------
# 157 propostas numeradas (011 a 167) organizadas em 11 capítulos temáticos.
# Cada marcador é o próprio número da proposta (padrão "\nNNN\n", único em
# todo o documento — confirmado que não há colisão com números de página,
# que vão só até 43 e nunca aparecem com zero à esquerda). Classificação
# item a item, majoritariamente seguindo o capítulo, com desvios pontuais
# documentados abaixo quando o conteúdo real da proposta diverge do tema do
# capítulo em que está inserida.
_ALLYSON_TEMA_POR_NUM = {}


def _add(rng, tema):
    for n in rng:
        _ALLYSON_TEMA_POR_NUM[n] = tema


_add(range(11, 18), "gestao_publica")        # CAP. 01 — Governo, Gestão, Finanças e Servidores
_add(range(18, 36), "economia")              # CAP. 02 — Desenvolvimento Econômico, Trabalho e Amb. de Negócios
_add(range(36, 52), "saude")                 # CAP. 03 — Saúde
_ALLYSON_TEMA_POR_NUM[37] = "assistencia_social"   # 037 Causa Animal (proteção/bem-estar animal, não saúde humana)
_add(range(52, 74), "educacao")              # CAP. 04 — Educação, Ciência, Tecnologia e Inovação
_add(range(74, 89), "seguranca")             # CAP. 05 — Segurança com Integração e Presença do Estado
_add(range(89, 110), "infraestrutura")       # CAP. 06 — Infraestrutura, Rec. Hídricos, Meio Ambiente e Mobilidade
_ALLYSON_TEMA_POR_NUM[99] = "meio_ambiente"        # 099 Consórcios de Resíduos e Economia Circular
_add(range(110, 121), "economia")            # CAP. 07 — Desenvolvimento Regional e Agricultura
_ALLYSON_TEMA_POR_NUM[116] = "meio_ambiente"       # 116 Convivência Produtiva com o Semiárido (conservação de solo/seca)
_add(range(121, 127), "economia")            # CAP. 08 — Turismo, Eventos e Experiências Potiguares
_add(range(127, 138), "assistencia_social")  # CAP. 09 — Inclusão, acessibilidade e respeito
_ALLYSON_TEMA_POR_NUM[129] = "saude"                # 129 RN Acolhe TEA (rede clínica/multiprofissional)
_ALLYSON_TEMA_POR_NUM[131] = "educacao"             # 131 Educação que Inclui (atendimento educacional especializado)
_ALLYSON_TEMA_POR_NUM[132] = "economia"             # 132 Trabalho e Empreendedorismo Inclusivos
_ALLYSON_TEMA_POR_NUM[133] = "infraestrutura"       # 133 Mobilidade para Todos
_ALLYSON_TEMA_POR_NUM[136] = "saude"                # 136 Órteses, Próteses e Tecnologia Assistiva
_add(range(138, 153), "assistencia_social")  # CAP. 10 — Mulheres, Cuidado e Proteção Social
_ALLYSON_TEMA_POR_NUM[139] = "saude"                 # 139 Saúde da Mulher Perto de Casa
_ALLYSON_TEMA_POR_NUM[140] = "saude"                 # 140 Maternidade Segura e Cuidado Neonatal
_ALLYSON_TEMA_POR_NUM[141] = "seguranca"             # 141 Proteção às Mulheres e Enfrentamento ao Feminicídio
_ALLYSON_TEMA_POR_NUM[143] = "economia"              # 143 Autonomia Econômica das Mulheres
_ALLYSON_TEMA_POR_NUM[149] = "infraestrutura"        # 149 RN Casa Digna (habitação)
_ALLYSON_TEMA_POR_NUM[150] = "infraestrutura"        # 150 Cidade Legal RN (regularização fundiária urbana)
_add(range(153, 168), "assistencia_social")  # CAP. 11 — Cultura, Esporte e Juventude
_ALLYSON_TEMA_POR_NUM[158] = "economia"              # 158 RN Criativo (economia criativa)
_ALLYSON_TEMA_POR_NUM[164] = "economia"              # 164 Jovem do Futuro RN (qualificação profissional)
_ALLYSON_TEMA_POR_NUM[165] = "economia"              # 165 Primeiro Emprego e Aprendizagem
_ALLYSON_TEMA_POR_NUM[166] = "economia"              # 166 Juventude Empreendedora e Conectada

assert set(_ALLYSON_TEMA_POR_NUM) == set(range(11, 168))

# Ordem FÍSICA real dos marcadores no texto (defeito de diagramação em duas
# colunas faz "017" aparecer antes de "016" — ambos gestao_publica, sem
# efeito temático; ver nota de metodologia).
_ALLYSON_ORDEM = [11, 12, 13, 14, 15, 17, 16] + list(range(18, 168))

MARCADORES_ALLYSON = [
    (f"\n{n:03d}\n", _ALLYSON_TEMA_POR_NUM[n]) for n in _ALLYSON_ORDEM
] + [
    # Capítulo de conclusão ("RN — Esperança e Trabalho pra Mudar o RN"),
    # sem numeração de proposta — tratado como "outros" (mesmo critério do
    # capítulo "CONSIDERAÇÕES FINAIS" de Álvaro Dias), em vez de deixá-lo
    # vazar para o tema da última proposta (167, assistencia_social).
    ("Todo plano de governo fala do futuro. Este nasce também de uma experiência concreta.", "outros"),
]

# --- Álvaro Dias ---------------------------------------------------------
# Documento de ~30,5 mil palavras. cursor_inicial pula o sumário inicial
# (que duplica todos os títulos usados como marcador) — usamos 5000 como
# ponto seguro depois do fim do sumário e antes da 1ª ocorrência real dos
# marcadores do capítulo diagnóstico ("O RN de Hoje").
MARCADORES_ALVARO = [
    # --- "O RN de Hoje: a realidade que precisamos endireitar" (capítulo
    # diagnóstico inicial, dividido pelas 5 subseções do próprio sumário; a
    # 4ª subseção foi ainda dividida em 3, pelas frases que efetivamente
    # abrem o diagnóstico de cada área dentro dela) ---
    ("Mais dinheiro arrecadado, pouco resultado entregue", "gestao_publica"),
    ("Um Estado que perdeu competitividade", "economia"),
    ("Quando falta oportunidade, cresce a vulnerabilidade", "assistencia_social"),
    ("Na educação, o Rio Grande do Norte precisa mudar de rumo", "educacao"),
    ("Na saúde, o Rio Grande do Norte ainda convive", "saude"),
    ("Na segurança pública, a população espera mais presença", "seguranca"),
    ("Ao longo dos encontros realizados em todas as regiões do Rio Grande", "outros"),
    # --- EIXO I — Estado Moderno e Gestão Eficiente (monotemático: as 3
    # subseções do sumário — modernização/governança, gestão de pessoas,
    # transformação digital — são todas gestao_publica; sem necessidade de
    # subdividir) ---
    ("EIXO I - Estado Moderno e Gestão Eficiente", "gestao_publica"),
    # --- EIXO II — Desenvolvimento Econômico, Inovação e Emprego (dividido:
    # intro geral + Turismo = economia; Cultura = assistencia_social,
    # seguindo o precedente do projeto mesmo o documento descrever turismo E
    # cultura como "atividades econômicas estratégicas" — ver
    # metodologia_nota; retorno a economia para Indústria/Comércio/
    # Agropecuária) ---
    ("EIXO II - Desenvolvimento Econômico,", "economia"),
    ("Implementar o Plano Estadual de Economia Criativa", "assistencia_social"),
    ("Modernizar e ampliar a infraestrutura logística do Rio Grande", "economia"),
    # --- EIXO III — Infraestrutura e Integração Territorial (monotemático:
    # malha rodoviária, logística, infra municipal, segurança hídrica,
    # energia, transporte público, saneamento, habitação — todas
    # infraestrutura) ---
    ("EIXO III - Infraestrutura e Integração", "infraestrutura"),
    # --- EIXO IV — Saúde, Educação, Segurança e Desenvolvimento Social
    # (intro multitemática = outros; depois dividido por Saúde/Educação/
    # Segurança; Esporte-Assist.Social-Combate à Pobreza-Primeira Infância-
    # Seg. Alimentar-Juventude-Mulheres-Pessoa Idosa-PCD-Direitos Humanos,
    # todas assistencia_social, tratadas como um único segmento final) ---
    ("EIXO IV - Saúde, Educação, Segurança e", "outros"),
    ("Implantar o Programa RN Saúde 2030", "saude"),
    ("Garantir a alfabetização de todas as crianças na idade certa", "educacao"),
    ("Implantar o Plano Estadual Integrado de Enfrentamento ao Crime", "seguranca"),
    ("Fortalecer a governança da Política Estadual de Esporte e Lazer", "assistencia_social"),
    # --- EIXO V — Sustentabilidade, Recursos Naturais e Resiliência
    # Climática (intro multitemática = outros; Meio Ambiente + Recursos
    # Hídricos = meio_ambiente; Causa Animal = assistencia_social, mesmo
    # precedente de Orleans Brandão/MA) ---
    ("EIXO V - Sustentabilidade, Recursos", "outros"),
    ("Fortalecer o Sistema Estadual de Gestão Ambiental", "meio_ambiente"),
    ("Instituir a Política Estadual de Proteção e Bem-Estar Animal", "assistencia_social"),
    ("CONSIDERAÇÕES FINAIS", "outros"),
]
ALVARO_CURSOR_INICIAL = 5000

# --- Cadu Xavier -----------------------------------------------------------
# 13 "Eixos", cada um com introdução + exatamente 4 "Diretrizes
# Estratégicas" numeradas. Eixos monotemáticos tratados como um único
# segmento; Eixos dedicados a um público específico (Mulheres, Juventude,
# Igualdade Racial, LGBTQIA+, Cultura/Esporte) têm cada diretriz classificada
# individualmente quando cruza tema (ver nota de metodologia).
MARCADORES_CADU = [
    ("EIXO 1\nDESENVOLVIMENTO ECONÔMICO,", "economia"),
    ("EIXO 2\nESTADO EFICIENTE", "gestao_publica"),
    ("EIXO 3\nASSISTÊNCIA SOCIAL", "assistencia_social"),
    ("EIXO 4\nEDUCAÇÃO, CIÊNCIA", "educacao"),
    ("EIXO 5\nSAÚDE, CUIDADO", "saude"),
    ("EIXO 6\nMULHERES, AUTONOMIA", "assistencia_social"),
    ("1. Autonomia econômica, trabalho, renda e prosperidade", "economia"),
    ("2. Vida livre de violência, prevenção e proteção da vida", "seguranca"),
    ("3. Saúde integral, direito ao cuidado e liberdade de tempo", "saude"),
    ("4. Equidade, participação e gestão integrada", "assistencia_social"),
    ("EIXO 7\nJUVENTUDE", "assistencia_social"),
    ("1. Educação que abre caminhos e organiza trajetórias", "educacao"),
    ("2. Trabalho digno, renda, inovação e profissões do futuro", "economia"),
    ("3. Saúde integral, proteção da vida e direito ao futuro", "saude"),
    ("4. Cultura, esporte, território e participação", "assistencia_social"),
    ("EIXO 8\nIGUALDADE RACIAL", "assistencia_social"),
    ("1. Estado antirracista, representativo e participativo", "assistencia_social"),
    ("2. Educação antirracista, cultura, memória e liberdade religiosa", "educacao"),
    ("3. Trabalho, renda e desenvolvimento com identidade", "economia"),
    ("4. Saúde, proteção da vida e dos territórios", "saude"),
    ("EIXO 9\nDIVERSIDADE", "assistencia_social"),
    ("1. Cidadania, participação e presença nos territórios", "assistencia_social"),
    ("2. Proteção da vida, enfrentamento às violências e acesso à justiça", "seguranca"),
    ("3. Saúde integral, cuidado e dignidade", "saude"),
    ("4. Educação, cultura, trabalho e autonomia", "assistencia_social"),
    ("EIXO 10\nCULTURA, ESPORTE", "assistencia_social"),
    ("1. Cultura viva, patrimônio e identidade em todos os territórios", "assistencia_social"),
    ("2. Fomento, trabalho e economia criativa", "economia"),
    ("3. Esporte, lazer, saúde e inclusão", "assistencia_social"),
    ("4. Rede territorial, cooperação e participação", "assistencia_social"),
    ("EIXO 11\nINFRAESTRUTURA E LOGÍSTICA", "infraestrutura"),
    ("EIXO 12\nSEGURANÇA PÚBLICA", "seguranca"),
    ("EIXO 13\nSUSTENTABILIDADE", "meio_ambiente"),
]

MARCADORES = {
    "allyson-bezerra": MARCADORES_ALLYSON,
    "alvaro-dias": MARCADORES_ALVARO,
    "cadu-xavier": MARCADORES_CADU,
}
CURSOR_INICIAL_PADRAO = {
    "alvaro-dias": ALVARO_CURSOR_INICIAL,
}


def tokenize(text: str):
    return [w.lower() for w in WORD_RE.findall(text)]


def word_freq(text: str, top_n=20):
    tokens = tokenize(text)
    total_tokens = len(tokens)
    filtered = [w for w in tokens if w not in ALL_STOPWORDS and len(w) > 2]
    counts = Counter(filtered)
    top = counts.most_common(top_n)
    return total_tokens, counts, top


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
# político com o plano nacional do partido/governo federal, sem citar
# evidência de fato. Isto é especialmente relevante no RN: Cadu Xavier
# (PT) cita o governo Lula/parcerias federais com frequência ao longo do
# documento (ver metodologia_nota) — confirmado que essas menções não
# disparam is_evidencia por si só. "plano nacional de logística" é mantido:
# é uma referência específica e legítima a um documento técnico federal,
# não um gatilho genérico de alinhamento partidário.
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
# TAREFA 4 — Texto compartilhado entre os 3 planos (achado pré-computado por
# find_shared_text_rn.py; resultado colado abaixo em achado_texto_compartilhado
# / texto_compartilhado, mesmo padrão usado nos demais estados).
# ---------------------------------------------------------------------------
ACHADO_TEXTO_COMPARTILHADO = {
    "resumo": (
        "A checagem de blocos de texto idêntico ou quase idêntico entre os "
        "três planos do RN (mínimo de 150 caracteres, 8 palavras "
        "consecutivas), par a par, não encontrou nenhum bloco compartilhado "
        "entre nenhum dos 3 pares possíveis — resultado no mesmo sentido do "
        "observado no Maranhão, Piauí, Ceará, Pernambuco e Alagoas (0 "
        "blocos em todos), e diferente do observado na Paraíba (blocos de "
        "texto idênticos entre planos de candidatos rivais, incluindo um "
        "parágrafo repetido nos três planos)."
    ),
    "pares_verificados": [
        "allyson-bezerra x alvaro-dias",
        "allyson-bezerra x cadu-xavier",
        "alvaro-dias x cadu-xavier",
    ],
    "blocos_encontrados": 0,
}

TEXTO_COMPARTILHADO = {
    "pares_comparados": [
        "allyson-bezerra_x_alvaro-dias",
        "allyson-bezerra_x_cadu-xavier",
        "alvaro-dias_x_cadu-xavier",
    ],
    "resultado_por_par": {
        "allyson-bezerra_x_alvaro-dias": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de 150+ caracteres idênticos (mínimo de 8 "
                "palavras consecutivas) encontrado entre estes dois planos."
            ),
        },
        "allyson-bezerra_x_cadu-xavier": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de 150+ caracteres idênticos (mínimo de 8 "
                "palavras consecutivas) encontrado entre estes dois planos."
            ),
        },
        "alvaro-dias_x_cadu-xavier": {
            "blocos_identicos": [],
            "observacao": (
                "Nenhum bloco de 150+ caracteres idênticos (mínimo de 8 "
                "palavras consecutivas) encontrado entre estes dois planos."
            ),
        },
    },
    "metodologia": (
        "Mesmo método de detecção usado nas análises da Paraíba, Maranhão, "
        "Piauí, Ceará, Pernambuco e Alagoas: índice de n-gramas de 8 "
        "palavras consecutivas para localizar trechos idênticos ou quase "
        "idênticos entre os planos, com blocos adjacentes mesclados e um "
        "piso de 150 caracteres para descartar coincidências triviais "
        "(conectores, boilerplate curto). O RN tem 3 candidatos com plano "
        "de governo coletado neste projeto, resultando em 3 pares possíveis."
    ),
    "observacao_editorial": (
        "Nenhum bloco foi encontrado entre os três planos do RN, nos três "
        "pares possíveis. Isso não prova ausência de uso de consultoria "
        "compartilhada ou de templates de propostas — apenas que não há "
        "trechos literalmente idênticos detectáveis por este método entre "
        "os documentos disponíveis. Os três planos têm perfis de redação e "
        "estrutura muito diferentes entre si (ver metodologia_nota), o que "
        "por si só já torna reaproveitamento de texto literal entre as "
        "campanhas pouco provável."
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
        if slug == "allyson-bezerra":
            raw_text = reparar_glifo_r_allyson(raw_text)
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        cursor_inicial = CURSOR_INICIAL_PADRAO.get(slug)
        if cursor_inicial is None:
            # Se o 1º marcador aparecer mais de uma vez (documento com
            # sumário/índice que repete os títulos das seções antes do
            # corpo real), pula para a 2ª ocorrência, para não segmentar
            # dentro do índice.
            primeiro_marcador = marcadores[0][0]
            primeira_ocorrencia = corpo.find(primeiro_marcador)
            segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
            n_ocorrencias_1o_marcador = corpo.count(primeiro_marcador)
            cursor_inicial = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
            print(f"{slug}: 1º marcador aparece {n_ocorrencias_1o_marcador}x no corpo "
                  f"(cursor_inicial={cursor_inicial})")
        else:
            print(f"{slug}: cursor_inicial fixo = {cursor_inicial} (pula sumário)")

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        # O Índice de Base Empírica também é calculado a partir de
        # corpo[cursor_inicial:], para não deixar o sumário/índice inicial
        # (que no plano de Álvaro Dias usa linhas com pontilhado de página,
        # ex.: "Modernização, Governança e Gestão por Resultados ....... 23")
        # contaminar os exemplos de "retórica sem evidência" com entradas de
        # sumário que nunca foram, de fato, uma frase do corpo do plano.
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
        "gerado_em": "19 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto, adaptada apenas no "
            "gentílico/nome do estado. Mostra os termos mais repetidos por "
            "candidato e o agregado dos três planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "marcadores de seção reais. Os três planos do RN têm estruturas "
            "muito diferentes entre si: o de Allyson Bezerra é organizado em "
            "157 propostas numeradas e classificado item a item; o de Álvaro "
            "Dias é organizado em 5 'Eixos' com um capítulo diagnóstico "
            "inicial dividido por área, usando como marcador a primeira "
            "frase narrativa que abre cada tema (não os títulos-legenda de "
            "ODS, que no PDF original aparecem deslocados dentro do bloco de "
            "texto que descrevem); o de Cadu Xavier é organizado em 13 "
            "'Eixos', cada um com 4 'Diretrizes Estratégicas' numeradas "
            "usadas diretamente como marcador. Cada segmento de texto entre "
            "dois marcadores consecutivos foi contado (em número de "
            "palavras) e atribuído a UM dos 9 temas. Quando um trecho do "
            "documento original já reunia explicitamente múltiplos temas de "
            "forma indivisível, o segmento foi classificado item a item "
            "sempre que os itens individuais eram identificáveis, ou como "
            "'outros' quando não era possível separar com segurança. Ver "
            "nota de metodologia completa no topo do script de análise "
            "(build_analysis_rn.py) para as decisões editoriais específicas "
            "de cada candidato."
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
            "específico para o RN, para manter comparabilidade entre "
            "estados. O regex de evidência (pilar C) NÃO trata menção a "
            "'plano nacional' ou alinhamento com o governo federal/Lula "
            "como evidência por si só — apenas referências específicas a "
            "estudos, dados institucionais (IBGE, IPEA, DATASUS etc.) ou "
            "modelos comprovadamente adotados contam (ver comentário no "
            "código-fonte sobre a correção do EVIDENCIA_RE)."
        ),
        "metodologia_nota": (
            "O RN não tem incumbente concorrendo (cadeira aberta) — os três "
            "planos analisados (Allyson Bezerra, Álvaro Dias, Cadu Xavier) "
            "são todos de candidatos classificados como 'desafiante', sem "
            "um candidato de continuidade direto do governo Fátima Bezerra "
            "para servir de contraponto ao padrão observado em outros "
            "estados do projeto (Paraíba, Maranhão, Alagoas). Ainda assim, "
            "Cadu Xavier (PT) é o candidato mais alinhado ao governo "
            "estadual atual e ao Governo Federal — seu plano cita o "
            "'governo da professora Fátima Bezerra' e o 'presidente Lula' "
            "com frequência, inclusive como parceiro estratégico em "
            "praticamente todos os 13 Eixos. Essas menções não disparam por "
            "si só o pilar C (evidência/mecanismo causal externo) do Índice "
            "de Base Empírica — ver metodologia_indice_base_empirica. "
            "O plano de Allyson Bezerra (União Brasil) foi extraído de um "
            "PDF com um defeito sistemático de fonte que substituiu a letra "
            "'r' antes de certas consoantes por um caractere combinador "
            "solto (416 ocorrências); esse defeito foi corrigido "
            "deterministicamente por regex antes da análise (função "
            "reparar_glifo_r_allyson em build_analysis_rn.py) — o arquivo-"
            "fonte original não foi alterado. O plano de Álvaro Dias (PL) é "
            "o mais extenso dos três (~30,5 mil palavras, quase o dobro do "
            "de Cadu Xavier e mais de 4x o de Allyson Bezerra) e o único "
            "com um capítulo diagnóstico inicial longo e tematicamente "
            "organizado ('O RN de Hoje'), que foi dividido por área "
            "(fiscal/gestão, economia, vulnerabilidade social, educação, "
            "saúde, segurança) em vez de tratado integralmente como "
            "'outros' — reduzindo essa categoria de ~29% para ~18,5% do "
            "texto. O plano de Cadu Xavier é o único dos três organizado "
            "explicitamente por público-alvo (Eixos dedicados a Mulheres, "
            "Juventude, Igualdade Racial e População Negra, Diversidade "
            "LGBTQIA+, além de Cultura/Esporte/Lazer), o que eleva "
            "estruturalmente sua parcela de 'assistencia_social' (~33,6% "
            "do texto) frente aos outros dois candidatos — um reflexo do "
            "desenho do próprio documento, não um artefato da metodologia "
            "de classificação."
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
