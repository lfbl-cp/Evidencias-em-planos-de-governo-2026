#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor compartilhado — Índice de Base Empírica, distribuição temática exaustiva,
tokenização/frequência de palavras e nuvem de palavras.

Extraído em 28/08/2026 (reorganização v2) dos 24 scripts `build_analysis_<uf>.py`
canônicos do projeto (25 estados menos Pernambuco, cujo script tinha nomes de
função ligeiramente diferentes mas o mesmo motor). Antes desta extração, cada
estado carregava uma cópia colada à mão desta lógica — o próprio projeto já
documentava isso como "heurística idêntica, reaproveitada sem alterações" em
todo `build_analysis_*.py`; esta extração só torna essa intenção estrutural.

Verificação feita antes de extrair (não coloque nada aqui de cabeça): diff
byte-a-byte de WORD_RE/STOPWORDS/TEMAS/JARGAO_TERMOS/NUM_ANY e das funções
tokenize/word_freq/strip_header/distribuicao_tematica_exaustiva/is_diagnostico/
is_efeito/is_evidencia/split_sentences/looks_like_header/base_empirica_analise
entre São Paulo, Minas Gerais, Piauí, Paraná, Distrito Federal e Acre (um
estado de cada região) — todas idênticas. Duas exceções reais (não apenas de
comentário) foram encontradas e viraram parâmetros opcionais em vez de serem
silenciosamente uniformizadas:

1. **Bahia** (`build_analysis_ba.py`): o PDF de Jerônimo Rodrigues usa o
   caractere de controle `\x90` como marcador de bullet (275 ocorrências) —
   BULLET_RE lá inclui `\x90` além de `-`/`•`. Ver parâmetro `bullet_re` de
   `split_sentences`/`base_empirica_analise` abaixo.
2. **Piauí** (`build_analysis_pi.py`, e possivelmente outros scripts dos
   primeiros estados processados): versão mais antiga de
   `gerar_wordcloud_png_b64` — gera a nuvem a partir de `counts` não
   filtrado (inclui stopwords) e `prefer_horizontal=0.92`, em vez da versão
   canônica (filtra stopwords, `prefer_horizontal=0.9`) usada pela maioria
   dos estados, entre eles São Paulo. Preservada como
   `gerar_wordcloud_png_b64_legacy_pi` para não alterar um PNG já publicado.
3. **Alagoas**, **Bahia** e **Rio Grande do Norte** (`build_analysis_al.py`,
   `build_analysis_ba.py`, `build_analysis_rn.py`), achado na migração de
   cada um para este motor (28/08/2026): `gerar_wordcloud_png_b64` nos três
   usa `max_words=20`, em vez do `max_words=120` canônico usado pela
   maioria dos estados, entre eles São Paulo. Preservado como parâmetro
   opcional `max_words` (default 120, idêntico ao comportamento anterior de
   todo estado que não passa o argumento) para não alterar um PNG já
   publicado de nenhum dos três.

Qualquer novo desvio real (não de comentário) encontrado ao migrar outro
estado para este motor deve ser tratado da mesma forma — um parâmetro opcional
documentado aqui, nunca uma cópia-garfo (fork) do módulo inteiro nem uma
normalização silenciosa que mude um número ou PNG já publicado.
"""
import base64
import re
from collections import Counter
from io import BytesIO

from wordcloud import WordCloud

# ---------------------------------------------------------------------------
# Tokenização e stopwords
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

# Termos estruturais comuns a todo plano de governo (candidato, governo,
# eleições...). Deliberadamente NÃO adaptados por estado (ex.: mantém
# "maranhão"/"maranhense" mesmo fora do Maranhão) — mesma convenção do
# projeto original, para preservar comparabilidade entre estados. Um estado
# pode estender com EXTRA_STOPWORDS_ESTADO na sua config; ver `word_freq`.
EXTRA_STOPWORDS_BASE = set("""
candidato candidata governador governadora vice-governador vice-governadora
plano governo maranhão maranhense maranhenses eleições 2026 partido número
coligação fonte fontes status texto seção seções eixo eixos parte partes
bloco blocos documento página páginas inclui incluem também estamos propõe
prevê abertura caminho proposto propostos principais desafios núcleo
contexto visão onde compromisso compromissos destaca destacados destacado
""".split()) | set("""
ods sumário monitoramento revisão implementação
""".split())

TEMAS = ["saude", "seguranca", "educacao", "infraestrutura", "meio_ambiente",
         "economia", "gestao_publica", "assistencia_social", "outros"]


def strip_header(text: str) -> str:
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx + len(marker):] if idx != -1 else text


def tokenize(text: str):
    return [w.lower() for w in WORD_RE.findall(text)]


def word_freq(text: str, all_stopwords, top_n=20):
    tokens = tokenize(text)
    total_tokens = len(tokens)
    filtered = [w for w in tokens if w not in all_stopwords and len(w) > 2]
    counts = Counter(filtered)
    top = counts.most_common(top_n)
    return total_tokens, counts, top


# ---------------------------------------------------------------------------
# Distribuição temática exaustiva
# ---------------------------------------------------------------------------
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
# Índice de Base Empírica
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

# CORRIGIDO em 09/10/2026 (projeto brasil_multiciclo, achado do kappa de
# confiabilidade via pipeline de 3 agentes em 25/09/2026, ver
# analise/RELATORIO_KAPPA_MULTICICLO.md, Padrões #1 e #2) -- is_efeito tinha
# dois bugs sistemáticos e direcionais (100% falso-positivo, 0 falso-negativo
# nas 27 discordâncias de B auditadas), ambos corrigidos juntos porque
# bloqueavam o mesmo pilar e foram tratados no mesmo item do roadmap:
#
# Padrão #1 (tempo verbal): EFEITO_RE dispara em qualquer frase com uma
# palavra-gatilho de efeito + um número, sem checar se é uma promessa futura
# ou um fato já ocorrido relatado no passado (ex.: "o estado perdeu 388 mil
# empregos, uma redução de", "houve uma queda de 6%") -- isso é diagnóstico
# (Pilar A), não efeito projetado (Pilar B). PASSADO_RE/FUTURO_RE abaixo
# resolvem isso: só conta como B se não houver marcador de passado, ou se
# houver também um marcador de futuro/meta que sobrepõe.
#
# Padrão #2 (numeração de lista): o número que satisfazia o gatilho não era
# a magnitude da promessa, e sim um rótulo de lista/seção/objetivo ("1)",
# "9.6.1", "Objetivo 11:", "12 •") adjacente à frase por causa do formato do
# PDF. has_real_number() abaixo ignora esses números-rótulo (reconhecidos
# pela forma dígitos/pontos cercada por delimitador de lista ou por grande
# espaço em branco de layout de PDF) e exige pelo menos um número que não
# seja rótulo.
#
# Validado contra a amostra de 204 frases do kappa (programs/build_amostra_kappa.py):
# kappa de Cohen (motor x codificador LLM cego) do Pilar B sobe de 0,469
# (moderada) para 0,769 (substancial); os 16 exemplos documentados dos
# Padrões #1 e #2 passam a classificar corretamente; os 15 casos de Pilar B
# já confirmados como verdadeiro-positivo continuam verdadeiros (zero
# regressão nesta amostra).
#
# CORRIGIDO de novo em 09/10/2026, mesmo dia -- um agente revisor adversarial
# (rodada 2 do pipeline de validação, ver analise/REVISAO_ADVERSARIAL_V2.md)
# achou uma regressão real que a amostra de 204 frases não continha: o
# gatilho genérico "em (19|20)\d{2}" tratava QUALQUER ano citado como
# passado, inclusive um ano futuro de meta ("Em 2030, aumentaremos a
# cobertura vacinal para 95%" virava falso-negativo só por usar "Em" em vez
# de "Até"). Corrigido tornando esse gatilho (e o de "entre ANO e ANO")
# condicional ao ano do próprio ciclo eleitoral do documento (`ano_ciclo`,
# já conhecido em todo ponto de chamada real -- build_indice_base_empirica.py
# processa um ciclo por vez): um ano só conta como marcador de passado se for
# anterior ao ano do ciclo; sem `ano_ciclo` (uso avulso/teste), esse gatilho
# específico fica desativado para não arriscar suprimir uma promessa
# genuína -- os demais marcadores de PASSADO_RE (verbos/citações datadas)
# continuam ativos independente de `ano_ciclo`. O mesmo revisor também achou
# "apontou" (verbo, ex.: "o Censo escolar 2025 apontou uma redução de...")
# fora da lista original -- adicionado.
#
# AUDITADO em 15/10/2026 -- usuário levantou a suspeita de que o índice
# estaria superestimando o PSTU (índice bem acima da média geral). Revisão
# manual dos 73 exemplos de Pilar B do PSTU (codificacao/indice_base_empirica_
# <ano>.json, campo exemplos_pilar_b) achou ~44% de falso-positivo, todos do
# mesmo padrão: a frase descreve um RESULTADO PASSADO/ATUAL negativo (texto
# tipicamente de crítica estrutural a um problema existente, estilo retórico
# comum no material do PSTU), mas contém alguma palavra de FUTURO_RE que
# fazia a exclusão de passado em is_efeito() ser ignorada. Causa raiz: a
# condição "meta (?:de|:)" em FUTURO_RE. Ex. real: "atingiu menos de 15% da
# meta de reduzir a mortalidade infantil" -- claramente passado (tem "atingiu"
# E é sobre uma meta NÃO alcançada), mas "meta de" nessa frase disparava
# FUTURO_RE e cancelava a exclusão de PASSADO_RE, classificando como projeção
# futura (Pilar B positivo) o que é, na verdade, um diagnóstico de fracasso
# passado. Outros padrões de passado/presente-crítico ausentes da lista
# também contribuíam ("em relação a <ano>", "no mesmo período de <ano>", "já
# está/estão", "que existe hoje", "sofrendo", "fez aumentar/diminuir/com que",
# "privatizou").
#
# Correção: (1) removido "meta (?:de|:)" de FUTURO_RE -- "meta" por si só não
# indica tempo verbal, quem indica é o resto da frase (já coberto por outros
# gatilhos de FUTURO_RE como "até <ano>", "próximo mandato" etc. quando a meta
# for de fato prospectiva); (2) adicionados a PASSADO_RE os padrões de
# comparação/crítica estrutural listados acima.
#
# Validação (isolada, 24 falso-positivos + 10 verdadeiro-positivos
# curados manualmente do corpus do PSTU): 10/24 falso-positivos corrigidos,
# 0/10 verdadeiro-positivos regredidos. Validação formal (kappa_gabarito_v3,
# 204 frases, programs/build_amostra_kappa.py): 0 frases mudam de
# classificação, kappa Pilar B inalterado em 0,769 -- ou seja, a amostra
# estratificada original não continha nenhum caso desse padrão específico
# (ele é concentrado em texto de partidos com retórica de crítica estrutural,
# como o PSTU), então a correção é estritamente aditiva sobre essa amostra:
# sem regressão medida, com ganho de precisão no PSTU que a amostra não
# capturava.
PASSADO_RE = re.compile(
    r"\b(houve|houveram|ocorreu|ocorreram|registrou(?:-se)?|registraram|"
    r"foi registrad[ao]|foram registrad[ao]s|perdeu|perdemos|perderam|"
    r"caiu|caíram|cresceu|cresceram|subiu|subiram|correspond(?:e|eu|ia)\s+a|"
    r"que representa|apresentou|apresentaram|apontou|apontaram|atingiu|"
    r"atingiram|chegou a|chegaram a|foi de|foram de|\bfoi\b|\bforam\b|teve|"
    r"tiveram|alcançou|alcançaram|em comparação com a gestão|"
    r"na gestão anterior|no governo anterior|segundo dados d[ao] pnad|"
    r"segundo dados d[ao] censo|pnad (?:19|20)\d{2}|"
    r"censo (?:escolar )?(?:19|20)\d{2}|"
    r"em rela[çc][ãa]o a[o]? (?:19|20)\d{2}|em rela[çc][ãa]o ao mesmo per[íi]odo|"
    r"no mesmo per[íi]odo de (?:19|20)\d{2}|que existe hoje|j[áa] est(?:á|ão)|"
    r"\bsofrendo\b|fez (?:aumentar|diminuir|com que)|\bprivatizou\b)\b|"
    r"-\s?\d+[,\.]?\d*\s?%",
    re.IGNORECASE,
)
FUTURO_RE = re.compile(
    r"\b(ir(?:emos|á|ão)|vamos |pretendemos|pretende(?:m)?|"
    r"até (?:19|20)\d{2}|no próximo mandato|nos próximos \d+ anos|"
    r"até o final do mandato|compromete(?:mos|-se|nos)?|objetivo é|objetivo:|"
    r"nos primeiros \d+ (?:dias|anos))\b",
    re.IGNORECASE,
)
EM_ANO_RE = re.compile(r"\bem ((?:19|20)\d{2})\b", re.IGNORECASE)
ENTRE_ANOS_RE = re.compile(r"\bentre ((?:19|20)\d{2}) e ((?:19|20)\d{2})\b", re.IGNORECASE)


def _tem_marcador_temporal_passado(s_low: str, ano_ciclo) -> bool:
    if PASSADO_RE.search(s_low):
        return True
    if ano_ciclo is not None:
        m = EM_ANO_RE.search(s_low)
        if m and int(m.group(1)) < ano_ciclo:
            return True
        m2 = ENTRE_ANOS_RE.search(s_low)
        if m2 and int(m2.group(1)) < ano_ciclo and int(m2.group(2)) < ano_ciclo:
            return True
    return False
LIST_PRECEDE_RE = re.compile(
    r"(?:^|\s{2,}|\b(?:objetivo|meta|eixo|ação|item|art\.?|artigo)\s*)$",
    re.IGNORECASE,
)
LIST_FOLLOW_RE = re.compile(r"^\s*(?:[\)\.\-–—•:]|\s{2,}|[A-ZÀ-Ý])")


def _is_list_marker_match(s: str, m: "re.Match") -> bool:
    start, end = m.span()
    before, after = s[:start], s[end:]
    token = m.group(0)
    if "%" in token or "r$" in token.lower():
        return False
    if not re.fullmatch(r"\d{1,2}(?:\.\d{1,3}){0,3}", token):
        return False
    return bool(LIST_PRECEDE_RE.search(before)) and bool(LIST_FOLLOW_RE.match(after))


def has_real_number(s_orig: str) -> bool:
    """Como NUM_ANY, mas ignora números que são rótulo de lista/seção/
    objetivo (ver Padrão #2 no comentário acima de EFEITO_RE)."""
    for m in NUM_ANY.finditer(s_orig):
        if not _is_list_marker_match(s_orig, m):
            return True
    return False


def is_efeito(s_orig: str, s_low: str, ano_ciclo=None) -> bool:
    """`ano_ciclo`: ano do ciclo eleitoral do documento (2014/2018/2022/2026),
    quando conhecido -- usado só para o gatilho "em ANO"/"entre ANO e ANO" de
    PASSADO_RE (ver comentário acima de PASSADO_RE)."""
    if not EFEITO_RE.search(s_low):
        return False
    if _tem_marcador_temporal_passado(s_low, ano_ciclo) and not FUTURO_RE.search(s_low):
        return False
    if has_real_number(s_orig):
        return True
    if re.search(r"\bentre (?:as|os) (?:dez|cinco|três)\b", s_low):
        return True
    return False


# CORRIGIDO em 09/10/2026 (brasil_multiciclo, pedido do pesquisador: "explorar as
# inconsistências de partidos como PSTU/PCO" + "fazer as correções
# metodológicas" pendentes). A investigação do índice alto de PSTU/PCO
# (média 12,3%/7,1% vs ~4-5% da maioria dos partidos) mostrou que a maior
# parte é um achado REAL -- esses partidos escrevem propostas em estilo mais
# denso em citação de dado oficial (IBGE/PNAD/Ipea/Datasus) para sustentar
# argumentos estruturais, não um artefato -- mas revelou também um
# mecanismo de falso-positivo real e sistemático em `is_evidencia`, o mesmo
# "jargão vazio" documentado como Padrão #5 no relatório de 25/09/2026 (10
# exemplos, 100% falso-positivo: `pilar_c`=True no motor, False no LLM
# cego), nunca corrigido até agora:
#
# 1. "a exemplo d[eo]/da" sozinho é "por exemplo", não citação de precedente
#    -- confirmado contra os 204 frases do kappa (11 ocorrências: 7
#    falso-positivo, 4 verdadeiro-positivo) E contra o corpus completo de
#    PSTU/PCO (22 ocorrências, TODAS falso-positivo -- nenhuma citava um
#    precedente real, eram listas de exemplos genéricos: "a exemplo da
#    carcinicultura", "a exemplo da greve", "a exemplo do Itapoã"). Testei
#    duas correções: remover o gatilho inteiro (perde as 4 verdadeiro-
#    positivo) vs. exigir um nome próprio capitalizado nas ~9 palavras
#    seguintes (`EXEMPLO_NOME_PROPRIO_RE` abaixo) -- a segunda preserva 3
#    das 4 verdadeiro-positivo (a 4ª, "a exemplo do que acontece hoje com a
#    produção de melão no município de", perde o nome próprio por corte de
#    frase antes dele -- mesmo fenômeno já documentado de frase cortada) e
#    ainda assim corrige as 7+22 falso-positivo. Fica um risco residual
#    documentado: um nome próprio citado sem ser precedente real (ex.: "a
#    exemplo da Guararapes" citando uma empresa-alvo, não uma evidência)
#    ainda passa -- não resolvido, mesmo padrão de limitação do Pilar B.
# 2. "baseado/baseada em X" e "com base em X" sem nomear nenhuma instituição,
#    lei ou número são jargão (S0180, S0129, S0021, S0026 -- todos
#    falso-positivo confirmados). Agora só contam se a MESMA frase também
#    tiver uma instituição nomeada (`INSTITUICAO_RE`), um número
#    (`NUM_ANY`) ou uma citação formal (`CITACAO_RE`) -- preserva o único
#    caso verdadeiro-positivo que usa essa forma (S0077, "com base na Lei
#    nº 10.097", que já teria batido via "lei nº" de qualquer forma).
# Não mexido (fora do escopo desta rodada, limitação conhecida e
# documentada): nome de instituição usado como sujeito de uma reivindicação
# política em vez de citação de fonte (ex. S0023 "disputa por um BNDES
# popular") -- precisaria de análise sintática, não só léxica, para
# distinguir, e fica como item em aberto.
#
# Validado contra as 204 frases do kappa: kappa de Cohen do Pilar C
# (motor x LLM cego) sobe de 0,681 (substancial) para 0,794 (quase
# perfeito). Dos 10 exemplos documentados do Padrão #5, 9/10 corrigidos (o
# 10º é exatamente o caso S0023 acima, deixado em aberto de propósito). Dos
# 40 casos de Pilar C já confirmados como verdadeiro-positivo, 36/40 (90%)
# continuam verdadeiros -- os 4 perdidos são custos reais e esperados do
# trade-off: 1 por frase cortada (mesmo fenômeno de truncamento de PDF já
# documentado), 2 por citarem uma fonte fora da lista fixa de instituições
# reconhecidas (lacuna pré-existente, já apontada no relatório de 25/09 como
# "lista de instituições incompleta", não introduzida por esta correção), e
# 1 ("experiência bem sucedida" sem instituição nem número) pelo próprio
# design do filtro de jargão.
INSTITUICAO_RE = re.compile(
    r"\b(estudo(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|mapbiomas|universidade|instituto)|"
    r"pesquisa(?:s)? (?:do|da|de) (?:ibge|ipea|inpe|mapbiomas|universidade|instituto)|"
    r"ibge|ipea|datasus|sinisa|mapbiomas|inpe|zee-ma|zee/ma|"
    r"organização mundial da saúde|\boms\b|banco mundial|\bbndes\b|\bbnb\b|"
    r"plano nacional de logística|marco legal do saneamento|"
    r"lei nº|lei n°)\b",
    re.IGNORECASE,
)
JARGAO_EVIDENCIA_RE = re.compile(
    r"\b(conforme (?:dados|estudos?|pesquisas?|levantamento|indicadores?)|"
    r"segundo (?:estudos?|dados|pesquisa)|modelo (?:já )?adotado|"
    r"experiência bem[- ]sucedida|"
    r"(?:baseado|baseada) (?:n[ao]|em) (?:dados|estudos?|evidências?|indicadores?|"
    r"modelo(?:s)?|pesquisas?|diagnóstico|informações|levantamento|resultados?)|"
    r"com base em (?:dados|estudos?|evidências?|indicadores?|modelo(?:s)?|pesquisas?|"
    r"diagnóstico|informações|levantamento|resultados?))\b",
    re.IGNORECASE,
)
EXEMPLO_RE = re.compile(r"\ba exemplo (?:d[eo]|da)\b", re.IGNORECASE)
EXEMPLO_NOME_PROPRIO_RE = re.compile(r"^(?:\s*\S+){0,9}?\s*\b([A-ZÀ-Ý][a-zà-ÿ]{2,})")

CITACAO_RE = re.compile(
    r"(?:estudo|pesquisa|levantamento|relatório)\s+[A-ZÀ-Ý][\wÀ-ÿ\s]{3,70}?"
    r"\(\s*[A-ZÀ-Ý]{2,15}(?:[\s,][A-ZÀ-Ý][\wÀ-ÿ]*)*,?\s*\d{4}\s*\)",
)


def _exemplo_cita_precedente(s_orig: str) -> bool:
    m = EXEMPLO_RE.search(s_orig)
    if not m:
        return False
    return bool(EXEMPLO_NOME_PROPRIO_RE.match(s_orig[m.end():]))


def is_evidencia(s_orig: str, s_low: str) -> bool:
    if INSTITUICAO_RE.search(s_low):
        return True
    if _exemplo_cita_precedente(s_orig):
        return True
    if JARGAO_EVIDENCIA_RE.search(s_low) and (
        INSTITUICAO_RE.search(s_low) or has_real_number(s_orig) or CITACAO_RE.search(s_orig)
    ):
        return True
    if CITACAO_RE.search(s_orig):
        return True
    return False


SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"'“”’)\]]?\s+|;\s+|\n+|(?=^-\s)|(?<=^-)\s+", re.MULTILINE)
BULLET_RE = re.compile(r"^[\-••]\s*")
NUMBERED_HEADER_RE = re.compile(r"^\d{1,2}\s?[—\-–]\s*")
MIN_SENTENCE_WORDS = 5

DATE_LINE_RE = re.compile(r"^\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}$", re.IGNORECASE)


def split_sentences(text: str, bullet_re=None):
    """`bullet_re`: override pontual (ver Bahia, docstring do módulo) — usa
    BULLET_RE canônico quando None."""
    br = bullet_re if bullet_re is not None else BULLET_RE
    parts = SENT_SPLIT_RE.split(text)
    cleaned = []
    for p in parts:
        p = p.strip().strip('"').strip("'").strip()
        p = br.sub("", p)
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


def base_empirica_analise(text: str, bullet_re=None, ano_ciclo=None):
    """`bullet_re`: ver `split_sentences` — override pontual da Bahia.
    `ano_ciclo`: ver docstring de `is_efeito`."""
    sentences = split_sentences(text, bullet_re=bullet_re)
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
        pb = is_efeito(s, s_low, ano_ciclo=ano_ciclo)
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
# Nuvem de palavras
# ---------------------------------------------------------------------------
def gerar_wordcloud_png_b64(counts: Counter, slug: str, wc_dir, all_stopwords, max_words=120) -> str:
    """Variante canônica (usada pela maioria dos estados, entre eles São
    Paulo): filtra stopwords antes de gerar a nuvem, prefer_horizontal=0.9.

    `max_words`: override pontual (ver Bahia, docstring do módulo) — usa 120
    (valor canônico) quando não passado."""
    freqs = {w: f for w, f in counts.items() if w not in all_stopwords and len(w) > 2}
    wc = WordCloud(width=800, height=500, background_color=None, mode="RGBA",
                   colormap="viridis", prefer_horizontal=0.9, max_words=max_words)
    wc.generate_from_frequencies(freqs)
    png_path = wc_dir / f"{slug}.png"
    wc.to_file(str(png_path))
    buf = BytesIO()
    wc.to_image().save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def gerar_wordcloud_png_b64_legacy_pi(counts: Counter, slug: str, wc_dir) -> str:
    """Variante antiga (Piauí e possivelmente outros estados iniciais do
    Nordeste): NÃO filtra stopwords antes de gerar a nuvem, prefer_horizontal
    =0.92. Preservada tal qual para não alterar um PNG já publicado; ver
    docstring do módulo."""
    wc = WordCloud(
        width=800, height=500, background_color=None, mode="RGBA",
        colormap="viridis", prefer_horizontal=0.92, max_words=120,
    ).generate_from_frequencies(counts)
    png_path = wc_dir / f"{slug}.png"
    wc.to_file(str(png_path))
    buf = BytesIO()
    wc.to_image().save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
