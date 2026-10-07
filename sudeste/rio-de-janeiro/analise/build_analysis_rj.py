#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Analista — Rio de Janeiro 2026.

Réplica da metodologia usada no Ceará (build_analysis_ce.py), que por sua vez
replicou a metodologia do Maranhão e da Paraíba: distribuição temática
exaustiva por segmentação de marcadores de seção reais (lidos e mapeados à
mão) e Índice de Base Empírica (heurística lexical/regex idêntica aos demais
estados, reaproveitada sem alterações para manter comparabilidade).

Reorganização v2 (28/08/2026): o motor (tokenização, stopwords base, os 3
pilares do Índice de Base Empírica e a geração de nuvem de palavras) foi
extraído para `programs/motor_indice_base_empirica.py`, reutilizado por todos
os estados. Este script mantém só o que é de fato específico do Rio de
Janeiro: CANDIDATOS, a segmentação temática (MARCADORES_*, obra de leitura
humana) e o texto narrativo (metodologia_nota). Ver o módulo compartilhado
para a verificação de que essa extração não mudou nenhum número publicado.

*** ATUALIZAÇÃO (09/09/2026): EDUARDO PAES ENTRA NA ANÁLISE, GAROTINHO SEGUE PENDENTE ***
Entre 25/08/2026 (última checagem registrada abaixo) e 09/09/2026, o plano de
governo de Eduardo Paes (PSD) passou a fazer parte da análise — o arquivo
chegou ao pesquisador diretamente em PDF ("pje-Plano de governo Eduardo Paes
2026.pdf"), sem confirmação de que já tenha sido formalmente protocolado no
TSE (ao contrário de Douglas Ruas, cujo PDF traz o padrão de nome de arquivo
do CDN oficial do TSE), rotulado no próprio documento como "VERSÃO PRELIMINAR
DO PROGRAMA DE GOVERNO":
8 páginas, carta de abertura + 5 compromissos + lista de ~15 propostas
pontuais, sem a granularidade/extensão dos planos "Eixo a Eixo" de outros
candidatos do projeto (ver nota sobre tamanho do documento em
"metodologia_nota"). O RJ passa a ter 2 candidatos nesta rodada: Douglas Ruas
(PL) e Eduardo Paes (PSD). Anthony Garotinho (Republicanos) segue SEM proposta
de governo localizada nesta data — pesquisa dedicada em 09/09/2026 (notícias +
portal de dados abertos do TSE) não encontrou confirmação de protocolo; sua
própria elegibilidade seguia sub judice no TSE na mesma data (ver
"metodologia_nota" para os detalhes e fontes). RJ segue, portanto, coberto
apenas por 2 dos 3 nomes mais competitivos nas pesquisas.

*** HISTÓRICO: SITUAÇÃO ATÉ 25/08/2026 (mantido para trilha de auditoria) ***
Até a checagem de 25/08/2026, o RJ tinha um único candidato analisável:
Douglas Ruas (PL). Segundo pesquisas Datafolha de 18-21/08/2026, os 2 nomes
mais competitivos ao governo do RJ eram Eduardo Paes (PSD, 41%, líder
disparado) e Douglas Ruas (PL, 19%, 2º lugar); um 3º nome, Anthony Garotinho
(Republicanos), aparecia com 9%. Checagem no portal de dados abertos do TSE
(proposta_governo_2026_RJ.zip) mostrou que, até aquela data, Eduardo Paes e
Anthony Garotinho AINDA NÃO haviam registrado proposta de governo em PDF
junto ao TSE — só Douglas Ruas tinha documento disponível. Decisão editorial
do pesquisador responsável na época: analisar o RJ apenas com Douglas Ruas,
documentando a ausência dos outros dois com destaque, e atualizar a análise
quando Paes/Garotinho registrassem suas propostas — o que agora ocorreu
parcialmente (Paes) em 09/09/2026.

Sobre a categoria de Douglas Ruas: ele foi Secretário de Estado de Cidades no
governo de Cláudio Castro (2023–mar/2026) e, em março de 2026, foi eleito
presidente da Alerj. Cláudio Castro renunciou ao cargo de governador em
março/2026 e foi declarado inelegível até 2030 pelo TSE — não é candidato a
nada em 2026. Embora a linha sucessória constitucional apontasse inicialmente
para Douglas Ruas (presidente da Alerj) assumir o governo interinamente, o
STF, em abril/2026, negou pedido da Alerj nesse sentido e manteve o
desembargador presidente do Tribunal de Justiça do RJ como governador
interino — precisamente para evitar que um pré-candidato ao pleito de 2026
(Douglas Ruas) governasse o Estado durante a própria campanha. Ou seja:
Douglas Ruas NÃO é vice-governador, não é sucessor formal de Castro no cargo
e não está no Executivo estadual hoje — é candidato do PL/bolsonarismo, que
herdou o espaço político (e o eleitorado) de Castro, mas não o cargo. Por
isso foi classificado como "desafiante" (challenger), e não como incumbente
ou como parte de um "governo em exercício" — ver "categoria" abaixo, com
fontes.
"""
import json
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
        "slug": "douglas_ruas",
        "nome": "Douglas Ruas",
        "partido": "PL",
        "vice": "Fernanda Louback",
        "categoria": (
            "desafiante — não é o governador em exercício nem o sucessor formal "
            "de Cláudio Castro. Douglas Ruas foi Secretário de Estado de Cidades "
            "no governo Castro (2023–mar/2026) e, em março de 2026, foi eleito "
            "presidente da Alerj. Castro renunciou ao governo em março/2026 e foi "
            "declarado inelegível até 2030 pelo TSE (não concorre a nada em "
            "2026). Embora a linha sucessória constitucional apontasse "
            "inicialmente para o presidente da Alerj assumir o governo "
            "interinamente, o STF negou pedido da Alerj nesse sentido em "
            "abril/2026 e manteve o desembargador presidente do TJ-RJ como "
            "governador interino, justamente para que um pré-candidato ao "
            "pleito de 2026 não governasse o Estado durante a própria campanha. "
            "Douglas Ruas herdou o espaço político e o eleitorado bolsonarista "
            "de Castro, mas não o cargo — concorre como desafiante em um "
            "Executivo estadual hoje sob interinidade judicial, não político-"
            "partidária. Fontes: Agência Brasil "
            "(https://agenciabrasil.ebc.com.br/politica/noticia/2026-03/entenda-o-que-acontece-no-rio-com-renuncia-de-claudio-castro , "
            "https://agenciabrasil.ebc.com.br/justica/noticia/2026-04/tse-publica-acordao-que-condenou-castro-inelegibilidade-ate-2030); "
            "TSE (https://www.tse.jus.br/comunicacao/noticias/2026/Marco/tse-torna-inelegivel-ex-governador-do-rio-claudio-castro); "
            "STF (https://noticias.stf.jus.br/postsnoticias/stf-nega-pedido-da-alerj-e-mantem-desembargador-como-governador-interino-do-rio-de-janeiro/); "
            "Congresso em Foco "
            "(https://www.congressoemfoco.com.br/noticia/117604/douglas-ruas-e-eleito-presidente-da-alerj-e-deve-assumir-governo-do-rj , "
            "https://www.congressoemfoco.com.br/noticia/118343/tse-reconhece-renuncia-de-castro-e-deixa-eleicao-no-rj-nas-maos-do-stf)."
        ),
    },
    {
        "slug": "eduardo_paes",
        "nome": "Eduardo Paes",
        "partido": "PSD",
        "vice": "Jane Reis",
        "categoria": (
            "desafiante — foi prefeito da cidade do Rio de Janeiro (4 mandatos, "
            "o mais recente iniciado em 2021) até deixar o cargo para concorrer "
            "ao governo do estado em 2026; não ocupa nem ocupou cargo no "
            "Executivo estadual, então concorre como desafiante ao governo em "
            "exercício, não como incumbente ou sucessor."
        ),
    },
]

# ---------------------------------------------------------------------------
# TAREFA 1 — Distribuição temática exaustiva
# ---------------------------------------------------------------------------
# Douglas Ruas ("Plano do Rio Real 2027-2030"): documento em PDF de 51
# páginas, com Sumário próprio (página 3-4) que NÃO repete os títulos reais
# usados como marcador (usa numeração/grafia levemente diferente: "Eixo 01"
# em vez de "Eixo 1", "Rio seguro" minúsculo em vez de "Rio\nSeguro", e a
# página "Apresentação dos Eixos" usa "EIXO 1" em versalete dentro de um
# diagrama, também distinto do marcador real "Eixo 1"). Verificado
# programaticamente que cada marcador usado abaixo ocorre exatamente o
# número de vezes esperado no arquivo (1x para a maioria; 2x para as seções
# "Compromissos" que se estendem por duas páginas sob o mesmo título) — não
# houve colisão com o Sumário nem com a página de diagrama dos eixos, então,
# ao contrário do Ceará/Maranhão, NÃO foi necessário nenhum cursor_inicial
# de correção (usa-se 0, ponto de partida real do corpo do documento).
#
# Estrutura real do documento: Capa → Carta de Compromisso (carta de
# abertura) → Sumário → Introdução → Apresentação dos Eixos (diagrama) →
# Eixo 1 "Rio Seguro" → Eixo 2 "Rio que Cuida" → Eixo 3 "Rio Próspero" →
# Eixo 4 "Rio que Avança" → Considerações Finais.
#
# Front matter (capa) fica automaticamente em "outros" (texto antes do 1º
# marcador). O 1º marcador, "Carta de\nCompromisso", também foi classificado
# como "outros": ele abre um segmento que inclui a própria carta de
# compromisso, o Sumário e a Introdução, e a página de Apresentação dos
# Eixos — nenhum desses tem conteúdo temático próprio atribuível a um único
# tema da taxonomia de 9 (a carta de abertura fala de segurança, saúde,
# educação e economia na mesma respiração; a Introdução resume os 4 eixos em
# bloco).
#
# Eixo 1 "Rio Seguro" é inteiramente monotemático (o próprio eixo já é
# "segurança pública") — por isso um único marcador ("Eixo 1") cobre o
# divisor + texto de diagnóstico + todas as 8 subseções de "Compromissos"
# (Escudo Fluminense, Cerco Financeiro, Linha Dura, Retomada do Estado, Mapa
# Único de Manchas Criminais, Rio por Elas: Segurança e Respeito, Gestão
# Integrada por Resultados, Polícia Forte/Policial Valorizado), todas
# classificadas como "seguranca".
#
# Eixo 2 "Rio que Cuida" cruza saúde, educação, habitação e assistência
# social sob um único rótulo — precisou de segmentação por subseção
# "Compromissos": o divisor + texto de diagnóstico introdutório (que mistura
# explicitamente saúde, educação e habitação num único parágrafo
# indivisível) foi classificado como "outros"; "Fila Curta, Cirurgia
# Rápida", "Saúde Perto de Casa" e "Saúde Integral da Mulher" = "saude";
# "Atenção à Pessoa com Espectro Autista" mistura diagnóstico/terapia em
# saúde com inclusão escolar, mas o núcleo da seção é cuidado e rede de
# apoio a uma população vulnerável (moldes semelhantes à seção "proteção e
# bem-estar animal"/"segurança alimentar" tratadas como assistência social
# em outros estados do projeto) — classificada como "assistencia_social";
# "Aprendizagem Nota 10" (2 páginas) e "Escola Protegida" = "educacao";
# "Propriedade Garantida e Segura" (política habitacional) = "infraestrutura",
# seguindo o precedente do Ceará/Maranhão/Paraíba de tratar habitação como
# infraestrutura; "Políticas Sociais e Autonomia" = "assistencia_social".
#
# Eixo 3 "Rio Próspero" é majoritariamente "economia": o divisor + texto de
# diagnóstico e as subseções "Investe Aqui", "Todo o Rio Crescendo", "Da
# Serra ao Mar" (2 páginas — turismo, economia do mar, bioeconomia), "Rio
# Criativo" (economia criativa/audiovisual — aqui tratada como "economia",
# não como "assistencia_social"/cultura genérica, porque a seção é
# explicitamente enquadrada como setor econômico gerador de emprego e renda,
# ao contrário de seções de cultura de outros planos do projeto que tratam
# cultura como política de acesso/identidade), "Empreende RJ" (2 páginas) e
# "Agro Grande" = "economia". Uma subseção, "RJ Integrado" (2 páginas), trata
# de infraestrutura econômica (rodovias, ferrovias, portos, energia,
# conectividade digital) e foi classificada como "infraestrutura", seguindo
# o mesmo precedente usado no Ceará de tratar conteúdo de infraestrutura
# física como "infraestrutura" mesmo quando aparece dentro de um eixo
# nominalmente econômico.
#
# Eixo 4 "Rio que Avança" cruza infraestrutura, mobilidade e meio ambiente —
# o próprio texto de abertura do eixo anuncia essa mistura explicitamente
# ("Reunimos aqui as políticas de infraestrutura, mobilidade e meio
# ambiente"), por isso o divisor + diagnóstico introdutório foi classificado
# como "outros" (indivisível). As subseções de infraestrutura/mobilidade
# ("Estado Parceiro das Cidades" [2 páginas], "Novos Corredores de
# Mobilidade", "Bilhete Único", "Rodovias RJ", "Concessões: Serviços que
# Funcionam" [2 páginas, inclui saneamento]) = "infraestrutura"; as
# subseções ambientais ("Proteção Contra Tragédias" — prevenção de
# desastres/eventos climáticos, e "RJ Verde Produtivo" [2 páginas] —
# resíduos, proteção animal, energia renovável) = "meio_ambiente".
MARCADORES_DOUGLAS_RUAS = [
    ("Carta de\nCompromisso", "outros"),
    ("Eixo 1", "seguranca"),
    ("Eixo 2", "outros"),
    ("Compromissos\nFILA CURTA, CIRURGIA RÁPIDA", "saude"),
    ("Compromissos\nSAÚDE PERTO DE CASA", "saude"),
    ("Compromissos\nSAÚDE INTEGRAL DA MULHER", "saude"),
    ("Compromissos\nATENÇÃO À PESSOA COM", "assistencia_social"),
    ("Compromissos\nAPRENDIZAGEM NOTA 10", "educacao"),
    ("Compromissos\nAPRENDIZAGEM NOTA 10", "educacao"),
    ("Compromissos\nESCOLA PROTEGIDA", "educacao"),
    ("Compromissos\nPROPRIEDADE GARANTIDA E SEGURA", "infraestrutura"),
    ("Compromissos\nPOLÍTICAS SOCIAIS E AUTONOMIA", "assistencia_social"),
    ("Eixo 3", "economia"),
    ("Compromissos\nINVESTE AQUI", "economia"),
    ("Compromissos\nTODO O RIO CRESCENDO", "economia"),
    ("Compromissos\nRJ INTEGRADO", "infraestrutura"),
    ("Compromissos\nRJ INTEGRADO", "infraestrutura"),
    ("Compromissos\nDA SERRA AO MAR", "economia"),
    ("Compromissos\nDA SERRA AO MAR", "economia"),
    ("Compromissos\nRIO CRIATIVO", "economia"),
    ("Compromissos\nEMPREENDE RJ", "economia"),
    ("Compromissos\nEMPREENDE RJ", "economia"),
    ("Compromissos\nAGRO GRANDE", "economia"),
    ("Eixo 4", "outros"),
    ("Compromissos\nESTADO PARCEIRO DAS CIDADES", "infraestrutura"),
    ("Compromissos\nESTADO PARCEIRO DAS CIDADES", "infraestrutura"),
    ("Compromissos\nNOVOS CORREDORES DE MOBILIDADE", "infraestrutura"),
    ("Compromissos\nBILHETE ÚNICO", "infraestrutura"),
    ("Compromissos\nRODOVIAS RJ", "infraestrutura"),
    ("Compromissos\nCONCESSÕES: SERVIÇOS", "infraestrutura"),
    ("Compromissos\nCONCESSÕES: SERVIÇOS", "infraestrutura"),
    ("Compromissos\nPROTEÇÃO CONTRA TRAGÉDIAS", "meio_ambiente"),
    ("Compromissos\nRJ VERDE PRODUTIVO", "meio_ambiente"),
    ("Compromissos\nRJ VERDE PRODUTIVO", "meio_ambiente"),
    ("Considerações\nFinais", "outros"),
]

# ---------------------------------------------------------------------------
# TAREFA 1b — Distribuição temática exaustiva: Eduardo Paes
# ---------------------------------------------------------------------------
# Documento curto (8 páginas, ~1955 palavras) e rotulado no próprio texto como
# "VERSÃO PRELIMINAR DO PROGRAMA DE GOVERNO" — sem a estrutura "Eixo a Eixo"
# de outros candidatos do projeto. Estrutura real: Capa → Carta de Abertura
# (diagnóstico geral, mistura segurança/saúde/educação/transporte/corrupção
# numa única narrativa indivisível) → "O que eu vi" (relato de viagens pelo
# interior, genérico) → "Por que assumo esta missão" (biografia/mandatos como
# prefeito, não temático) → "Os compromissos que assumimos" (5 compromissos
# em prosa corrida, cada um com um título de 1 frase seguido de parágrafo(s))
# → assinatura → "Compromissos centrais do governo Eduardo Paes" (lista de
# ~15 bullets que detalham os mesmos 5 compromissos, um por bullet ou grupo
# de bullets).
#
# Front matter (capa) cai automaticamente em "outros" (texto antes do 1º
# marcador). Carta de Abertura + O Que Eu Vi + Por Que Assumo Esta Missão +
# a frase de transição "Assumimos esses compromissos..." antes do 1º
# compromisso nomeado foram classificados como "outros": são diagnóstico e
# biografia explicitamente multitemáticos (a própria Carta de Abertura fala
# de violência, saúde, educação e transporte no mesmo fôlego), sem frase
# atribuível a um único tema — mesmo critério usado nos outros estados do
# projeto para introduções mistas e indivisíveis.
#
# Dos 5 compromissos nomeados: "Devolver a segurança..." = seguranca (tema
# único). "Melhorar a qualidade dos serviços públicos de saúde, educação e
# transporte." é um título que já anuncia mistura de 3 temas — o título em si
# foi classificado como "outros" (só a frase-título, sem conteúdo próprio),
# e os 3 parágrafos que o seguem SÃO separáveis por tema (cada um começa
# tratando de um assunto só: hospitais/UPAs = saude; ensino técnico/Faetecs =
# educacao; Supervia/BRT/Metrô/estradas = infraestrutura, mesmo critério de
# tratar transporte/mobilidade como infraestrutura usado em todo o projeto).
# "Destravar a economia..." = economia (tema único, título+parágrafo juntos).
# "Governar para todos e em parceria com todos os municípios." (repasses,
# relação com prefeituras) e "Colocar a máquina pública estadual em ordem."
# (finanças, capacidade de planejar/fiscalizar) = gestao_publica (gestão e
# relação intergovernamental, não uma política setorial). O parágrafo de
# fechamento ("Assumimos esses compromissos com uma condição...") é
# rhetórico/genérico = outros.
#
# Na lista de bullets ("Compromissos centrais..."): o próprio título da
# seção = outros (divisor, sem conteúdo). Bullets de segurança (violência,
# crime organizado, indicação política em cargos de PM/PC) = seguranca;
# bullets de saúde (hospitais/UPAs, rede em regiões distantes, médicos e
# remédios) = saude; bullet de ensino técnico = educacao; o bullet sobre
# apoiar prefeituras "na educação inclusiva e na assistência às famílias de
# crianças com autismo" mistura educação e assistência social — classificado
# como assistencia_social, mesmo precedente usado no plano de Douglas Ruas
# para o bullet equivalente sobre espectro autista (cuidado/rede de apoio a
# população vulnerável, não conteúdo pedagógico em si); bullet de atração de
# empresas/investimento = economia; bullets de transporte metropolitano,
# Linha 3 do metrô e recuperação de estradas = infraestrutura; bullet sobre
# plano de obras contra enchentes/deslizamentos = meio_ambiente (único
# conteúdo ambiental explícito do documento); bullets de contas públicas e de
# parceria com os 92 prefeitos/Conselho das Cidades = gestao_publica.
MARCADORES_EDUARDO_PAES = [
    ("CARTA DE ABERTURA", "outros"),
    ("Devolver a segurança e o direito de ir e vir das pessoas.", "seguranca"),
    ("Melhorar a qualidade dos serviços públicos de saúde, educação e\ntransporte.", "outros"),
    ("Recuperar os hospitais e UPAs estaduais", "saude"),
    ("Ampliar o ensino técnico profissionalizante em tempo integral, fazer as Faetecs", "educacao"),
    ("No transporte, vamos colocar a Supervia", "infraestrutura"),
    ("Destravar a economia para gerar mais oportunidades de trabalho e renda.", "economia"),
    ("Governar para todos e em parceria com todos os municípios.", "gestao_publica"),
    ("Colocar a máquina pública estadual em ordem.", "gestao_publica"),
    ("Assumimos esses compromissos com uma condição", "outros"),
    ("Compromissos centrais\ndo governo Eduardo Paes", "outros"),
    ("Reduzir a violência no estado", "seguranca"),
    ("Estancar o crescimento territorial do crime organizado", "seguranca"),
    ("Eliminar imediatamente as indicações de políticos", "seguranca"),
    ("Recuperar os serviços públicos de saúde do estado", "saude"),
    ("Ampliar a rede e o atendimento nas regiões distantes", "saude"),
    ("Contratar mais médicos e especialistas e oferecer", "saude"),
    ("Expandir o ensino médio profissionalizante em tempo integral", "educacao"),
    ("Apoiar as prefeituras na educação inclusiva", "assistencia_social"),
    ("Fazer o estado voltar a atrair empresas", "economia"),
    ("Investir na melhoria do transporte metropolitano", "infraestrutura"),
    ("Iniciar as obras da Linha 3 do metrô", "infraestrutura"),
    ("Recuperar as estradas do interior", "infraestrutura"),
    ("Implantar um grande plano de obras para combater as enchentes", "meio_ambiente"),
    ("Colocar as contas públicas em ordem", "gestao_publica"),
    ("Governar em parceria com os prefeitos dos 92 municípios", "gestao_publica"),
]

MARCADORES = {
    "douglas_ruas": MARCADORES_DOUGLAS_RUAS,
    "eduardo_paes": MARCADORES_EDUARDO_PAES,
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

        marcadores = MARCADORES[slug]
        # Diferente do Ceará/Maranhão, o plano de Douglas Ruas não repete o
        # 1º marcador num sumário (verificado: 'Carta de\nCompromisso'
        # ocorre exatamente 1 vez no documento), então cursor_inicial = 0.
        cursor_inicial = 0

        pct, contagem_abs, segmentos_debug = motor.distribuicao_tematica_exaustiva(
            corpo, marcadores, cursor_inicial=cursor_inicial
        )

        be = motor.base_empirica_analise(corpo[cursor_inicial:])

        wc_b64 = motor.gerar_wordcloud_png_b64(counts, slug, WC_DIR, ALL_STOPWORDS)

        entry = {
            "slug": slug,
            "nome": c["nome"],
            "partido": c["partido"],
            "vice": c["vice"],
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

    analise_anterior = {}
    out_path = ANALISE_DIR / "analise.json"
    if out_path.exists():
        analise_anterior = json.loads(out_path.read_text(encoding="utf-8"))

    analise = {
        **analise_anterior,
        "candidatos": resultado_candidatos,
        "top_palavras_agregado": [{"palavra": w, "freq": f} for w, f in top_agregado],
        "gerado_em": "9 de setembro de 2026",
        "metodologia_frequencia_palavras": (
            "Contagem de todas as palavras do corpo do plano (após o "
            "cabeçalho padronizado), com remoção de stopwords do português e "
            "de termos estruturais do próprio documento (ex.: 'candidato', "
            "'governo', 'eleições'). A lista de stopwords estruturais é a "
            "mesma usada em todos os estados do projeto (inclui termos "
            "específicos de outro estado, como 'maranhão'/'maranhense', "
            "mantidos propositalmente sem ajuste para preservar "
            "comparabilidade metodológica entre estados). Mostra os termos "
            "mais repetidos no plano. Até 09/09/2026 esta rodada do RJ tinha "
            "apenas 1 candidato, e o 'top_palavras_agregado' era idêntico ao "
            "'top_palavras' do único candidato; com a entrada de Eduardo "
            "Paes, o agregado passa a somar as duas listas de frequência."
        ),
        "metodologia_distribuicao_tematica": (
            "Classificação exaustiva (100% do corpo do documento, sem "
            "amostragem): o plano foi lido integralmente e segmentado por "
            "seus marcadores de seção reais (títulos de eixo/bloco de "
            "'Compromissos'). Cada segmento de texto entre dois marcadores "
            "consecutivos foi contado (em número de palavras) e atribuído a "
            "UM dos 9 temas. Quando um trecho do documento original já "
            "reunia explicitamente múltiplos temas de forma indivisível "
            "(ex.: os textos de abertura dos Eixos 2 e 4, que anunciam a "
            "mistura de saúde/educação/habitação ou infraestrutura/meio "
            "ambiente em um único parágrafo), o segmento foi classificado "
            "como 'outros'."
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
            "Paraíba, sem nenhum ajuste específico para o Rio de Janeiro, "
            "para manter comparabilidade entre estados."
        ),
        "metodologia_nota": (
            "*** ATENÇÃO — CASO ESPECIAL: RODADA COM APENAS 1 CANDIDATO. *** "
            "Ao contrário de todos os demais estados do projeto, esta análise "
            "do Rio de Janeiro cobre um ÚNICO candidato — Douglas Ruas (PL). "
            "Isso NÃO é uma escolha de amostragem, é um reflexo do estágio "
            "do registro de propostas de governo no TSE nesta data de coleta "
            "(24/08/2026). "
            "Segundo pesquisas Datafolha de 18 a 21/08/2026, os 2 candidatos "
            "mais competitivos ao governo do RJ em 2026 são Eduardo Paes "
            "(PSD), líder disparado com 41% das intenções de voto, e Douglas "
            "Ruas (PL), em 2º lugar com 19%; um 3º nome, Anthony Garotinho "
            "(Republicanos), aparece com 9%. Ao verificar o portal de dados "
            "abertos do TSE (arquivo proposta_governo_2026_RJ.zip, "
            "cdn.tse.jus.br), constatou-se que, nesta data, Eduardo Paes e "
            "Anthony Garotinho AINDA NÃO haviam registrado proposta de "
            "governo em PDF junto ao TSE — apenas Douglas Ruas possui "
            "documento oficial disponível (2026RJ190002542887_01.pdf, 51 "
            "páginas). Sem o documento-fonte primário, não há como aplicar a "
            "mesma metodologia de análise textual a Paes ou a Garotinho nesta "
            "rodada. "
            "Decisão do pesquisador responsável pelo projeto: publicar a "
            "análise do RJ apenas com Douglas Ruas nesta rodada, documentando "
            "essa ausência com destaque (inclusive no dashboard do estado), e "
            "atualizar a análise assim que Eduardo Paes e/ou Anthony "
            "Garotinho registrarem suas propostas de governo — o prazo "
            "eleitoral para esse registro ainda não se encerrou. Até lá, "
            "qualquer leitura comparativa envolvendo o RJ (ex.: rankings "
            "entre estados por índice de base empírica) deve ter em mente "
            "que o candidato líder nas pesquisas para o cargo NÃO está "
            "representado nesta análise. "
            "Sobre a categoria de Douglas Ruas: ver o campo 'categoria' do "
            "candidato, com fontes — em resumo, ele não é o governador em "
            "exercício nem o sucessor formal de Cláudio Castro (que renunciou "
            "em março/2026 e foi declarado inelegível até 2030 pelo TSE); o "
            "STF manteve um desembargador (presidente do TJ-RJ) como "
            "governador interino, negando pedido para que o presidente da "
            "Alerj (cargo ocupado por Douglas Ruas desde março/2026) "
            "assumisse o Executivo durante a campanha. Douglas Ruas concorre, "
            "portanto, como desafiante. "
            "Sobre a segmentação temática: o plano de Douglas Ruas é "
            "organizado em 4 'Eixos' com subseções tituladas 'Compromissos', "
            "sem o problema de sumário duplicado encontrado no Ceará/"
            "Maranhão — os marcadores usados aqui foram verificados "
            "programaticamente contra o texto extraído para confirmar que "
            "cada um ocorre exatamente o número de vezes esperado antes de "
            "compor a lista final (ver comentários no script). Decisões de "
            "classificação não óbvias — 'Atenção à Pessoa com Espectro "
            "Autista' como assistência social (não saúde nem educação, "
            "apesar de cruzar as duas); 'Rio Criativo' (economia criativa) "
            "como economia (não como cultura/assistência social, diferente "
            "do tratamento dado a seções de cultura genérica em outros "
            "planos do projeto, porque aqui a seção é enquadrada "
            "explicitamente como setor econômico gerador de emprego e "
            "renda); habitação ('Propriedade Garantida e Segura') como "
            "infraestrutura, seguindo o precedente do Ceará/Maranhão/"
            "Paraíba — estão documentadas linha a linha nos comentários do "
            "script de análise. "
            "ADENDO (verificação posterior): o PDF de Douglas Ruas (51 "
            "páginas) tem diagramação em duas colunas com um artefato de "
            "extração que intercala trechos de colunas adjacentes linha a "
            "linha no .txt — mesmo tipo de defeito já documentado no Ceará "
            "(Ciro Gomes) e no Centro-Oeste (Otaviano Pivetta/MT, Daniel "
            "Vilela/GO). Isso fragmenta bastante as frases na etapa de "
            "split_sentences (código canônico, idêntico em todo o "
            "projeto), o que pode contribuir para o Índice de Base "
            "Empírica particularmente baixo deste candidato (1,0%: apenas "
            "1 trecho com base empírica contra 96 de retórica sem "
            "evidência) — não corrigido, para manter a metodologia "
            "idêntica entre estados, mas registrado aqui como limitação "
            "conhecida da extração, não uma característica do conteúdo do "
            "plano em si. "
            "[Reverificação (25/08/2026): checagem direta do arquivo "
            "proposta_governo_2026_RJ.zip no CDN do TSE (regenerado pelo "
            "TSE em 24/08/2026, 07:02) confirma que a situação permanece "
            "inalterada — o zip contém 8 documentos de propostas de "
            "governo para o RJ (André Marinho/Novo, Coronel Busnello/"
            "Missão, Cyro Garcia/PSTU, Douglas Ruas/PL, Juliete/UP, Luan "
            "Monteiro/PCO, William Siri/PSOL, mais um arquivo aparentemente "
            "mal classificado como proposta de Deputada Estadual), mas "
            "NENHUM de Eduardo Paes (PSD) nem de Anthony Garotinho "
            "(Republicanos) — apesar de ambos aparecerem como candidatos a "
            "GOVERNADOR oficialmente registrados no cadastro do TSE após o "
            "encerramento do prazo de registro (15/08/2026). Ou seja, "
            "registro de candidatura e envio de proposta de governo em PDF "
            "são etapas distintas no TSE, e a segunda ainda está pendente "
            "para os dois nomes mais competitivos da corrida. Esta análise "
            "continua cobrindo apenas Douglas Ruas até que isso mude.] "
            "[Atualização (09/09/2026): o plano de governo de Eduardo Paes "
            "(PSD) passou a integrar a análise. O PDF foi recebido pelo "
            "pesquisador diretamente da campanha ('pje-Plano de governo "
            "Eduardo Paes 2026.pdf'), sem confirmação de que já tenha sido "
            "formalmente protocolado no TSE — diferente de Douglas Ruas, cujo "
            "PDF traz o padrão de nome de arquivo do CDN oficial do TSE. O "
            "documento "
            "é curto (8 páginas, ~1.955 palavras no corpo) e se apresenta, no "
            "próprio texto, como 'VERSÃO PRELIMINAR DO PROGRAMA DE GOVERNO' — "
            "uma carta de abertura, 5 compromissos em prosa corrida e uma "
            "lista de ~15 propostas pontuais, sem o detalhamento 'Eixo a "
            "Eixo' de outros planos do projeto (o de Douglas Ruas tem 51 "
            "páginas). Isso importa para a leitura do índice: o diagnóstico "
            "de sensibilidade a tamanho do documento (ver "
            "NOTAS_METODOLOGICAS_PENDENTES.md, testes de 28/08/2026) mostrou "
            "que a correlação entre tamanho e Índice de Base Empírica é real "
            "e substantiva, não um artefato de medição — ou seja, um "
            "documento estruturalmente curto como este tende a ter menos "
            "oportunidade de conter trechos com base empírica, "
            "independentemente do estilo do candidato, e essa leitura deve "
            "acompanhar qualquer comparação do índice de Eduardo Paes com "
            "candidatos que enviaram planos mais longos e detalhados. A "
            "segmentação temática do texto (sem marcadores de eixo próprios) "
            "foi feita por parágrafo/bullet, documentada linha a linha nos "
            "comentários do script. Anthony Garotinho (Republicanos) segue "
            "SEM proposta de governo localizada: busca dedicada em "
            "09/09/2026 (cobertura de imprensa + portal de dados abertos do "
            "TSE) não encontrou confirmação de protocolo; a própria "
            "elegibilidade de Garotinho seguia sub judice no TSE nesta data "
            "(decisão do TRE-RJ de 27/08/2026 restringindo a campanha dele "
            "foi revertida pelo TSE em 29/08/2026, mas o mérito do registro "
            "continuava em julgamento, sem prazo definido). O RJ permanece, "
            "portanto, coberto por 2 dos 3 nomes mais competitivos nas "
            "pesquisas de agosto/2026 (Paes e Ruas), com Garotinho ainda de "
            "fora — a análise será atualizada novamente se/quando ele "
            "registrar sua proposta.]"
        ),
        "lista_jargao_utilizada": motor.JARGAO_TERMOS,
    }

    out_path.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    main()
