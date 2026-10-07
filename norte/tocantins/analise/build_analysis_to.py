#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Tocantins 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver, por
exemplo, /home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py):
distribuição temática exaustiva por segmentação de marcadores de seção reais
(lidos e mapeados à mão) e Índice de Base Empírica (heurística
lexical/regex idêntica à usada em todos os outros estados, reaproveitada
sem alterações para manter comparabilidade entre estados e entre regiões
— Nordeste e Norte).

Caso do Tocantins: os dois candidatos mais competitivos da corrida NÃO
incluem o governador em exercício, Wanderlei Barbosa (PSD) — que sucedeu
Mauro Carlesse (renúncia, 2022) e depois se elegeu por conta própria em
2022, com uma discussão jurídica em aberto sobre o limite de reeleições
consecutivas (art. 14, §5º, da Constituição) que não é resolvida aqui.
Em vez disso, a disputa é entre:
  - Professora Dorinha (União): deputada federal, publicamente apoiada e
    com engajamento ativo na campanha pelo próprio governador Wanderlei
    Barbosa, que declarou voto nela e defendeu a "continuidade dos
    avanços" do seu governo — perfil de candidata de continuidade por
    apoio explícito do incumbente, embora ela própria nunca tenha
    ocupado o Executivo estadual.
  - Vicentinho Júnior (PSDB): ex-prefeito de Araguaína, concorre como
    desafiante, sem o apoio do governador Wanderlei Barbosa (que apoia a
    concorrente); parte da cobertura jornalística registra apoio pontual
    de ao menos um prefeito filiado ao partido do governador
    (Republicanos) a Vicentinho, mas não do próprio governador.
Fontes desta leitura eleitoral (agosto de 2026): reportagens de O
Girassol, Gazeta do Cerrado, Conexão Tocantins e Folha do Bico sobre a
campanha; ver detalhamento no campo "categoria" de cada candidato e na
metodologia_nota, ao final deste arquivo. Essa é uma leitura eleitoral,
não textual: não influenciou nenhuma etapa da extração ou classificação
dos planos.

Ressalva sobre o partido de Professora Dorinha: parte da cobertura
jornalística de pré-campanha (ex.: matéria "Republicanos oficializa
Professora Dorinha ao Governo do Tocantins...") associou a candidata ao
partido Republicanos. O registro OFICIAL da proposta de governo dela no
TSE (fonte primária e autoritativa usada neste projeto,
cdn.tse.jus.br/proposta_governo_2026_TO.zip), porém, lista o partido como
UNIÃO (União Brasil). Este script usa o dado oficial do TSE. Não
investigamos a fundo a causa da discrepância (possível troca de partido
de última hora antes do registro de candidatura, ou imprecisão de
cobertura jornalística anterior à oficialização) — reportamos apenas o
fato para transparência metodológica.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/norte/tocantins/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/norte/tocantins/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "professora-dorinha", "nome": "Professora Dorinha", "partido": "União",
     "categoria": "candidata de continuidade — publicamente apoiada e com engajamento "
                  "ativo na campanha pelo governador em exercício Wanderlei Barbosa "
                  "(PSD), que declarou voto nela e defendeu a “continuidade dos "
                  "avanços” do seu governo, embora ela própria nunca tenha ocupado "
                  "o Executivo estadual (é deputada federal) — fonte: cobertura "
                  "jornalística de agosto de 2026 (O Girassol, Gazeta do Cerrado, "
                  "Conexão Tocantins)"},
    {"slug": "vicentinho-junior", "nome": "Vicentinho Júnior", "partido": "PSDB",
     "categoria": "desafiante — ex-prefeito de Araguaína, concorre sem o apoio do "
                  "governador em exercício Wanderlei Barbosa (que apoia publicamente "
                  "a candidata concorrente); parte da cobertura jornalística registra "
                  "apoio isolado de ao menos um prefeito filiado ao partido do "
                  "governador (Republicanos), mas não do próprio governador — fonte: "
                  "cobertura jornalística de agosto de 2026 (Folha do Bico)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os demais estados do
# projeto (Nordeste e Norte), não adaptadas ao Tocantins, para preservar
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

# Professora Dorinha (União): documento extremamente bem estruturado — um
# capítulo diagnóstico inicial (TOCANTINS EM NÚMEROS: demografia, povos e
# culturas, economia, síntese dos indicadores), uma seção de valores e
# metodologia da campanha, e depois 10 "Eixos Estruturantes" numerados, cada
# um com Contexto + Diretrizes + Propostas organizadas em subseções com
# títulos temáticos claros.
#
# Front matter (capítulo diagnóstico + valores + metodologia do plano):
# como no Ceará/Maranhão, texto puramente de diagnóstico/abertura ou de
# metodologia da própria campanha (não uma proposta de política pública) cai
# em "outros", EXCETO quando a subseção diagnóstica tem um tema único e
# claro — o mesmo critério usado no Ceará para "CONTEXTOS E AVANÇOS" de
# Elmano de Freitas. Por esse critério: "DEMOGRAFIA E TERRITÓRIO" e "POVOS E
# CULTURAS" ficam em "outros" (são diagnóstico geral de perfil populacional e
# identidade cultural, sem se resumir a um único dos 9 temas — "POVOS E
# CULTURAS", em particular, mistura direitos de povos indígenas/quilombolas
# com identidade cultural, sem ser possível separar com segurança dentro de
# um único parágrafo corrido). Já "ECONOMIA" (diagnóstico de PIB, mercado de
# trabalho, estrutura produtiva) tem tema único e claro, e foi classificada
# como "economia". "O QUE O CONJUNTO DOS INDICADORES REVELA" é uma síntese
# que passa por vários temas ao mesmo tempo (saneamento, educação, meio
# ambiente, economia) em poucas linhas cada, genuinamente indivisível =
# "outros". "VALORES ESTRATÉGICOS" lista princípios de gestão (eficiência,
# eficácia, efetividade, transparência, inovação) — classificado como
# "gestao_publica" por serem princípios de administração pública, não
# diagnóstico geral. "METODOLOGIA DO PLANO" e a introdução/tabela de "EIXOS
# ESTRUTURANTES" descrevem o processo de construção do documento de
# campanha (não uma política de governo em si) = "outros".
#
# Dentro do Eixo 1 (Educação e Capital Humano), as subseções finais
# "Juventude" e "Esporte e Lazer" foram classificadas como
# "assistencia_social", replicando o precedente usado em outros estados do
# projeto (esporte, juventude e políticas de proteção social = assistência
# social, mesmo quando organizadas dentro de um eixo nominalmente de
# educação — o próprio texto de abertura do eixo já sinaliza isso: "Além da
# educação, os temas de juventude e de esportes também integram, de forma
# transversal, esse eixo").
#
# O Eixo 3 (Segurança Pública, Desenvolvimento Social e Direitos Humanos) é
# explicitamente tri-temático desde o parágrafo de abertura ("trata de
# segurança pública e penal, desenvolvimento social e direitos humanos como
# uma política transversal, e não como três agendas paralelas") e foi
# segmentado subseção a subseção: "Governança e institucionalidade dos
# direitos humanos" = assistencia_social (não há eixo temático dedicado a
# direitos humanos na taxonomia de 9 temas do projeto; segue o mesmo
# critério usado para outras pautas de direitos/proteção de grupos
# vulneráveis no projeto); "Valorização e capacidade das forças de segurança
# pública", "Acesso à justiça, segurança cidadã e política penal" e
# "Prevenção da violência e cultura de paz" = seguranca; as demais
# subseções (assistência social/segurança alimentar, direitos das mulheres,
# igualdade racial/quilombolas, povos indígenas, crianças/adolescentes/
# juventudes, pessoa idosa/PcD/populações em vulnerabilidade) =
# assistencia_social.
#
# O Eixo 5 (Desenvolvimento Econômico e Sustentável) é predominantemente
# "economia" (indústria, agronegócio, mineração, ciência/tecnologia/inovação
# tratada aqui como parte do ecossistema econômico-empresarial — FAPT,
# Parque Tecnológico, cadeias industriais — e não como formação educacional,
# ao contrário do precedente usado no Ceará, onde C&T estava emparelhada
# com o eixo de educação; aqui a própria candidata emparelha C&T com
# desenvolvimento econômico, então seguimos a divisão que ela mesma propõe
# no documento). A cadeia de subseções de logística de transporte ("Plano
# Tocantins Multimodal", rodovias, Ferrovia Norte-Sul, hidrovia, polos
# logísticos/portos secos, aviação regional, segurança e inteligência
# logística, investimento/governança de longo prazo, observatório da
# logística) foi destacada como "infraestrutura", por ser literalmente sobre
# obras e operação de infraestrutura de transporte, e não sobre política
# industrial em si — mesmo tratamento dado a conteúdo de mobilidade em
# outras seções do próprio documento (Eixo 4). O bloco final de mineração
# ("Governança e Ambiente Institucional" em diante) volta a "economia"
# (política mineral, ambiente de negócios, cadeia produtiva mineral).
#
# O Eixo 6 (Desenvolvimento Regional e Redução das Desigualdades) foi
# mantido como bloco único em "gestao_publica": a lógica unificadora do eixo
# inteiro é de planejamento territorial e governança regional (índice de
# priorização orçamentária, painel de convergência regional, fortalecimento
# técnico das prefeituras, sistema de acompanhamento da execução
# orçamentária), mesmo quando propostas específicas tocam setores como
# saneamento, rodovias ou turismo — decisão editorial para preservar a
# coerência da narrativa de governança regional do eixo, análoga à forma
# como o Ceará tratou "GESTÃO ESTRATÉGICA, GOVERNANÇA INTERFEDERA-" como um
# bloco único de gestao_publica mesmo cobrindo múltiplos setores.
#
# O Eixo 7 (Agropecuária e Desenvolvimento Rural) é "economia", exceto a
# subseção "Logística, infraestrutura rural e segurança hídrica" — sobre
# rodovias, ferrovia, portos fluviais, armazenagem e irrigação — destacada
# como "infraestrutura" pelo mesmo critério usado no Eixo 5.
#
# O Eixo 8 (Meio Ambiente, Sustentabilidade e Causa Animal) é
# "meio_ambiente", exceto a subseção final "Bem-Estar e Proteção Animal",
# classificada como "assistencia_social" — replicando o precedente já usado
# no Ceará (proteção e bem-estar animal = assistência social).
#
# O Eixo 9 (Cultura, Turismo e Desenvolvimento Criativo) foi mantido como
# bloco único em "assistencia_social", replicando o precedente do projeto
# para cultura (o documento da própria candidata já integra cultura e
# turismo como uma única política de "economia criativa", sem separá-los).
MARCADORES_DORINHA = [
    ("TOCANTINS EM NÚMEROS: COMPREENDER O CONTEXTO PARA", "outros"),
    ("DEMOGRAFIA E TERRITÓRIO", "outros"),
    ("POVOS E CULTURAS", "outros"),
    ("ECONOMIA", "economia"),
    ("O QUE O CONJUNTO DOS INDICADORES REVELA", "outros"),
    ("VALORES ESTRATÉGICOS", "gestao_publica"),
    ("METODOLOGIA DO PLANO", "outros"),
    ("EIXOS ESTRUTURANTES: O TOCANTINS QUE QUEREMOS COMEÇA", "outros"),
    ("EIXO 1 – EDUCAÇÃO E CAPITAL HUMANO", "educacao"),
    ("Juventude", "assistencia_social"),
    ("Esporte e Lazer", "assistencia_social"),
    ("EIXO 2 – SAÚDE E QUALIDADE DE VIDA", "saude"),
    ("EIXO 3 – SEGURANÇA PÚBLICA, DESENVOLVIMENTO SOCIAL E", "outros"),
    ("Governança e institucionalidade dos direitos humanos", "assistencia_social"),
    ("Valorização e capacidade das forças de segurança pública", "seguranca"),
    ("Acesso à justiça, segurança cidadã e política penal", "seguranca"),
    ("Prevenção da violência e cultura de paz", "seguranca"),
    ("Assistência social, segurança alimentar e inclusão produtiva", "assistencia_social"),
    ("Direitos das mulheres: proteção e autonomia", "assistencia_social"),
    ("Igualdade racial e comunidades quilombolas", "assistencia_social"),
    ("Povos indígenas e comunidades tradicionais", "assistencia_social"),
    ("Crianças, adolescentes e juventudes", "assistencia_social"),
    ("Pessoa idosa, pessoa com deficiência e populações em situação de", "assistencia_social"),
    ("EIXO 4 – INFRAESTRUTURA, HABITAÇÃO E CONECTIVIDADE", "infraestrutura"),
    ("EIXO 5 – DESENVOLVIMENTO ECONÔMICO E SUSTENTÁVEL", "economia"),
    ("Plano Tocantins Multimodal", "infraestrutura"),
    ("Governança e Ambiente Institucional", "economia"),
    ("EIXO 6 – DESENVOLVIMENTO REGIONAL E REDUÇÃO DAS", "gestao_publica"),
    ("EIXO 7 – AGROPECUÁRIA E DESENVOLVIMENTO RURAL", "economia"),
    ("Logística, infraestrutura rural e segurança hídrica", "infraestrutura"),
    ("Agricultura familiar, cooperativismo e inclusão produtiva", "economia"),
    ("EIXO 8 – MEIO AMBIENTE, SUSTENTABILIDADE E CAUSA ANIMAL", "meio_ambiente"),
    ("Bem-Estar e Proteção Animal", "assistencia_social"),
    ("EIXO 9 – CULTURA, TURISMO E DESENVOLVIMENTO CRIATIVO", "assistencia_social"),
    ("EIXO 10 – GOVERNANÇA, TRANSPARÊNCIA E TRANSFORMAÇÃO", "gestao_publica"),
]

# Vicentinho Júnior (PSDB): documento em formato de catálogo — uma carta de
# abertura ("UMA CONVERSA COM OS TOCANTINENSES") e um SUMÁRIO paginado,
# seguidos por 28 "Eixos" numerados (o eixo 23 não consta do sumário, mas
# existe no corpo do texto), cada um com dezenas de propostas numeradas no
# formato "NNN. Título / Ação: .../ Resultado Esperado: ...". O SUMÁRIO
# repete os títulos dos eixos antes do corpo real — mesmo padrão de "índice
# que antecede o corpo" já visto em outros estados do projeto — corrigido
# com a mesma lógica: o primeiro marcador ("EIXO 1: ACESSIBILIDADE E
# INCLUSÃO") usa sua 2ª ocorrência no texto (a do corpo, não a do sumário)
# como ponto de partida da segmentação.
#
# A maioria dos 28 eixos é monotemática (o próprio "Foco:" declarado no
# início de cada eixo já indica um tema único e coerente com o conteúdo das
# propostas), e foi mantida como bloco único. Cinco eixos são explicitamente
# multitemáticos (o "Foco:" já nomeia mais de um domínio) e foram segmentados
# item a item, usando o número e o título verbatim de cada proposta como
# marcador:
#   - Eixo 5 (Desenvolvimento Regional Integrado — Foco: "Logística de
#     Fronteira, Bioeconomia e Saúde"): 10 propostas cobrindo economia
#     (ZDE, Projeto Sampaio, Cadeia do Babaçu, Polo Logístico, Rota
#     Turística), saúde (Complexo Hospitalar de Augustinópolis), educação
#     (Universidade do Bico), segurança (Batalhão de Divisas) e
#     infraestrutura (Regularização Fundiária Rural, Conectividade Total
#     nas Escolas) — segmentado proposta a proposta.
#   - Eixo 9 (Povos Indígenas — Foco: "Reconhecimento, proteção e
#     desenvolvimento"): 11 propostas segmentadas item a item, pois cruzam
#     saúde (107), educação (102), infraestrutura/saneamento (109),
#     economia/bioeconomia (108) e temas de governança/proteção de direitos
#     sem tema dedicado na taxonomia de 9 eixos, classificados como
#     "assistencia_social" (101, 103, 105, 106 [conectividade em aldeias,
#     tratada aqui como parte da política de proteção/inclusão territorial
#     indígena, não como infraestrutura genérica], 110) ou "gestao_publica"
#     (111, fortalecimento institucional/jurídico de associações) ou
#     "meio_ambiente" (104, pagamento por serviços ambientais).
#   - Eixo 12 (Oportunidades de Desenvolvimento Econômico e Social — Foco:
#     "Logística e oportunidade"): mantido majoritariamente "economia"
#     (mineração, piscicultura, turismo, fintechs), com duas propostas de
#     infraestrutura física destacadas (135 PPPs de Saneamento; 140
#     Logística Multimodal/porto seco).
#   - Eixo 22 (Tecnologia — Estado Digital) e Eixo 23 (Tecnologia Aplicada):
#     ambos reúnem soluções tecnológicas para problemas de natureza muito
#     diferente (saúde, educação, segurança, meio ambiente, gestão fiscal,
#     infraestrutura, economia) sob o guarda-chuva comum de "tecnologia" —
#     tema sem eixo dedicado na taxonomia de 9 temas do projeto — e por isso
#     foram integralmente segmentados item a item, cada proposta classificada
#     pelo problema que resolve, não pelo meio tecnológico usado.
#
# Demais eixos mantidos como bloco único, pelo tema declarado no "Foco:" e
# confirmado pelo conteúdo das propostas: Acessibilidade e Inclusão (PcD) =
# assistencia_social; Agenda Municipalista (institucional/apoio técnico a
# municípios) = gestao_publica; Agronegócio 5.0 = economia; Cultura, Esporte
# e Bem-Estar (economia criativa) = assistencia_social (precedente do
# projeto para cultura/esporte); Economia Verde e Descarbonização =
# meio_ambiente (mesmo as propostas com efeito econômico colateral — PSA,
# crédito de carbono, bioindústria, energia solar social — estão
# emolduradas pelo eixo como instrumentos de política ambiental, não como
# agenda industrial); Educação = educacao; Fazenda Pública (SEFAZ, tributos)
# = gestao_publica; Indústria = economia; Mineração = economia; Parcerias e
# Terceiro Setor (Foco: "Desoneração da Administração Pública") =
# gestao_publica; Pleno Emprego e Trabalho = economia (agenda explícita de
# emprego/renda, ao contrário do precedente do Ceará em que "Trabalho e Ação
# Social" nomeava apenas a pasta de assistência social — aqui o conteúdo é
# genuinamente sobre mercado de trabalho); Prestação de Serviços Estatais
# (Foco: "Logística e Digitalização", fomento a serviços privados) =
# economia; Proteção e Promoção da Mulher, Proteção e Promoção da Pessoa
# Idosa, Diversidade (LGBTQIA+) = assistencia_social; Saúde Pública = saude;
# Segurança Jurídica (ambiente regulatório/contratual) = gestao_publica;
# Segurança Pública = seguranca; Servidores Públicos = gestao_publica;
# Esporte e Lazer = assistencia_social; Defesa e Bem-Estar Animal =
# assistencia_social (precedente do projeto); Desenvolvimento das Rodovias
# Estaduais = infraestrutura.
MARCADORES_VICENTINHO = [
    ("EIXO 1: ACESSIBILIDADE E INCLUSÃO", "assistencia_social"),
    ("EIXO 2: AGENDA MUNICIPALISTA", "gestao_publica"),
    ("EIXO 3: AGRONEGÓCIO 5.0", "economia"),
    ("EIXO 4: CULTURA, ESPORTE E BEM-ESTAR", "assistencia_social"),
    ("EIXO 5: DESENVOLVIMENTO REGIONAL INTEGRADO", "outros"),
    ("041. Zona de Desenvolvimento Especial (ZDE)", "economia"),
    ("042. Revitalização do Projeto Sampaio", "economia"),
    ("043. Complexo Hospitalar de Augustinópolis", "saude"),
    ("044. Cadeia Industrial do Babaçu", "economia"),
    ("045. Polo Logístico da Ponte de Xambioá", "infraestrutura"),
    ("046. Universidade do Bico", "educacao"),
    ("047. Rota Turística Encontro das Águas", "economia"),
    ("048. Batalhão de Divisas", "seguranca"),
    ("049. Regularização Fundiária Rural", "infraestrutura"),
    ("050. Conectividade Total nas Escolas", "infraestrutura"),
    ("EIXO 6: ECONOMIA VERDE E DESCARBONIZAÇÃO", "meio_ambiente"),
    ("EIXO 7: EDUCAÇÃO", "educacao"),
    ("EIXO 8: FAZENDA PÚBLICA", "gestao_publica"),
    ("EIXO 9: POVOS INDÍGENAS", "outros"),
    ("101. Observatório Estadual de Dados Socio-territoriais Indígenas", "assistencia_social"),
    ("102. Educação Escolar Indígena, Bilíngue e Intercultural", "educacao"),
    ("103. Governança, Direitos Territoriais e Consulta Prévia", "assistencia_social"),
    ("104. Sustentabilidade e Pagamento por Serviços Ambientais (PSA)", "meio_ambiente"),
    ("105. Proteção a Lideranças e Defensores dos Direitos Humanos", "assistencia_social"),
    ("106. Conectividade e Inclusão Digital nas Aldeias", "assistencia_social"),
    ("107. Saúde Indígena Integral e Cuidados Tradicionais", "saude"),
    ("108. Inclusão Produtiva e Bioeconomia Indígena", "economia"),
    ("109. Saneamento Básico e Segurança Hídrica nas Aldeias", "infraestrutura"),
    ("110. Soberania Alimentar e Fortalecimento da Agricultura Tradicional", "assistencia_social"),
    ("111. Fomento Institucional e Adequação Jurídica de Organizações Indígenas", "gestao_publica"),
    ("EIXO 10: INDÚSTRIA", "economia"),
    ("EIXO 11: MINERAÇÃO", "economia"),
    ("EIXO 12: OPORTUNIDADES DE DESENVOLVIMENTO ECONÔMICO E SOCIAL DO", "economia"),
    ("135. PPPs de Saneamento", "infraestrutura"),
    ("136. Piscicultura em Grandes Lagos", "economia"),
    ("140. Logística Multimodal", "infraestrutura"),
    ("141. Fruticultura Irrigada", "economia"),
    ("EIXO 13: PARCERIAS E TERCEIRO SETOR (Pacto de Cooperação)", "gestao_publica"),
    ("EIXO 14: PLENO EMPREGO", "economia"),
    ("EIXO 15: PRESTAÇÃO DE SERVIÇOS ESTATAIS", "economia"),
    ("EIXO 16: PROTEÇÃO E PROMOÇÃO DA MULHER", "assistencia_social"),
    ("EIXO 17: PROTEÇÃO E PROMOÇÃO DA PESSOA IDOSA", "assistencia_social"),
    ("EIXO 18: SAÚDE PÚBLICA", "saude"),
    ("EIXO 19: SEGURANÇA JURÍDICA", "gestao_publica"),
    ("EIXO 20: SEGURANÇA PÚBLICA", "seguranca"),
    ("EIXO 21: SERVIDORES PÚBLICOS", "gestao_publica"),
    ("EIXO 22: TECNOLOGIA - ESTADO DIGITAL", "outros"),
    ("221. Parque Tecnológico AgroTech", "economia"),
    ("222. Governo Sem Papel", "gestao_publica"),
    ("223. Conectividade Rural (5G)", "infraestrutura"),
    ("224. Identidade Digital Única", "gestao_publica"),
    ("225. Videomonitoramento com IA", "seguranca"),
    ("226. Telemedicina Rural", "saude"),
    ("227. Educação Criadora (Maker)", "educacao"),
    ("228. Big Data Fiscal", "gestao_publica"),
    ("229. Sandbox Regulatório", "economia"),
    ("230. Cibersegurança (SOC)", "gestao_publica"),
    ("EIXO 23: TECNOLOGIA APLICADA", "outros"),
    ("231. Agricultura 5.0", "economia"),
    ("232. Realização de hackathon na área de tecnologia em prol da Administração Pública com", "gestao_publica"),
    ("233. Blockchain Fundiário", "infraestrutura"),
    ("234. Águas Inteligentes", "meio_ambiente"),
    ("235. Infraestrutura Digital", "infraestrutura"),
    ("236. Bioacústica Ambiental", "meio_ambiente"),
    ("237. Turismo Imersivo (VR)", "economia"),
    ("238. EdTechGamificada", "educacao"),
    ("239. Telemonitoramento de Pacientes Crônicos", "saude"),
    ("240. Centralização de Dados (IA)", "gestao_publica"),
    ("EIXO 24: TRABALHO", "economia"),
    ("EIXO 25: ESPORTE E LAZER", "assistencia_social"),
    ("EIXO 26: DIVERSIDADE", "assistencia_social"),
    ("EIXO 27: DEFESA E BEM-ESTAR ANIMAL", "assistencia_social"),
    ("EIXO 28: DESENVOLVIMENTO DAS RODOVIAS ESTADUAIS", "infraestrutura"),
]

MARCADORES = {
    "professora-dorinha": MARCADORES_DORINHA,
    "vicentinho-junior": MARCADORES_VICENTINHO,
}

# Ponto de partida da análise de Base Empírica (Tarefa 2) para cada
# candidato: nenhum dos dois planos do Tocantins tem uma capa/sumário longo
# o bastante para distorcer a extração de frases (o sumário paginado de
# Vicentinho Júnior é uma lista curta de títulos, não texto corrido em
# frases completas), então a análise roda sobre o corpo inteiro do
# documento (posição 0), sem pular nenhum trecho inicial.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "professora-dorinha": 0,
    "vicentinho-junior": 0,
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
        "gerado_em": "23 de agosto de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados — por isso "
            "'Tocantins' e 'tocantinense(s)' NÃO são filtrados e aparecem "
            "naturalmente entre os termos mais frequentes de ambos os "
            "planos). Mostra os termos mais repetidos por candidato e o "
            "agregado dos dois planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/subseção, ou, "
            "quando um eixo reunia explicitamente mais de um domínio "
            "temático, o início verbatim de cada proposta numerada dentro "
            "dele). Cada segmento de texto entre dois marcadores "
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
            "Heurística idêntica à usada nas análises dos 9 estados do "
            "Nordeste, sem nenhum ajuste específico para o Tocantins, para "
            "manter comparabilidade entre estados e entre regiões."
        ),
        "metodologia_nota": (
            "O Tocantins é o primeiro estado da Região Norte incluído no "
            "projeto, com a mesma metodologia usada nos 9 estados do "
            "Nordeste. Os dois candidatos mais competitivos da corrida NÃO "
            "incluem o governador em exercício, Wanderlei Barbosa (PSD), que "
            "sucedeu Mauro Carlesse (renúncia, em 2022) e depois se elegeu "
            "por conta própria naquele mesmo ano — há uma discussão jurídica "
            "em aberto sobre o limite de reeleições consecutivas (art. 14, "
            "§5º, da Constituição) que este projeto não resolve nem precisa "
            "resolver, já que Wanderlei Barbosa não está entre os dois "
            "candidatos analisados aqui. Em vez disso, a disputa mais "
            "competitiva é entre Professora Dorinha (União), publicamente "
            "apoiada e com campanha ativa do próprio governador Wanderlei "
            "Barbosa — perfil de candidata de continuidade por apoio "
            "explícito do incumbente, mesmo nunca tendo ocupado o Executivo "
            "estadual — e Vicentinho Júnior (PSDB), ex-prefeito de "
            "Araguaína, que concorre como desafiante sem o apoio do "
            "governador. Essa é uma leitura eleitoral, baseada em cobertura "
            "jornalística de agosto de 2026 (ver fontes no campo "
            "'categoria' de cada candidato), e não influenciou nenhuma "
            "etapa da extração ou classificação textual dos planos. "
            "Ressalva sobre o partido de Professora Dorinha: parte da "
            "cobertura jornalística de pré-campanha associou a candidata ao "
            "partido Republicanos; o registro oficial da proposta de "
            "governo dela no TSE (fonte primária usada neste projeto) lista "
            "o partido como UNIÃO, e é esse o dado usado aqui — não "
            "investigamos a fundo a causa da discrepância (possível troca "
            "de partido de última hora antes do registro de candidatura, ou "
            "imprecisão de cobertura jornalística anterior à "
            "oficialização). "
            "Estruturalmente, os dois planos do Tocantins são bem "
            "diferentes entre si: o de Professora Dorinha é um documento "
            "tradicional em prosa, organizado em 10 'Eixos Estruturantes' "
            "com Contexto + Diretrizes + Propostas; o de Vicentinho Júnior é "
            "um catálogo de mais de 260 propostas numeradas em formato "
            "'Ação / Resultado Esperado', organizado em 28 'Eixos' "
            "temáticos, com um SUMÁRIO paginado no início que repete os "
            "títulos dos eixos antes do corpo real — mesmo padrão de índice "
            "duplicado já visto em outros estados do projeto, corrigido com "
            "a mesma lógica (2ª ocorrência do primeiro marcador usada como "
            "ponto de partida da segmentação). Note-se que o eixo 23 "
            "('TECNOLOGIA APLICADA') existe no corpo do texto de Vicentinho "
            "Júnior mas não consta do SUMÁRIO do documento original — "
            "inconsistência do próprio documento-fonte, não da extração. O "
            "formato extremamente granular do plano de Vicentinho Júnior "
            "(propostas de 1 a 3 frases cada, sem parágrafos corridos) "
            "produz naturalmente menos frases longas com múltiplos "
            "qualificadores retóricos do que um texto em prosa, o que pode "
            "influenciar a comparabilidade direta do Índice de Base "
            "Empírica entre os dois candidatos — resultado do formato "
            "escolhido por cada campanha para apresentar seu plano, não um "
            "artefato da extração. "
            "Ressalva adicional sobre o Índice de Base Empírica: assim como "
            "já registrado no Ceará, os dois .txt do Tocantins preservam a "
            "quebra de linha visual do PDF original linha a linha, com "
            "espaçamento irregular de justificação de texto (ex.: "
            "'Tocantins     precisa   transformar   sua   capacidade "
            "  produtiva   em'), em vez de texto corrido por parágrafo. "
            "Como a função de divisão de frases ('split_sentences', "
            "idêntica à dos demais estados do projeto) trata quebras de "
            "linha como fim de frase, isso produz mais fragmentos de frase "
            "cortados no meio (ex.: uma citação de exemplo do Pilar C que "
            "termina em vírgula, no meio de uma referência legal) do que em "
            "planos cujo texto foi extraído já como parágrafos corridos, e "
            "contribui para os Índices de Base Empírica relativamente "
            "baixos observados nos dois candidatos do Tocantins (4,3% e "
            "3,6%) em comparação a estados cujo texto-fonte não tem esse "
            "problema de extração. Não alteramos a função para não "
            "introduzir uma diferença de metodologia específica do "
            "Tocantins; o efeito atinge a contagem de sentenças avaliadas "
            "para o índice, mas não a contagem de palavras nem a "
            "distribuição temática (que operam por posição de caractere, "
            "não por frase). "
            "Cinco eixos do plano de Vicentinho "
            "Júnior (5, 9, 12, 22 e 23) e algumas subseções do plano de "
            "Professora Dorinha (dentro dos Eixos 1, 3, 5, 7 e 8) reúnem "
            "mais de um tema da taxonomia de 9 eixos do projeto sob um único "
            "título e foram segmentados em nível de proposta/subseção "
            "individual para preservar a exaustividade da classificação; "
            "todas as decisões não óbvias de classificação (ex.: proteção "
            "animal e cultura/esporte = assistência social; segurança "
            "hídrica, viária e logística = infraestrutura; ciência e "
            "tecnologia agrupada com economia, e não com educação, no plano "
            "de Dorinha) estão documentadas linha a linha nos comentários "
            "do script de análise."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
