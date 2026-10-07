#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica em producao (25/08/2026) as correcoes validadas na Fase 1/2 do
robustecimento do Indice de Base Empirica (ver RESULTADOS_FASE1_FASE2_25082026.md):

1) Remove "linha de base" de DIAG_KEYWORDS_RE (gatilho ambiguo, capturava
   descricao de sistema de monitoramento futuro, nao diagnostico existente)
2) Remove os gatilhos genericos "evidênci"/"comprovad" isolados de EVIDENCIA_RE
   (over-triggering em uso tecnico nao-politico) e adiciona CITACAO_RE (padrao
   de citacao academica "Estudo/Pesquisa NOME (FONTE, ANO)", cobre estudos
   nao nomeados na lista fixa de instituicoes)
3) Adiciona PROPOSAL_RE (verbos/expressoes de compromisso programatico) e
   muda o denominador do indice de "frases com jargao" para "frases de
   compromisso sem base empirica" (indice de cobertura) -- correlacao de
   Spearman 0.92 com o indice legado, mas cobre uma fatia mais representativa
   do texto. O calculo ANTERIOR e preservado em paralelo (indice_legado /
   n_retorica_sem_evidencia) para trilha de auditoria.

Testado contra a amostra de validacao de 265 frases (Fase 2): kappa agregado
sobe de 0.767 para 0.797. A correcao do pilar B (proximidade numero-verbo)
foi tambem testada e REJEITADA (piorava o kappa de 0.525 para 0.395) -- por
isso EFEITO_RE fica INALTERADO.

Aplica em 1 dos 25 scripts com estrutura identica de
build_analysis_*.py/analise/. Nao toca no piloto da Paraiba
(build_analysis_v3.py), que tem regex proprio e recebe correcao separada em
corrigir_pb.py. Nao roda main() nem escreve analise.json -- so edita o
codigo-fonte. Verifica, antes de escrever, que cada bloco-alvo aparece
exatamente 1 vez no arquivo (senao, aborta e reporta).
"""
import glob
import sys
from pathlib import Path

FILES = sorted(glob.glob("/home/claude/brasil_2026/*/*/analise/build_analysis_*.py"))
FILES = [f for f in FILES if "/replicacao/" not in f]

# ---------------------------------------------------------------------------
# Patch 1: DIAG_KEYWORDS_RE -- remove "linha de base"
# ---------------------------------------------------------------------------
OLD_DIAG = '''r"não contam com|não dispõe|não dispõem|não sabe ler|"
    r"abaixo da linha de pobreza|linha de base|posição no ranking|"'''
NEW_DIAG = '''r"não contam com|não dispõe|não dispõem|não sabe ler|"
    r"abaixo da linha de pobreza|posição no ranking|"'''

# nota: o termo "zee-ma|zee/ma" (Zoneamento Ecologico-Economico do
# MARANHAO) aparece em DIAG_KEYWORDS_RE/EVIDENCIA_RE de TODOS os 25
# arquivos canonicos, inclusive estados sem nenhuma relacao com o MA --
# artefato de copia da metodologia original do Maranhao/Ceara, carregado
# adiante sem limpeza. Nao faz parte desta rodada de correcao (nao afeta o
# kappa medido) -- registrado aqui soh para documentar que OLD_DIAG/OLD_EVID
# abaixo precisam bater com essa string tambem presente no arquivo real.

# ---------------------------------------------------------------------------
# Patch 2: EVIDENCIA_RE -- remove gatilhos genericos, adiciona CITACAO_RE,
# muda assinatura/corpo de is_evidencia
# ---------------------------------------------------------------------------
OLD_EVID = '''EVIDENCIA_RE = re.compile(
    r"\\b(a exemplo (?:d[eo]|da)|conforme (?:dados|estudos?|pesquisas?|levantamento|indicadores?)|"
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
    r"organização mundial da saúde|\\boms\\b|banco mundial|\\bbndes\\b|\\bbnb\\b|"
    r"plano nacional de logística|marco legal do saneamento|"
    r"lei nº|lei n°)\\b",
    re.IGNORECASE,
)


def is_evidencia(s_low: str) -> bool:
    return bool(EVIDENCIA_RE.search(s_low))'''

NEW_EVID = '''EVIDENCIA_RE = re.compile(
    r"\\b(a exemplo (?:d[eo]|da)|conforme (?:dados|estudos?|pesquisas?|levantamento|indicadores?)|"
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
    r"organização mundial da saúde|\\boms\\b|banco mundial|\\bbndes\\b|\\bbnb\\b|"
    r"plano nacional de logística|marco legal do saneamento|"
    r"lei nº|lei n°)\\b",
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
    r"(?:estudo|pesquisa|levantamento|relatório)\\s+[A-ZÀ-Ý][\\wÀ-ÿ\\s]{3,70}?"
    r"\\(\\s*[A-ZÀ-Ý]{2,15}(?:[\\s,][A-ZÀ-Ý][\\wÀ-ÿ]*)*,?\\s*\\d{4}\\s*\\)",
)


def is_evidencia(s_orig: str, s_low: str) -> bool:
    if EVIDENCIA_RE.search(s_low):
        return True
    if CITACAO_RE.search(s_orig):
        return True
    return False'''

# ---------------------------------------------------------------------------
# Patch 3: call site pc = is_evidencia(s_low) -> pc = is_evidencia(s.strip(), s_low)
# ---------------------------------------------------------------------------
OLD_CALL = "        pc = is_evidencia(s_low)"
NEW_CALL = "        pc = is_evidencia(s.strip(), s_low)"

# ---------------------------------------------------------------------------
# Patch 4: base_empirica_analise -- adiciona PROPOSAL_RE + compromisso_sem_base
# + indice_legado, muda o "indice" principal para denominador de cobertura
# ---------------------------------------------------------------------------
OLD_BE_TAIL = '''        if pa or pb or pc:
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
    }'''

NEW_BE_TAIL = '''        if pa or pb or pc:
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
    }'''

OLD_BE_HEAD = '''    sentences = split_sentences(text)
    com_a, com_b, com_c = [], [], []
    com_base = []
    retorica = []'''
NEW_BE_HEAD = '''    sentences = split_sentences(text)
    com_a, com_b, com_c = [], [], []
    com_base = []
    retorica = []
    compromisso_sem_base = []'''

PROPOSAL_RE_BLOCK = '''
# ADICIONADO (25/08/2026, validacao Fase 1/2): verbos/expressoes de
# compromisso programatico -- usado como o novo denominador do indice
# (substitui "frases com jargao" por "frases de compromisso/proposta", com
# ou sem jargao). E uma escolha de constructo alternativa, testada e
# validada contra a amostra de 265 frases (Spearman rho=0.92 com o indice
# legado) -- ver nota de metodologia.
PROPOSAL_RE = re.compile(
    r"\\b(implementar|implantar|criar|ampliar|garantir|construir|reduzir(?:emos|á)?|"
    r"aumentar|fortalecer|promover|desenvolver|expandir|instituir|estabelecer|"
    r"assegurar|viabilizar|elaborar|executar|investir|oferecer|disponibilizar|"
    r"realizar|instalar|modernizar|qualificar|capacitar|estimular|apoiar|"
    r"vamos |iremos |irá |será[- ]?(?:criad|implantad|construíd|ampliad)|"
    r"criação de|construção de|implantação de|ampliação de|modernização de|"
    r"reforma de|reforma do|reforma da|programa de|política de)\\b",
    re.IGNORECASE,
)

'''

# ---------------------------------------------------------------------------
# Patch 5: main() -- assembla os novos campos no analise.json
# ---------------------------------------------------------------------------
OLD_JSON_BLOCK = '''            "indice_base_empirica_pct": be["indice"],
            "indice_base_empirica_detalhe": {
                "n_trechos_com_base_empirica": be["n_com_base_empirica"],
                "n_trechos_retorica_sem_evidencia": be["n_retorica_sem_evidencia"],
                "n_pilar_a_diagnostico": be["n_pilar_a_diagnostico"],
                "n_pilar_b_efeito_mensuravel": be["n_pilar_b_efeito"],
                "n_pilar_c_evidencia_causal_externa": be["n_pilar_c_evidencia_causal"],
            },'''
NEW_JSON_BLOCK = '''            "indice_base_empirica_pct": be["indice"],
            "indice_base_empirica_legado_pct": be["indice_legado"],
            "indice_base_empirica_detalhe": {
                "n_trechos_com_base_empirica": be["n_com_base_empirica"],
                "n_trechos_retorica_sem_evidencia": be["n_retorica_sem_evidencia"],
                "n_trechos_compromisso_sem_base": be["n_compromisso_sem_base"],
                "n_pilar_a_diagnostico": be["n_pilar_a_diagnostico"],
                "n_pilar_b_efeito_mensuravel": be["n_pilar_b_efeito"],
                "n_pilar_c_evidencia_causal_externa": be["n_pilar_c_evidencia_causal"],
            },'''


PATCHES = [
    ("DIAG_KEYWORDS_RE (remove linha de base)", OLD_DIAG, NEW_DIAG),
    ("EVIDENCIA_RE + is_evidencia + CITACAO_RE", OLD_EVID, NEW_EVID),
    ("call site is_evidencia", OLD_CALL, NEW_CALL),
    ("base_empirica_analise: head (compromisso_sem_base)", OLD_BE_HEAD, NEW_BE_HEAD),
    ("base_empirica_analise: tail (indice_legado/indice novo)", OLD_BE_TAIL, NEW_BE_TAIL),
    ("main(): JSON block com novos campos", OLD_JSON_BLOCK, NEW_JSON_BLOCK),
]


def main():
    dry_run = "--apply" not in sys.argv
    ok, fail = [], []

    for f in FILES:
        src = open(f, encoding="utf-8").read()
        original = src
        problems = []

        for name, old, new in PATCHES:
            n = src.count(old)
            if n != 1:
                problems.append(f"  [{name}] ocorrencias={n} (esperado 1)")
            else:
                src = src.replace(old, new, 1)

        # insere o bloco PROPOSAL_RE logo antes de "def base_empirica_analise"
        marker = "\ndef base_empirica_analise("
        if src.count(marker) != 1:
            problems.append(f"  [insercao PROPOSAL_RE] marcador 'def base_empirica_analise(' ocorrencias={src.count(marker)}")
        else:
            src = src.replace(marker, PROPOSAL_RE_BLOCK.rstrip("\n") + "\n\n" + marker.lstrip("\n"), 1)
            # normaliza: o replace acima duplica a quebra de linha; corrige abaixo
            src = src.replace(PROPOSAL_RE_BLOCK.rstrip("\n") + "\n\n\ndef base_empirica_analise(",
                               PROPOSAL_RE_BLOCK.rstrip("\n") + "\n\n\ndef base_empirica_analise(")

        if problems:
            fail.append((f, problems))
            continue

        # valida que o resultado ainda e Python valido
        try:
            compile(src, f, "exec")
        except SyntaxError as e:
            fail.append((f, [f"  ERRO DE SINTAXE apos patch: {e}"]))
            continue

        ok.append(f)
        if not dry_run:
            open(f, "w", encoding="utf-8").write(src)

    print(f"{'[DRY RUN] ' if dry_run else ''}OK: {len(ok)}/{len(FILES)}")
    for f in ok:
        print("  ok:", f.split('/')[-1])
    if fail:
        print(f"\nFALHAS: {len(fail)}")
        for f, probs in fail:
            print(f" {f}")
            for p in probs:
                print(p)
    if dry_run:
        print("\n(dry run -- rode com --apply para escrever os arquivos)")


if __name__ == "__main__":
    main()
