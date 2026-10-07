#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Rondônia 2026.

Réplica da metodologia usada nos 9 estados do Nordeste (build_analysis_ma.py
como script canônico, já corrigido por um validador independente): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica à
usada em todos os outros estados, reaproveitada sem alterações para manter
comparabilidade). Também gera as nuvens de palavras (wordcloud) embutidas em
base64 em cada candidato.

NOTA METODOLÓGICA ESPECÍFICA DE RONDÔNIA — DOIS DOCUMENTOS BEM ESTRUTURADOS,
MAS COM TRATAMENTOS DE CURSOR DIFERENTES PARA A DISTRIBUIÇÃO TEMÁTICA E PARA
O ÍNDICE DE BASE EMPÍRICA:

Adailton Fúria: documento em PDF de 116 páginas com um "navegação do
documento" (sumário) logo na abertura, seguido de dois capítulos de bio
(Adailton, depois o vice Everton Leoni), um capítulo de diagnóstico ("O Estado
que a população sente") e um capítulo de método/estrutura ("O que propomos
fazer") — só então começam os 4 pilares numerados (1. a 4.), cada um dividido
em 5 programas numerados (1.1 a 4.5) com subseções em algarismos romanos (I,
II, III). Para a DISTRIBUIÇÃO TEMÁTICA, todo esse material introdutório
(sumário + bios + diagnóstico + metodologia) cai automaticamente em "outros"
como front matter, pois o primeiro marcador usado ("1. Proteger\na Vida.")
não se repete no sumário (o sumário grafa o título em uma única linha, sem a
quebra "Proteger\na Vida" usada no corpo real) — não é necessário nenhum
truque de 2ª ocorrência aqui. Para o ÍNDICE DE BASE EMPÍRICA, seguindo
instrução específica deste estado, aplicamos um corte fixo de
cursor_inicial=6397 caracteres — o ponto exato em que termina a página de
"navegação do documento" (sumário/TOC) e começa o corpo real de prosa
("Adailton Furia:\nUma história de trabalho,..."). Esse corte é aplicado
SOMENTE à chamada de base_empirica_analise (não à distribuição temática, nem
ao total_palavras), seguindo o padrão já usado em build_analysis_al.py:
`be = base_empirica_analise(corpo[cursor_inicial:], slug)`. Isso preserva no
cálculo do índice o parágrafo de diagnóstico da carta de abertura ("nove em
cada dez rondonienses dependem da saúde pública", "cerca de metade da
população... Cadastro Único"), que contém dado quantitativo relevante para o
pilar de diagnóstico, ao mesmo tempo em que descarta o sumário/TOC (que não
contém frases analisáveis).

Adailton Fúria — decisões de classificação não óbvias: dentro do programa 1.5
("Mulher Protegida, Autônoma e Saudável"), o conteúdo é dominado por
prevenção/proteção contra violência (feminicídio, Rede Lilás, DEAMs) e não
por assistência à saúde propriamente dita — classificado como
assistencia_social, seguindo o precedente do projeto para seções de proteção
a grupos vulneráveis. Dentro do programa 2.5 ("Cultura, Esporte e
Juventude"), mantém-se o precedente do projeto (cultura/esporte/juventude =
assistencia_social). O programa 3.3 ("Água, Saneamento e Proteção
Climática") foi dividido em suas 2 subseções: a subseção I ("Água,
esgotamento, CAERD e regulação") = infraestrutura; a subseção II ("Resíduos,
proteção da água e adaptação climática", que trata de resíduos sólidos,
proteção de mananciais e adaptação a secas/cheias/incêndios) = meio_ambiente.
O programa 4.1 ("Ciência, Talentos e Inovação") foi classificado como
economia (não como educação), seguindo o precedente já registrado em
build_analysis_al.py: seções de inovação/ciência e tecnologia voltadas a
startups, incubadoras, propriedade intelectual e investimento produtivo são
tratadas como economia em todos os estados do projeto — aqui o conteúdo é
dominado por fomento a startups, incubadoras, empresas inovadoras e
propriedade intelectual, e não por currículo escolar ou universidades (que já
têm seção própria em 1.2, classificada como educacao). Por fim, a seção final
"Os primeiros 100 dias" reorganiza, sob 4 subtítulos temáticos únicos no
documento (SAÚDE / EDUCAÇÃO / SEGURANÇA PÚBLICA / GOVERNAR PARA ENTREGAR),
uma síntese de compromissos já detalhados nos pilares anteriores — foi
segmentada por esses 4 subtítulos (mapeados aos respectivos temas) em vez de
cair inteira em "outros", já que os próprios subtítulos declaram o tema de
cada bloco.

Marcos Rogério: documento também bem estruturado, em 10 "Eixos de
Desenvolvimento" numerados (EIXO 1 a EIXO 10), cada um com título temático
claro e conteúdo internamente coerente com o tema anunciado — dispensando,
com uma única exceção, segmentação abaixo do nível de Eixo. O documento tem
um "II. SUMÁRIO" (índice) que repete o título de cada Eixo antes do corpo
real (mesmo padrão observado em Ceará/Alagoas/Piauí/Maranhão) — protegido
pela lógica-padrão do projeto: como o primeiro marcador ("EIXO 1 - SAÚDE:
PESSOAS EM PRIMEIRO LUGAR") aparece 2 vezes no corpo (a 1ª no sumário, a 2ª
no corpo real), a distribuição temática usa a 2ª ocorrência como ponto de
partida da segmentação (cursor_inicial calculado automaticamente, replicando
o padrão de todos os demais scripts do projeto). Isso evita que o sumário
seja segmentado como se fosse o Eixo 1. Para o ÍNDICE DE BASE EMPÍRICA, a
instrução específica deste estado é cursor_inicial_base_empirica=0: não há
carta de capa nem sumário "relevante" o bastante para exigir corte — a carta
de abertura do candidato e o capítulo de diagnóstico (IV. DIAGNÓSTICO), que
antecedem o sumário e os Eixos, já trazem prosa analisável rica em dados
(taxas de criminalidade, indicadores de saúde, dados orçamentários) que deve
ser preservada no cálculo do índice; o próprio sumário (blocos curtos de
título + reticências + número de página) não passa pelo filtro de
MIN_SENTENCE_WORDS/looks_like_header, então sua presença no corpo usado para
base_empirica não distorce o resultado. Por isso `cursor_inicial_base_empirica
= 0` e `be = base_empirica_analise(corpo[0:], slug)` — ou seja, o corpo
completo, sem nenhum corte.

Marcos Rogério — decisão de classificação não óbvia: dentro do EIXO 8 ("MEIO
AMBIENTE"), a subseção "PROTEÇÃO ANIMAL" (bem-estar animal, castração,
delegacia eletrônica de defesa animal) foi destacada como assistencia_social,
seguindo o mesmo precedente usado em Ceará/Maranhão/Paraíba para seções de
proteção e bem-estar animal — o restante do Eixo 8 (zoneamento, licenciamento
ambiental, combate a incêndios, bioeconomia florestal) permanece
meio_ambiente. O EIXO 6 ("DESENVOLVIMENTO ECONÔMICO") inclui trechos sobre
licenciamento ambiental e regularização fundiária rural (SEDAM/IDARON,
LAC Florestal, "Renda Verde Rondônia"/bioeconomia) que, no texto, são
explicitamente enquadrados como desburocratização e fomento à produção (não
como política ambiental autônoma) — mantidos em economia, consistente com o
título e o fio condutor do Eixo. O EIXO 9 ("DESENVOLVIMENTO URBANO E
MUNICIPALISMO"), cujo conteúdo é dominado por habitação, saneamento,
mobilidade urbana e obras municipais, foi classificado como infraestrutura
(e não gestao_publica), seguindo o precedente do projeto para seções de
desenvolvimento urbano/habitação/saneamento.
"""
import base64
import re
from collections import Counter
from io import BytesIO
from pathlib import Path
import json

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/rondonia/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/rondonia/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "adailton-furia", "arquivo": "adailton_furia", "nome": "Adailton Fúria", "partido": "PSD",
     "categoria": ("candidato de continuidade — apoiado publicamente pelo governador em "
                   "exercício Marcos Rocha (PSD, ex-União Brasil), que não pode concorrer "
                   "à reeleição por já estar em seu 2º mandato consecutivo (2019-2023, "
                   "reeleito para 2023-2027) [fonte: Rondônia Dinâmica/Portal Rondônia, "
                   "fev/2026, \"Marcos Rocha declara apoio à pré-candidatura de Adailton "
                   "Fúria\"]")},
    {"slug": "marcos-rogerio", "arquivo": "marcos_rogerio", "nome": "Marcos Rogério", "partido": "PL",
     "categoria": ("desafiante — senador da República pelo PL, consolidado como principal "
                   "opositor ao atual governo estadual; candidatura própria do PL, sem "
                   "apoio do governador em exercício [fonte: Rondônia Ao Vivo, maio/2026, "
                   "\"Marcos Rogério vai se consolidando como principal oposição ao atual "
                   "governo\"; Poder360, \"PL lança Marcos Rogério ao governo de Rondônia\"]")},
    {"slug": "hildon-chaves", "arquivo": "hildon_chaves", "nome": "Hildon Chaves",
     "partido": "Federação União Progressista e Republicanos",
     "categoria": ("desafiante — ex-prefeito de Porto Velho; está em empate técnico genuíno "
                   "com Adailton Fúria (PSD, candidato de continuidade apoiado pelo "
                   "governador Marcos Rocha) pela 2ª colocação e pela vaga no 2º turno, "
                   "atrás do líder isolado Marcos Rogério (PL), conforme pesquisa Phoenix "
                   "(22/08/2026) — situação estruturalmente parecida com o empate técnico "
                   "do Paraná (ver RELATORIO_COMPARATIVO_SUL.md), mas aqui sem uma "
                   "arbitragem dedicada equivalente; passou a ser coberto como candidato "
                   "pleno em 25/08/2026 por não haver justificativa clara para preferir "
                   "Adailton Fúria isoladamente")},
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
plano governo rondônia rondoniense rondonienses eleições 2026 partido número
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

# Adailton Fúria: 4 pilares numerados (1. a 4.), cada um com 5 programas
# (1.1 a 4.5), cada programa subdividido em 2-3 subseções em algarismos
# romanos. Como cada programa (1.1, 1.2, ...) tem título temático claro e
# conteúdo internamente coerente com o tema anunciado, a granularidade de
# marcador usada é a de programa (não a de subseção romana), exceto no
# programa 3.3 ("Água, Saneamento e Proteção Climática"), que precisou ser
# dividido em suas 2 subseções romanas por cruzar dois temas do projeto
# (infraestrutura de água/esgoto x proteção ambiental/climática). Ver notas
# completas de classificação no docstring do módulo.
MARCADORES_ADAILTON = [
    ("1. Proteger\na Vida.", "outros"),  # abertura do Pilar 1 (recapitula os 5 programas, sem tema próprio)
    ("1.1 Saúde Perto de Quem\nPrecisa", "saude"),
    ("1.2 Educação para a Vida e o\nFuturo", "educacao"),
    ("1.3 Cuidado, Direitos e\nCidadania", "assistencia_social"),
    ("1.4 Rondônia Segura e de Paz", "seguranca"),
    ("1.5 Mulher Protegida,\nAutônoma e Saudável", "assistencia_social"),
    ("2. Dar força a\nquem trabalha e\nproduz.", "outros"),  # abertura do Pilar 2
    ("2.1 Campo Forte: Agricultura\nFamiliar e Agroindústria", "economia"),
    ("2.2 Bioeconomia, Cadeias e\nNovos Mercados", "economia"),
    ("2.3 Trabalho, Negócios e\nRenda", "economia"),
    ("2.4 Indústria, Comércio,\nTurismo e Inovação", "economia"),
    ("2.5 Cultura, Esporte e\nJuventude", "assistencia_social"),
    ("3. Abrir caminhos\npara viver\nbem, produzir e\npreservar.", "outros"),  # abertura do Pilar 3
    ("3.1 Rondônia Conectada:\nEnergia e Internet", "infraestrutura"),
    ("3.2 Estradas e Logística que\nAproximam", "infraestrutura"),
    ("3.3 Água, Saneamento e\nProteção Climática", "infraestrutura"),  # intro + subseção I (água/CAERD)
    ("II Resíduos, proteção da água e adaptação\nclimática", "meio_ambiente"),  # subseção II de 3.3
    ("3.4 Moradia, Cidades e Terra\nRegular", "infraestrutura"),
    ("3.5 Floresta Viva e\nDesenvolvimento\nResponsável", "meio_ambiente"),
    ("4. Governar para\nEntregar Mais.", "outros"),  # abertura do Pilar 4
    ("4.1 Ciência, Talentos e\nInovação", "economia"),
    ("4.2 Serviço Público que\nResolve", "gestao_publica"),
    ("4.3 Contas em Ordem e Futuro\nProtegido", "gestao_publica"),
    ("4.4 Planejar, Investir e Prestar\nContas", "gestao_publica"),
    ("4.5 Governo Íntegro e\nMunicípios Fortes", "gestao_publica"),
    ("Os primeiros\n100 dias", "outros"),  # transição para o capítulo "plano tático"
    ("SAÚDE\n\n\n\n▪", "saude"),
    ("EDUCAÇÃO\n\n\n\n▪", "educacao"),
    ("SEGURANÇA PÚBLICA\n\n\n\n▪", "seguranca"),
    ("GOVERNAR PARA ENTREGAR\n\n\n\n▪", "gestao_publica"),
    ("O futuro de Rondônia\ncomeça com confiança.", "outros"),  # encerramento
]

# Marcos Rogério: 10 "Eixos de Desenvolvimento" numerados, cada um com título
# temático claro e conteúdo internamente coerente — dispensando segmentação
# abaixo do nível de Eixo, com a única exceção da subseção "PROTEÇÃO ANIMAL"
# dentro do EIXO 8 (Meio Ambiente). Ver notas completas de classificação no
# docstring do módulo.
MARCADORES_MARCOS = [
    ("EIXO 1 - SAÚDE: PESSOAS EM PRIMEIRO LUGAR", "saude"),
    ("EIXO 2 - EDUCAÇÃO E INOVAÇÃO: PREPARANDO PARA O AMANHÃ", "educacao"),
    ("EIXO 3 - DESENVOLVIMENTO SOCIAL E CIDADANIA", "assistencia_social"),
    ("EIXO 4 - CULTURA, ESPORTE E LAZER", "assistencia_social"),
    ("EIXO 5 - SEGURANÇA PÚBLICA: PAZ NO CAMPO, SEGURANÇA NA\n            CIDADE E COMBATE AO CRIME ORGANIZADO.",
     "seguranca"),
    ("EIXO 6 - DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("EIXO 7 - INFRAESTRUTURA E LOGÍSTICA", "infraestrutura"),
    ("EIXO 8 - MEIO AMBIENTE", "meio_ambiente"),
    ("PROTEÇÃO ANIMAL", "assistencia_social"),  # subseção do Eixo 8
    ("EIXO 9 - DESENVOLVIMENTO URBANO E MUNICIPALISMO", "infraestrutura"),
    ("EIXO 10 - GESTÃO ESTRATÉGICA, FINANÇAS/ECONOMIA E\n                     VALORIZAÇÃO DO SERVIDOR",
     "gestao_publica"),
    ("VIII. A MUDANÇA DA QUAL RONDÔNIA PRECISA", "outros"),  # encerramento
]

# Hildon Chaves (adicionado em 25/08/2026 — ver docstring do módulo para o
# contexto da adição): documento em 14 "Eixos" numerados (EIXO 01 a EIXO 14),
# cada um com um título de 1 a 3 linhas, seguido de "Frentes e Diretrizes
# Estratégicas" (subseções x.1, x.2, ...) e, ao final, um apêndice "PLANO
# TÁTICO DOS 100 PRIMEIROS DIAS" organizado em 3 Blocos com 19 ações
# numeradas. Estrutura muito próxima à de Marcos Rogério (Eixos numerados,
# títulos temáticos claros, conteúdo internamente coerente com o tema
# anunciado) — por isso a granularidade usada aqui é, na maior parte, a de
# Eixo inteiro, com duas exceções documentadas abaixo. Cada título de Eixo
# tem 2 ocorrências no corpo (a página "EIXO NN" de abertura/divisória do
# capítulo — que só repete o título e a lista de frentes, sem conteúdo
# analisável — e a página seguinte, com o título de novo e o texto real do
# capítulo); como a lógica-padrão do projeto (usada em main()) só pula para
# a 2ª ocorrência do PRIMEIRO marcador da lista, os títulos dos Eixos 2 a 14
# usados aqui são buscados a partir do cursor (posição) deixado pelo
# marcador anterior — como esse cursor já está bem à frente da página
# "divisória" de cada Eixo (ela é sempre imediatamente anterior ao corpo
# real dentro do próprio Eixo, nunca antes dele), o find() sempre encontra
# a ocorrência correta (a página divisória do Eixo seguinte, que é de fato
# onde aquele Eixo começa), sem precisar de nenhum truque adicional.
#
# Exceção 1 — EIXO 01 ("Cidadania e Combate à Corrupção"): título único no
# documento (não bate com o texto do sumário/TOC, que grafa o título em
# linha única com pontos e número de página), por isso é o único Eixo cuja
# 1ª ocorrência (página divisória "EIXO 01") cai no corte automático do
# cursor_inicial_distribuicao (ver main()) — a 2ª ocorrência (corpo real) é
# usada como início da segmentação, e tudo antes dela (capa, sumário,
# apresentação, mensagem, "o momento de Rondônia", a própria página
# divisória do Eixo 1) cai em "outros" como front matter. Dentro do Eixo 1,
# o conteúdo mistura dois temas do projeto sem nenhuma subseção nomeada que
# permita separá-los preservando a granularidade de "frente" usada no
# resto do documento: as 2 primeiras propostas (Programa de Integridade,
# transparência/acesso à informação) são gestão pública, e as 4 seguintes
# (cidadania itinerante, igualdade de oportunidades, combate a preconceito,
# direitos humanos) são assistência social — mesmo par de temas que Adailton
# Fúria já separa em seções distintas neste mesmo estado ("Governo Íntegro"
# = gestao_publica vs. "Cuidado, Direitos e Cidadania" = assistencia_social).
# Como não há subtítulo textual dividindo as 6 propostas do Eixo 1, o corte
# foi feito no início literal da 3ª proposta ("Expandir as ações itinerantes
# de cidadania"), a única forma de preservar a divisão temática real sem
# inventar um marcador que não existe no documento.
#
# Exceção 2 — o apêndice "PLANO TÁTICO DOS 100 PRIMEIROS DIAS": diferente
# dos 14 Eixos, os 3 "Blocos" deste apêndice NÃO são internamente coerentes
# com um único tema (ex.: o Bloco II mistura ações de segurança, saúde,
# educação, infraestrutura e economia) — por isso, seguindo o mesmo
# princípio já usado no "Os primeiros 100 dias" de Adailton Fúria (segmentar
# por subtítulo real quando o subtítulo declara o tema do bloco), aqui a
# segmentação desce ao nível de cada uma das 19 ações numeradas (ou grupos
# consecutivos de ações do mesmo tema), usando o título de cada ação como
# marcador. O Bloco I (ações 01-05) é inteiramente gestão pública (sistema
# de governança, prioridades estratégicas, capacidade financeira, painel de
# resultados, integridade) e não precisou ser subdividido. O Bloco II
# (ações 06-14) foi dividido em 5 segmentos: 06-07 segurança (recursos do
# Fundo Nacional de Segurança Pública; plano de redução do feminicídio —
# mantido em segurança, mesmo precedente já usado no próprio Eixo 2 deste
# candidato para a Patrulha Maria da Penha), 08-10 saúde (filas, plano
# materno-infantil, capacidade de atendimento), 11-12 educação (governança
# das aquisições da SEDUC, inventário da infraestrutura escolar — mantido em
# educação, e não em infraestrutura ou gestao_publica, por serem ações
# operacionais específicas da rede escolar), 13 infraestrutura (malha
# rodoviária e pontes) e 14 economia (mapa das cadeias produtivas). O Bloco
# III (ações 15-19) foi dividido em 3 segmentos: 15-17 economia (ambiente de
# negócios, base exportadora, observatório do turismo), 18 assistência
# social (mapa único de vulnerabilidade social) e 19 gestão pública
# (priorização de serviços públicos digitais). Os textos de abertura de cada
# Bloco (breves parágrafos de transição antes da 1ª ação) caem em "outros"
# quando o Bloco mistura temas (Bloco II e III) ou ficam dentro do primeiro
# segmento temático quando o Bloco é uniforme (Bloco I). O fechamento "Ao
# final dos 100 dias" e o capítulo "ENCERRAMENTO" (mensagem de fechamento do
# plano, sem conteúdo classificável em um tema específico) foram mantidos
# como "outros", seguindo o mesmo precedente usado para os encerramentos de
# Adailton Fúria e Marcos Rogério.
#
# Decisão de classificação não óbvia adicional: a subseção 13.6 ("Proteção
# da Fauna, Bem-estar Animal e Biodiversidade", dentro do Eixo 13 —
# Desenvolvimento Ambiental) foi MANTIDA em meio_ambiente, ao contrário do
# precedente usado para a subseção equivalente de Marcos Rogério ("PROTEÇÃO
# ANIMAL", classificada como assistencia_social). A diferença: em Marcos
# Rogério a subseção é uma seção autônoma dedicada quase exclusivamente a
# bem-estar de animais domésticos (castração, delegacia eletrônica de
# defesa animal); aqui a única proposta da subseção funde, numa única frase
# indivisível, bem-estar animal doméstico (castração de cães e gatos),
# proteção de fauna silvestre e combate ao tráfico de animais, e o texto de
# abertura da diretriz enquadra explicitamente o conjunto como "componente
# essencial da política ambiental" — não há como separar sem fragmentar uma
# única proposta em pedaços menores que os demais marcadores do documento.
MARCADORES_HILDON = [
    ("CIDADANIA E COMBATE À\nCORRUPÇÃO", "gestao_publica"),  # Eixo 1, propostas 1-2 (integridade/transparência)
    ("Expandir as ações itinerantes de cidadania", "assistencia_social"),  # Eixo 1, propostas 3-6 (cidadania/direitos)
    ("SEGURANÇA PÚBLICA", "seguranca"),  # Eixo 2 inteiro, inclui Subeixo 2.1 (sistema prisional) e 2.2 (trânsito)
    ("SAÚDE PÚBLICA", "saude"),  # Eixo 3 inteiro
    ("EDUCAÇÃO PÚBLICA", "educacao"),  # Eixo 4 inteiro
    ("ASSISTÊNCIA SOCIAL", "assistencia_social"),  # Eixo 5 inteiro
    ("AGROPECUÁRIA E CADEIAS\nPRODUTIVAS", "economia"),  # Eixo 6 inteiro, inclui 6.4 bioeconomia
    ("INFRAESTRUTURA", "infraestrutura"),  # Eixo 7 inteiro
    ("HABITAÇÃO E\nDESENVOLVIMENTO TERRITORIAL", "infraestrutura"),  # Eixo 8 inteiro
    ("CULTURA", "assistencia_social"),  # Eixo 9 inteiro
    ("ESPORTE E LAZER", "assistencia_social"),  # Eixo 10 inteiro
    ("INDÚSTRIA, COMÉRCIO,\nEMPREENDEDORISMO E\nINOVAÇÃO", "economia"),  # Eixo 11 inteiro
    ("TURISMO", "economia"),  # Eixo 12 inteiro
    ("DESENVOLVIMENTO AMBIENTAL E\nSUSTENTÁVEL", "meio_ambiente"),  # Eixo 13 inteiro, inclui 13.6 (ver nota acima)
    ("MODERNIZAÇÃO DA\nADMINISTRAÇÃO PÚBLICA E\nCIDADANIA", "gestao_publica"),  # Eixo 14 inteiro
    ("PLANO TÁTICO\n100 PRIMEIROS DIAS", "outros"),  # abertura do apêndice tático
    ("ORGANIZAR O GOVERNO E FORTALECER A CAPACIDADE DE\nEXECUÇÃO", "gestao_publica"),  # Bloco I (ações 01-05)
    ("CONHECER A REALIDADE E COLOCAR AS PRIORIDADES EM\nEXECUÇÃO", "outros"),  # abertura do Bloco II (mistura temas)
    ("DESTRAVAR A EXECUÇÃO DOS RECURSOS DA SEGURANÇA PÚBLICA", "seguranca"),  # Bloco II, ações 06-07
    ("MOBILIZAR A SAÚDE PARA FAZER AS FILAS ANDAREM", "saude"),  # Bloco II, ações 08-10
    ("ESTRUTURAR A GOVERNANÇA DAS AQUISIÇÕES DA EDUCAÇÃO", "educacao"),  # Bloco II, ações 11-12
    ("INVENTARIAR 100% DA MALHA RODOVIÁRIA E DAS PONTES ESTADUAIS", "infraestrutura"),  # Bloco II, ação 13
    ("CRIAR O MAPA DAS CADEIAS PRODUTIVAS POR TERRITÓRIO", "economia"),  # Bloco II, ação 14
    ("PREPARAR RONDÔNIA PARA CRESCER E ENTREGAR MELHOR", "outros"),  # abertura do Bloco III (mistura temas)
    ("LEVANTAR OS MAIORES GARGALOS DO AMBIENTE DE NEGÓCIOS", "economia"),  # Bloco III, ações 15-17
    ("CRIAR O MAPA ÚNICO DE VULNERABILIDADE SOCIAL", "assistencia_social"),  # Bloco III, ação 18
    ("PRIORIZAR OS SERVIÇOS PÚBLICOS DIGITAIS MAIS UTILIZADOS", "gestao_publica"),  # Bloco III, ação 19
    ("AO FINAL DOS 100 DIAS", "outros"),  # fechamento do apêndice tático
    ("ENCERRAMENTO", "outros"),  # capítulo de encerramento do plano
]

MARCADORES = {
    "adailton-furia": MARCADORES_ADAILTON,
    "marcos-rogerio": MARCADORES_MARCOS,
    "hildon-chaves": MARCADORES_HILDON,
}

# Corte fixo aplicado SOMENTE ao Índice de Base Empírica (não à distribuição
# temática, nem ao total_palavras) — ver docstring do módulo.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "adailton-furia": 6397,
    "marcos-rogerio": 0,
    # Hildon Chaves: corte no caractere onde termina a capa + o sumário
    # ("navegação do documento", que aqui é uma lista de eixos com números
    # de página, sem prosa analisável) e começa o corpo real de prosa, a
    # partir do cabeçalho real "APRESENTAÇÃO" (a 2ª das 2 ocorrências da
    # palavra no documento — a 1ª é a entrada do próprio sumário). Ao
    # contrário do corte de Adailton Fúria, aqui o corte preserva não só a
    # "Apresentação" mas também "Mensagem", "Compromisso com os
    # Rondonienses" e "O Momento de Rondônia" — o capítulo de diagnóstico
    # que antecede o Eixo 1 e cita "um amplo diagnóstico elaborado pelos
    # órgãos de controle externo", relevante para o Índice de Base Empírica.
    "hildon-chaves": 16610,
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
    segmentos_debug.append(("[FRONT MATTER: carta de abertura/sumário/diagnóstico/metodologia]", "outros", n_intro))

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
        raw_text = (PLANOS_DIR / f"{c['arquivo']}.txt").read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # Cursor da DISTRIBUIÇÃO TEMÁTICA: se o 1º marcador aparecer mais de
        # uma vez no corpo (documento com sumário/índice que repete os
        # títulos das seções antes do corpo real), pula para a 2ª ocorrência,
        # para não segmentar dentro do sumário. Mesma lógica-padrão usada em
        # todos os outros estados do projeto — independente do corte fixo
        # usado no Índice de Base Empírica (ver CURSOR_INICIAL_BASE_EMPIRICA).
        primeiro_marcador = marcadores[0][0]
        primeira_ocorrencia = corpo.find(primeiro_marcador)
        segunda_ocorrencia = corpo.find(primeiro_marcador, primeira_ocorrencia + 1)
        n_ocorrencias_1o_marcador = corpo.count(primeiro_marcador)
        cursor_inicial_distribuicao = segunda_ocorrencia if segunda_ocorrencia != -1 else 0
        print(f"{slug}: 1º marcador aparece {n_ocorrencias_1o_marcador}x no corpo "
              f"(cursor_inicial_distribuicao={cursor_inicial_distribuicao})")

        pct, contagem_abs, segmentos_debug = distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial_distribuicao
        )

        cursor_inicial_be = CURSOR_INICIAL_BASE_EMPIRICA[slug]
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
        "gerado_em": "23 de agosto de 2026",
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
            "seus marcadores de seção reais (títulos de pilar/programa, no "
            "plano de Adailton Fúria; títulos de Eixo, no plano de Marcos "
            "Rogério). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível, o "
            "segmento foi classificado item a item sempre que os itens "
            "individuais eram identificáveis (ex.: a subseção 'Proteção "
            "Animal', dentro do Eixo de Meio Ambiente de Marcos Rogério, foi "
            "destacada como assistência social), ou como 'outros' quando não "
            "era possível separar com segurança (front matter: carta de "
            "abertura, sumário, diagnóstico geral, metodologia de "
            "elaboração do plano)."
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
            "Nordeste já concluídos, sem nenhum ajuste específico para "
            "Rondônia, para manter comparabilidade entre estados e entre "
            "regiões. O cálculo do índice usa um recorte de corpo específico "
            "por candidato — corpo[6397:] para Adailton Fúria (pulando o "
            "sumário/'navegação do documento' inicial), corpo completo para "
            "Marcos Rogério (cursor 0), corpo[16610:] para Hildon Chaves "
            "(pulando a capa e o sumário, preservando a apresentação e o "
            "capítulo de diagnóstico que os antecedem) — aplicado SOMENTE "
            "ao índice de base empírica, nunca à distribuição temática nem "
            "ao total de palavras, que sempre usam o corpo inteiro do plano."
        ),
        "metodologia_nota": (
            "Rondônia foi o primeiro estado da região Norte analisado neste "
            "projeto, replicando a metodologia consolidada nos 9 estados do "
            "Nordeste. Os dois planos são documentos oficiais registrados no "
            "TSE, ambos bem estruturados em capítulos/eixos numerados com "
            "títulos temáticos claros — um contraste com estados do "
            "Nordeste cujos planos exigiram segmentação parágrafo a "
            "parágrafo por ausência de subtítulos internos. "
            "Quanto à categoria eleitoral dos candidatos: Marcos Rocha "
            "(PSD, ex-União Brasil) é o governador em exercício e está em "
            "seu 2º mandato consecutivo, não podendo concorrer à reeleição "
            "em 2026; em fevereiro de 2026 declarou apoio público à "
            "pré-candidatura de Adailton Fúria (também do PSD), tornando-o "
            "o candidato de continuidade do atual governo. Marcos Rogério "
            "(PL), senador da República, foi lançado pelo PL como candidato "
            "próprio, sem o apoio do governador, e se consolidou como o "
            "principal opositor ao governo estadual — por isso classificado "
            "como desafiante. As fontes usadas para essa checagem estão "
            "citadas no campo 'categoria' de cada candidato. "
            "Nota sobre o plano de Adailton Fúria: o documento abre com uma "
            "página de 'navegação do documento' (sumário/TOC de 116 "
            "páginas) que antecede o corpo real de prosa; para o Índice de "
            "Base Empírica, aplicamos o corte fixo cursor_inicial=6397 "
            "(caracteres), que pula exatamente esse sumário e preserva o "
            "parágrafo de diagnóstico da carta de abertura ('nove em cada "
            "dez rondonienses dependem da saúde pública', 'cerca de metade "
            "da população... Cadastro Único'). Esse corte NÃO foi aplicado "
            "à distribuição temática nem ao total de palavras, que usam o "
            "corpo inteiro do documento (o sumário cai naturalmente em "
            "'outros', pois o primeiro marcador de seção usado não se "
            "repete lá — o sumário grafa os títulos em linha única, sem a "
            "quebra de linha usada nos títulos do corpo real). "
            "Nota sobre o plano de Marcos Rogério: o documento também tem "
            "um sumário ('II. SUMÁRIO') que repete o título de cada um dos "
            "10 Eixos antes do corpo real; para a distribuição temática, "
            "isso foi resolvido com a mesma lógica-padrão do projeto (usar "
            "a 2ª ocorrência do primeiro marcador de seção como ponto de "
            "partida da segmentação). Já para o Índice de Base Empírica, "
            "não há necessidade de nenhum corte (cursor_inicial=0): o "
            "sumário é composto por linhas curtas de título + página, que "
            "não passam pelo filtro de tamanho mínimo de frase nem são "
            "capturadas pelos regex de diagnóstico/efeito/evidência, e a "
            "carta de abertura e o capítulo de diagnóstico que antecedem o "
            "sumário contêm prosa analisável relevante (indicadores de "
            "criminalidade, saúde e orçamento) que deve ser preservada no "
            "cálculo do índice. "
            "Ressalva sobre a frequência de palavras no plano de Marcos "
            "Rogério: aproximadamente metade do documento (a partir do "
            "Eixo 3, por volta da linha 1458 do corpo, até o Eixo 10) foi "
            "extraída de um PDF cujo mecanismo de extração falhou ao "
            "converter o ligature 'ti' de determinada fonte, produzindo um "
            "espaço em branco no lugar dessas duas letras (ex.: 'polí ca' "
            "em vez de 'política', 'ins tucional' em vez de 'institucional', "
            "'gara ndo' em vez de 'garantindo', 'ar culação' em vez de "
            "'articulação' — 153 ocorrências identificadas apenas para os "
            "padrões mais comuns). Isso fragmenta essas palavras em dois "
            "tokens menores na contagem de frequência e na nuvem de "
            "palavras (ex.: 'polí' e 'ca' em vez de 'política'), com efeito "
            "visível no wordcloud de Marcos Rogério (fragmentos como "
            "'garan', 'polí', 'ins', 'logís'). Não corrigimos esse ruído "
            "para não introduzir uma etapa de normalização de texto "
            "específica de Rondônia, ausente da metodologia canônica "
            "replicada dos 9 estados do Nordeste — o mesmo tipo de "
            "ressalva sobre ruído de extração de PDF já documentado (por "
            "razões distintas) em outros estados do projeto. O efeito é "
            "apenas sobre a lista de termos mais frequentes e a nuvem de "
            "palavras; a distribuição temática (que opera por posição de "
            "caractere, não por palavra tokenizada) e o Índice de Base "
            "Empírica (que opera sobre a frase inteira via regex, "
            "raramente dependente da grafia exata de 'política'/"
            "'institucional'/'garantindo') não são afetados de forma "
            "material por esse ruído. "
            "ATUALIZAÇÃO (25/08/2026): Hildon Chaves (Federação União "
            "Progressista e Republicanos), ex-prefeito de Porto Velho, foi "
            "adicionado como 3º candidato pleno de Rondônia a pedido do "
            "pesquisador responsável, que decidiu que o critério de seleção "
            "deve cobrir todos os candidatos competitivos nas pesquisas, e "
            "não um número fixo por estado. Uma reverificação de "
            "categorização política encontrou que a pesquisa Phoenix "
            "(22/08/2026) mostra Hildon Chaves em empate técnico genuíno "
            "com Adailton Fúria pela 2ª colocação e pela vaga no 2º turno, "
            "atrás do líder isolado Marcos Rogério — sem uma justificativa "
            "clara para cobrir apenas um dos dois. Ver o campo 'categoria' "
            "de Hildon Chaves para as fontes dessa checagem, e "
            "RELATORIO_COMPARATIVO_NORTE.md (seção 8) para o registro do "
            "empate. O documento de Hildon Chaves (138 páginas, 14 Eixos de "
            "Governo numerados + apêndice 'Plano Tático dos 100 Primeiros "
            "Dias') segue a mesma estrutura de capítulos numerados com "
            "títulos temáticos claros já usada por Marcos Rogério, e foi "
            "segmentado na mesma granularidade (Eixo inteiro), com duas "
            "exceções documentadas no docstring do módulo e nos comentários "
            "de MARCADORES_HILDON: (1) o Eixo 1 ('Cidadania e Combate à "
            "Corrupção') foi dividido em 2 segmentos (gestão pública vs. "
            "assistência social), por misturar 2 temas do projeto sem "
            "nenhuma subseção nomeada que permita a separação; (2) o "
            "apêndice 'Plano Tático dos 100 Primeiros Dias', cujos 3 Blocos "
            "não são internamente coerentes com um único tema (ao contrário "
            "dos 14 Eixos), foi segmentado por ação numerada, seguindo o "
            "mesmo princípio já usado no equivalente de Adailton Fúria. "
            "Para o Índice de Base Empírica, o corte usado (corpo[16610:]) "
            "está documentado em CURSOR_INICIAL_BASE_EMPIRICA."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
