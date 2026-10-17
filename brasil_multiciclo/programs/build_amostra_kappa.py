"""
Extrai frases de todas as propostas de governo (4 ciclos), classifica cada uma
com o motor determinístico (mesma lógica de base_empirica_analise), e monta
uma amostra estratificada por (ano, categoria) para servir de teste de
confiabilidade (kappa de Cohen) contra um segundo codificador (agente LLM).

Gera dois arquivos:
- kappa_amostra_cega.json  -> só {id, ano, uf, frase} (o que o codificador vê)
- kappa_gabarito.json      -> {id, ano, uf, frase, bucket, pilar_a, pilar_b, pilar_c}
  (gabarito do motor determinístico, NÃO deve ser mostrado ao codificador)

Uso: python3 build_amostra_kappa.py
"""
import json
import os
import random
import re
import subprocess
import sys

sys.path.insert(0, "/home/claude/brasil_multiciclo/programs")
from motor_indice_base_empirica import (
    split_sentences, looks_like_header, MIN_SENTENCE_WORDS,
    is_diagnostico, is_efeito, is_evidencia, JARGAO_TERMOS, PROPOSAL_RE,
)

random.seed(42)

ANOS = [2014, 2018, 2022, 2026]
BASE = "/home/claude/brasil_multiciclo"
SQ_RE = re.compile(r"\d{9,14}")
ALVO_POR_BUCKET = {"A": 10, "B": 10, "C": 10, "retorica": 8, "compromisso": 8, "neutro": 5}


def extrair_texto(caminho_pdf):
    try:
        r = subprocess.run(["pdftotext", "-layout", caminho_pdf, "-"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60)
        return r.stdout
    except Exception:
        return ""


def classificar_frases(texto):
    frases = []
    for s in split_sentences(texto):
        if looks_like_header(s):
            continue
        if len(s.split()) < MIN_SENTENCE_WORDS:
            continue
        s_low = s.lower()
        pa = is_diagnostico(s_low)
        pb = is_efeito(s_low)
        pc = is_evidencia(s.strip(), s_low)
        if pa:
            bucket = "A"
        elif pb:
            bucket = "B"
        elif pc:
            bucket = "C"
        elif any(t in s_low for t in JARGAO_TERMOS):
            bucket = "retorica"
        elif PROPOSAL_RE.search(s):
            bucket = "compromisso"
        else:
            bucket = "neutro"
        frases.append({"frase": s.strip(), "bucket": bucket, "pilar_a": pa, "pilar_b": pb, "pilar_c": pc})
    return frases


pool = {ano: {b: [] for b in ALVO_POR_BUCKET} for ano in ANOS}

for ano in ANOS:
    base_dir = f"{BASE}/propostas/{ano}"
    ufs = sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))
    for uf in ufs:
        pasta = f"{base_dir}/{uf}"
        pdfs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf") and f.lower() != "leiame.pdf"]
        for nome in sorted(pdfs):
            m = SQ_RE.findall(nome)
            sq = m[0] if m else None
            texto = extrair_texto(f"{pasta}/{nome}")
            if not texto.strip():
                continue
            for item in classificar_frases(texto):
                item["ano"] = ano
                item["uf"] = uf
                item["sq_candidato"] = sq
                item["arquivo"] = nome
                pool[ano][item["bucket"]].append(item)
    print(f"{ano}: pool coletado — " + ", ".join(f"{b}={len(pool[ano][b])}" for b in ALVO_POR_BUCKET))

amostra = []
idx = 0
for ano in ANOS:
    for bucket, alvo in ALVO_POR_BUCKET.items():
        candidatos = pool[ano][bucket]
        n = min(alvo, len(candidatos))
        escolhidos = random.sample(candidatos, n)
        for item in escolhidos:
            idx += 1
            item["id"] = f"S{idx:04d}"
            amostra.append(item)

random.shuffle(amostra)

cega = [{"id": it["id"], "ano": it["ano"], "uf": it["uf"], "frase": it["frase"]} for it in amostra]
gabarito = [{"id": it["id"], "ano": it["ano"], "uf": it["uf"], "frase": it["frase"],
             "bucket": it["bucket"], "pilar_a": it["pilar_a"], "pilar_b": it["pilar_b"],
             "pilar_c": it["pilar_c"], "arquivo": it["arquivo"], "sq_candidato": it["sq_candidato"]}
            for it in amostra]

os.makedirs(f"{BASE}/analise", exist_ok=True)
with open(f"{BASE}/analise/kappa_amostra_cega.json", "w", encoding="utf-8") as f:
    json.dump(cega, f, ensure_ascii=False, indent=2)
with open(f"{BASE}/analise/kappa_gabarito.json", "w", encoding="utf-8") as f:
    json.dump(gabarito, f, ensure_ascii=False, indent=2)

print(f"\nAmostra total: {len(amostra)} frases")
for ano in ANOS:
    sub = [it for it in amostra if it["ano"] == ano]
    print(f"  {ano}: {len(sub)} — " + ", ".join(f"{b}={sum(1 for it in sub if it['bucket']==b)}" for b in ALVO_POR_BUCKET))
print(f"\nSalvo: {BASE}/analise/kappa_amostra_cega.json (para o codificador)")
print(f"Salvo: {BASE}/analise/kappa_gabarito.json (gabarito, não mostrar ao codificador)")
