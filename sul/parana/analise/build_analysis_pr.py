#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Paraná 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia do Maranhão e da Paraíba: distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica à dos
demais estados, reaproveitada sem alterações para manter comparabilidade
entre estados).

Caso especial do Paraná: o atual governador Ratinho Junior (PSD) NÃO é
candidato — já cumpriu 2 mandatos consecutivos (limite constitucional).
Sergio Moro (PL) é senador, ex-juiz da Operação Lava Jato e ex-ministro da
Justiça, nunca ocupou o Executivo estadual, e aparece como líder isolado nas
pesquisas de jul-ago/2026 (37-46%). O 2º lugar foi objeto de empate técnico
entre Requião Filho (PDT) e Sandro Alex (PSD, candidato ligado a Ratinho
Junior) — ver nota de metodologia e a `categoria` de Requião Filho abaixo
para o detalhe da arbitragem do desempate. Isso não muda a metodologia de
análise textual (idêntica aos demais estados), mas é relevante para o
enquadramento editorial do achado.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/sul/parana/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/sul/parana/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "sergio_moro", "nome": "Sergio Moro", "partido": "PL",
     "categoria": "desafiante — nunca ocupou o Executivo estadual (senador, ex-juiz da "
                  "Operação Lava Jato, ex-ministro da Justiça e Segurança Pública), mas "
                  "líder isolado nas pesquisas de jul-ago/2026 (37-46%); concorre porque "
                  "o governador em exercício, Ratinho Junior (PSD), não é candidato por "
                  "já ter cumprido 2 mandatos consecutivos (limite constitucional)"},
    {"slug": "requiao_filho", "nome": "Requião Filho", "partido": "PDT",
     "categoria": "desafiante — 2º lugar nas pesquisas em empate técnico com Sandro Alex "
                  "(PSD, candidato ligado a Ratinho Junior); em arbitragem sobre 8 "
                  "pesquisas de jul-ago/2026, Requião Filho venceu o desempate pelo "
                  "critério de menor número de derrotas estatisticamente significativas "
                  "fora da margem de erro (4 vitórias/2 empates/2 derrotas, contra "
                  "2 vitórias/2 empates/4 derrotas de Sandro Alex) — nota de "
                  "transparência: um recorte só dos dados de agosto (mais recentes) "
                  "inverteria o resultado a favor de Sandro Alex, portanto este é um "
                  "empate técnico genuíno que poderia ter sido decidido para qualquer "
                  "um dos dois lados"},
    {"slug": "sandro_alex", "nome": "Sandro Alex", "partido": "PSD",
     "categoria": "desafiante — candidato ligado ao grupo político do governador "
                  "Ratinho Junior (PSD), que não concorre por já ter cumprido 2 "
                  "mandatos consecutivos; esteve em empate técnico genuíno com "
                  "Requião Filho (PDT) pelo 2º lugar nas pesquisas de jul-ago/2026, "
                  "atrás do líder isolado Sergio Moro (PL) — uma arbitragem "
                  "dedicada (ver metodologia_nota e RELATORIO_COMPARATIVO_SUL.md) "
                  "favoreceu Requião Filho por desempenho agregado no período, mas "
                  "pesquisas mais recentes (fim de agosto/2026) mostram Sandro "
                  "Alex consolidando vantagem sobre Requião Filho; passou a ser "
                  "coberto como candidato pleno em 25/08/2026 por não haver mais "
                  "justificativa clara para excluí-lo"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas ao Ceará/Maranhão/Paraíba (não
# adaptadas ao Paraná), para preservar comparabilidade entre estados.
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

# Requião Filho: documento muito bem estruturado em 12 seções numeradas
# ("1. Governo presente para cuidar das pessoas e proteger o patrimônio
# público" até "12. Cultura, esporte e turismo"), cada uma monotemática o
# suficiente para ser usada diretamente como marcador — sem necessidade de
# segmentação item a item por proposta individual (compromisso). Nenhum dos
# 12 títulos se repete no documento (não há sumário/índice que duplique os
# títulos), então cursor_inicial cai em 0 (a saudação de abertura "O Paraná
# que cuida" até o primeiro marcador vira "outros" automaticamente, via o
# bucket de front matter).
#
# Itens 1 e 2 (governança/administração e apoio institucional aos
# municípios/planejamento regional) = gestao_publica: o conteúdo é sobre
# capacidade administrativa, transparência, carreira do servidor, Celepar,
# IPARDES, consórcios e coordenação intergovernamental — não entrega direta
# de obras/serviços, que ficaria em infraestrutura.
# Item 6 (trabalho/renda/desenvolvimento econômico) e item 7 (agricultura) =
# economia, seguindo o mesmo critério usado no plano de Sergio Moro (ver
# TEMÁTICA 2.7 abaixo): qualificação para o mercado de trabalho e renda no
# campo são agenda econômica, não assistência social.
# Item 10 ("Meio ambiente, água, saneamento e clima") é fundido pelo próprio
# candidato num único bloco que mistura conteúdo de saneamento/infraestrutura
# (Sanepar, água e esgoto) com conteúdo ambiental estrito (clima,
# mananciais, licenciamento). Como o candidato escolheu nomear e enquadrar a
# seção inteira como pauta ambiental (e não dentro do item 8, que é sua
# seção de infraestrutura/logística/mobilidade), classificamos o bloco
# inteiro como meio_ambiente, respeitando o enquadramento textual do próprio
# documento em vez de fragmentar por proposta individual.
# Item 12 ("Cultura, esporte e turismo") funde três pautas sem subtítulos
# internos. Cultura e esporte seguem o precedente do projeto (=
# assistencia_social, mesmo tratamento dado a Elmano de Freitas/Ciro Gomes
# no Ceará); turismo, aqui, aparece com enquadramento comunitário/de acesso
# ("turismo regional e comunitário", "turismo seguro"), não como agenda de
# competitividade econômica (que é como Sergio Moro trata o tema em sua
# TEMÁTICA 2.4 – TURISMO, dentro do pilar econômico). Como os três temas
# estão irremediavelmente fundidos num único bloco sem subtítulos e cultura
# e esporte dominam o conteúdo (10 dos 12 itens do bloco), classificamos a
# seção inteira como assistencia_social.
MARCADORES_REQUIAO = [
    ("1. Governo presente para cuidar das pessoas e proteger", "gestao_publica"),
    ("2. Apoio aos municípios e desenvolvimento regional", "gestao_publica"),
    ("3. Saúde pública e regionalização do atendimento", "saude"),
    ("4. Educação, ciência e ensino superior", "educacao"),
    ("5. Segurança pública, justiça e defesa civil", "seguranca"),
    ("6. Trabalho, renda e desenvolvimento econômico", "economia"),
    ("7. Agricultura e desenvolvimento rural", "economia"),
    ("8. Infraestrutura, logística e mobilidade", "infraestrutura"),
    ("9. Habitação, cidades e planejamento urbano", "infraestrutura"),
    ("10. Meio ambiente, água, saneamento e clima", "meio_ambiente"),
    ("11. Proteção social, igualdade, direitos e ciclos de vida", "assistencia_social"),
    ("12. Cultura, esporte e turismo", "assistencia_social"),
]

# Sergio Moro: documento com ÍNDICE completo no início (SUMÁRIO) repetindo
# (com pontos de preenchimento e número de página) os títulos de PILAR e
# TEMÁTICA usados como marcador — mesmo padrão de "bug" já visto no plano de
# Elmano de Freitas (Ceará) e Felipe Camarão (Maranhão). Protegido pela
# mesma lógica de `cursor_inicial` (2ª ocorrência do primeiro marcador,
# "PILAR 1", usada como ponto de partida — pula a saudação de abertura, os
# "Princípios de Governo", o texto sobre "Governança Regionalizada" e o
# SUMÁRIO inteiro, tudo classificado automaticamente como "outros" via o
# bucket de front matter).
#
# Estrutura real do documento: 5 PILARES numerados, cada um com um pequeno
# texto de abertura (bucket "PILAR N" = outros, por reunir de forma
# deliberadamente genérica todos os temas do pilar antes de abrir as
# TEMÁTICAS individuais) e uma lista de TEMÁTICAS numeradas (ex. "TEMÁTICA
# 1.1 – EDUCAÇÃO"), cada uma tratada como um único segmento monotemático.
#
# Decisões de classificação não óbvias:
#  - TEMÁTICA 1.2 (CULTURA) e 1.3 (ESPORTE) = assistencia_social, seguindo o
#    mesmo precedente usado no Ceará (Elmano/Ciro) e aplicado também ao
#    plano de Requião Filho (PR) para manter comparabilidade entre os dois
#    candidatos do próprio Paraná.
#  - TEMÁTICA 2.5 (INOVAÇÃO, PESQUISA, TECNOLOGIA E ECONOMIA DIGITAL) =
#    economia, ao contrário do precedente do Ceará (onde Ciência e
#    Tecnologia foi classificada como educacao). A diferença é editorial e
#    deliberada: no Ceará, os candidatos agrupavam C&T explicitamente com
#    universidades/educação superior; aqui, Sergio Moro agrupa o tema
#    explicitamente dentro do PILAR 2 "Desenvolvimento Econômico
#    Sustentável", com foco em clusters produtivos, startups e
#    competitividade empresarial — o enquadramento textual do próprio
#    candidato é que decide, não uma regra fixa por assunto.
#  - TEMÁTICA 2.7 (TRABALHO, QUALIFICAÇÃO E RENDA) = economia: o conteúdo é
#    sobre empregabilidade, qualificação profissional e mercado de trabalho
#    (Observatório do Trabalho, Qualifica Paraná, Primeiro Emprego), não
#    proteção social — consistente com a classificação do item 6 de Requião
#    Filho ("Trabalho, renda e desenvolvimento econômico").
#  - TEMÁTICA 4.1 e 4.2 (MODERNIZAÇÃO DA GESTÃO PÚBLICA; TRANSPARÊNCIA E
#    INTEGRIDADE) = gestao_publica, sem ambiguidade.
#  - PILAR 5 inteiro (SEGURANÇA, JUSTIÇA E COMBATE À CORRUPÇÃO) — todas as 6
#    TEMÁTICAS (5.1 a 5.6, incluindo 5.2 "Combate à Corrupção" e 5.6
#    "Justiça e Cidadania") = seguranca. Embora o conteúdo de "Combate à
#    Corrupção" (agência anticorrupção, auditoria, compliance) se pareça
#    tematicamente com "Transparência e Integridade" (TEMÁTICA 4.2,
#    classificada como gestao_publica), o candidato — ex-juiz da Lava Jato —
#    optou deliberadamente por agrupar corrupção, investigação, perícia,
#    sistema prisional, defesa civil e justiça/cidadania num único pilar de
#    segurança pública/justiça, separado do pilar de gestão administrativa.
#    Respeitamos esse enquadramento textual do próprio candidato. Essa
#    escolha também maximiza a comparabilidade com o plano de Requião Filho,
#    cujo item 5 ("Segurança pública, justiça e defesa civil") já reúne
#    segurança, justiça e defesa civil num único bloco mapeado para
#    seguranca — mantendo o mesmo critério para os dois candidatos do PR.
MARCADORES_MORO = [
    ("PILAR 1", "outros"),
    ("TEMÁTICA 1.1 – EDUCAÇÃO", "educacao"),
    ("TEMÁTICA 1.2 – CULTURA", "assistencia_social"),
    ("TEMÁTICA 1.3 – ESPORTE", "assistencia_social"),
    ("TEMÁTICA 1.4 – SAÚDE", "saude"),
    ("TEMÁTICA 1.5 - ASSISTÊNCIA SOCIAL", "assistencia_social"),
    ("PILAR 2", "outros"),
    ("TEMÁTICA 2.1 – AGRICULTURA", "economia"),
    ("TEMÁTICA 2.2 – INDÚSTRIA", "economia"),
    ("TEMÁTICA 2.3 – COMÉRCIO, SERVIÇOS, EMPREENDEDORISMO E MICRO E", "economia"),
    ("TEMÁTICA 2.4 – TURISMO", "economia"),
    ("TEMÁTICA 2.5 – INOVAÇÃO, PESQUISA, TECNOLOGIA E ECONOMIA DIGITAL", "economia"),
    ("TEMÁTICA 2.6 – INTERNACIONALIZAÇÃO, ATRAÇÃO E RETENÇÃO DE", "economia"),
    ("TEMÁTICA 2.7 – TRABALHO, QUALIFICAÇÃO E RENDA", "economia"),
    ("TEMÁTICA 2.8 – MEIO AMBIENTE E SUSTENTABILIDADE", "meio_ambiente"),
    ("PILAR 3", "outros"),
    ("TEMÁTICA 3.1 - HABITAÇÃO E REGULARIZAÇÃO FUNDIÁRIA", "infraestrutura"),
    ("TEMÁTICA 3.2 - MOBILIDADE URBANA E REGIONAL", "infraestrutura"),
    ("TEMÁTICA 3.3 - INFRAESTRUTURA URBANA", "infraestrutura"),
    ("TEMÁTICA 3.4 – SANEAMENTO", "infraestrutura"),
    ("TEMÁTICA 3.5 - LOGÍSTICA E TRANSPORTES", "infraestrutura"),
    ("TEMÁTICA 3.6 - ENERGIA E GÁS", "infraestrutura"),
    ("TEMÁTICA 3.7 - CONECTIVIDADE E TELECOMUNICAÇÕES", "infraestrutura"),
    ("PILAR 4", "outros"),
    ("TEMÁTICA 4.1 – MODERNIZAÇÃO DA GESTÃO PÚBLICA", "gestao_publica"),
    ("TEMÁTICA 4.2 – TRANSPARÊNCIA E INTEGRIDADE", "gestao_publica"),
    ("PILAR 5", "outros"),
    ("TEMÁTICA 5.1 - SEGURANÇA PÚBLICA E COMBATE AO CRIME ORGANIZADO", "seguranca"),
    ("TEMÁTICA 5.2 - COMBATE À CORRUPÇÃO", "seguranca"),
    ("TEMÁTICA 5.3 - INTELIGÊNCIA, TECNOLOGIA E PREVENÇÃO", "seguranca"),
    ("TEMÁTICA 5.4 - SISTEMA PRISIONAL E REINTEGRAÇÃO SOCIAL", "seguranca"),
    ("TEMÁTICA 5.5 - DEFESA CIVIL E PROTEÇÃO DA VIDA", "seguranca"),
    ("TEMÁTICA 5.6 - JUSTIÇA E CIDADANIA", "seguranca"),
    ("O Paraná construído por todos nós", "outros"),
]

# Sandro Alex: documento com uma arquitetura textual muito mais elaborada que
# a dos outros dois candidatos do PR — "Cinco Pontes" (eixos estratégicos),
# cada uma associada a um "Compromisso" e estruturada em cinco "Pilares
# Estratégicos" (25 pilares no total: 5 Pontes × 5 Pilares). Cada Pilar tem
# um título em caixa alta único no documento (nenhum se repete — não há
# sumário/índice que duplique os títulos antes do corpo real, ao contrário do
# plano de Sergio Moro), o que foi confirmado por contagem de ocorrências de
# cada um dos 25 títulos antes de definir os marcadores. Por isso
# cursor_inicial cai em 0: todo o bloco de abertura ("Um convite para
# construir o futuro do Paraná", a Visão/Método/Estratégia do Plano, a
# apresentação conceitual das Cinco Pontes/Cinco Compromissos/25 Pilares/5
# Princípios de Governo, a Jornada do Cidadão) vira "outros" via o bucket de
# front matter — é conteúdo genuinamente proemial (sobre a arquitetura do
# próprio Plano), não uma proposta temática specific. Esse bloco de abertura
# é bem mais longo que nos outros dois planos do PR (cerca de 50 páginas de
# um total de 274), refletindo o estilo mais conceitual/metodológico do
# documento; ver ressalva de volume na metodologia_nota.
#
# Cada título de Pilar é usado tal como aparece no documento, incluindo, em
# dois casos, o espaçamento irregular produzido por justificação de texto na
# extração do PDF ("AGROPECUÁRIA,     COOPERATIVISMO, ..." e "HABITAÇÃO,
# MOBILIDADE, ..."); e, em três casos, o título quebra em duas linhas no PDF
# — como já feito nos marcadores de Sergio Moro (ex.: TEMÁTICA 2.3, 2.6),
# usa-se apenas a primeira linha do título como marcador.
#
# Ao final das 25 Pontes/Pilares, o documento fecha com uma seção de
# encerramento ("Pra Frente Sempre, Paraná: A Liderança para um Novo Ciclo",
# incluindo as cartas de despedida de Sandro Alex e de seu vice Rafael Greca
# e a nota metodológica sobre uso de IA na elaboração do Plano). Sem um
# marcador dedicado para essa seção, todo esse conteúdo cairia dentro do
# tema do último Pilar (Sustentabilidade Intergeracional e Patrimônio
# Público), distorcendo sua contagem. Seguindo exatamente o mesmo precedente
# usado no plano de Sergio Moro (marcador final "O Paraná construído por
# todos nós" = outros), adicionamos um 26º marcador para essa seção de
# encerramento, mapeado para "outros".
#
# Decisões de classificação não óbvias (tema por tema, seguindo o
# enquadramento textual do próprio candidato — mesmo critério editorial
# usado nos dois marcadores acima):
#  - Pilar 1.5 (Cultura, Esporte e Lazer) = assistencia_social, seguindo o
#    mesmo precedente do projeto usado para Requião Filho e Sergio Moro.
#  - Pilares 2.1 a 2.5 (Indústria/Comércio/Serviços; Trabalho/
#    Empreendedorismo; Agropecuária/Cooperativismo/Bioeconomia;
#    Desenvolvimento Regional; Turismo/Economia Criativa/
#    Internacionalização) = economia, todos. O Pilar de Turismo explicita no
#    próprio Objetivo Estratégico que trata o setor como "instrumento
#    estratégico de desenvolvimento regional" e o território como "um bem
#    econômico" — enquadramento econômico explícito, ao contrário do plano
#    de Requião Filho (turismo com enquadramento comunitário/de acesso,
#    classificado como assistencia_social). O Pilar de Desenvolvimento
#    Regional trata explicitamente de "potencialidades econômicas de cada
#    região" e geração de emprego/renda — economia, não gestao_publica.
#  - Pilar 3.4 (Ensino Superior, Ciência, Tecnologia e Inovação) =
#    educacao, ao contrário do critério usado no plano de Sergio Moro
#    (Inovação/Tecnologia = economia) — aqui o próprio Objetivo Estratégico
#    do Pilar declara explicitamente que ele "dá continuidade à trajetória
#    educacional iniciada na educação básica (Pilar 1.1)", ancorando o tema
#    no eixo educacional. O enquadramento textual do candidato é que decide
#    (mesmo princípio editorial já usado para diferenciar Moro do Ceará em
#    relação a C&T), não uma regra fixa por assunto.
#  - Pilar 3.5 (Economia Digital, Conectividade e Inteligência Artificial) =
#    economia, seguindo o precedente da TEMÁTICA 2.5 de Sergio Moro
#    (inovação/tecnologia/economia digital = economia). O título já leva
#    "Economia Digital" como primeiro termo e o Objetivo Estratégico fala em
#    "acelerar a transformação digital da economia", "elevar a
#    produtividade" e "preparar o Paraná para a economia do futuro" — mesmo
#    fazendo fronteira com conectividade (que poderia sugerir
#    infraestrutura) e com a modernização da administração pública (Pilar
#    4.4, tratado à parte, ver abaixo), o próprio Pilar se declara
#    complementar e distinto desses dois eixos.
#  - Pilares 4.1 a 4.5 (Modernização Administrativa; Planejamento
#    Estratégico e Gestão por Resultados; Transparência, Integridade e
#    Controle Social; Governo Digital; Cooperação Federativa) =
#    gestao_publica, todos. Diferente do plano de Sergio Moro (que agrupa
#    "Combate à Corrupção" dentro do pilar de segurança/justiça, uma escolha
#    editorial deliberada e documentada do próprio candidato), o plano de
#    Sandro Alex não faz essa fusão: Transparência e Integridade aparece
#    dentro da mesma Ponte (Ponte da Confiança) que Modernização
#    Administrativa, Planejamento e Governo Digital — todos eixos de
#    capacidade/gestão administrativa, sem qualquer menção a segurança
#    pública ou investigação criminal. Respeitamos o enquadramento textual
#    de cada candidato individualmente, mesmo quando isso produz
#    classificações diferentes para temas de nome parecido entre os três
#    planos do PR.
#  - Pilares 5.1 a 5.5 (Institucionalização de Políticas de Estado; Visão
#    Paraná 2055 e Planejamento de Longo Prazo; Desenvolvimento
#    Institucional/Formação de Lideranças/Excelência Pública;
#    Sustentabilidade Intergeracional e Patrimônio Público) = gestao_publica
#    para 4 dos 5 (exceção: Pilar 5.4, ver abaixo). Esses pilares tratam de
#    continuidade de políticas públicas entre governos, planejamento
#    estratégico de longo prazo, formação de servidores/lideranças e
#    responsabilidade fiscal/patrimonial intergeracional — capacidade e
#    responsabilidade administrativa do Estado, o mesmo campo temático dos
#    Pilares 4.1-4.5. O Pilar "Sustentabilidade Intergeracional e Patrimônio
#    Público" é explicitamente multitemático por definição textual (o
#    próprio Objetivo Estratégico enumera quatro dimensões: fiscal,
#    ambiental, social e patrimonial, tratadas como um "balanço patrimonial
#    intergeracional" único e indivisível) — como o título e o conceito
#    estruturante ("Herança Paraná") giram em torno de responsabilidade
#    fiscal e patrimônio público, e não especificamente meio ambiente,
#    classificamos o pilar inteiro como gestao_publica, respeitando o
#    enquadramento textual predominante em vez de fragmentar por dimensão.
#  - Pilar 5.4 (Identidade, Integração Regional e Orgulho de Ser
#    Paranaense) = outros. Trata de identidade cultural, memória,
#    patrimônio histórico simbólico e integração regional/pertencimento —
#    o próprio Objetivo Estratégico o declara complementar, mas distinto,
#    do acesso à cultura (Pilar 1.5, já classificado como
#    assistencia_social) e da economia criativa (Pilar 2.5, já classificado
#    como economia). Não há um tema substantivo entre os 8 restantes que
#    capture adequadamente "orgulho de pertencimento"/coesão simbólica
#    territorial sem forçar a classificação; por isso vai para "outros",
#    mesmo tratamento dado a conteúdo proemial/estrutural nos demais planos
#    do projeto.
MARCADORES_SANDRO_ALEX = [
    ("EDUCAÇÃO BÁSICA, DESENVOLVIMENTO HUMANO E TRAJETÓRIA", "educacao"),
    ("SAÚDE, BEM-ESTAR E LONGEVIDADE", "saude"),
    ("SEGURANÇA PÚBLICA, ACESSO À JUSTIÇA E DEFESA CIVIL", "seguranca"),
    ("MULHERES, FAMÍLIAS, PROTEÇÃO SOCIAL E CIDADANIA", "assistencia_social"),
    ("CULTURA, ESPORTE E LAZER", "assistencia_social"),
    ("INDÚSTRIA, COMÉRCIO, SERVIÇOS E AMBIENTE DE NEGÓCIOS", "economia"),
    ("TRABALHO, EMPREENDEDORISMO E ECONOMIA DO FUTURO", "economia"),
    ("AGROPECUÁRIA,     COOPERATIVISMO,                                        BIOECONOMIA                     E", "economia"),
    ("DESENVOLVIMENTO REGIONAL E POTENCIALIDADES PRODUTIVAS", "economia"),
    ("TURISMO, ECONOMIA CRIATIVA E INTERNACIONALIZAÇÃO", "economia"),
    ("INFRAESTRUTURA, ENERGIA E LOGÍSTICA", "infraestrutura"),
    ("HABITAÇÃO,   MOBILIDADE,                                  CIDADES            E       COMUNIDADES", "infraestrutura"),
    ("MEIO AMBIENTE, RECURSOS HÍDRICOS, SANEAMENTO E CLIMA", "meio_ambiente"),
    ("ENSINO SUPERIOR, CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "educacao"),
    ("ECONOMIA DIGITAL, CONECTIVIDADE E INTELIGÊNCIA ARTIFICIAL", "economia"),
    ("MODERNIZAÇÃO ADMINISTRATIVA E EFICIÊNCIA", "gestao_publica"),
    ("PLANEJAMENTO ESTRATÉGICO E GESTÃO POR RESULTADOS", "gestao_publica"),
    ("TRANSPARÊNCIA, INTEGRIDADE E CONTROLE SOCIAL", "gestao_publica"),
    ("GOVERNO DIGITAL, SIMPLIFICAÇÃO E DESBUROCRATIZAÇÃO", "gestao_publica"),
    ("COOPERAÇÃO FEDERATIVA E ATENDIMENTO AO CIDADÃO", "gestao_publica"),
    ("INSTITUCIONALIZAÇÃO DE POLÍTICAS DE ESTADO", "gestao_publica"),
    ("VISÃO PARANÁ 2055 E PLANEJAMENTO DE LONGO PRAZO", "gestao_publica"),
    ("DESENVOLVIMENTO INSTITUCIONAL, FORMAÇÃO DE LIDERANÇAS", "gestao_publica"),
    ("IDENTIDADE, INTEGRAÇÃO REGIONAL E ORGULHO DE SER", "outros"),
    ("SUSTENTABILIDADE INTERGERACIONAL E PATRIMÔNIO PÚBLICO", "gestao_publica"),
    ("PRA FRENTE SEMPRE, PARANÁ: A LIDERANÇA", "outros"),
]

MARCADORES = {
    "sergio_moro": MARCADORES_MORO,
    "requiao_filho": MARCADORES_REQUIAO,
    "sandro_alex": MARCADORES_SANDRO_ALEX,
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
            "específicos de outros estados, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso 'Paraná' "
            "e 'paranaense'/'paranaenses' NÃO são filtrados e podem aparecer "
            "nos termos mais frequentes). Mostra os termos mais repetidos "
            "por candidato e o agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de pilar/temática/item "
            "numerado). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível "
            "(sem subtítulos internos que permitissem separar), o segmento "
            "foi classificado por como o próprio candidato o enquadrou "
            "textualmente (título da seção, pilar em que foi inserido), e "
            "não fragmentado item a item — ver nota de metodologia para as "
            "decisões específicas de cada candidato."
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
            "Paraíba, sem nenhum ajuste específico para o Paraná, para "
            "manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "O Paraná é um caso especial dentro do projeto: o governador em "
            "exercício, Ratinho Junior (PSD), NÃO é candidato — já cumpriu "
            "2 mandatos consecutivos e está impedido de concorrer por limite "
            "constitucional. Sergio Moro (PL), senador e ex-juiz da Operação "
            "Lava Jato, nunca ocupou o Executivo estadual, mas aparece como "
            "líder isolado nas pesquisas de jul-ago/2026 (37-46%). O 2º "
            "lugar foi objeto de empate técnico entre Requião Filho (PDT) e "
            "Sandro Alex (PSD, candidato ligado a Ratinho Junior): uma "
            "arbitragem sobre 8 pesquisas de jul-ago/2026 concluiu que "
            "Requião Filho venceu o desempate pelo critério de menor número "
            "de derrotas estatisticamente significativas fora da margem de "
            "erro (Requião: 4 vitórias/2 empates/2 derrotas; Sandro Alex: 2 "
            "vitórias/2 empates/4 derrotas). Nota de transparência: um "
            "recorte só dos dados de agosto (mais recentes) inverteria o "
            "resultado a favor de Sandro Alex — este é, portanto, um empate "
            "técnico genuíno que poderia ter sido decidido para qualquer um "
            "dos dois lados; a escolha de Requião Filho como o 2º nome "
            "analisado neste painel não deve ser lida como uma afirmação de "
            "vantagem inequívoca sobre Sandro Alex. Essa é uma leitura "
            "eleitoral, não textual: não influenciou nenhuma etapa da "
            "extração ou classificação dos planos. "
            "No plano de Sergio Moro, o SUMÁRIO no início do documento "
            "repete (com pontos de preenchimento e número de página) os "
            "mesmos títulos de PILAR e TEMÁTICA usados como marcador de "
            "seção — o mesmo problema já identificado nos planos de Felipe "
            "Camarão (Maranhão) e Elmano de Freitas (Ceará). Corrigido com a "
            "mesma lógica: o primeiro marcador ('PILAR 1') usa sua 2ª "
            "ocorrência no texto como ponto de partida da segmentação, "
            "pulando o sumário. O plano de Requião Filho não tem sumário — "
            "os 12 títulos numerados aparecem uma única vez cada, então a "
            "segmentação começa do início do corpo do documento (logo após "
            "o cabeçalho padronizado do projeto). "
            "Decisões de classificação não óbvias (cultura e esporte = "
            "assistência social; combate à corrupção e justiça/cidadania, "
            "no plano de Moro, classificados como segurança por seguirem o "
            "enquadramento do próprio candidato dentro do pilar de "
            "'Segurança, Justiça e Combate à Corrupção', em vez de gestão "
            "pública; inovação/tecnologia classificada como economia no "
            "plano de Moro, diferente do precedente do Ceará, por seguir o "
            "enquadramento textual de cada candidato em vez de uma regra "
            "fixa por assunto) estão documentadas linha a linha nos "
            "comentários do script de análise. "
            "Ressalva sobre a extração de texto: o PDF do plano de Sergio "
            "Moro preserva o ligado tipográfico Unicode 'ﬁ'/'ﬂ' em várias "
            "palavras (ex.: 'eﬁciência', 'qualiﬁcação', 'beneﬁciar'), um "
            "caractere de ligadura válido gerado pela fonte do PDF original, "
            "não uma falha de extração — mas que o regex de tokenização do "
            "projeto não reconhece como letra, fragmentando essas palavras "
            "em dois tokens (ex.: 'e' e 'ﬁciência' funcionam como duas "
            "palavras diferentes na contagem de frequência). Efeito "
            "colateral pequeno (364 ocorrências de 'ﬁ' e 12 de 'ﬂ' em ~23,1 "
            "mil palavras de corpo) e já visto em outros estados do projeto "
            "(ex.: Fábio Trad, em Mato Grosso do Sul); não corrigido, para "
            "preservar a metodologia idêntica entre estados. Nenhuma outra "
            "anomalia de extração (texto fora de ordem de leitura, "
            "duplicação de rodapé ao longo do corpo) foi identificada em "
            "nenhum dos dois .txt do Paraná. "
            "Ressalva sobre volume: os planos têm tamanhos muito diferentes "
            "(~23,1 mil palavras no de Sergio Moro, documento de 91 "
            "páginas, contra ~3,9 mil no de Requião Filho, documento de 15 "
            "páginas) — trate os percentuais de distribuição temática como "
            "indicativos de ênfase relativa dentro de cada plano, não como "
            "comparação de volume absoluto entre candidatos. "
            "ATUALIZAÇÃO (25/08/2026): Sandro Alex (PSD) foi adicionado nesta "
            "rodada como 3º candidato pleno na análise do Paraná, a pedido do "
            "pesquisador responsável pelo projeto, que decidiu que o critério de "
            "seleção de candidatos deve incluir TODOS os candidatos "
            "competitivos nas pesquisas, e não um número fixo por estado. Como "
            "registrado acima, o 2º lugar nas pesquisas de jul-ago/2026 foi um "
            "empate técnico genuíno entre Requião Filho e Sandro Alex, e uma "
            "arbitragem anterior (documentada em RELATORIO_COMPARATIVO_SUL.md, "
            "seção 1.1) havia escolhido cobrir apenas Requião Filho, com base no "
            "desempenho agregado num conjunto de 8-9 pesquisas de jul-ago/2026. "
            "Essa mesma arbitragem já registrava, porém, que pesquisas mais "
            "recentes de fim de agosto/2026 (TMC/Instituto Alfa, 24/08: Sandro "
            "Alex 26% x Requião Filho 20%; Paraná Pesquisas, 17/08: cenário "
            "semelhante) mostravam Sandro Alex consolidando vantagem sobre "
            "Requião Filho. Diante disso, e do critério revisado de cobrir "
            "todos os competitivos, deixou de haver justificativa clara para "
            "manter a exclusão de Sandro Alex, e ele passa a ser tratado como "
            "candidato pleno, com a mesma metodologia de extração, "
            "segmentação temática e Índice de Base Empírica aplicada aos "
            "demais dois candidatos do Paraná (e a todos os candidatos dos "
            "demais estados do projeto), sem nenhum ajuste específico. O plano "
            "de governo de Sandro Alex tem uma arquitetura textual mais "
            "elaborada e um volume bastante maior que os outros dois planos do "
            "PR (documento de 274 páginas, organizado em 'Cinco Pontes' — "
            "eixos estratégicos —, cada uma associada a um 'Compromisso' e "
            "estruturada em cinco 'Pilares Estratégicos', totalizando 25 "
            "pilares); ver os comentários da lista MARCADORES_SANDRO_ALEX no "
            "script para o detalhe completo das decisões de mapeamento "
            "temático de cada um dos 25 pilares."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
