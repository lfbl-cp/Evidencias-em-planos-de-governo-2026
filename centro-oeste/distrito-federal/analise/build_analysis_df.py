#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Distrito Federal 2026.

Réplica EXATA da metodologia usada nos 9 estados do Nordeste (ver, por
exemplo, /home/claude/brasil_2026/nordeste/ceara/analise/build_analysis_ce.py),
nos estados já processados do Norte (Tocantins, Rondônia etc.) e no Centro-
Oeste (Mato Grosso, ver
/home/claude/brasil_2026/centro-oeste/mato-grosso/analise/build_analysis_mt.py):
distribuição temática exaustiva por segmentação de marcadores de seção reais
(lidos e mapeados à mão) e Índice de Base Empírica (heurística lexical/regex
idêntica à usada em todos os outros estados, reaproveitada sem alterações
para manter comparabilidade entre estados e regiões).

Caso do Distrito Federal: o governador titular, Ibaneis Rocha (MDB), estava em
seu 2º mandato consecutivo (portanto inelegível para um 3º mandato seguido) e,
em março de 2026, renunciou ao cargo para disputar uma vaga ao Senado. Sua
vice, Celina Leão (PP), assumiu integralmente o governo em 30/03/2026 (fontes:
Metrópoles, "Celina Leão assume governo do DF nesta segunda (30/3)"; CLDF,
"Celina Leão assume o governo em cerimônia nesta segunda-feira (30) na CLDF";
Correio Braziliense, "Eleições: Ibaneis Rocha deixa o governo do DF para
concorrer ao Senado") e hoje é a governadora em exercício, concorrendo a
mandato próprio — classificada aqui como "incumbente por sucessão" (mesmo
critério usado para Otaviano Pivetta no Mato Grosso). Notável: ao longo de
2026 houve um rompimento político entre Ibaneis Rocha e Celina Leão (fontes:
Gazeta do Povo, "Ibaneis Rocha rompe com Celina Leão, que rebate: 'sucessão
nunca será submissão'"; O Tempo, "Ibaneis Rocha ataca Celina Leão e fala em
candidatura própria do MDB no DF contra ela"), mas isso não muda sua condição
de governadora em exercício por sucessão — ela permanece a titular do cargo
que ocupa hoje, concorrendo a um mandato próprio. Segundo pesquisa Paraná
Pesquisas de julho de 2026 (fonte: Gazeta do Povo, "Paraná Pesquisas divulga
levantamento para o governo do DF"), Celina Leão lidera com 34,6% contra
28,1% de José Roberto Arruda.
O outro candidato analisado, José Roberto Arruda (PSD), já foi governador do
Distrito Federal (2007-2010), mandato interrompido por impeachment após o
escândalo do "Mensalão do DEM", revelado pela Operação Caixa de Pandora
(fonte: CNN Brasil, "Quem são os candidatos a governador do Distrito Federal
em 2026") — retorna à disputa como opositor à atual gestão, classificado aqui
como "desafiante".
Essa é uma leitura eleitoral, baseada em fontes institucionais e cobertura
jornalística de 2026, e não influenciou nenhuma etapa da extração ou
classificação textual dos planos.
"""
import base64
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path

from wordcloud import WordCloud

PLANOS_DIR = Path("/home/claude/brasil_2026/centro-oeste/distrito-federal/planos")
ANALISE_DIR = Path("/home/claude/brasil_2026/centro-oeste/distrito-federal/analise")
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATOS = [
    {"slug": "celina_leao", "nome": "Celina Leão", "partido": "PP",
     "categoria": "incumbente por sucessão — era vice-governadora de Ibaneis Rocha (MDB, "
                  "em seu 2º mandato consecutivo, inelegível para um 3º mandato seguido) e "
                  "assumiu integralmente o governo em 30/03/2026, após a renúncia de "
                  "Ibaneis para disputar o Senado; hoje governadora em exercício, concorre "
                  "a mandato próprio pelo PP e lidera as pesquisas — fontes: Metrópoles, "
                  "\"Celina Leão assume governo do DF nesta segunda (30/3)\"; CLDF, \"Celina "
                  "Leão assume o governo em cerimônia nesta segunda-feira (30) na CLDF\"; "
                  "Correio Braziliense, \"Eleições: Ibaneis Rocha deixa o governo do DF para "
                  "concorrer ao Senado\"; Gazeta do Povo, \"Paraná Pesquisas divulga "
                  "levantamento para o governo do DF\" (34,6% x 28,1%, jul/2026). Nota: "
                  "houve rompimento político público entre Ibaneis Rocha e Celina Leão ao "
                  "longo de 2026 (fonte: Gazeta do Povo, \"Ibaneis Rocha rompe com Celina "
                  "Leão, que rebate: 'sucessão nunca será submissão'\"), mas isso não altera "
                  "sua condição de governadora em exercício por sucessão"},
    {"slug": "arruda", "nome": "José Roberto Arruda", "partido": "PSD",
     "categoria": "desafiante — já foi governador do Distrito Federal (2007-2010), mandato "
                  "interrompido por impeachment após o escândalo do \"Mensalão do DEM\", "
                  "revelado pela Operação Caixa de Pandora; retorna à disputa em oposição à "
                  "atual gestão (Ibaneis Rocha/Celina Leão) — fonte: CNN Brasil, \"Quem são "
                  "os candidatos a governador do Distrito Federal em 2026\"; segundo "
                  "pesquisa Paraná Pesquisas de julho de 2026, aparece em 2º lugar com "
                  "28,1% contra 34,6% de Celina Leão (fonte: Gazeta do Povo)"},
]

# ---------------------------------------------------------------------------
# Tokenização e stopwords — idênticas às usadas em todos os demais estados do
# projeto (Nordeste, Norte e Centro-Oeste), não adaptadas ao Distrito Federal,
# para preservar comparabilidade entre estados. Mantidas verbatim, inclusive
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

# Celina Leão (PP): documento muito bem estruturado — Carta de Apresentação
# seguida de 5 EIXOS numerados, cada um dividido em subseções temáticas
# próprias, com título em caixa alta seguido do número de "ações" (ex.:
# "FAMÍLIA    6 ações"). Todos os títulos de subseção usados como marcador
# ocorrem exatamente uma vez no arquivo inteiro (verificado via grep -c),
# então não há risco de colisão nem necessidade da lógica de "pular para a
# 2ª ocorrência" usada em outros estados para documentos com sumário/índice
# repetindo os títulos — a Apresentação de Celina Leão não tem um índice
# desse tipo.
#
# EIXO 1 (CUIDADO, DIGNIDADE E INCLUSÃO SOCIAL): FAMÍLIA, MULHERES, PESSOA
# IDOSA, JUVENTUDE, PESSOAS COM DEFICIÊNCIA/ACESSIBILIDADE/INCLUSÃO,
# DESENVOLVIMENTO SOCIAL E SUPERAÇÃO DAS VULNERABILIDADES, IGUALDADE/
# RESPEITO/CIDADANIA = assistencia_social (nenhum desses eixos tem uma
# política setorial própria na taxonomia de 9 temas do projeto — grupos
# populacionais/proteção social, mesmo critério usado em todos os demais
# estados para família, mulher, idoso, pessoa com deficiência, igualdade
# racial/de gênero etc.); SEGURANÇA ALIMENTAR = assistencia_social
# (precedente do Ceará/Maranhão/Paraíba); SAÚDE = saude; EDUCAÇÃO =
# educacao; SEGURANÇA PÚBLICA = seguranca; ESPORTE E LAZER = assistencia_
# social (precedente do projeto). JUVENTUDE mistura formação profissional,
# prevenção à violência e esporte/cultura, mas está posicionada dentro do
# EIXO 1 (eixo de cuidado/proteção social) e é apresentada como política de
# proteção à juventude (não como capítulo de educação autônomo, que já
# existe separadamente no documento) — mantida como assistencia_social,
# consistente com o próprio enquadramento do documento.
#
# EIXO 2 (MORADIA, INFRAESTRUTURA, MOBILIDADE E SUSTENTABILIDADE): HABITAÇÃO
# E REGULARIZAÇÃO FUNDIÁRIA, INFRAESTRUTURA/SANEAMENTO/ILUMINAÇÃO/OBRAS
# PÚBLICAS, MOBILIDADE URBANA = infraestrutura; SUSTENTABILIDADE E MEIO
# AMBIENTE = meio_ambiente; PROTEÇÃO ANIMAL = assistencia_social
# (precedente do projeto, replicado do Ceará/Maranhão/Paraíba).
#
# EIXO 3 (DESENVOLVIMENTO ECONÔMICO, TRABALHO E VOCAÇÕES REGIONAIS):
# DESENVOLVIMENTO ECONÔMICO/TRABALHO/RENDA, FEIRAS, AGRICULTURA, TURISMO =
# economia (turismo como vocação econômica, mesmo precedente do Ceará);
# CULTURA E ECONOMIA CRIATIVA = assistencia_social (precedente do projeto
# para "cultura", mesmo quando o título do capítulo menciona "economia
# criativa" — o conteúdo do capítulo é predominantemente sobre acesso a
# políticas culturais, patrimônio e fomento a artistas, não sobre política
# industrial do setor criativo).
#
# EIXO 4 (BRB, DESENVOLVIMENTO E FOMENTO DO DF): PATRIMÔNIO ESTRATÉGICO
# (banco público BRB: crédito, microcrédito, fomento a empresas) =
# economia; ENTORNO (governança interfederativa com Goiás/Minas
# Gerais/RIDE-DF, cooperação em múltiplas políticas ao mesmo tempo) =
# gestao_publica, mesmo critério usado no Ceará para "GESTÃO ESTRATÉGICA,
# GOVERNANÇA INTERFEDERA-" (Elmano de Freitas): trecho que atravessa
# deliberadamente vários temas sob o guarda-chuva de governança regional,
# sem predominância de obras físicas que justificasse "infraestrutura".
#
# EIXO 5 (GESTÃO, GOVERNANÇA, TRANSFORMAÇÃO DIGITAL E GOVERNO DE
# PROXIMIDADE): GESTÃO DE PESSOAS E VALORIZAÇÃO DOS SERVIDORES,
# TRANSFORMAÇÃO DIGITAL/GOVERNO INTELIGENTE/INOVAÇÃO, PLANEJAMENTO/
# ORÇAMENTO/GESTÃO/GOVERNANÇA, SOCIEDADE CIVIL E GOVERNO DE PROXIMIDADE =
# gestao_publica (máquina administrativa, servidores, fiscal, digital,
# participação social institucional).
MARCADORES_CELINA = [
    ("FAMÍLIA", "assistencia_social"),
    ("MULHERES", "assistencia_social"),
    ("PESSOA IDOSA", "assistencia_social"),
    ("JUVENTUDE", "assistencia_social"),
    ("PESSOAS COM DEFICIÊNCIA, ACESSIBILIDADE E INCLUSÃO", "assistencia_social"),
    ("DESENVOLVIMENTO SOCIAL E SUPERAÇÃO DAS VULNERABILIDADES", "assistencia_social"),
    ("SEGURANÇA ALIMENTAR", "assistencia_social"),
    ("SAÚDE ", "saude"),
    ("EDUCAÇÃO ", "educacao"),
    ("SEGURANÇA PÚBLICA", "seguranca"),
    ("ESPORTE E LAZER", "assistencia_social"),
    ("IGUALDADE, RESPEITO E CIDADANIA", "assistencia_social"),
    ("HABITAÇÃO E REGULARIZAÇÃO FUNDIÁRIA", "infraestrutura"),
    ("INFRAESTRUTURA, SANEAMENTO, ILUMINAÇÃO E OBRAS PÚBLICAS", "infraestrutura"),
    ("MOBILIDADE URBANA", "infraestrutura"),
    ("SUSTENTABILIDADE E MEIO AMBIENTE", "meio_ambiente"),
    ("PROTEÇÃO ANIMAL", "assistencia_social"),
    ("DESENVOLVIMENTO ECONÔMICO, TRABALHO E RENDA", "economia"),
    ("FEIRAS", "economia"),
    ("AGRICULTURA", "economia"),
    ("TURISMO", "economia"),
    ("CULTURA E ECONOMIA CRIATIVA", "assistencia_social"),
    ("PATRIMÔNIO ESTRATÉGICO", "economia"),
    ("ENTORNO", "gestao_publica"),
    ("GESTÃO DE PESSOAS E VALORIZAÇÃO DOS SERVIDORES", "gestao_publica"),
    ("TRANSFORMAÇÃO DIGITAL, GOVERNO INTELIGENTE E INOVAÇÃO", "gestao_publica"),
    ("PLANEJAMENTO, ORÇAMENTO, GESTÃO E GOVERNANÇA", "gestao_publica"),
    ("SOCIEDADE CIVIL E GOVERNO DE PROXIMIDADE", "gestao_publica"),
]

# José Roberto Arruda (PSD): documento extenso (183 páginas), com um corpo
# narrativo inicial organizado em 4 EIXOS (I RESGATAR A GESTÃO, II CUIDAR
# DAS PESSOAS, III GERAR PROSPERIDADE, IV TRANSFORMAR O TERRITÓRIO), cada
# um com subseções temáticas em prosa, seguido de TRÊS "Cadernos de
# Projetos e Ações" (ANEXO I, II e III), que detalham as mesmas 4 eixos em
# formato de capítulos numerados com propostas específicas: ANEXO I detalha
# o Eixo I (Resgatar a Gestão), ANEXO II detalha o Eixo II (Cuidar das
# Pessoas, 14 capítulos numerados 1-14) e ANEXO III detalha, em sequência,
# o Eixo III (Gerar Prosperidade) e o Eixo IV (Transformar o Território,
# incluindo um grande capítulo final de integração metropolitana DF-
# Entorno). Não há um "ANEXO IV" separado — o próprio ANEXO III muda de
# assunto (de prosperidade para território) na metade do arquivo, sem novo
# cabeçalho "ANEXO", apenas a mudança dos títulos de capítulo (ex.:
# "TRANSPORTE PÚBLICO SOBRE TRILHOS" já é conteúdo do Eixo IV).
#
# Os marcadores usados cobrem, em sequência, o corpo narrativo (linhas
# ~505-1751) e os 3 anexos (linhas ~1751 até o fim do arquivo, ~6028
# linhas). Como o documento repete os mesmos títulos de capítulo em pontos
# diferentes (ex.: "SAÚDE" aparece como subtítulo no corpo narrativo, e de
# novo como título do capítulo 2 do ANEXO II; "EDUCAÇÃO", "CULTURA",
# "ESPORTE" e "TURISMO" também se repetem), os marcadores foram escolhidos
# e ORDENADOS estritamente na sequência real de leitura do documento: a
# função de segmentação (`distribuicao_tematica_exaustiva`) avança um
# cursor de posição de caractere a cada marcador consumido, então um título
# repetido (ex. "SAÚDE") é sempre localizado a partir de onde o cursor
# parou, nunca reencontra uma ocorrência anterior já consumida. Isso exige
# que a lista de marcadores seja EXAUSTIVA e na ordem certa (nenhum título
# de capítulo pode ser pulado), o que foi verificado lendo o documento
# integralmente e conferido também via segmentação de debug
# (_debug_segmentos_arruda.txt) após a primeira execução do script.
#
# Classificações não óbvias:
# - No corpo narrativo e no ANEXO I (Eixo I "Resgatar a Gestão"), todos os
#   capítulos de "transformação digital" (GDF NA PALMA DA MÃO, SAÚDE
#   DIGITAL, EDUCAÇÃO DIGITAL, GOVERNO SEM PAPEL, IA NO GOVERNO, ECONOMIA
#   DIGITAL E INOVAÇÃO, GOVERNO BASEADO EM DADOS, SEGURANÇA CIBERNÉTICA)
#   foram classificados como gestao_publica, e não pelo tema aparente do
#   nome (ex. "Saúde Digital" ≠ saude): são ferramentas/sistemas de gestão
#   do aparato estatal, parte do eixo "Resgatar a Gestão", não entrega de
#   serviço de saúde/educação em si (mesmo critério usado no Mato Grosso e
#   no Ceará para agrupar "governo digital" como gestao_publica). Exceção:
#   "DF CONECTADO – INTERNET GRATUITA PARA TODOS" foi classificado como
#   infraestrutura, por ser literalmente obra de conectividade física
#   (rede), e não uma ferramenta de gestão.
# - "CIÊNCIA, TECNOLOGIA E INOVAÇÃO" (corpo narrativo, Eixo III) e o
#   capítulo equivalente do ANEXO III ("CIÊNCIA, TECNOLOGIA, INOVAÇÃO E
#   TRANSFORMAÇÃO DIGITAL", com startups, IA, universidade-empresa) foram
#   classificados como economia, e não educacao — a taxonomia de 9 temas
#   do projeto não tem eixo dedicado a C&T, e aqui o candidato agrupa
#   explicitamente esse conteúdo ao Eixo III "Gerar Prosperidade"
#   (desenvolvimento econômico), não ao Eixo II "Cuidar das Pessoas" (onde
#   está o capítulo autônomo de Educação) — mesmo precedente usado no Mato
#   Grosso (Wellington Fagundes).
# - "ECONOMIA CRIATIVA" (corpo narrativo, Eixo III) foi classificado como
#   economia, diferente do tratamento dado a "CULTURA" isolada (Eixo II) e
#   a "CULTURA COMO PATRIMÔNIO, IDENTIDADE E DESENVOLVIMENTO" (ANEXO III,
#   também assistencia_social): o capítulo de Economia Criativa está
#   posicionado dentro do eixo de prosperidade econômica e é enquadrado
#   pelo próprio texto como modelo de negócio/geração de renda do setor
#   criativo, distinto dos capítulos de acesso a políticas culturais.
# - CULTURA, ESPORTE (corpo narrativo e ANEXO II) e as subseções de cultura
#   e esporte do ANEXO III ("CULTURA COMO PATRIMÔNIO...", "ESPORTE, ALTO
#   RENDIMENTO...", "ESPORTE PARA A VIDA") seguem o precedente do projeto =
#   assistencia_social; já "TURISMO, EVENTOS E DESTINO INTERNACIONAL" e o
#   capítulo "TURISMO" (corpo narrativo, Eixo III, e ANEXO II capítulo 13)
#   seguem o precedente turismo = economia.
# - "SOCIOEDUCATIVO" (ANEXO II, capítulo 10, sistema de medidas
#   socioeducativas para adolescentes em conflito com a lei) foi
#   classificado como seguranca, junto com SEGURANÇA PÚBLICA e SISTEMA
#   PENAL, por integrar o mesmo sistema de justiça/segurança do documento
#   (os 3 capítulos são consecutivos e tratados como um bloco único de
#   segurança pública e justiça criminal/socioeducativa no próprio
#   documento).
# - "JUSTIÇA, CIDADANIA E DIREITOS HUMANOS", "MULHER", "POLÍTICAS DE
#   EQUIDADE", "FAMÍLIA: DA PRIMEIRA INFÂNCIA À PESSOA IDOSA" e
#   "DESENVOLVIMENTO HUMANO" (ANEXO II, sobre pessoas com deficiência/
#   acessibilidade) = assistencia_social, mesmo critério do plano de Celina
#   Leão para grupos populacionais sem eixo setorial próprio na taxonomia.
# - No grande capítulo final de integração metropolitana DF-Entorno (fim do
#   ANEXO III), cada subseção foi classificada pelo tema anunciado no
#   próprio título (ex.: "REDE METROPOLITANA DE SAÚDE" = saude; "ZONAS DE
#   DESENVOLVIMENTO ECONÔMICO INTEGRADO", "PROGRAMA EMPREGA ENTORNO",
#   "DISTRITO INDUSTRIAL E LOGÍSTICO METROPOLITANO" = economia; "CENTRO
#   INTEGRADO DE SEGURANÇA METROPOLITANA", "SISTEMA METROPOLITANA DE
#   VIDEOMONITORAMENTO INTELIGENTE" = seguranca; "PROGRAMA JUVENTUDE
#   METROPOLITANA", "PROGRAMA DE SUPERAÇÃO DA POBREZA E INCLUSÃO
#   PRODUTIVA" = assistencia_social; "FORTALECIMENTO DA RIDE E DA AMB" e
#   "OBSERVATÓRIO METROPOLITANO DA GRANDE BRASÍLIA" = gestao_publica
#   (governança interfederativa e inteligência de dados regional, mesmo
#   critério usado para "ENTORNO" no plano de Celina Leão); as demais
#   (transporte, habitação, centralidades urbanas, plano diretor, estradas,
#   anel viário) = infraestrutura.
MARCADORES_ARRUDA = [
    # --- Corpo narrativo: EIXO I – RESGATAR A GESTÃO ---
    ("EIXO I – RESGATAR A GESTÃO", "outros"),
    ("MUDAR A GESTÃO PARA TRANSFORMAR MAIS", "gestao_publica"),
    ("CENTRO DE COORDENAÇÃO DO GOVERNO E GESTÃO ESTRATÉGICA", "gestao_publica"),
    ("GOVERNO INTELIGENTE, DADOS E INTELIGÊNCIA ARTIFICIAL", "gestao_publica"),
    ("RESPONSABILIDADE FISCAL, QUALIDADE DO GASTO", "gestao_publica"),
    ("GOVERNANÇA, TRANSPARÊNCIA E APRENDIZAGEM INSTITUCIONAL", "gestao_publica"),
    # --- Corpo narrativo: EIXO II - CUIDAR DAS PESSOAS ---
    ("EIXO II - CUIDAR DAS PESSOAS", "outros"),
    ("AMPLIAR CAPACIDADES HUMANAS PARA MULTIPLICAR OPORTUNIDADES", "outros"),
    ("EDUCAÇÃO", "educacao"),
    ("SAÚDE", "saude"),
    ("ASSISTÊNCIA SOCIAL E DESENVOLVIMENTO HUMANO", "assistencia_social"),
    ("JUVENTUDE", "assistencia_social"),
    ("ESPORTE", "assistencia_social"),
    ("CULTURA", "assistencia_social"),
    ("LONGEVIDADE E ENVELHECIMENTO ATIVO", "assistencia_social"),
    # --- Corpo narrativo: EIXO III — GERAR PROSPERIDADE ---
    ("EIXO III — GERAR PROSPERIDADE", "outros"),
    ("TRANSFORMAR CAPACIDADES EM PROSPERIDADE", "outros"),
    ("DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "economia"),
    ("EMPREENDEDORISMO, COMPETITIVIDADE E AMBIENTE DE NEGÓCIOS", "economia"),
    ("TURISMO", "economia"),
    ("INTERNACIONALIZAÇÃO E ATRAÇÃO DE INVESTIMENTOS", "economia"),
    ("ECONOMIA CRIATIVA", "economia"),
    # --- Corpo narrativo: EIXO IV — TRANSFORMAR O TERRITÓRIO ---
    ("EIXO IV — TRANSFORMAR O TERRITÓRIO", "outros"),
    ("TRANSFORMAR O TERRITÓRIO EM UMA VANTAGEM COMPETITIVA", "outros"),
    ("MOBILIDADE URBANA", "infraestrutura"),
    ("PLANEJAMENTO TERRITORIAL E DESENVOLVIMENTO URBANO", "infraestrutura"),
    ("HABITAÇÃO E DESENVOLVIMENTO TERRITORIAL", "infraestrutura"),
    ("SANEAMENTO, RECURSOS HÍDRICOS E RESILIÊNCIA", "infraestrutura"),
    ("MEIO AMBIENTE, SUSTENTABILIDADE E CIDADES INTELIGENTES", "meio_ambiente"),
    ("GESTÃO ESTRATÉGICA DO TERRITÓRIO", "gestao_publica"),
    ("UMA NOVA FORMA DE GOVERNAR", "outros"),
    # --- ANEXO I: Caderno de Projetos e Ações — EIXO I (Resgatar a Gestão) ---
    ("FINANÇAS PÚBLICAS", "gestao_publica"),
    ("GDF NA PALMA DA MÃO", "gestao_publica"),
    ("SAÚDE DIGITAL", "gestao_publica"),
    ("EDUCAÇÃO DIGITAL", "gestao_publica"),
    ("GOVERNO SEM PAPEL", "gestao_publica"),
    ("INTELIGÊNCIA ARTIFICIAL NO GOVERNO", "gestao_publica"),
    ("ECONOMIA DIGITAL E INOVAÇÃO", "gestao_publica"),
    ("DF CONECTADO", "infraestrutura"),
    ("GOVERNO BASEADO EM DADOS", "gestao_publica"),
    ("SEGURANÇA CIBERNÉTICA", "gestao_publica"),
    ("SERVIDOR PÚBLICO CAPACITADO PARA O FUTURO", "gestao_publica"),
    ("DF PARTICIPA", "gestao_publica"),
    ("PARCERIAS COM O SETOR PRIVADO", "gestao_publica"),
    ("CENTRO ADMINISTRATIVO INTEGRADO - CENTRAD", "gestao_publica"),
    ("UMA NOVA FORMA DE GOVERNAR", "gestao_publica"),
    ("GOVERNO QUE RESPEITA O TEMPO DAS PESSOAS", "gestao_publica"),
    ("CENTRO DE COORDENAÇÃO E INTELIGÊNCIA ESTRATÉGICA", "gestao_publica"),
    # --- ANEXO II: Caderno de Projetos e Ações — EIXO II (Cuidar das Pessoas) ---
    ("EDUCAÇÃO", "educacao"),
    ("SAÚDE", "saude"),
    ("DESENVOLVIMENTO SOCIAL", "assistencia_social"),
    ("JUSTIÇA, CIDADANIA E DIREITOS HUMANOS", "assistencia_social"),
    ("MULHER", "assistencia_social"),
    ("POLÍTICAS DE EQUIDADE", "assistencia_social"),
    ("FAMÍLIA: DA PRIMEIRA INFÂNCIA À PESSOA IDOSA", "assistencia_social"),
    ("SEGURANÇA PÚBLICA", "seguranca"),
    ("SISTEMA PENAL", "seguranca"),
    ("SOCIOEDUCATIVO", "seguranca"),
    ("CULTURA", "assistencia_social"),
    ("ESPORTE", "assistencia_social"),
    ("TURISMO", "economia"),
    ("DESENVOLVIMENTO HUMANO", "assistencia_social"),
    # --- ANEXO III: Caderno de Projetos e Ações — EIXO III (Gerar Prosperidade) ---
    ("DESENVOLVIMENTO ECONÔMICO", "economia"),
    ("CULTURA COMO PATRIMÔNIO, IDENTIDADE E DESENVOLVIMENTO", "assistencia_social"),
    ("TURISMO, EVENTOS E DESTINO INTERNACIONAL", "economia"),
    ("ESPORTE, ALTO RENDIMENTO E DESENVOLVIMENTO HUMANO", "assistencia_social"),
    ("ESPORTE PARA A VIDA", "assistencia_social"),
    ("CIÊNCIA, TECNOLOGIA, INOVAÇÃO E TRANSFORMAÇÃO DIGITAL", "economia"),
    # --- ANEXO III (continuação): EIXO IV (Transformar o Território) ---
    ("TRANSPORTE PÚBLICO SOBRE TRILHOS", "infraestrutura"),
    ("SETOR RURAL", "economia"),
    ("MEIO AMBIENTE", "meio_ambiente"),
    ("HABITAÇÃO", "infraestrutura"),
    ("REGULARIZAÇÃO FUNDIÁRIA", "infraestrutura"),
    ("FORTALECIMENTO DA RIDE E DA AMB", "gestao_publica"),
    ("SISTEMA INTEGRADO DE TRANSPORTE DF-ENTORNO", "infraestrutura"),
    ("PLANO METROPOLITANO DE HABITAÇÃO", "infraestrutura"),
    ("NOVAS CENTRALIDADES URBANAS", "infraestrutura"),
    ("REDE METROPOLITANA DE SAÚDE", "saude"),
    ("ZONAS DE DESENVOLVIMENTO ECONÔMICO INTEGRADO", "economia"),
    ("PROGRAMA EMPREGA ENTORNO", "economia"),
    ("DISTRITO INDUSTRIAL E LOGÍSTICO METROPOLITANO", "economia"),
    ("EDUCAÇÃO, QUALIFICAÇÃO E UNIVERSIDADES METROPOLITANAS", "educacao"),
    ("SISTEMA DE TRANSPORTE ESTUDANTIL METROPOLITANO", "infraestrutura"),
    ("CENTRO INTEGRADO DE SEGURANÇA METROPOLITANA", "seguranca"),
    ("SISTEMA METROPOLITANA DE VIDEOMONITORAMENTO INTELIGENTE", "seguranca"),
    ("PROGRAMA ESTRADAS DA GRANDE BRASÍLIA", "infraestrutura"),
    ("ANEL VIÁRIO METROPOLITANO", "infraestrutura"),
    ("PROGRAMA JUVENTUDE METROPOLITANA", "assistencia_social"),
    ("PROGRAMA DE SUPERAÇÃO DA POBREZA E INCLUSÃO PRODUTIVA", "assistencia_social"),
    ("PLANO DIRETOR DA GRANDE BRASÍLIA", "infraestrutura"),
    ("OBSERVATÓRIO METROPOLITANO DA GRANDE BRASÍLIA", "gestao_publica"),
    ("RESULTADOS ESPERADOS", "outros"),
]

MARCADORES = {
    "celina_leao": MARCADORES_CELINA,
    "arruda": MARCADORES_ARRUDA,
}

# Ponto de partida da análise de Base Empírica (Tarefa 2) para cada
# candidato: nenhum dos dois planos do DF tem um sumário/índice longo o
# bastante em texto corrido que pudesse distorcer a extração de frases
# (Celina Leão não tem sumário; Arruda tem apenas os índices curtos dos 4
# eixos, repetidos como lista de títulos antes de cada ANEXO, não frases
# completas), então a análise roda sobre o corpo inteiro do documento
# (posição 0) para os dois candidatos.
CURSOR_INICIAL_BASE_EMPIRICA = {
    "celina_leao": 0,
    "arruda": 0,
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
            "comparabilidade metodológica entre estados — por isso 'Brasília' "
            "e 'brasiliense(s)' NÃO são filtrados e aparecem naturalmente "
            "entre os termos mais frequentes de ambos os planos). Mostra os "
            "termos mais repetidos por candidato e o agregado dos dois "
            "planos."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/capítulo/"
            "subseção). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível "
            "(ex.: seções de integração metropolitana ou de governança "
            "interfederativa que atravessam vários setores ao mesmo tempo), "
            "o segmento foi classificado item a item sempre que os itens "
            "individuais eram identificáveis (subtítulos próprios), ou como "
            "'outros'/pelo tema predominante do trecho quando não era "
            "possível separar com segurança."
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
            "Centro-Oeste, sem nenhum ajuste específico para o Distrito "
            "Federal, para manter comparabilidade entre estados e regiões."
        ),
        "metodologia_nota": (
            "O Distrito Federal tem uma particularidade sucessória "
            "semelhante à observada no Mato Grosso: o governador titular, "
            "Ibaneis Rocha (MDB), estava em seu 2º mandato consecutivo "
            "(portanto inelegível para um 3º mandato seguido) e, em março "
            "de 2026, renunciou ao cargo para disputar uma vaga ao Senado. "
            "Sua vice, Celina Leão (PP), assumiu integralmente o governo em "
            "30/03/2026 (fontes: Metrópoles, 'Celina Leão assume governo do "
            "DF nesta segunda (30/3)'; CLDF, 'Celina Leão assume o governo "
            "em cerimônia nesta segunda-feira (30) na CLDF'; Correio "
            "Braziliense, 'Eleições: Ibaneis Rocha deixa o governo do DF "
            "para concorrer ao Senado') e hoje é a governadora em "
            "exercício, concorrendo a mandato próprio pelo PP e liderando "
            "as pesquisas (Paraná Pesquisas, jul/2026: 34,6% x 28,1%, fonte "
            "Gazeta do Povo) — classificada neste projeto como 'incumbente "
            "por sucessão', mesmo critério usado para Otaviano Pivetta no "
            "Mato Grosso. Ao longo de 2026 houve um rompimento político "
            "público entre Ibaneis Rocha e Celina Leão (fontes: Gazeta do "
            "Povo, 'Ibaneis Rocha rompe com Celina Leão, que rebate: "
            "\"sucessão nunca será submissão\"'; O Tempo, 'Ibaneis Rocha "
            "ataca Celina Leão e fala em candidatura própria do MDB no DF "
            "contra ela'), mas isso não altera sua condição de governadora "
            "em exercício por sucessão, que é o critério de classificação "
            "usado neste projeto. O outro candidato analisado, José Roberto "
            "Arruda (PSD), já foi governador do Distrito Federal "
            "(2007-2010), mandato interrompido por impeachment após o "
            "escândalo do 'Mensalão do DEM', revelado pela Operação Caixa "
            "de Pandora (fonte: CNN Brasil, 'Quem são os candidatos a "
            "governador do Distrito Federal em 2026') — retorna à disputa "
            "em oposição à atual gestão, classificado como 'desafiante'; "
            "segundo a mesma pesquisa Paraná Pesquisas, aparece em 2º lugar "
            "com 28,1%. Essa é uma leitura eleitoral, baseada em fontes "
            "institucionais e cobertura jornalística de 2026, e não "
            "influenciou nenhuma etapa da extração ou classificação textual "
            "dos planos. "
            "Ressalva sobre a extração do plano de José Roberto Arruda: o "
            "PDF de origem (183 páginas) apresentava um defeito de extração "
            "DIFERENTE do já conhecido problema de ligaduras tipográficas "
            "quebradas ('fi'/'fl' convertidas em espaço) observado em "
            "outros planos do projeto — a extração padrão via pdftotext "
            "produzia caracteres corrompidos (mojibake) em acentuação de "
            "diversas palavras. O problema foi resolvido reextraindo o PDF "
            "com a biblioteca PyMuPDF (fitz) em vez de pdftotext, o que "
            "produziu texto limpo (confirmado: 0 caracteres de substituição "
            "U+FFFD no arquivo final usado nesta análise). Este é o "
            "TERCEIRO tipo de defeito de extração de PDF já documentado no "
            "projeto (após ligaduras fi/fl quebradas e colunas de página "
            "entrelaçadas linha a linha, observadas em outros estados). O "
            "plano de Celina Leão não apresentou nenhum desses problemas de "
            "extração. "
            "Ressalva estrutural sobre o plano de Arruda: o documento "
            "repete os mesmos títulos de capítulo em pontos diferentes do "
            "arquivo (o corpo narrativo inicial, organizado em 4 Eixos, "
            "apresenta em prosa os mesmos temas que depois são detalhados, "
            "em maior profundidade, em 3 'Cadernos de Projetos e Ações' "
            "anexos — ANEXO I para o Eixo I, ANEXO II para o Eixo II, e "
            "ANEXO III para os Eixos III e IV combinados, sem cabeçalho "
            "'ANEXO IV' separado). Títulos como 'SAÚDE', 'EDUCAÇÃO', "
            "'CULTURA', 'ESPORTE', 'TURISMO' e 'MEIO AMBIENTE' aparecem, "
            "portanto, mais de uma vez como marcador de seção ao longo do "
            "arquivo — isso é tratado corretamente pela função de "
            "segmentação, que avança um cursor de posição de caractere a "
            "cada marcador consumido (nunca reencontra uma ocorrência já "
            "processada), mas exigiu que a lista de marcadores fosse "
            "construída de forma exaustiva e na ordem exata de leitura do "
            "documento inteiro, sem pular nenhum capítulo, para evitar que "
            "um título repetido fosse localizado no lugar errado. "
            "Decisões de classificação não óbvias (capítulos de "
            "'transformação digital' do Eixo I = gestão pública, e não pelo "
            "tema aparente do nome, ex. 'Saúde Digital' ≠ saúde; ciência e "
            "tecnologia agrupada com economia, seguindo o precedente do "
            "Mato Grosso; 'Economia Criativa' = economia, distinto do "
            "tratamento dado a 'Cultura' isolada = assistência social; "
            "socioeducativo agrupado com segurança pública e sistema penal; "
            "subseções do capítulo de integração metropolitana DF-Entorno "
            "classificadas item a item pelo tema anunciado no próprio "
            "título) estão documentadas linha a linha nos comentários do "
            "script de análise."
        ),
        "lista_jargao_utilizada": JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
