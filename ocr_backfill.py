"""
Pré-processa (via OCR) todos os PDFs sem texto extraível por pdftotext, populando
o cache em OCR_CACHE_DIR (ver extrair_texto_ocr em build_indice_base_empirica.py)
antes de rodar o pipeline principal. Rodar isso uma vez evita que o reprocessamento
dos 4 ciclos (build_indice_base_empirica.py <ano>, 4x) refaça OCR do zero.

Usa multiprocessing (poucos workers, já que o ambiente tem poucas CPUs) para não
levar ~80min sequenciais. Lê a lista de arquivos a partir do próprio diretório
propostas/<ano>/<UF>/, tentando pdftotext primeiro (pula o que já tem texto ou já
está em cache) -- não depende de uma lista hardcoded de "falhas conhecidas", porque
a lista exata já mudou uma vez neste projeto (ex: arquivos adicionados depois).

Uso: python3 ocr_backfill.py
Progresso: imprime cada arquivo conforme termina, com tempo e nº de palavras.
"""
import os
import sys
import time
from multiprocessing import Pool

from build_indice_base_empirica import extrair_texto_pdftotext, extrair_texto_ocr, extrair_sq
from motor_indice_base_empirica import tokenize

ANOS = ["2014", "2018", "2022", "2026"]
BASE = "/home/claude/brasil_multiciclo/propostas"


def listar_candidatos():
    tarefas = []
    for ano in ANOS:
        base_dir = f"{BASE}/{ano}"
        if not os.path.isdir(base_dir):
            continue
        for uf in sorted(os.listdir(base_dir)):
            pasta = f"{base_dir}/{uf}"
            if not os.path.isdir(pasta):
                continue
            for nome in sorted(os.listdir(pasta)):
                if not nome.lower().endswith(".pdf") or nome.lower() == "leiame.pdf":
                    continue
                sq = extrair_sq(nome, uf)
                if sq is None:
                    continue
                caminho = f"{pasta}/{nome}"
                cache_key = f"{ano}_{uf}_{sq}"
                cache_path = f"/home/claude/brasil_multiciclo/ocr_cache/{cache_key}.txt"
                if os.path.exists(cache_path):
                    continue  # já processado (OCR já tentado, com ou sem sucesso)
                texto = extrair_texto_pdftotext(caminho)
                if len(tokenize(texto)) > 0:
                    continue  # pdftotext já resolve, não precisa de OCR
                tarefas.append((ano, uf, nome, caminho, cache_key))
    return tarefas


def worker(tarefa):
    ano, uf, nome, caminho, cache_key = tarefa
    t0 = time.time()
    texto = extrair_texto_ocr(caminho, cache_key)
    dt = time.time() - t0
    n = len(tokenize(texto))
    return (ano, uf, nome, dt, n)


def main():
    tarefas = listar_candidatos()
    print(f"Total de PDFs para OCR (pdftotext vazio, ainda sem cache): {len(tarefas)}", flush=True)
    if not tarefas:
        print("Nada a fazer.", flush=True)
        return
    t0 = time.time()
    with Pool(processes=2) as pool:
        for i, (ano, uf, nome, dt, n) in enumerate(pool.imap_unordered(worker, tarefas), 1):
            status = "OK" if n > 0 else "SEM TEXTO (OCR falhou)"
            print(f"[{i}/{len(tarefas)}] {ano} {uf} {nome}: {dt:.1f}s, {n} palavras -- {status}", flush=True)
    print(f"Concluído em {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
