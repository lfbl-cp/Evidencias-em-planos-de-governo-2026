#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 1/2 do robustecimento do Índice de Base Empírica (25/08/2026).

Importa dinamicamente cada build_analysis_<uf>.py já publicado (sem executar
main() e sem escrever em nenhum arquivo do projeto) e reaplica a MESMA lógica
de classificação sentença-a-sentença (split_sentences / looks_like_header /
is_diagnostico / is_efeito / is_evidencia / JARGAO_TERMOS), reaproveitando os
objetos de regex de cada módulo (garante fidelidade exata às regras
publicadas, inclusive as 2 exceções documentadas — Bahia/BULLET_RE e o piloto
da Paraíba/DIAG_KEYWORDS_RE+EVIDENCIA_RE).

Diferença deliberada frente ao pipeline publicado: aqui classificamos o corpo
INTEIRO de cada plano (cursor_inicial=0 uniforme), sem replicar o corte de
front matter/sumário que cada main() aplica de forma bespoke por estado antes
da distribuição temática. Isso adiciona um pequeno número de frases de
capa/sumário à base amostral (não usadas na distribuição temática publicada),
mas não compromete a validação de confiabilidade do classificador — que é
sentence-level e agnóstica a em que seção do documento a frase está. Por
causa disso, os totais agregados aqui podem diferir ligeiramente (poucas
dezenas de frases em ~4.700) dos n_com_base_empirica/n_retorica_sem_evidencia
publicados em analise.json.

Saída: /home/claude/brasil_2026/metodologia/indice_base_empirica/frases_classificadas.jsonl
(uma linha JSON por frase classificada, com estado/slug/nome/pilares/retórica)
"""
import importlib.util
import glob
import json
import sys
from pathlib import Path

FILES = sorted(glob.glob("/home/claude/brasil_2026/*/*/analise/build_analysis_*.py")) + \
    ["/home/claude/pb2026_v2/analise/build_analysis_v3.py"]
# exclui a cópia de replicação do Ceará dentro de nordeste/replicacao (mesmo
# conteúdo do build_analysis_ce.py canônico, seria duplicata)
FILES = [f for f in FILES if "/replicacao/" not in f]

OUT_PATH = Path("/home/claude/brasil_2026/metodologia/indice_base_empirica/frases_classificadas.jsonl")


def load_module(path):
    spec = importlib.util.spec_from_file_location(f"mod_{Path(path).stem}_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_raw_text(mod, c):
    candidates = []
    if "arquivo" in c:
        candidates.append(c["arquivo"] if c["arquivo"].endswith(".txt") else f"{c['arquivo']}.txt")
    slug = c.get("slug", "")
    candidates += [f"{slug}.txt", f"{slug.replace('-', '_')}.txt", f"{slug.replace('_', '-')}.txt"]
    for cand in candidates:
        p = mod.PLANOS_DIR / cand
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Nenhum arquivo de plano encontrado para {c} em {mod.PLANOS_DIR} (tentativas: {candidates})")


def main():
    n_records = 0
    n_candidatos = 0
    errors = []
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for f in FILES:
            uf_state = Path(f).parent.parent.name  # .../<estado>/analise/build_analysis_x.py
            regiao = Path(f).parent.parent.parent.name
            try:
                mod = load_module(f)
            except Exception as e:
                errors.append((f, f"falha ao importar: {e}"))
                continue

            for c in mod.CANDIDATOS:
                try:
                    raw_text = find_raw_text(mod, c)
                except Exception as e:
                    errors.append((f, f"{c.get('slug')}: {e}"))
                    continue

                corpo = mod.strip_header(raw_text)
                sentences = mod.split_sentences(corpo)
                n_candidatos += 1

                for s in sentences:
                    if mod.looks_like_header(s):
                        continue
                    if len(s.split()) < mod.MIN_SENTENCE_WORDS:
                        continue
                    s_low = s.lower()
                    pa = bool(mod.is_diagnostico(s_low))
                    pb = bool(mod.is_efeito(s_low))
                    pc = bool(mod.is_evidencia(s_low))
                    jargoes = [t for t in mod.JARGAO_TERMOS if t in s_low]
                    com_base = pa or pb or pc
                    retorica = bool(jargoes) and not com_base

                    rec = {
                        "regiao": regiao,
                        "estado": uf_state,
                        "slug": c.get("slug"),
                        "nome": c.get("nome"),
                        "frase": s.strip(),
                        "pilar_a": pa,
                        "pilar_b": pb,
                        "pilar_c": pc,
                        "com_base": com_base,
                        "jargoes": jargoes,
                        "retorica_sem_evidencia": retorica,
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_records += 1

    print(f"OK. {n_records} frases classificadas de {n_candidatos} candidatos, salvas em {OUT_PATH}")
    if errors:
        print(f"\n{len(errors)} erro(s):")
        for f, e in errors:
            print(f"  {f}: {e}")


if __name__ == "__main__":
    main()
