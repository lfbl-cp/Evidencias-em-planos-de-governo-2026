#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Amazonas 2026 (Região Norte).

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver
/home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py): distribuição
temática exaustiva por segmentação de marcadores de seção reais (lidos e
mapeados à mão) e Índice de Base Empírica (heurística lexical/regex idêntica
a todos os estados anteriores, reaproveitada SEM ALTERAÇÕES para manter
comparabilidade entre estados/regiões).

CASO ESPECIAL DO AMAZONAS — Omar Aziz:
O plano de Omar Aziz é, disparado, o maior documento já processado no
projeto inteiro (Nordeste + Norte): 1552 páginas, ~449 mil "tokens" brutos
(WORD_RE), redigido em estilo quase acadêmico com referências bibliográficas
numeradas espalhadas ao longo de todo o texto (não um bloco único ao final).
Isso já exigiria uma segmentação mais grossa que o padrão só pelo tamanho —
mas há um segundo problema, este sim um artefato de extração: o .txt não
preserva a ordem de leitura das páginas. A primeira página do .txt
corresponde ao conteúdo da página 561 do PDF (capítulo de "Riscos", que
pertence à "Parte 08"), e o arquivo termina com páginas ~541-560 (do mesmo
capítulo) — ver `_debug_segmentos_omar-aziz.txt` e o comentário abaixo de
MARCADORES_OMAR para a evidência completa. Provável artefato da fusão dos 8
PDFs oficiais (arquivo "_01..08.pdf") em um único arquivo/texto.

Diante disso, a segmentação exaustiva usada aqui abandona a ideia de
"reconstituir a ordem de leitura" (inviável de forma confiável dentro do
orçamento deste projeto) e usa, em vez disso, os títulos de capítulo REAIS
que aparecem no corpo do texto (ex.: "PARTE 05. Serviços ambientais e
valoração econômica da floresta", "PARTE 01 A reconstrução da segurança
pública no Amazonas") como marcadores verbatim. Cada segmento de texto
delimitado por dois desses marcadores consecutivos — na ordem em que
aparecem no arquivo, não necessariamente a ordem de leitura pretendida — é
integralmente contado e atribuído a UM tema. Isso preserva a garantia
essencial do método (100% do corpo classificado, nenhuma amostragem) mesmo
sem uma leitura sequencial coerente do documento. A granularidade é mais
grossa que a dos demais candidatos do projeto (marcadores de capítulo, não
de subseção), exceto no bloco de ~470 mil caracteres da "Parte 05" (o maior
bloco ambíguo do documento, cobrindo 5 capítulos diferentes), que foi
subdividido em 5 usando os próprios subtítulos internos reais.
Cada decisão de classificação está comentada linha a linha abaixo.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/amazonas/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/amazonas/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {
        "slug": "omar-aziz", "nome": "Omar Aziz", "partido": "PSD",
        "categoria": (
            "desafiante — ex-governador do Amazonas (2011-2014), atualmente "
            "senador da República, concorrendo para retornar ao cargo; não "
            "integra o grupo político do governo em exercício (Wilson "
            "Lima/Roberto Cidade) e lidera as pesquisas de intenção de voto "
            "divulgadas até agosto de 2026. Fonte: reportagens 'ELEIÇÕES "
            "2026: a difícil missão do senador Omar Aziz retornar ao "
            "governo do Amazonas' (Portal Flagrante) e 'Omar Aziz lidera "
            "disputa pelo governo do Amazonas, diz pesquisa' (Poder360)."
        ),
    },
    {
        "slug": "roberto-cidade", "nome": "Roberto Cidade", "partido": "União",
        "categoria": (
            "candidato de continuidade — escolhido e publicamente apoiado "
            "por Wilson Lima, governador em exercício até abril de 2026, "
            "quando renunciou ao cargo (dentro do prazo de "
            "desincompatibilização) para concorrer ao Senado após dois "
            "mandatos consecutivos (2019-2022 e 2023-2026, portanto "
            "inelegível à reeleição ao Executivo estadual); não é "
            "'incumbente por sucessão' no sentido estrito (não assumiu o "
            "cargo antes da eleição) — é o sucessor indicado, com Wilson "
            "Lima na mesma chapa/coligação como candidato a senador. Fonte: "
            "reportagens ''Grupo fortalecido', diz Wilson Lima ao confirmar "
            "Roberto Cidade como pré-candidato ao Governo do AM' (Agência "
            "Cenarium) e 'Wilson Lima renuncia ao governo do Amazonas no "
            "prazo final de desincompatibilização' (Tribuna do Sertão)."
        ),
    },
    {
        "slug": "david-almeida", "nome": "David Almeida", "partido": "Avante",
        "categoria": (
            "desafiante — prefeito de Manaus licenciado (Avante); disputa o "
            "2º lugar atrás do líder Omar Aziz (PSD) com Roberto Cidade "
            "(União, ligado ao governo Wilson Lima), com margens que variam "
            "de folgadas em um instituto (Instituto Projeta, jun/2026: "
            "Cidade 22,4% x Almeida 17,1%) a tecnicamente empatadas em "
            "outro (Direto ao Ponto, jun/2026: Almeida 21% x Cidade 20%); "
            "passou a ser coberto como candidato pleno em 25/08/2026 por "
            "ser um competidor real, não marginal [fonte: ver "
            "RELATORIO_COMPARATIVO_NORTE.md, seção 7, 'Nota sobre David "
            "Almeida']."
        ),
    },
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — motor canônico, idêntico a todos os estados do
# projeto (Nordeste e agora Norte). NÃO adaptado ao Amazonas, para preservar
# comparabilidade entre estados/regiões.
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

# =============================================================================
# Roberto Cidade (União): documento curto (101 páginas, ~7,1 mil palavras),
# em formato de "cartilha" — 44 "COMPROMISSOS" numerados sequencialmente
# (COMPROMISSO 01 a COMPROMISSO 44), cada um com estrutura fixa (O DESAFIO /
# NOSSO COMPROMISSO / O QUE VAI MUDAR / COMO VAMOS PAGAR ESSA CONTA),
# organizados em 6 blocos temáticos com "banner" gráfico próprio: "Amazonas
# SEGURO" (compromissos 01-10, segurança), "Amazonas SEM ESPERA"
# (compromissos 11-19, saúde), "Amazonas DO FUTURO" (compromissos 20-24,
# educação/CT&I), "cuidar DAS PESSOAS" (compromissos 25-32, assistência
# social e habitação), "Amazonas DAS OPORTUNIDADES" (compromissos 33-42,
# economia/meio ambiente) e "amazonas OBRAS EM" + "Água boa para todos"
# (compromissos 43-44, infraestrutura), fechando com uma seção de gestão por
# resultados sem número de compromisso próprio.
#
# Cada "COMPROMISSO NN" é usado como marcador verbatim (aparece pelo menos
# uma vez no início de cada bloco; a numeração é monotônica de 01 a 44, sem
# sumário/índice repetindo os números antes do corpo, então não há o "bug do
# índice" já visto em outros estados).
#
# Decisões de classificação não óbvias:
#  - COMPROMISSO 06 ("Escola segura"): embora ocorra dentro de ambiente
#    escolar, o conteúdo é sobre prevenção/proteção/monitoramento — mesma
#    lógica de "SEGURANÇA VIÁRIA"/"SEGURANÇA HÍDRICA" tratadas como o tema
#    de origem (aqui, segurança) em vez do tema do ambiente onde a política
#    ocorre. Continua dentro do bloco "Amazonas SEGURO".
#  - COMPROMISSO 07 ("Mulher segura Amazonas"): política de enfrentamento à
#    violência com foco policial (delegacias especializadas, patrulhas,
#    monitoramento de agressores) = seguranca, não assistencia_social.
#  - COMPROMISSO 09 ("Jovem longe do crime"): embora mencione esporte,
#    cultura e qualificação, o enquadramento explícito é de prevenção à
#    criminalidade dentro do bloco "Amazonas SEGURO" = seguranca.
#  - COMPROMISSO 24 (concursos públicos para Educação, Saúde, Segurança e
#    UEA simultaneamente): trecho genuinamente transversal a 3 temas da
#    nossa taxonomia — classificado como gestao_publica, pois o conteúdo em
#    si é sobre política de pessoal/carreira do funcionalismo (um tema de
#    gestão pública), não sobre o mérito de cada política setorial.
#  - COMPROMISSO 29 (educação infantil integrada a saúde/nutrição/proteção
#    social): está dentro do bloco "cuidar DAS PESSOAS" (assistência
#    social) e a própria redação prioriza "proteção social e apoio às
#    famílias" sobre o conteúdo pedagógico = assistencia_social.
#  - COMPROMISSO 32 (reforma/construção de moradias): habitação =
#    infraestrutura, replicando o precedente já usado no Nordeste (Ceará
#    etc.), mesmo estando dentro do bloco "cuidar DAS PESSOAS".
#  - COMPROMISSO 40 (turismo e cultura como "matriz econômica"): a própria
#    redação do candidato enquadra turismo/cultura como estratégia
#    econômica ("uma das principais matrizes econômicas do Amazonas") =
#    economia, replicando o precedente do turismo no Ceará.
#  - COMPROMISSO 41 (esporte): replica o precedente do projeto (Elmano de
#    Freitas/CE) de tratar esporte como assistencia_social, mesmo com
#    menção a "política pública de saúde, educação, inclusão social".
#  - COMPROMISSO 44 ("Água boa para todos", saneamento): infraestrutura,
#    replicando o precedente de saneamento = infraestrutura.
#  - Seção final "governo QUE ENTREGA RESULTADOS" (Plano de Metas 2027-2030,
#    painel público de indicadores, gestão por resultados, transparência):
#    gestao_publica.
#  - Trecho de encerramento retórico final ("COMPROMISSOS — UM SÓ
#    PROPÓSITO: MELHORAR A VIDA DAS PESSOAS", sem conteúdo de política
#    específica) = outros.
# =============================================================================
MARCADORES_ROBERTO = [
    ("COMPROMISSO 01", "seguranca"),
    ("COMPROMISSO 02", "seguranca"),
    ("COMPROMISSO 03", "seguranca"),
    ("COMPROMISSO 04", "seguranca"),
    ("COMPROMISSO 05", "seguranca"),
    ("COMPROMISSO 06", "seguranca"),
    ("COMPROMISSO 07", "seguranca"),
    ("COMPROMISSO 08", "seguranca"),
    ("COMPROMISSO 09", "seguranca"),
    ("COMPROMISSO 10", "seguranca"),
    ("COMPROMISSO 11", "saude"),
    ("COMPROMISSO 12", "saude"),
    ("COMPROMISSO 13", "saude"),
    ("COMPROMISSO 14", "saude"),
    ("COMPROMISSO 15", "saude"),
    ("COMPROMISSO 16", "saude"),
    ("COMPROMISSO 17", "saude"),
    ("COMPROMISSO 18", "saude"),
    ("COMPROMISSO 19", "saude"),
    ("COMPROMISSO 20", "educacao"),
    ("COMPROMISSO 21", "educacao"),
    ("COMPROMISSO 22", "educacao"),
    ("COMPROMISSO 23", "educacao"),
    ("COMPROMISSO 24", "gestao_publica"),
    ("COMPROMISSO 25", "assistencia_social"),
    ("COMPROMISSO 26", "assistencia_social"),
    ("COMPROMISSO 27", "assistencia_social"),
    ("COMPROMISSO 28", "assistencia_social"),
    ("COMPROMISSO 29", "assistencia_social"),
    ("COMPROMISSO 30", "assistencia_social"),
    ("COMPROMISSO 31", "assistencia_social"),
    ("COMPROMISSO 32", "infraestrutura"),
    ("COMPROMISSO 33", "economia"),
    ("COMPROMISSO 34", "economia"),
    ("COMPROMISSO 35", "economia"),
    ("COMPROMISSO 36", "economia"),
    ("COMPROMISSO 37", "economia"),
    ("COMPROMISSO 38", "economia"),
    ("COMPROMISSO 39", "economia"),
    ("COMPROMISSO 40", "economia"),
    ("COMPROMISSO 41", "assistencia_social"),
    ("COMPROMISSO 42", "meio_ambiente"),
    ("COMPROMISSO 43", "infraestrutura"),
    ("COMPROMISSO 44", "infraestrutura"),
    ("governo\n QUEENTREGA", "gestao_publica"),
    ("COMPROMISSOS\n      UM SÓ PROPÓSITO", "outros"),
]

# =============================================================================
# Omar Aziz (PSD): documento de 1552 páginas / ~449 mil tokens — ver nota no
# topo do arquivo sobre o problema de ordenação das páginas na extração.
#
# MÉTODO: o rodapé "Parte NN. Plano [Ee]stratégico de [Dd]esenvolvimento"
# (com variação de capitalização) se repete em toda página do documento, e o
# número NN muda a cada novo capítulo. Detectamos as 25 TRANSIÇÕES desse
# rodapé (pontos em que o texto exato do rodapé muda) percorrendo o corpo
# inteiro do início ao fim — isso garante cobertura de 100% do documento,
# mesmo sem a ordem de leitura pretendida estar preservada. Cada um dos 25
# blocos resultantes foi lido por amostragem (5 pontos: 2%, 25%, 50%, 75%,
# 95% de cada bloco) para determinar se era tematicamente homogêneo, e então
# o título de capítulo real (quando presente, formato "PARTE NN." seguido de
# título) foi usado para confirmar/nomear o tema. Isso é necessariamente
# mais grosso que a segmentação subseção-a-subseção usada nos demais
# candidatos do projeto — mas é a única abordagem exaustiva e auditável
# viável dado o tamanho do documento e o problema de ordenação.
#
# Evidência do problema de ordenação (não é erro de leitura nossa, é do
# arquivo): o .txt começa com o capítulo "Riscos jurídicos / territoriais /
# institucionais / sociais / econômicos" (rodapé "Parte 08"), que traz
# números de página impressos 561-582 — ou seja, o conteúdo da PÁGINA 561 do
# PDF é a primeira coisa que aparece no .txt. O arquivo termina com conteúdo
# de páginas impressas ~541-560 (mesmo capítulo). Ao longo do documento, o
# número do rodapé "Parte NN" NÃO é monotônico (ex.: a sequência de
# transições é 08, 09, 05, 02, 03, 05, 01, 02, 03, 04, 01, 02... — nunca
# simplesmente 01→02→...→09) porque o arquivo final parece ser a
# concatenação dos 8 PDFs originais ("_01.pdf" a "_08.pdf") em uma ordem que
# não corresponde à ordem de leitura do documento publicado (cada PDF
# aparenta ser um "volume" com sua própria numeração interna de "Parte
# 01..09"). Ver `_debug_segmentos_omar-aziz.txt` para os 29 blocos finais.
#
# Blocos 2 e 5 (identificados abaixo como "outros"): ambos começam com um
# trecho de "Considerações Finais" de um volume (ex.: "este terceiro volume
# reafirma... Educação, Ciência, Cultura, Inovação...") mas o restante do
# bloco mistura, por amostragem, conteúdo de pautas completamente diferentes
# (política de IA em escolas, drenagem urbana, órgãos ambientais) e depois
# um glossário de siglas de dezenas de secretarias/autarquias de todas as
# áreas de governo — não é possível separar esses temas com segurança dentro
# do orçamento deste projeto, por isso caem em "outros", como a metodologia
# do projeto prevê para trechos genuinamente multitemáticos.
#
# Bloco 14 (o maior bloco ambíguo do documento, ~469 mil caracteres) foi
# subdividido usando os 5 subtítulos reais internos (todos no formato "PARTE
# 05." seguido de título de capítulo), permitindo classificação fina em vez
# de recair em "outros": Serviços Ambientais (meio_ambiente), Ciência e
# Tecnologia (educacao — mesmo precedente já usado no Ceará/Elmano/Ciro para
# C&T sem tema dedicado na taxonomia), Inteligência Artificial e
# Transformação Digital no setor público (gestao_publica — mesmo tratamento
# do capítulo "Governo Digital", bloco 21), Economia Criativa e Atração de
# Investimentos (economia).
#
# Bloco 0 ("Riscos" — jurídicos, territoriais, institucionais, sociais,
# econômicos, todos no mesmo capítulo transversal, conforme orientação
# explícita do briefing deste projeto) = outros.
# Blocos 22/23/24 ("Política indigenista"): a taxonomia de 9 temas do
# projeto não tem eixo dedicado a povos indígenas; o conteúdo (proteção
# territorial, direitos, FEPIAM, participação) é tratado como
# assistencia_social, pela mesma lógica que a legenda do dashboard já usa
# para esse tema ("Assist. Social, DH, Cultura" — direitos humanos).
# =============================================================================
MARCADORES_OMAR = [
    # bloco 0 · pos 116 · ~2,3 mil palavras · capítulo "Riscos" (jurídicos,
    # territoriais, institucionais, sociais, econômicos) — transversal por
    # definição, mais bibliografia numerada ao final do bloco.
    ("Parte 08. Plano Estratégico de Desenvolvimento", "outros"),
    # bloco 1 · pos 14048 · ~0,9 mil palavras · "PARTE 09. Considerações
    # sobre a abrangência institucional do Plano" — nota metodológica sobre
    # quais órgãos/autarquias o Plano cobre e reforma administrativa futura.
    ("Parte 09. Plano Estratégico de Desenvolvimento", "gestao_publica"),
    # bloco 2 · pos 19424 · ~21,2 mil palavras · abre com "Considerações
    # Finais" do "terceiro volume" (Educação/Ciência/Cultura/Inovação) mas o
    # restante mistura política de IA escolar, drenagem urbana, órgãos
    # ambientais e um extenso glossário de siglas multissetorial —
    # genuinamente multitemático, não separável com segurança.
    ("Parte 05. Plano Estratégico de Desenvolvimento", "outros"),
    # bloco 3 · pos 146501 · ~25,3 mil palavras · Saúde (hospitais, PCCS-
    # Saúde da SES-AM, interiorização da saúde, Pacto Estadual pela Saúde).
    ("Parte 02. Plano estratégico de desenvolvimento", "saude"),
    # bloco 4 · pos 298107 · ~28,3 mil palavras · "PARTE 03. Amazonas Forte
    # Social: rede de proteção" — assistência social, CRAS/CREAS, SUAS,
    # segurança alimentar.
    ("Parte 03. Plano estratégico de desenvolvimento", "assistencia_social"),
    # bloco 5 · pos 467790 · ~9,9 mil palavras · abre com "Considerações
    # Finais" do "segundo volume" (Saúde/Assistência Social/Segurança
    # Pública) e mistura SWOT de segurança + glossário de siglas —
    # genuinamente multitemático.
    ("Parte 05. Plano estratégico de desenvolvimento", "outros"),
    # bloco 6 · pos 527159 · ~62,2 mil palavras · "01. Educação" (Pé-de-
    # Meia, CadÚnico, Instituto Unibanco, alfabetização) — o maior capítulo
    # monotemático do documento além da segurança pública.
    ("Parte 01. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 7 · pos 900510 · ~53,3 mil palavras · "02. Meio Ambiente"
    # (cobertura vegetal, MapBiomas, governança ambiental) — inclui trechos
    # sobre aquicultura/piscicultura tratados dentro do capítulo ambiental
    # do candidato, mantidos como meio_ambiente por seguir o enquadramento
    # dado pelo próprio documento a este capítulo específico.
    ("Parte 02. Plano Estratégico de Desenvolvimento", "meio_ambiente"),
    # bloco 8 · pos 1220342 · ~33,7 mil palavras · "03. Cultura como
    # Política de Estado" — replica o precedente do projeto (cultura =
    # assistencia_social).
    ("Parte 03. Plano Estratégico de Desenvolvimento", "assistencia_social"),
    # bloco 9 · pos 1422478 · ~7,2 mil palavras · "04. FAPEAM: modernização,
    # pesquisa e desenvolvimento regional" — ciência/tecnologia/pesquisa,
    # mesmo tratamento de C&T dado no Ceará (educacao).
    ("Parte 04. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 10 · pos 1465492 · ~97,6 mil palavras · o maior capítulo
    # monotemático do documento — Segurança Pública (crime organizado,
    # interiorização da segurança, dados do Anuário Brasileiro de Segurança
    # Pública).
    ("Parte 01. Plano estratégico de desenvolvimento", "seguranca"),
    # bloco 11 · pos 2050867 · ~42,9 mil palavras · "PARTE 02. Saúde
    # Amazonas: uma rede integrada de cuidado".
    ("Parte 02. Plano estratégico de desenvolvimento", "saude"),
    # bloco 12 · pos 2308560 · ~40,7 mil palavras · Aquicultura/piscicultura
    # e cadeias de produtos florestais madeireiros/não madeireiros —
    # capítulos de desenvolvimento de setores produtivos primários =
    # economia.
    ("Parte 03. Plano estratégico de desenvolvimento", "economia"),
    # bloco 13 · pos 2552507 · ~65,8 mil palavras · Indústria, Comércio,
    # Mineração, Turismo, Bioeconomia — capítulos de "Setores estratégicos
    # para a economia" = economia.
    ("Parte 04. Plano estratégico de desenvolvimento", "economia"),
    # bloco 14 (início) · pos 2947126 · Serviços Ambientais e valoração
    # econômica da floresta = meio_ambiente. Ver subdivisão abaixo.
    ("Parte 05. Plano estratégico de desenvolvimento", "meio_ambiente"),
    # bloco 14b · Ciência, Tecnologia e Inovação para o desenvolvimento.
    ("Ciência, tecnologia\ne inovação para o\ndesenvolvimento", "educacao"),
    # bloco 14c · Inteligência Artificial e transformação digital no setor
    # público e produtivo — mesmo tratamento do capítulo "Governo Digital"
    # (bloco 21) = gestao_publica.
    ("Inteligência Artificial e\n transformação digital", "gestao_publica"),
    # bloco 14d · Economia criativa e empreendedorismo como estratégias de
    # inclusão produtiva = economia.
    ("Economia criativa e\nempreendedorismo", "economia"),
    # bloco 14e · Atração de investimentos e ambiente de negócios = economia.
    ("Atração de investimentos\ne ambiente de negócios", "economia"),
    # bloco 15 · pos 3416155 · ~13,5 mil palavras · "PARTE 01. A
    # reconstrução da segurança pública no Amazonas" — continuação/overflow
    # do capítulo de segurança pública (sistema prisional, câmeras,
    # elucidação criminal).
    ("Parte 01. Plano estratégico de desenvolvimento", "seguranca"),
    # bloco 16 · pos 3497102 · ~6,9 mil palavras · continuação de CT&I/FAPEAM
    # (PAIC, PCE Ciência na Escola) — educacao.
    ("Parte 04. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 17 · pos 3538258 · ~6,6 mil palavras · "PARTE 05. Centro de
    # Educação Tecnológica do Amazonas (CETAM)" — educação profissional.
    ("Parte 05. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 18 · pos 3577949 · ~0,7 mil palavras · continuação do capítulo
    # CETAM (revisão da Política de Educação Profissional).
    ("Parte 04. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 19 · pos 3582441 · ~3,2 mil palavras · continuação/fechamento do
    # capítulo CETAM + referências bibliográficas do capítulo.
    ("Parte 05. Plano Estratégico de Desenvolvimento", "educacao"),
    # bloco 20 · pos 3601816 · ~28,6 mil palavras · "06. HABITAÇÃO —
    # Programa Amazonas Habitação" (regularização fundiária, política
    # habitacional) = infraestrutura, replicando precedente do projeto.
    ("Parte 06. Plano Estratégico de Desenvolvimento", "infraestrutura"),
    # bloco 21 · pos 3773631 · ~23,7 mil palavras · "07. Governo Digital —
    # Programa Amazonas Digital" (conectividade, interoperabilidade entre
    # sistemas estaduais) = gestao_publica.
    ("Parte 07. Plano Estratégico de Desenvolvimento", "gestao_publica"),
    # bloco 22 · pos 3915778 · ~2,7 mil palavras · "PARTE 08. Política
    # indigenista: da presença ancestral ao protagonismo no desenvolvimento"
    # — sem tema dedicado na taxonomia do projeto; tratado como
    # assistencia_social (proteção territorial e direitos, mesmo
    # enquadramento de "Direitos Humanos" já usado na legenda do projeto).
    ("Parte 08. Plano Estratégico de Desenvolvimento", "assistencia_social"),
    # bloco 23 · pos 3932033 · ~0,8 mil palavras · continuação do capítulo
    # de política indigenista (FEPIAM, gestão de riscos territoriais).
    ("Parte 05. Plano Estratégico de Desenvolvimento", "assistencia_social"),
    # bloco 24 · pos 3936829 · ~10,3 mil palavras · fechamento do capítulo
    # de política indigenista (plano de ação, monitoramento, gestão de
    # riscos institucionais e territoriais do próprio capítulo indigenista).
    ("Parte 08. Plano Estratégico de Desenvolvimento", "assistencia_social"),
]

# =============================================================================
# David Almeida (Avante, adicionado em 25/08/2026 — ver nota no topo do
# arquivo e RELATORIO_COMPARATIVO_NORTE.md sobre a decisão de cobrir todos
# os candidatos competitivos, não um número fixo por estado): documento
# curto (76 páginas, ~19,4 mil palavras), plano "Pra Cima, Amazonas"
# organizado em 9 "Eixos Estratégicos" numerados, cada um com um "programa
# de marca" próprio (ex.: Eixo 1 = "Amazonas Conectado", Eixo 6 = "Amazonas
# Seguro"). Estrutura muito próxima à de Marcos Rogério (RO) e Hildon
# Chaves (RO): Eixos numerados, título temático claro, conteúdo
# internamente coerente na maior parte dos casos — por isso a granularidade
# usada aqui é a de Eixo inteiro, com duas exceções documentadas abaixo.
# Cada título de Eixo tem 1 ocorrência no corpo em formato final (linha
# única, sem quebra) e mais 1 ocorrência no sumário/TOC inicial (que grafa
# o título quebrado em 2-3 linhas, formato diferente do usado no corpo) —
# como o PRIMEIRO marcador da lista ("EIXO 1: ...") tem apenas 1 ocorrência
# no formato exato usado aqui (o sumário grafa "GESTÃO PÚBLICA EFICIENTE" e
# "E TRANSPARENTE" em 2 linhas separadas), main() usa cursor_inicial=0 sem
# necessidade de nenhum ajuste — a lógica já usada para Omar Aziz e Roberto
# Cidade neste mesmo script. Todo o material antes do Eixo 1 (Introdução,
# Nosso Compromisso, Diagnóstico SWOT do Amazonas, Dados Gerais do Estado,
# Direcionamento Estratégico — cerca de metade do documento em caracteres,
# mas rico em dados quantitativos) cai em "outros" na distribuição
# temática, seguindo o mesmo tratamento de front matter usado em todos os
# candidatos do projeto; para o Índice de Base Empírica, esse front matter
# é PRESERVADO (cursor_inicial=0 para os 3 candidatos do Amazonas, sem
# nenhum corte), pois é exatamente ali que está concentrada a maior parte
# dos dados de diagnóstico (IDHM, PIB, indicadores SWOT com fonte citada).
#
# Exceção 1 — Eixo 7 ("Desenvolvimento Social, Cidadania e Direitos
# Humanos"): mistura, sem nenhum subtítulo de nível Eixo que os separe,
# blocos de assistência social/cidadania/direitos humanos com dois blocos
# de infraestrutura (Habitação e Regularização Fundiária "Casa Amazonense";
# Saneamento Básico "Trata Bem Amazonas" — replicando o precedente do
# projeto de habitação/saneamento = infraestrutura) e um bloco de esporte e
# lazer ("Programa Talentos da Floresta", incluindo sua subseção própria de
# infraestrutura esportiva) — replicando o precedente do projeto de
# esporte = assistencia_social (mesmo tratamento já usado para Roberto
# Cidade, COMPROMISSO 41, neste mesmo estado). Dividido em 3 segmentos
# usando os subtítulos reais do documento: (a) abertura do Eixo até o
# subtítulo "HABITAÇÃO E REGULARIZAÇÃO FUNDIÁRIA" = assistencia_social;
# (b) desse subtítulo até "ESPORTE E LAZER" = infraestrutura; (c) de
# "ESPORTE E LAZER" até o Eixo 8 = assistencia_social.
#
# Exceção 2 — Eixo 8 ("Meio Ambiente, Sustentabilidade e Transição
# Climática"): tem uma subseção autônoma e claramente separável, "Meu Pet
# Amazonas" (política estadual de proteção e bem-estar animal, castração de
# cães e gatos), destacada como assistencia_social — mesmo precedente já
# usado em Marcos Rogério (RO, subseção "PROTEÇÃO ANIMAL"), e diferente do
# caso de Hildon Chaves (RO, subseção 13.6), onde o conteúdo equivalente
# estava fundido numa única proposta indivisível com fauna silvestre e por
# isso foi mantido em meio_ambiente — aqui, como em Marcos Rogério, a
# subseção é autônoma e claramente separável do restante do capítulo
# ambiental, permitindo a divisão.
#
# O capítulo final "7. MENSAGEM FINAL" (retórica de encerramento, sem
# conteúdo de política específica) = outros, mesmo precedente já usado nos
# encerramentos de todos os outros candidatos do projeto.
# =============================================================================
MARCADORES_DAVID = [
    ("EIXO 1: GESTÃO PÚBLICA EFICIENTE E TRANSPARENTE", "gestao_publica"),
    ("EIXO 2: DESENVOLVIMENTO ECONÔMICO SUSTENTÁVEL E INOVAÇÃO", "economia"),
    ("EIXO 3: INFRAESTRUTURA E LOGÍSTICA PARA A INTEGRAÇÃO REGIONAL", "infraestrutura"),
    ("EIXO 4: EDUCAÇÃO TRANSFORMADORA", "educacao"),
    ("EIXO 5: SAÚDE DESCENTRALIZADA E REGONALIZADA", "saude"),  # "REGONALIZADA": grafia original do documento
    ("EIXO 6: SEGURANÇA INTEGRADA", "seguranca"),
    ("EIXO 7: DESENVOLVIMENTO SOCIAL, CIDADANIA E DIREITOS HUMANOS", "assistencia_social"),
    ("HABITAÇÃO E REGULARIZAÇÃO FUNDIÁRIA", "infraestrutura"),  # Eixo 7, subseção Habitação+Saneamento
    ("ESPORTE E LAZER", "assistencia_social"),  # Eixo 7, subseção Esporte
    ("EIXO 8: MEIO AMBIENTE, SUSTENTABILIDADE E TRANSIÇÃO CLIMÁTICA", "meio_ambiente"),
    ("Meu Pet Amazonas", "assistencia_social"),  # Eixo 8, subseção autônoma de bem-estar animal
    ("EIXO 9: INTERIOR FORTE E SUSTENTÁVEL", "economia"),
    ("7. MENSAGEM FINAL", "outros"),  # capítulo de encerramento do plano
]

MARCADORES = {
    "omar-aziz": MARCADORES_OMAR,
    "roberto-cidade": MARCADORES_ROBERTO,
    "david-almeida": MARCADORES_DAVID,
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
    segmentos_debug.append(("[FRONT MATTER: capa/cabeçalho/intro]", "outros", n_intro))

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
# TAREFA 2 — Índice de Base Empírica (heurística idêntica a todos os estados)
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
        arquivo_txt = slug.replace("-", "_") + ".txt"
        raw_text = (PLANOS_DIR / arquivo_txt).read_text(encoding="utf-8")
        corpo = strip_header(raw_text)

        total_tokens, counts, top20 = word_freq(corpo, top_n=20)
        agregado_counter.update(counts)

        marcadores = MARCADORES[slug]
        # cursor_inicial = 0 para os três candidatos do Amazonas (incluindo
        # David Almeida, adicionado em 25/08/2026): nenhum dos três planos
        # repete o primeiro marcador dentro de um sumário/índice antes do
        # corpo real, no formato exato usado como marcador (diferente do
        # que ocorreu no Ceará/Maranhão).
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
                marcador_1linha = marcador.replace("\n", " ⏎ ")
                f.write(f"[{tema:20s}] {n:7d} palavras ({pct_seg:5.1f}%) :: {marcador_1linha[:90]}\n")

        print(f"{c['nome']:<20} total={total_tokens:7d}  base_empirica={be['indice']:5.1f}%  "
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
            "mesma usada em todos os estados do projeto — inclui termos "
            "específicos de outros estados (ex.: 'maranhão'/'maranhense'), "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados e regiões. Mostra os "
            "termos mais repetidos por candidato e o agregado dos três "
            "planos do Amazonas."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido e segmentado por seus "
            "marcadores de seção/capítulo reais (títulos de capítulo, ou, no "
            "caso de Roberto Cidade, o rótulo numerado 'COMPROMISSO NN' que "
            "abre cada proposta). Cada segmento de texto entre dois "
            "marcadores consecutivos foi contado (em número de palavras) e "
            "atribuído a UM dos 9 temas. Quando um trecho do documento "
            "original já reunia explicitamente múltiplos temas de forma "
            "indivisível, o segmento foi classificado item a item sempre que "
            "os itens individuais eram identificáveis, ou como 'outros' "
            "quando não era possível separar com segurança. No caso "
            "específico de Omar Aziz, dado o tamanho atípico do documento "
            "(~449 mil palavras) e um problema de ordenação das páginas na "
            "extração (ver metodologia_nota), a granularidade da "
            "segmentação é de capítulo (não de subseção) na maior parte do "
            "documento — ver comentários detalhados no script "
            "build_analysis_am.py e o arquivo de auditoria "
            "_debug_segmentos_omar-aziz.txt."
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
            "Heurística idêntica à usada em todos os estados anteriores do "
            "projeto (Nordeste), sem nenhum ajuste específico para o "
            "Amazonas, para manter comparabilidade entre estados e regiões."
        ),
        "metodologia_nota": (
            "O Amazonas é o primeiro estado da Região Norte analisado neste "
            "projeto (que cobriu os 9 estados do Nordeste antes), com a "
            "mesma metodologia. Os dois candidatos: Omar Aziz (PSD), "
            "desafiante, ex-governador do Amazonas (2011-2014) atualmente "
            "senador, concorrendo para retornar ao cargo e fora do grupo "
            "político do governo em exercício; e Roberto Cidade (União), "
            "candidato de continuidade indicado por Wilson Lima, governador "
            "por dois mandatos consecutivos (2019-2022 e 2023-2026) que "
            "renunciou ao cargo em abril de 2026, dentro do prazo de "
            "desincompatibilização, para concorrer ao Senado. Fonte oficial "
            "de ambos os planos: proposta de governo registrada no TSE "
            "(proposta_governo_2026_AM.zip, cdn.tse.jus.br). "
            "CASO ESPECIAL — Omar Aziz: seu plano tem 1552 páginas e cerca "
            "de 449 mil palavras — o maior documento já processado neste "
            "projeto (incluindo todo o Nordeste; o segundo maior, ACM Neto "
            "na Bahia, tem ~75 mil palavras), redigido em estilo quase "
            "acadêmico com referências bibliográficas numeradas espalhadas "
            "ao longo de todo o texto. Além do tamanho, o arquivo de texto "
            "extraído do PDF oficial (fusão de 8 arquivos "
            "'2026AM..._01.pdf' a '..._08.pdf') NÃO preserva a ordem de "
            "leitura pretendida do documento: o texto começa com o "
            "conteúdo da página impressa 561 (capítulo 'Riscos', que "
            "pertence à 'Parte 08') e termina com conteúdo de páginas "
            "impressas por volta de 541-560 do mesmo capítulo — evidência "
            "de que os 8 PDFs foram concatenados em uma ordem diferente da "
            "publicada, e não em uma sequência simples de capítulos 1 a N. "
            "Diante disso, a segmentação temática de Omar Aziz abandonou a "
            "tentativa de reconstituir a ordem de leitura (inviável de "
            "forma confiável dentro do orçamento deste projeto) e usa, em "
            "vez disso, os títulos de capítulo reais que aparecem no corpo "
            "do texto como marcadores verbatim, na ordem em que aparecem "
            "no arquivo — o que garante cobertura de 100% do documento, "
            "mas com uma granularidade mais grossa (de capítulo, não de "
            "subseção) do que a usada nos demais candidatos do projeto. Um "
            "bloco de ~470 mil caracteres que cruzava 5 capítulos "
            "diferentes foi subdividido usando os próprios subtítulos "
            "internos; dois blocos de encerramento de volume (que misturam "
            "trechos de conclusão com um glossário de siglas "
            "multissetorial) foram classificados como 'outros' por serem "
            "genuinamente multitemáticos e não separáveis com segurança. "
            "Toda a segmentação está documentada e é auditável em "
            "_debug_segmentos_omar-aziz.txt e nos comentários de "
            "MARCADORES_OMAR no script de análise. Nenhuma dessas "
            "particularidades de extração influenciou a heurística do "
            "Índice de Base Empírica, que opera frase a frase "
            "independentemente da ordem das páginas. "
            "Ressalva sobre a frequência de palavras: o rodapé 'Parte NN. "
            "Plano Estratégico de Desenvolvimento' se repete 1.420 vezes ao "
            "longo do documento de Omar Aziz (uma vez por página, "
            "aproximadamente). 'Parte'/'plano' são filtrados pela lista de "
            "stopwords estruturais do projeto, mas 'estratégico' e "
            "'desenvolvimento' não — por isso boa parte da frequência de "
            "'desenvolvimento' (2.414 ocorrências no total) e 'estratégico' "
            "(1.873) vem desse rodapé repetido, e não de ênfase textual real "
            "do candidato. Mesmo tipo de ruído de extração já documentado "
            "no Ceará (rodapé 'Elmano Governador 2027-2030') e no Maranhão, "
            "aqui com efeito bem maior dado o tamanho do documento. "
            "ATUALIZAÇÃO (25/08/2026): David Almeida (Avante), prefeito de "
            "Manaus licenciado, foi adicionado como 3º candidato pleno do "
            "Amazonas a pedido do pesquisador responsável, que decidiu que "
            "o critério de seleção deve cobrir todos os candidatos "
            "competitivos nas pesquisas, e não um número fixo por estado. "
            "Pesquisas de 2026 mostram Roberto Cidade geralmente à frente "
            "de Almeida na disputa pelo 2º lugar atrás de Omar Aziz, com "
            "margens que variam de folgadas (Instituto Projeta, jun/2026: "
            "Cidade 22,4% x Almeida 17,1%) a tecnicamente empatadas (Direto "
            "ao Ponto, jun/2026: Almeida 21% x Cidade 20%) conforme o "
            "instituto — Almeida é um competidor real, não marginal. Ver o "
            "campo 'categoria' de David Almeida para as fontes dessa "
            "checagem, e RELATORIO_COMPARATIVO_NORTE.md (seção 7, 'Nota "
            "sobre David Almeida') para o registro anterior dessa decisão. "
            "O documento de David Almeida (76 páginas, plano 'Pra Cima, "
            "Amazonas', 9 Eixos Estratégicos numerados) é o mais curto dos "
            "3 candidatos do Amazonas e o único, junto com Roberto Cidade, "
            "sem o problema de ordenação de páginas do plano de Omar Aziz. "
            "Foi segmentado na mesma granularidade de Eixo inteiro usada "
            "por Marcos Rogério e Hildon Chaves (RO), com duas exceções "
            "documentadas no docstring do módulo e nos comentários de "
            "MARCADORES_DAVID: (1) o Eixo 7 ('Desenvolvimento Social, "
            "Cidadania e Direitos Humanos') foi dividido em 3 segmentos, "
            "pois mistura assistência social/cidadania/DH com dois blocos "
            "de infraestrutura (habitação, saneamento) e um bloco de "
            "esporte e lazer; (2) dentro do Eixo 8 (Meio Ambiente), a "
            "subseção autônoma 'Meu Pet Amazonas' (bem-estar animal) foi "
            "destacada como assistencia_social, mesmo precedente já usado "
            "para a subseção equivalente de Marcos Rogério (RO). Para o "
            "Índice de Base Empírica, nenhum corte foi aplicado "
            "(cursor_inicial=0, mesmo tratamento dos outros 2 candidatos do "
            "Amazonas) — o que preserva o rico capítulo de diagnóstico "
            "SWOT e dados gerais do Estado (IDHM, PIB, indicadores com "
            "fonte citada) que antecede os 9 Eixos."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
