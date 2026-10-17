"""
Roda o motor do Índice de Base Empírica (herdado do brasil_2026) sobre todos os
PDFs de "Proposta de Governo" de um ciclo, casando cada PDF com seu
SQ_CANDIDATO (via nome de arquivo) e salvando um CSV/JSON por ciclo.

Uso: python3 build_indice_base_empirica.py <ano>
"""
import csv
import json
import os
import re
import subprocess
import sys

from motor_indice_base_empirica import base_empirica_analise, tokenize

SQ_RE = re.compile(r"\d{9,14}")


def extrair_sq(nome_arquivo, uf):
    matches = SQ_RE.findall(nome_arquivo)
    return matches[0] if matches else None


OCR_CACHE_DIR = "/home/claude/brasil_multiciclo/ocr_cache"
os.makedirs(OCR_CACHE_DIR, exist_ok=True)


def extrair_texto_pdftotext(caminho_pdf):
    try:
        r = subprocess.run(
            ["pdftotext", "-layout", caminho_pdf, "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        return r.stdout
    except Exception:
        return ""


def extrair_texto_ocr(caminho_pdf, cache_key):
    """OCR via pdftoppm + tesseract (idioma por), com cache em disco -- OCR é
    lento (~1-2s/página), então cada PDF só é OCRizado uma vez. Usado como
    fallback quando pdftotext não extrai nada (PDF escaneado/imagem) -- ver
    NOTA em build_indice_base_empirica.py (correção de 09/10/2026)."""
    cache_path = f"{OCR_CACHE_DIR}/{cache_key}.txt"
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as tmp:
            prefix = f"{tmp}/page"
            subprocess.run(
                ["pdftoppm", "-r", "200", "-gray", caminho_pdf, prefix],
                capture_output=True, timeout=300,
            )
            paginas = sorted(f for f in os.listdir(tmp) if f.endswith(".pgm"))
            textos = []
            for pg in paginas:
                r = subprocess.run(
                    ["tesseract", f"{tmp}/{pg}", "-", "-l", "por", "--psm", "6"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=120,
                )
                textos.append(r.stdout)
            texto = "\n".join(textos)
    except Exception as e:
        texto = ""
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


def extrair_texto(caminho_pdf, cache_key):
    texto = extrair_texto_pdftotext(caminho_pdf)
    if len(tokenize(texto)) > 0:
        return texto, "pdftotext"
    texto_ocr = extrair_texto_ocr(caminho_pdf, cache_key)
    if len(tokenize(texto_ocr)) > 0:
        return texto_ocr, "ocr"
    return "", "sem_texto"


def main():
    ano = sys.argv[1] if len(sys.argv) > 1 else "2026"
    base_dir = f"/home/claude/brasil_multiciclo/propostas/{ano}"
    out_csv = f"/home/claude/brasil_multiciclo/codificacao/indice_base_empirica_{ano}.csv"
    out_json = f"/home/claude/brasil_multiciclo/codificacao/indice_base_empirica_{ano}.json"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    resultados = []
    erros = []

    ufs = sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))
    for uf in ufs:
        pasta = f"{base_dir}/{uf}"
        pdfs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf") and f.lower() != "leiame.pdf"]
        for nome in sorted(pdfs):
            sq = extrair_sq(nome, uf)
            if sq is None:
                erros.append((uf, nome, "sem SQ_CANDIDATO reconhecível no nome"))
                continue
            caminho = f"{pasta}/{nome}"
            cache_key = f"{ano}_{uf}_{sq}"
            texto, fonte_texto = extrair_texto(caminho, cache_key)
            n_palavras = len(tokenize(texto))
            if n_palavras == 0:
                erros.append((uf, nome, "sem texto extraível mesmo após OCR (PDF ilegível/corrompido?)"))
            elif fonte_texto == "ocr":
                erros.append((uf, nome, f"OCR aplicado (pdftotext vazio) — {n_palavras} palavras extraídas"))
            analise = base_empirica_analise(texto, ano_ciclo=int(ano))
            linha = {
                "ANO": ano,
                "SG_UF": uf,
                "SQ_CANDIDATO": sq,
                "ARQUIVO_PDF": nome,
                "N_PALAVRAS": n_palavras,
                "FONTE_TEXTO": fonte_texto,
            }
            # remove os campos de exemplos (frases) do CSV plano; ficam só no JSON
            for k, v in analise.items():
                if not k.startswith("exemplos_"):
                    linha[k] = v
            linha["_exemplos"] = {k: v for k, v in analise.items() if k.startswith("exemplos_")}
            resultados.append(linha)

    print(f"=== Índice de Base Empírica — {ano} ===")
    print(f"PDFs processados: {len(resultados)}")
    print(f"Erros/avisos: {len(erros)}")
    for uf, nome, msg in erros:
        print(f"  [{uf}] {nome}: {msg}")

    if resultados:
        indices = [r["indice"] for r in resultados]
        print(f"\nÍndice médio: {sum(indices)/len(indices):.1f}")
        print(f"Índice mediano: {sorted(indices)[len(indices)//2]:.1f}")
        palavras = [r["N_PALAVRAS"] for r in resultados]
        print(f"Palavras por plano — mín: {min(palavras)}, máx: {max(palavras)}, média: {sum(palavras)/len(palavras):.0f}")

    campos_csv = ["ANO", "SG_UF", "SQ_CANDIDATO", "ARQUIVO_PDF", "N_PALAVRAS", "FONTE_TEXTO",
                  "indice", "indice_legado", "n_com_base_empirica",
                  "n_retorica_sem_evidencia", "n_compromisso_sem_base",
                  "n_pilar_a_diagnostico", "n_pilar_b_efeito", "n_pilar_c_evidencia_causal"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos_csv)
        writer.writeheader()
        for r in resultados:
            writer.writerow({k: r.get(k, "") for k in campos_csv})

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em: {out_csv}")
    print(f"Salvo em: {out_json}")


if __name__ == "__main__":
    main()
