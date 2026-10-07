#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Paraíba 2026.

Migração para o padrão de pasta por estado (10/09/2026): a Paraíba foi o
PRIMEIRO estado analisado no projeto (17-25/08/2026), antes de o projeto
adotar a estrutura `<regiao>/<estado>/{planos,analise,dashboard}` usada por
todos os outros 24 estados com dashboard — por isso ficou de fora do mapa
nacional (nenhum link "Ver dashboard completo do estado" apontava para ela).
Os números publicados (Índice de Base Empírica, distribuição temática) NÃO
mudam nesta migração — são os mesmos já usados em
`nordeste/analise_geral_ne/dados_consolidados.json` e em
`nacional/dados_nacionais.json` desde a correção de 25/08/2026. O que muda é
só a organização: este script substitui o antigo pipeline solto (em
`/home/claude/pb2026_v2/`, nunca versionado dentro de `brasil_2026/`) pelo
motor compartilhado (`programs/motor_indice_base_empirica.py`), com a mesma
segmentação temática (MARCADORES_*, obra de leitura humana, herdada sem
alterações do script original) e os mesmos CANDIDATOS.

Verificação feita antes desta migração (não redigido de cabeça): rodar os
três planos através de `motor_indice_base_empirica.py` reproduz, byte a
byte, total_palavras, n_pilar_a/b/c, n_retorica_sem_evidencia,
n_compromisso_sem_base, indice_base_empirica_pct e
indice_base_empirica_legado_pct já publicados para os 3 candidatos — e a
`distribuicao_tematica_exaustiva` com os MARCADORES abaixo reproduz,
percentual a percentual, a distribuição já publicada em
nacional/dados_nacionais.json. Ou seja: o motor compartilhado (usado por
todos os outros estados) já é compatível com a Paraíba sem nenhum ajuste de
regex específico — ao contrário do que o script original de 18/08/2026
(preservado em `nordeste/replicacao/codigo/python/build_analysis_pb.py`,
uma cópia histórica pré-correções de 20/08 e 25/08/2026) fazia, com sua
própria cópia (já desatualizada) das regras de pilar A/B/C.

--- Sobre o achado de texto compartilhado (achado_texto_compartilhado /
texto_compartilhado, abaixo) ---
A Paraíba foi o estado onde esse achado foi encontrado pela primeira vez no
projeto (por isso ele é citado como referência nos scripts de outros
estados, como Maranhão e Ceará): comparação automatizada par a par dos 3
planos encontrou blocos de texto idênticos (150+ caracteres, casamento
literal palavra por palavra e pontuação por pontuação) entre pares de
candidatos concorrentes — o mais notável, um parágrafo inteiro sobre o
Instituto de Polícia Científica da Paraíba (IPC) que aparece idêntico nos
TRÊS planos. Este achado não é regenerado por este script (é um resultado de
pesquisa já fechado e revisado editorialmente, feito com
`find_shared_text.py`/`build_shared_text_analysis.py` no pipeline original)
— os dicionários `ACHADO_TEXTO_COMPARTILHADO` e `TEXTO_COMPARTILHADO` abaixo
são uma cópia literal do resultado já publicado, preservados tal qual nesta
migração de pasta.

Sobre CANDIDATOS: os textos `categoria` abaixo são cópias literais do campo
`categoria_raw` já publicado em `nacional/dados_nacionais.json` (25/08/2026),
para manter uma única fonte de verdade sobre a classificação editorial de
cada candidato.
"""
import sys
from collections import Counter
from pathlib import Path

ESTADO_DIR = Path(__file__).resolve().parents[1]
PLANOS_DIR = ESTADO_DIR / "planos"
ANALISE_DIR = ESTADO_DIR / "analise"
WC_DIR = ANALISE_DIR / "wordclouds"
WC_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "programs"))
import motor_indice_base_empirica as motor  # noqa: E402

ALL_STOPWORDS = motor.STOPWORDS | motor.EXTRA_STOPWORDS_BASE

CANDIDATOS = [
    {
        "slug": "cicero-lucena",
        "nome": "Cícero Lucena",
        "partido": "MDB",
        "vice": "Diogo Cunha Lima",
        "categoria": (
            "desafiante (deixou a prefeitura de João Pessoa em abril/2026 "
            "para concorrer; oposição ao governo estadual atual)"
        ),
    },
    {
        "slug": "efraim-filho",
        "nome": "Efraim Filho",
        "partido": "PL",
        "vice": "Nayana Pontes",
        "categoria": (
            "desafiante (senador federal, migrou do União Brasil para o PL "
            "em março/2026; oposição ao governo estadual atual)"
        ),
    },
    {
        "slug": "lucas-ribeiro",
        "nome": "Lucas Ribeiro",
        "partido": "PP",
        "vice": "Lígia Feliciano (Dra. Lígia)",
        "categoria": (
            "incumbente por sucessão (assumiu o governo em 02/04/2026 após "
            "a renúncia de João Azevêdo, PSB, que concorre ao Senado; "
            "concorre à reeleição na condição de titular, com apoio de "
            "coalizão ampla incl. PT e governo federal)"
        ),
    },
]

# ---------------------------------------------------------------------------
# Distribuição temática exaustiva — marcadores (obra de leitura humana,
# 17-18/08/2026, herdados sem alterações do script original
# nordeste/replicacao/codigo/python/build_analysis_pb.py). Ver docstring do
# módulo: verificado que a nova execução via motor compartilhado reproduz
# percentual a percentual a distribuição já publicada.
# ---------------------------------------------------------------------------
MARCADORES_CICERO = [
    ("SÍNTESE DO PLANO — OS COMPROMISSOS COM A PARAÍBA", "outros"),
    ("1. O PONTO DE PARTIDA", "outros"),
    ("2.1 SEGURANÇA COM VALORIZAÇÃO PROFISSIONAL, INTELIGÊNCIA, PREVENÇÃO E RESPOSTA", "seguranca"),
    ("2.2 DESCENTRALIZAÇÃO DA SAÚDE: FILA MENOR, CUIDADO MAIS PERTO", "saude"),
    ("2.3 ESCOLA DO FUTURO: PARA APRENDER, PERMANECER E TRABALHAR", "educacao"),
    ("2.4 EDUCAÇÃO SUPERIOR: UEPB PROTAGONISTA DO DESENVOLVIMENTO", "educacao"),
    ("2.5 MAIS EMPREGOS E NOVOS NEGÓCIOS, NUMA ECONOMIA POR COMPETÊNCIAS", "economia"),
    ("2.6 GOVERNO MUNICIPALISTA E DIGITAL", "gestao_publica"),
    ("2.7 A PARAÍBA COM SEGURANÇA HÍDRICA", "infraestrutura"),
    ("2.8 CRONOGRAMA DE OBRAS POR UMA PARAÍBA INTEGRADA", "infraestrutura"),
    ("3. PARAÍBA VERDE: SUSTENTABILIDADE E RESPEITO AO MEIO AMBIENTE", "meio_ambiente"),
    ("4. AS TRÊS FORMAS DE EXECUTAR O QUE ESTE PLANO PROPÕE", "outros"),
    ("EIXOS TEMÁTICOS", "outros"),
    ("EIXO 1 — SEGURANÇA PÚBLICA E DEFESA SOCIAL", "seguranca"),
    ("EIXO 2 — SAÚDE", "saude"),
    ("EIXO 3 — EDUCAÇÃO E CULTURA", "educacao"),
    ("Compromissos com a cultura:", "assistencia_social"),
    ("Propostas, Programas e Ações", "educacao"),
    ("Cultura: financiamento e fomento", "assistencia_social"),
    ("EIXO 4 — RECURSOS HÍDRICOS", "infraestrutura"),
    ("EIXO 5 — AGRICULTURA, PESCA E DESENVOLVIMENTO RURAL", "economia"),
    ("EIXO 6 — ASSISTÊNCIA SOCIAL E COMBATE À POBREZA", "assistencia_social"),
    ("EIXO 7 — CIÊNCIA, TECNOLOGIA E INOVAÇÃO", "economia"),
    ("EIXO 8 — DESENVOLVIMENTO ECONÔMICO, RECURSOS MINERAIS E EMPREENDEDORISMO", "economia"),
    ("EIXO 9 — DIREITOS HUMANOS, MULHERES E INCLUSÃO SOCIAL", "assistencia_social"),
    ("EIXO 10 — ESPORTE E LAZER", "assistencia_social"),
    ("EIXO 11 — GESTÃO PÚBLICA, GOVERNANÇA E TRANSFORMAÇÃO DIGITAL", "gestao_publica"),
    ("EIXO 12 — HABITAÇÃO, URBANISMO E DESENVOLVIMENTO REGIONAL", "infraestrutura"),
    ("EIXO 13 — INFRAESTRUTURA, MOBILIDADE E LOGÍSTICA", "infraestrutura"),
    ("EIXO 14 — MEIO AMBIENTE E SUSTENTABILIDADE", "meio_ambiente"),
    ("EIXO 15 — TURISMO, ECONOMIA CRIATIVA E EVENTOS", "economia"),
    ("EIXO 16 — PROTEÇÃO E BEM-ESTAR ANIMAL", "assistencia_social"),
    ("CONSIDERAÇÕES FINAIS", "outros"),
]

MARCADORES_EFRAIM = [
    ("SUMÁRIO", "outros"),
    ("INTRODUÇÃO", "outros"),
    ("PARTE I — GOVERNANÇA, ESTADO DIGITAL E INOVAÇÃO PÚBLICA", "gestao_publica"),
    ("Seção 1 — Governança, Gestão Pública e Integridade", "gestao_publica"),
    ("Seção 2 — Fazenda e Tributação", "gestao_publica"),
    ("Seção 3 — Governo Digital, Inteligência Artificial (IA) e Computação Soberana", "gestao_publica"),
    ("Seção 4 — Inovação e Tecnologia", "economia"),
    ("PARTE II — DESENVOLVIMENTO ECONÔMICO E TRABALHO", "economia"),
    ("Seção 5 — Desenvolvimento Econômico", "economia"),
    ("4.1. Polos de Desenvolvimento", "economia"),
    ("Seção 6 — Empreendedorismo e Ambiente de Negócios", "economia"),
    ("Seção 7 — Agropecuária", "economia"),
    ("Seção 8 — Turismo", "economia"),
    ("Seção 9 — Cooperativismo", "economia"),
    ("Seção 10 — Juventude, Qualificação Profissional e Empregabilidade", "economia"),
    ("PARTE III — INFRAESTRUTURA, ÁGUA E MEIO AMBIENTE", "infraestrutura"),
    ("Seção 11 — Infraestrutura e Logística", "infraestrutura"),
    ("Seção 12 — Rodovias", "infraestrutura"),
    ("Seção 13 — Mobilidade Urbana", "infraestrutura"),
    ("Seção 14 — Recursos Hídricos", "infraestrutura"),
    ("Seção 15 — Esgotamento Sanitário", "infraestrutura"),
    ("Seção 16 — Habitação", "infraestrutura"),
    ("Seção 17 — Meio Ambiente, Energia e Sustentabilidade", "meio_ambiente"),
    ("7.2. Infraestrutura para Segurança Hídrica e Saneamento", "infraestrutura"),
    ("7.3. Infraestrutura para Mobilidade Urbana", "infraestrutura"),
    ("7.4. Infraestrutura para o Porto de Cabedelo", "infraestrutura"),
    ("7.5. Infraestrutura para Mineração", "economia"),
    ("7.6. Energia Renovável, Gás e Eletricidade", "meio_ambiente"),
    ("PARTE IV — DESENVOLVIMENTO HUMANO E PROTEÇÃO SOCIAL", "outros"),
    ("Seção 18 — Educação", "educacao"),
    ("Seção 19 — Saúde", "saude"),
    ("Seção 20 — Assistência Social", "assistencia_social"),
    ("Seção 21 — Mulher, Infância, Juventude, Pessoas com Deficiência e Neurodesenvolvimento", "assistencia_social"),
    ("Seção 22 — Cultura", "assistencia_social"),
    ("Seção 23 — Esporte e Lazer", "assistencia_social"),
    ("Seção 24 — Proteção e Bem-Estar Animal", "assistencia_social"),
    ("PARTE V — SEGURANÇA PÚBLICA E DEFESA CIVIL", "seguranca"),
    ("Seção 25 — Segurança Pública e Defesa Civil", "seguranca"),
    ("FECHAMENTO — COMPROMISSO FINAL", "outros"),
]

MARCADORES_LUCAS = [
    ("EIXO 1 — SEGURANÇA PÚBLICA, JUSTIÇA E PROTEÇÃO DA VIDA", "seguranca"),
    ("EIXO 2 — DESENVOLVIMENTO HUMANO INTEGRAL E BEM-ESTAR SOCIAL", "outros"),
    ("2.1. Saúde", "saude"),
    ("2.2. Educação", "educacao"),
    ("2.3. Cultura e Lazer", "assistencia_social"),
    ("2.4. Juventudes e Esporte", "assistencia_social"),
    ("EIXO 3 — MULHERES, DIVERSIDADE, DIREITOS HUMANOS E ANIMAL", "outros"),
    ("3.1. Mulheres", "assistencia_social"),
    ("3.2. População LGBTQIAPN+ e Equidade Racial", "assistencia_social"),
    ("3.3. Pessoas com deficiência (PCD), Transtorno do Espectro Autista (TEA) e pessoas com altas habilidades/superdotação", "assistencia_social"),
    ("3.4. Assistência Social", "assistencia_social"),
    ("3.5. Habitação", "infraestrutura"),
    ("3.6. Proteção aos Animais", "assistencia_social"),
    ("3.7. Direitos Humanos", "assistencia_social"),
    ("EIXO 4 — ECONOMIA PRODUTIVA, INOVAÇÃO E TRABALHO", "economia"),
    ("4.1. Polos de Desenvolvimento", "economia"),
    ("4.2 Indústria e Comércio", "economia"),
    ("4.3. Agropecuária e Agricultura Familiar", "economia"),
    ("4.4. Ciência, Tecnologia e Ecossistema de Inovação", "economia"),
    ("4.5. Turismo sustentável e Interiorizado", "economia"),
    ("4.6 Empreendedorismo", "economia"),
    ("EIXO 5 — GOVERNANÇA DIGITAL E GESTÃO PÚBLICA MODERNA", "gestao_publica"),
    ("5.1. Servidores Públicos", "gestao_publica"),
    ("5.2 Sustentabilidade Fiscal e Contencioso Tributário", "gestao_publica"),
    ("EIXO 6 — DESENVOLVIMENTO TERRITORIAL E INTERIORIZAÇÃO", "outros"),
    ("6.1. Infraestrutura Regional", "infraestrutura"),
    ("6.2. Cadeias Produtivas", "economia"),
    ("EIXO 7 — INFRAESTRUTURA, MOBILIDADE E SUSTENTABILIDADE AMBIENTAL", "outros"),
    ("7.2. Infraestrutura para Segurança Hídrica e Saneamento", "infraestrutura"),
    ("7.3. Infraestrutura para Mobilidade Urbana", "infraestrutura"),
    ("7.4. Infraestrutura para o Porto de Cabedelo", "infraestrutura"),
    ("7.5. Infraestrutura para Mineração", "economia"),
    ("7.6. Energia Renovável, Gás e Eletricidade", "meio_ambiente"),
]

MARCADORES = {
    "cicero-lucena": MARCADORES_CICERO,
    "efraim-filho": MARCADORES_EFRAIM,
    "lucas-ribeiro": MARCADORES_LUCAS,
}

# ---------------------------------------------------------------------------
# Achado de texto compartilhado — cópia literal do resultado já publicado
# (ver docstring do módulo). Não regenerado por este script.
# ---------------------------------------------------------------------------
ACHADO_TEXTO_COMPARTILHADO = {
    "titulo": "Blocos de texto idênticos entre planos de governo rivais",
    "resumo": (
        "A apuração identificou 3 blocos de texto idênticos, palavra por "
        "palavra e pontuação por pontuação, entre os planos de Efraim Filho "
        "(PL) e Lucas Ribeiro (PP), somando 9270 caracteres (o maior bloco "
        "isolado tem 3817 caracteres). Isso equivale a cerca de 33,7% de "
        "todo o texto do plano de Lucas Ribeiro (o mais curto dos dois) e "
        "12,2% do texto do plano de Efraim Filho. Os blocos aparecem nos "
        "eixos de Segurança Pública, Desenvolvimento Econômico e "
        "Infraestrutura/Meio Ambiente. Uma comparação mais ampla, entre "
        "todos os pares dos 3 candidatos, mostrou que o fenômeno não é "
        "exclusivo desse par: um parágrafo sobre o Instituto de Polícia "
        "Científica (IPC) aparece idêntico nos TRÊS planos, e Lucas Ribeiro "
        "e Cícero Lucena (MDB) também compartilham um bloco extenso na área "
        "de Saúde. Ver detalhamento completo na seção dedicada a esse "
        "achado neste painel."
    ),
    "observacao_editorial": (
        "Este achado documenta uma coincidência factual de texto entre "
        "planos de governo de candidaturas concorrentes — não há, nos dados "
        "aqui analisados, qualquer evidência sobre a causa ou sobre quem "
        "redigiu o quê primeiro. Antes de publicar qualquer nota sobre este "
        "achado, a redação deve buscar comentário das campanhas de Efraim "
        "Filho, Lucas Ribeiro e Cícero Lucena, já que uma explicação "
        "plausível é o uso de uma mesma consultoria, redator técnico ou "
        "template de propostas por mais de uma campanha (prática comum em "
        "planos de governo no Brasil) — não se deve caracterizar isso como "
        "plágio ou fraude sem essa checagem."
    ),
    "arquivo_detalhado": "texto_compartilhado.json",
}

TEXTO_COMPARTILHADO = {
    "metodologia": (
        "Comparação automatizada de texto entre os 3 planos (corpo do "
        "texto, após o cabeçalho de metadados), feita por casamento de "
        "n-gramas de palavras (janelas de 8 palavras consecutivas, "
        "indexadas por hash) com extensão de correspondência token a token "
        "— uma alternativa mais rápida e igualmente rigorosa ao difflib."
        "SequenceMatcher a nível de caractere para textos longos (o "
        "SequenceMatcher clássico não escalou para os pares maiores dentro "
        "de tempo hábil). Blocos candidatos com 150+ caracteres foram "
        "inspecionados manualmente: cada um foi comparado caractere a "
        "caractere após normalizar apenas espaços em branco/marcadores de "
        "lista ('-', quebras de linha duplicadas), para verificar se a "
        "igualdade é literal (mesmas palavras, mesma pontuação de frase) ou "
        "apenas estrutural. Em todos os blocos reportados abaixo a "
        "igualdade textual é de 100% após essa normalização — ou seja, são "
        "idênticos palavra por palavra e pontuação por pontuação, mudando "
        "apenas a formatação de lista (uso de '-' e de linhas em branco "
        "entre itens)."
    ),
    "pares_comparados": [
        "efraim-filho_x_lucas-ribeiro",
        "efraim-filho_x_cicero-lucena",
        "lucas-ribeiro_x_cicero-lucena",
    ],
    "resultado_por_par": {
        "efraim-filho_x_lucas-ribeiro": {
            "blocos_identicos": [
                {
                    "tamanho_caracteres": 3817,
                    "eixo_efraim": "Seção 25 — Segurança Pública e Defesa Civil",
                    "eixo_lucas": "Eixo 1 — Segurança Pública, Justiça e Proteção da Vida",
                    "citacao_abertura": (
                        "As propostas deste eixo constroem uma segurança "
                        "moderna e integrada: fortalecem a inteligência "
                        "policial e penitenciária, ampliam o monitoramento "
                        "tecnológico, articulam Polícia Militar, Polícia "
                        "Civil, Polícia Penal, Bombeiros, Defe…"
                    ),
                    "observacao": (
                        "Bloco cobre a introdução do eixo de segurança "
                        "inteira e os primeiros bullets de propostas "
                        "(incluindo o parágrafo sobre o novo prédio do "
                        "Instituto de Polícia Científica - IPC, a "
                        "reorganização do sistema prisional e o termo "
                        "'mulheridades', presente nos dois textos)."
                    ),
                },
                {
                    "tamanho_caracteres": 3362,
                    "eixo_efraim": "Seção 5 — Desenvolvimento Econômico",
                    "eixo_lucas": "Eixo 4 — Economia Produtiva, Inovação e Trabalho",
                    "citacao_abertura": (
                        "Este eixo propõe uma economia mais moderna, "
                        "inovadora e competitiva, capaz de impulsionar a "
                        "indústria, fortalecer a agropecuária, expandir o "
                        "turismo, dinamizar os polos regionais de "
                        "desenvolvimento e valorizar as cadeias produtiva…"
                    ),
                    "observacao": "Bloco cobre a introdução do eixo econômico/polos de desenvolvimento.",
                },
                {
                    "tamanho_caracteres": 2091,
                    "eixo_efraim": "Seção 17 — Meio Ambiente, Energia e Sustentabilidade",
                    "eixo_lucas": "Eixo 7 — Infraestrutura, Mobilidade e Sustentabilidade Ambiental",
                    "citacao_abertura": (
                        "As propostas são alinhadas aos ODS 1, 3, 4, 7, 10, "
                        "11, 14, 15 e 16. As propostas pactuadas para o "
                        "Eixo 7 reafirmam o compromisso de concluir grandes "
                        "obras estruturantes, ampliar a segurança hídrica, "
                        "modernizar a mobilidade urbana…"
                    ),
                    "observacao": (
                        "Bloco cobre o parágrafo de alinhamento aos ODS e o "
                        "fechamento do eixo de infraestrutura/meio "
                        "ambiente/segurança hídrica."
                    ),
                },
            ],
            "pct_texto_lucas_duplicado_de_efraim": 33.7,
            "pct_texto_efraim_duplicado_de_lucas": 12.2,
            "pct_texto_lucas_duplicado_de_efraim_em_palavras": 33.3,
            "pct_texto_efraim_duplicado_de_lucas_em_palavras": 11.3,
            "observacao": (
                "Este é o par com o compartilhamento de texto mais extenso "
                "e mais concentrado dos três: 3 blocos, somando "
                "~9.270-9.277 caracteres (~1.278 palavras) idênticos, "
                "distribuídos em 3 eixos temáticos diferentes (segurança, "
                "economia, meio ambiente/infraestrutura). Como o plano de "
                "Lucas Ribeiro é bem mais curto, esse volume representa "
                "cerca de 1/3 de todo o seu texto."
            ),
        },
        "efraim-filho_x_cicero-lucena": {
            "blocos_identicos": [
                {
                    "tamanho_caracteres": 1017,
                    "eixo_efraim": "Seção 25 — Segurança Pública e Defesa Civil",
                    "eixo_cicero": "Eixo 1 — Segurança Pública e Defesa Social",
                    "citacao_abertura": (
                        "Construir uma nova instalação para o Instituto de "
                        "Polícia Científica da Paraíba (IPC), com "
                        "laboratórios modernos, uma cadeia de custódia "
                        "digital e integração com bancos de dados "
                        "nacionais.\n- Reorganizar o sistema prisional com "
                        "con…"
                    ),
                    "observacao": (
                        "Mesmo parágrafo do IPC/sistema prisional/PCDA — "
                        "este trecho é idêntico nos TRÊS planos (Efraim, "
                        "Lucas e Cícero)."
                    ),
                },
            ],
            "pct_texto_efraim_duplicado_de_cicero": 1.3,
            "pct_texto_cicero_duplicado_de_efraim": 0.9,
            "observacao": (
                "O compartilhamento entre Efraim Filho e Cícero Lucena é "
                "pontual: apenas 1 bloco de ~1.017 caracteres, o mesmo "
                "parágrafo sobre o Instituto de Polícia Científica (IPC), "
                "reorganização do sistema prisional e segurança territorial "
                "que também aparece no plano de Lucas Ribeiro — ou seja, "
                "esse parágrafo específico é idêntico nos TRÊS planos "
                "analisados, não apenas no par Efraim x Lucas. Fora esse "
                "trecho, não foram encontrados outros blocos de 150+ "
                "caracteres idênticos entre esses dois planos."
            ),
        },
        "lucas-ribeiro_x_cicero-lucena": {
            "blocos_identicos": [
                {
                    "tamanho_caracteres": 4573,
                    "eixo_lucas": "Eixo 2 — Desenvolvimento Humano Integral e Bem-Estar Social / 2.1. Saúde",
                    "eixo_cicero": "Eixo 2 — Saúde",
                    "citacao_abertura": (
                        "Promover Políticas Públicas voltadas à atenção "
                        "primária e à atenção especializada.\n- Consolidar "
                        "o Centro Estadual de Regulação Hospitalar.\n- "
                        "Aprimorar a Rede de Apoio Institucional para a "
                        "qualificação e o matriciamento gerencial d…"
                    ),
                    "observacao": (
                        "Bloco cobre um trecho extenso de propostas de "
                        "saúde (regulação hospitalar, REAPQUALI, programas "
                        "especiais Opera Paraíba/Paraíba contra o Câncer/"
                        "Coração Paraibano/Saúde Digital). Este bloco NÃO "
                        "aparece no plano de Efraim Filho."
                    ),
                },
                {
                    "tamanho_caracteres": 1028,
                    "eixo_lucas": "Eixo 1 — Segurança Pública, Justiça e Proteção da Vida",
                    "eixo_cicero": "Eixo 1 — Segurança Pública e Defesa Social",
                    "citacao_abertura": (
                        "Construir uma nova instalação para o Instituto de "
                        "Polícia Científica da Paraíba (IPC), com "
                        "laboratórios modernos, uma cadeia de custódia "
                        "digital e integração com bancos de dados "
                        "nacionais.\n\n- Reorganizar o sistema prisional "
                        "com co…"
                    ),
                    "observacao": (
                        "Mesmo parágrafo do IPC/sistema prisional/PCDA "
                        "compartilhado também com Efraim Filho (ver bloco "
                        "de segurança acima) — ou seja, este trecho "
                        "específico é idêntico nos TRÊS planos."
                    ),
                },
                {
                    "tamanho_caracteres": 193,
                    "eixo_lucas": "Eixo 2 — Desenvolvimento Humano Integral e Bem-Estar Social (Esporte)",
                    "eixo_cicero": "Eixo (Esporte, antes do Eixo 11 — Gestão Pública)",
                    "citacao_abertura": (
                        "Criar programa dedicado à formação de "
                        "paratletas.\n- Ampliar a articulação e incentivos "
                        "para atrair eventos do calendário esportivo "
                        "nacional.\n- Concluir e equipar a Vila Olímpica de "
                        "Sousa.\n\nEIXO 3 — MU…"
                    ),
                    "observacao": (
                        "Trecho curto sobre política esportiva (paratletas, "
                        "calendário esportivo nacional, Vila Olímpica de "
                        "Sousa)."
                    ),
                },
            ],
            "pct_texto_lucas_duplicado_de_cicero": 21.0,
            "pct_texto_cicero_duplicado_de_lucas": 4.9,
            "observacao": (
                "Lucas Ribeiro e Cícero Lucena compartilham 3 blocos, "
                "totalizando ~5.788-5.794 caracteres idênticos — incluindo "
                "um bloco extenso (~4.573 caracteres) na área de Saúde que "
                "NÃO aparece no plano de Efraim Filho, e o mesmo parágrafo "
                "do IPC/sistema prisional que aparece nos três planos. Isso "
                "mostra que o fenômeno de texto compartilhado não é "
                "exclusivo do par Efraim x Lucas: ele também ocorre, em "
                "menor escala e em trechos parcialmente diferentes, entre "
                "Lucas e Cícero."
            ),
        },
    },
    "sintese_geral": (
        "A comparação sistemática dos três pares mostra que o fenômeno de "
        "texto idêntico não é exclusivo do par Efraim Filho x Lucas Ribeiro, "
        "mas é mais intenso nele: esse par concentra o maior volume de "
        "texto compartilhado (~9.270 caracteres / ~1.278 palavras em 3 "
        "blocos grandes, cobrindo 3 eixos temáticos inteiros). Já Lucas "
        "Ribeiro e Cícero Lucena compartilham um volume menor mas ainda "
        "relevante (~5.790 caracteres), com destaque para um bloco extenso "
        "na área de Saúde. Efraim Filho e Cícero Lucena compartilham apenas "
        "1 bloco pontual. Notavelmente, um mesmo parágrafo sobre o "
        "Instituto de Polícia Científica (IPC) aparece de forma idêntica "
        "nos TRÊS planos, sugerindo que pelo menos parte desse conteúdo "
        "pode circular como texto-base comum entre diferentes candidaturas "
        "(por exemplo, via consultoria/redator técnico compartilhado ou "
        "template de propostas de segurança pública usado por mais de uma "
        "campanha), e não apenas entre os dois planos citados na denúncia "
        "inicial."
    ),
    "observacao_editorial": (
        "Este achado documenta uma coincidência factual de texto entre "
        "planos de governo de candidaturas concorrentes — não há, nos dados "
        "aqui analisados, qualquer evidência sobre a causa ou sobre quem "
        "redigiu o quê primeiro. Antes de publicar qualquer nota sobre este "
        "achado, a redação deve buscar comentário das campanhas de Efraim "
        "Filho, Lucas Ribeiro e Cícero Lucena, já que uma explicação "
        "plausível é o uso de uma mesma consultoria, redator técnico ou "
        "template de propostas por mais de uma campanha (prática comum em "
        "planos de governo no Brasil) — não se deve caracterizar isso como "
        "plágio ou fraude sem essa checagem."
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
        corpo = motor.strip_header(raw_text)

        total_tokens, counts, top20 = motor.word_freq(corpo, ALL_STOPWORDS, top_n=20)
        agregado_counter.update(counts)

        pct, contagem_abs, segmentos_debug = motor.distribuicao_tematica_exaustiva(
            corpo, MARCADORES[slug]
        )

        be = motor.base_empirica_analise(corpo)

        wc_b64 = motor.gerar_wordcloud_png_b64(counts, slug, WC_DIR, ALL_STOPWORDS)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "vice": c["vice"],
            "categoria": c["categoria"],
            "status_fonte": "completo (fonte primária oficial)",
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

        debug_path = ANALISE_DIR / f"_debug_segmentos_{slug}.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            for marcador, tema, n in segmentos_debug:
                pct_seg = round(n / total_tokens * 100, 1) if total_tokens else 0.0
                f.write(f"[{tema:20s}] {n:6d} palavras ({pct_seg:5.1f}%) :: {marcador[:80]}\n")

        print(f"{c['nome']:<16} total={total_tokens:6d}  base_empirica={be['indice']:5.1f}%  "
              f"legado={be['indice_legado']:5.1f}%  (a={be['n_pilar_a_diagnostico']} "
              f"b={be['n_pilar_b_efeito']} c={be['n_pilar_c_evidencia_causal']} "
              f"/ retorica={be['n_retorica_sem_evidencia']} / compromisso_sem_base={be['n_compromisso_sem_base']})")
        soma_pct = round(sum(pct.values()), 1)
        print(f"  soma distribuicao_tematica_pct = {soma_pct}")

    top_agregado = agregado_counter.most_common(30)

    analise = {
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "10 de setembro de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo de cada plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo de cada documento, sem "
            "amostragem): cada plano foi lido integralmente e segmentado "
            "pelos seus próprios marcadores de seção reais — títulos de "
            "'EIXO N' (Cícero Lucena e Lucas Ribeiro), títulos de 'PARTE N'/"
            "'Seção N' (Efraim Filho) e subseções numeradas internas "
            "('2.1 Saúde', '4.3. Agropecuária e Agricultura Familiar' etc., "
            "usadas quando uma Parte/Eixo do documento original já reunia "
            "mais de um tema em subdivisões nomeadas). Cada segmento de "
            "texto entre dois marcadores consecutivos foi contado por "
            "inteiro (número de palavras) e atribuído a UM dos 9 rótulos da "
            "taxonomia comum do projeto — necessária porque os 3 planos "
            "usam estruturas de eixo diferentes entre si (16 eixos em "
            "Cícero, 25 áreas em 5 partes em Efraim, 7 eixos com subseções "
            "em Lucas), mas cobrem, em essência, assuntos equivalentes. A "
            "categoria 'outros' foi reservada estritamente para conteúdo "
            "genuinamente residual, sem tema programático próprio: cartas "
            "de abertura, sumário/índice, introduções gerais multitemáticas "
            "indivisíveis, texto de encerramento, e títulos/parágrafos de "
            "abertura de Partes/Eixos explicitamente multitemáticos por "
            "desenho."
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
            "'fortalecimento' etc.) contam como retórica sem evidência ou "
            "como compromisso sem lastro (quando a frase propõe uma ação "
            "concreta, via verbo de proposta — 'implementar', 'ampliar', "
            "'criar' etc. — mas sem nenhum dos três pilares). "
            "indice_base_empirica_pct usa como denominador trechos_com_base"
            "_empirica + trechos_de_compromisso_sem_base (o 'índice de "
            "cobertura', adotado centralmente em todo o projeto em "
            "25/08/2026, ver metodologia/indice_base_empirica/); "
            "indice_base_empirica_legado_pct preserva a fórmula anterior "
            "(denominador = trechos_com_base_empirica + "
            "trechos_retorica_sem_evidencia), mantida para trilha de "
            "auditoria. Heurística idêntica à usada em todos os outros "
            "estados do projeto, sem nenhum ajuste específico para a "
            "Paraíba."
        ),
        "metodologia_nota": (
            "A Paraíba foi o PRIMEIRO estado analisado neste projeto "
            "(17-25/08/2026) — por isso serviu de piloto para a própria "
            "metodologia, incluindo as duas rodadas de correção "
            "documentadas em `nordeste/analise_geral_ne/RELATORIO_"
            "COMPARATIVO.md` (Seção 9): a correção de regex de 20/08/2026 "
            "(pilar C amplo demais) e a validação estatística/migração de "
            "denominador de 25/08/2026 (segundo codificador, kappa de "
            "Cohen, migração para o índice de cobertura). Os três números "
            "publicados aqui já refletem ambas as correções — "
            "indice_base_empirica_pct de Cícero Lucena caiu de 15,1% "
            "(fórmula legada) para 7,5% nessa migração, a maior queda "
            "percentual do estudo do Nordeste. "
            "[Atualização de organização, 10/09/2026: até esta data, a "
            "Paraíba era o único dos 26 estados cobertos pelo projeto sem "
            "uma pasta dedicada em `brasil_2026/<regiao>/<estado>/` — a "
            "análise e o dashboard originais viviam num pipeline separado, "
            "fora do repositório do projeto (por terem sido o piloto, antes "
            "de o padrão de pasta por estado existir), e por isso a Paraíba "
            "não aparecia no seletor de estados do painel nacional. Esta "
            "migração recria a análise inteiramente através do motor "
            "compartilhado do projeto (`programs/motor_indice_base_"
            "empirica.py`), reaproveitando a mesma segmentação temática "
            "manual (MARCADORES_*) já validada — os números não mudam "
            "(reprodutibilidade verificada campo a campo antes da "
            "publicação desta migração), só a organização de pasta e a "
            "disponibilidade de um dashboard interativo acessível a partir "
            "do mapa nacional.]"
        ),
        "achado_texto_compartilhado": ACHADO_TEXTO_COMPARTILHADO,
        "texto_compartilhado": TEXTO_COMPARTILHADO,
        "lista_jargao_utilizada": motor.JARGAO_TERMOS,
    }

    out_path = ANALISE_DIR / "analise.json"
    out_path.write_text(
        __import__("json").dumps(analise, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
