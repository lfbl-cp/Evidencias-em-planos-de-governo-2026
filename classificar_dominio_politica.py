"""
Quebra o Índice de Base Empírica por área de política pública (saúde,
educação, segurança, economia), reaproveitando o texto já extraído das
propostas de governo -- sem precisar de dado novo.

Pedido do usuário (15/10/2026), decisão de método (17/10/2026, AskUserQuestion):
"topic modeling do texto das propostas para quebrar o índice por área de
política pública ... isso te dá uma segunda dimensão de achado para o artigo
('onde a base empírica é mais fraca') sem precisar de dado novo, só reaproveitar
o texto que você já extraiu." Entre classificação por dicionário (transparente,
auditável, mesma disciplina de validação do motor principal) e LDA/NMF
(descoberta não-supervisionada, mais instável e difícil de validar), o usuário
escolheu dicionário -- 4 áreas pré-definidas tornam isso natural, e mantém a
mesma metodologia determinística/auditável do resto do projeto.

Método: para cada candidatura, reextrai o texto (mesmo cache de OCR usado em
detectar_duplicatas_texto.py), quebra em frases (mesma lógica do motor
principal, split_sentences), e para cada frase classificada como
"com base empírica" (pilar A, B ou C -- mesmas funções do motor,
is_diagnostico/is_efeito/is_evidencia) OU "compromisso sem base" (PROPOSAL_RE
sem nenhum pilar -- o mesmo denominador do índice principal), verifica se a
frase cita algum termo de um dicionário de 4 áreas de política pública. Uma
frase pode contar para mais de uma área (ex. "reduzir a evasão escolar via
programa de renda" é educação E economia -- isso é esperado, não um bug).

índice_por_dominio(candidato, área) = n_base_área / (n_base_área + n_compromisso_área) * 100
-- mesma fórmula do índice geral (ver motor_indice_base_empirica.py linha ~566),
só que particionada por área. Candidato que NUNCA menciona uma área (denominador
0) fica com índice=None para essa área -- "não fala do tema" é dado faltante,
não índice zero (mesma disciplina do TEXTO_EXTRAIVEL em build_painel_multiciclo.py).

LIMITAÇÃO REGISTRADA: os dicionários abaixo não passaram pela mesma validação
formal por kappa (amostra de 204 frases + codificador LLM cego) que o motor
principal -- isso exigiria rotular uma nova amostra por área, não feito nesta
passada. Validação aqui é um audit manual de amostra (ver
analise/amostra_dominio_auditoria.json) -- tratar os achados por área como
exploratórios/descritivos para o artigo, não com o mesmo grau de confiança do
índice geral.

Uso: python3 classificar_dominio_politica.py
Saída:
  analise/indice_por_dominio.json -- uma linha por (ano, sq, área) com
    n_base, n_compromisso, indice
  analise/resumo_dominio_politica.json -- agregado por área/ciclo (e por área
    sozinha, todos os ciclos)
  analise/amostra_dominio_auditoria.json -- amostra aleatória de 10 frases por
    área para audit manual de face-validity
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

BASE = "/home/claude/brasil_multiciclo"
OCR_CACHE = f"{BASE}/ocr_cache"
ANOS = [2014, 2018, 2022, 2026]

# Dicionários por área -- termos em minúsculas, casados por substring (mesmo
# estilo do motor principal: re.search case-insensitive). Deliberadamente
# amplos o bastante para cobrir variação de redação, mas específicos o
# bastante para não invadir as outras 3 áreas sistematicamente.
DOMINIOS = {
    "saude": [
        r"sa[úu]de", r"hospital", r"\bubs\b", r"\bsus\b", r"\bleito", r"posto de sa[úu]de",
        r"aten[çc][ãa]o b[áa]sica", r"\buti\b", r"enfermage", r"enfermeir", r"m[ée]dic",
        r"medicament", r"farm[áa]c", r"vacin", r"mortalidade infantil", r"mortalidade materna",
        r"policl[íi]nic", r"\bcaps\b", r"\bsamu\b", r"ambul[âa]ncia", r"\bupa\b",
        r"doen[çc]a", r"epidemia", r"pandemia", r"\bcovid", r"dengue", r"atendimento m[ée]dico",
        r"\bexame\b", r"cirurgia", r"oncolog", r"sa[úu]de mental", r"psiqui[áa]tric",
        r"pronto[- ]socorro", r"pronto atendimento", r"agente comunit[áa]rio de sa[úu]de",
        r"consult[óo]rio", r"zoonose", r"vigil[âa]ncia sanit[áa]ria",
        # "saneamento" MOVIDO para meio_ambiente em 17/10/2026 (ver validação por kappa abaixo) --
        # ficava aqui, mas a maioria das frases sobre saneamento básico/marco legal do saneamento
        # fala de infraestrutura hídrica/ambiental, não de assistência à saúde propriamente.
    ],
    "educacao": [
        r"educa[çc][ãa]o", r"\bescola", r"ensino", r"\bcreche", r"pr[ée]-escola",
        r"alfabetiz", r"professor", r"docente", r"universidad", r"faculdade",
        r"ensino superior", r"ensino m[ée]dio", r"ensino fundamental", r"merenda escolar",
        r"\beja\b", r"\bideb\b", r"evas[ãa]o escolar", r"matr[íi]cula", r"vaga escolar",
        r"biblioteca", r"bolsa de estudo", r"\baluno", r"\baluna", r"pedag[óo]gic",
        r"educacional", r"escola.{0,20}tempo integral", r"\bfundeb\b", r"estudante",
    ],
    "seguranca": [
        r"seguran[çc]a p[úu]blica", r"pol[íi]cia", r"policial", r"policiamento",
        r"homic[íi]dio", r"criminalidade", r"\bcrime\b", r"viol[êe]ncia", r"delegacia",
        r"pres[íi]dio", r"penitenci[áa]ri", r"sistema prisional", r"bombeiro",
        r"guarda municipal", r"patrulha", r"tr[áa]fico de drogas", r"narcotr[áa]fico",
        r"feminic[íi]dio", r"\broubo\b", r"\bfurto\b", r"seguran[çc]a cidad[ãa]",
        r"intelig[êe]ncia policial", r"viatura", r"c[âa]meras? de (?:seguran[çc]a|monitoramento)",
        r"\bronda\b",
    ],
    "economia": [
        r"economia", r"emprego", r"desemprego", r"gera[çc][ãa]o de emprego", r"\brenda\b",
        r"\bpib\b", r"investimento", r"ind[úu]stria", r"agropecu[áa]ri", r"agroneg[óo]cio",
        r"turismo", r"com[ée]rcio", r"empresa", r"empreendedorismo", r"cr[ée]dito",
        r"financiamento", r"desenvolvimento econ[ôo]mico", r"arrecada[çc][ãa]o",
        r"\bimposto", r"tribut[áa]ri", r"\bicms\b", r"royalties", r"exporta[çc][ãa]o",
        r"produ[çc][ãa]o", r"setor produtivo", r"microempreendedor", r"mercado de trabalho",
        r"trabalho formal", r"trabalhador",
    ],
    # NOTA (17/10/2026): domínio adicionado a pedido do usuário -- "separe em
    # Educação, Segurança, Saúde, economia e meio ambiente". Termos escolhidos
    # para não invadir sistematicamente "economia" (agronegócio/agropecuária
    # ficam só em economia -- atividade econômica, não pauta ambiental; aqui
    # entram só termos de conservação/impacto ambiental propriamente ditos).
    # Evitado de propósito: "app" sozinho (quase sempre "aplicativo" em
    # português corrente, não "área de preservação permanente" -- ambíguo
    # demais pra valer o risco de falso-positivo).
    "meio_ambiente": [
        r"\bsaneamento", r"meio ambiente", r"sustentabilidade", r"sustent[áa]vel", r"desmatamento",
        r"reflorestamento", r"preserva[çc][ãa]o ambiental", r"unidade de conserva[çc][ãa]o",
        r"mudan[çc]a clim[áa]tica", r"aquecimento global", r"reciclagem", r"res[íi]duos s[óo]lidos",
        r"\blixo\b", r"aterro sanit[áa]rio", r"polui[çc][ãa]o", r"poluente",
        r"licenciamento ambiental", r"[áa]rea de preserva[çc][ãa]o", r"bacia hidrogr[áa]fica",
        r"biodiversidade", r"\bfauna\b", r"\bflora\b", r"queimada", r"inc[êe]ndio florestal",
        r"energia renov[áa]vel", r"energia solar", r"energia e[óo]lica", r"agroecologia",
        r"economia verde", r"recursos h[íi]dricos", r"gest[ãa]o ambiental", r"[óo]rg[ãa]o ambiental",
        r"[áa]rea verde", r"parque (?:natural|ambiental|estadual)",
    ],
}
import re
DOMINIO_RE = {d: re.compile("|".join(termos), re.IGNORECASE) for d, termos in DOMINIOS.items()}


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


def dominios_da_frase(s_low):
    return [d for d, rx in DOMINIO_RE.items() if rx.search(s_low)]


def main():
    random.seed(42)
    todos = []
    for ano in ANOS:
        with open(f"{BASE}/codificacao/indice_base_empirica_{ano}.json", encoding="utf-8") as f:
            regs = json.load(f)
        for r in regs:
            if r["N_PALAVRAS"] > 0:
                todos.append(r)

    print(f"Processando {len(todos)} candidaturas com texto extraível...", flush=True)

    linhas = []  # (ano, sq, dominio) -> contagens
    amostra_por_dominio = {d: [] for d in DOMINIOS}

    for i, r in enumerate(todos):
        ano, uf, sq = r["ANO"], r["SG_UF"], r["SQ_CANDIDATO"]
        texto = extrair_texto(ano, uf, sq, r["ARQUIVO_PDF"])
        sentences = split_sentences(texto)

        contagem = {d: {"n_base": 0, "n_compromisso": 0} for d in DOMINIOS}

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
            tem_compromisso_sem_base = (not tem_base) and bool(PROPOSAL_RE.search(s))

            if not (tem_base or tem_compromisso_sem_base):
                continue

            doms = dominios_da_frase(s_low)
            for d in doms:
                if tem_base:
                    contagem[d]["n_base"] += 1
                    if len(amostra_por_dominio[d]) < 60:
                        amostra_por_dominio[d].append({"ano": ano, "sq": sq, "tipo": "com_base", "frase": s.strip()})
                else:
                    contagem[d]["n_compromisso"] += 1

        for d, c in contagem.items():
            n_base, n_comp = c["n_base"], c["n_compromisso"]
            denom = n_base + n_comp
            indice_d = round(100 * n_base / denom, 1) if denom else None
            linhas.append({
                "ano": ano, "sq": sq, "uf": uf, "partido": None,  # preenchido abaixo via painel
                "dominio": d, "n_base": n_base, "n_compromisso": n_comp, "indice_dominio": indice_d,
            })

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(todos)} processadas...", flush=True)

    # junta partido via painel (para agregação por partido, se quiser depois)
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)
    # NOTA (17/10/2026): ANO do painel é int, mas `linha["ano"]` (vindo de
    # indice_base_empirica_<ano>.json) é string -- mesmo bug já documentado em
    # resumo_ciclo abaixo. Usar str(r["ANO"]) aqui para a chave bater (bug
    # encontrado nesta rodada: todo "partido" saía None antes desta correção).
    partido_por_ano_sq = {(str(r["ANO"]), r["SQ_CANDIDATO"]): r.get("SG_PARTIDO") for r in painel}
    for linha in linhas:
        linha["partido"] = partido_por_ano_sq.get((linha["ano"], linha["sq"]))

    with open(f"{BASE}/analise/indice_por_dominio.json", "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)

    # amostra para audit manual -- 10 frases aleatórias por área, das até-60 coletadas
    amostra_audit = {}
    for d, exs in amostra_por_dominio.items():
        amostra_audit[d] = random.sample(exs, min(10, len(exs)))
    with open(f"{BASE}/analise/amostra_dominio_auditoria.json", "w", encoding="utf-8") as f:
        json.dump(amostra_audit, f, ensure_ascii=False, indent=2)

    # resumo agregado: por área x ciclo, e por área (todos os ciclos)
    resumo_ciclo = []
    for d in DOMINIOS:
        for ano in ANOS:
            # NOTA (17/10/2026): ANO vem como string do JSON de origem
            # (indice_base_empirica_<ano>.json) -- comparar como str(ano), não
            # int, senão o filtro nunca bate (bug encontrado e corrigido nesta
            # mesma rodada: a primeira versão deu 0 candidatos em todo ciclo).
            vals = [l["indice_dominio"] for l in linhas if l["dominio"] == d and l["ano"] == str(ano) and l["indice_dominio"] is not None]
            n_fala = len(vals)
            n_total = sum(1 for l in linhas if l["dominio"] == d and l["ano"] == str(ano))
            resumo_ciclo.append({
                "dominio": d, "ano": ano, "n_candidatos_que_falam_do_tema": n_fala,
                "n_candidatos_total": n_total,
                "pct_que_falam_do_tema": round(100 * n_fala / n_total, 1) if n_total else None,
                "indice_medio": round(sum(vals) / len(vals), 2) if vals else None,
                "indice_mediano": round(sorted(vals)[len(vals) // 2], 2) if vals else None,
            })

    resumo_geral = []
    for d in DOMINIOS:
        vals = [l["indice_dominio"] for l in linhas if l["dominio"] == d and l["indice_dominio"] is not None]
        n_total = sum(1 for l in linhas if l["dominio"] == d)
        resumo_geral.append({
            "dominio": d, "n_candidatos_que_falam_do_tema": len(vals), "n_candidatos_total": n_total,
            "pct_que_falam_do_tema": round(100 * len(vals) / n_total, 1) if n_total else None,
            "indice_medio": round(sum(vals) / len(vals), 2) if vals else None,
            "indice_mediano": round(sorted(vals)[len(vals) // 2], 2) if vals else None,
        })
    resumo_geral.sort(key=lambda x: -(x["indice_medio"] or 0))

    with open(f"{BASE}/analise/resumo_dominio_politica.json", "w", encoding="utf-8") as f:
        json.dump({"por_ciclo": resumo_ciclo, "geral": resumo_geral}, f, ensure_ascii=False, indent=2)

    print("\n=== Índice médio por área de política pública (todos os ciclos) ===")
    print(f"{'área':<12}{'fala do tema':>14}{'% do total':>12}{'índice médio':>14}{'índice mediano':>16}")
    for r in resumo_geral:
        print(f"{r['dominio']:<12}{r['n_candidatos_que_falam_do_tema']:>14}{(r['pct_que_falam_do_tema'] or 0):>11.1f}%"
              f"{(r['indice_medio'] or 0):>14.2f}{(r['indice_mediano'] or 0):>16.2f}")

    print(f"\nSalvo em: {BASE}/analise/indice_por_dominio.json")
    print(f"Salvo em: {BASE}/analise/resumo_dominio_politica.json")
    print(f"Salvo em: {BASE}/analise/amostra_dominio_auditoria.json")


if __name__ == "__main__":
    main()
