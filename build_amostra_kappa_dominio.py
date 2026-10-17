"""
Amostra para validação por kappa da classificação por área de política pública
(programs/classificar_dominio_politica.py) -- pedido do usuário (17/10/2026):
"vamos validar por kappa".

Mesma lógica de reextração de texto/frases do script principal, mas em vez de
só contar, guarda uma amostra ALEATÓRIA (reservoir sampling, não só as
primeiras encontradas) de:
  - até 25 frases "com base" por área (das que o dicionário classificou nessa
    área) -- testa precisão (frases que o dicionário disse ser da área X, são
    mesmo da área X?).
  - até 30 frases "com base" que o dicionário NÃO classificou em NENHUMA área
    -- testa recall/falso-negativo (o dicionário está deixando passar frases
    que deveriam ter sido marcadas com alguma área?).

Saída: analise/amostra_kappa_dominio_gabarito.json -- cada item com um "id"
sequencial (S0001...), a frase, e o rótulo do DICIONÁRIO (lista de áreas ou
[] se nenhuma) -- isso é o "gabarito" atual do motor por dicionário, a ser
comparado com uma rotulagem cega (sem ver este arquivo) feita por um
agente/codificador separado.

Uso: python3 build_amostra_kappa_dominio.py
"""
import json
import os
import random
import subprocess
import sys

sys.path.insert(0, "/home/claude/brasil_multiciclo/programs")
from motor_indice_base_empirica import (  # noqa: E402
    is_diagnostico, is_efeito, is_evidencia, looks_like_header,
    split_sentences, MIN_SENTENCE_WORDS, PROPOSAL_RE,
)
from classificar_dominio_politica import DOMINIOS, dominios_da_frase  # noqa: E402

BASE = "/home/claude/brasil_multiciclo"
OCR_CACHE = f"{BASE}/ocr_cache"
ANOS = [2014, 2018, 2022, 2026]
N_POR_DOMINIO = 25
N_SEM_DOMINIO = 30


def extrair_texto(ano, uf, sq, arquivo):
    cache_path = f"{OCR_CACHE}/{ano}_{uf}_{sq}.txt"
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()
    caminho = f"{BASE}/propostas/{ano}/{uf}/{arquivo}"
    try:
        r = subprocess.run(["pdftotext", "-layout", caminho, "-"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60)
        return r.stdout
    except Exception:
        return ""


class Reservoir:
    """Reservoir sampling (Algoritmo R) -- amostra uniforme de tamanho k de um
    stream de tamanho desconhecido de antemão, sem guardar tudo em memória."""
    def __init__(self, k):
        self.k = k
        self.n = 0
        self.sample = []

    def add(self, item):
        self.n += 1
        if len(self.sample) < self.k:
            self.sample.append(item)
        else:
            j = random.randint(0, self.n - 1)
            if j < self.k:
                self.sample[j] = item


def main():
    random.seed(7)
    todos = []
    for ano in ANOS:
        with open(f"{BASE}/codificacao/indice_base_empirica_{ano}.json", encoding="utf-8") as f:
            regs = json.load(f)
        for r in regs:
            if r["N_PALAVRAS"] > 0:
                todos.append(r)

    print(f"Processando {len(todos)} candidaturas...", flush=True)

    reservoirs = {d: Reservoir(N_POR_DOMINIO) for d in DOMINIOS}
    reservoir_sem_dominio = Reservoir(N_SEM_DOMINIO)

    for i, r in enumerate(todos):
        ano, uf, sq = r["ANO"], r["SG_UF"], r["SQ_CANDIDATO"]
        texto = extrair_texto(ano, uf, sq, r["ARQUIVO_PDF"])
        sentences = split_sentences(texto)

        for s in sentences:
            if looks_like_header(s):
                continue
            if len(s.split()) < MIN_SENTENCE_WORDS:
                continue
            s_low = s.lower()
            pa = is_diagnostico(s_low)
            pb = is_efeito(s, s_low, ano_ciclo=int(ano))
            pc = is_evidencia(s.strip(), s_low)
            tem_base = pa or pb or pc
            if not tem_base:
                continue  # só nos interessa a classificação de domínio das frases COM base

            doms = dominios_da_frase(s_low)
            item = {"ano": ano, "sq": sq, "uf": uf, "frase": s.strip(), "dominios_dicionario": doms}
            if doms:
                for d in doms:
                    reservoirs[d].add(item)
            else:
                reservoir_sem_dominio.add(item)

        if (i + 1) % 150 == 0:
            print(f"  {i+1}/{len(todos)}...", flush=True)

    amostra = []
    seq = 1
    vistos = set()
    for d, res in reservoirs.items():
        for item in res.sample:
            chave = (item["ano"], item["sq"], item["frase"])
            if chave in vistos:
                continue
            vistos.add(chave)
            amostra.append({"id": f"S{seq:04d}", **item})
            seq += 1
    for item in reservoir_sem_dominio.sample:
        chave = (item["ano"], item["sq"], item["frase"])
        if chave in vistos:
            continue
        vistos.add(chave)
        amostra.append({"id": f"S{seq:04d}", **item})
        seq += 1

    random.shuffle(amostra)

    with open(f"{BASE}/analise/amostra_kappa_dominio_gabarito.json", "w", encoding="utf-8") as f:
        json.dump(amostra, f, ensure_ascii=False, indent=2)

    # versão "cega" para o codificador -- só id + frase, sem o rótulo do dicionário
    cega = [{"id": item["id"], "frase": item["frase"]} for item in amostra]
    with open(f"{BASE}/analise/amostra_kappa_dominio_cega.json", "w", encoding="utf-8") as f:
        json.dump(cega, f, ensure_ascii=False, indent=2)

    print(f"\nAmostra total: {len(amostra)} frases "
          f"({sum(1 for a in amostra if a['dominios_dicionario'])} com domínio pelo dicionário, "
          f"{sum(1 for a in amostra if not a['dominios_dicionario'])} sem domínio pelo dicionário)")
    print(f"Salvo em: {BASE}/analise/amostra_kappa_dominio_gabarito.json (com rótulo do dicionário)")
    print(f"Salvo em: {BASE}/analise/amostra_kappa_dominio_cega.json (sem rótulo -- para o codificador cego)")


if __name__ == "__main__":
    main()
