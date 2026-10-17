"""
Junta censo + proposta de governo (índice de base empírica) + resultado
eleitoral dos 4 ciclos (2014, 2018, 2022, 2026) numa única tabela-painel,
uma linha por candidatura a governador.

Incumbência é derivada automaticamente: para (ano, UF), olha quem foi
ELEITO no ciclo anterior (ano-4) naquele mesmo estado (via NR_CPF_CANDIDATO,
que — ao contrário de SQ_CANDIDATO — identifica a MESMA PESSOA entre
ciclos) e marca se o candidato atual é essa mesma pessoa. 2014 não tem
ciclo anterior nos nossos dados (2010 fora do escopo), então incumbência
fica marcada como indisponível (None) para 2014.

Uso: python3 build_painel_multiciclo.py
"""
import csv
import json
import os

ANOS = [2014, 2018, 2022, 2026]
BASE = "/home/claude/brasil_multiciclo"


def carregar(ano, subpasta, arquivo):
    caminho = f"{BASE}/{subpasta}/{ano}/derivados/{arquivo}_{ano}.json" if "derivados" not in arquivo else None
    return caminho


def load_json(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


censo = {ano: load_json(f"{BASE}/dados_tse/{ano}/derivados/censo_governador_{ano}.json") for ano in ANOS}
indice = {ano: load_json(f"{BASE}/codificacao/indice_base_empirica_{ano}.json") for ano in ANOS}
resultados = {ano: load_json(f"{BASE}/dados_tse/{ano}/derivados/resultados_governador_{ano}.json") for ano in ANOS}

# NOTA (15/10/2026): cluster de texto quase-idêntico (template de partido reusado entre
# candidatos/estados/ciclos) -- ver CLAUDE.md "duplicação de template infla N de alguns
# partidos" e programs/detectar_duplicatas_texto.py. Usado para que qualquer agregação por
# partido possa contar textos únicos (N efetivo), não candidaturas nominais, quando a
# diferença importar (caso notório: PCO, 42 candidaturas -> 7 textos únicos).
clusters_texto = load_json(f"{BASE}/analise/clusters_texto.json")
if isinstance(clusters_texto, list):  # load_json devolve [] se o arquivo ainda não existe
    clusters_texto = {}

# --- lookup de eleito por (ano, uf) -> CPF, a partir do próprio censo ---
eleito_cpf = {}
for ano in ANOS:
    for c in censo[ano]:
        if c.get("DS_SIT_TOT_TURNO") == "ELEITO":
            eleito_cpf[(ano, c["SG_UF"])] = c.get("NR_CPF_CANDIDATO")

# --- índices auxiliares para join ---
indice_por_ano_sq = {}
for ano in ANOS:
    for r in indice[ano]:
        indice_por_ano_sq[(ano, r["SQ_CANDIDATO"])] = r

resultado_por_ano_sq = {}
for ano in ANOS:
    for r in resultados[ano]:
        resultado_por_ano_sq[(ano, r["SQ_CANDIDATO"])] = r

painel = []
for ano in ANOS:
    for c in censo[ano]:
        sq = c["SQ_CANDIDATO"]
        uf = c["SG_UF"]
        idx = indice_por_ano_sq.get((ano, sq))
        res = resultado_por_ano_sq.get((ano, sq))

        cpf_incumbente = eleito_cpf.get((ano - 4, uf))
        if ano == 2014:
            incumbente = None  # sem dado de 2010 no escopo deste projeto
        else:
            incumbente = (cpf_incumbente is not None and cpf_incumbente == c.get("NR_CPF_CANDIDATO"))

        linha = {
            "ANO": ano,
            "SG_UF": uf,
            "SQ_CANDIDATO": sq,
            "NR_CPF_CANDIDATO": c.get("NR_CPF_CANDIDATO"),
            "NM_URNA_CANDIDATO": c.get("NM_URNA_CANDIDATO"),
            "SG_PARTIDO": c.get("SG_PARTIDO"),
            "DS_SITUACAO_CANDIDATURA": c.get("DS_SITUACAO_CANDIDATURA"),
            "DS_SIT_TOT_TURNO": c.get("DS_SIT_TOT_TURNO"),
            "FOI_A_2_TURNO": c.get("FOI_A_2_TURNO"),
            "INCUMBENTE": incumbente,
            "DS_GENERO": c.get("DS_GENERO"),
            "DS_COR_RACA": c.get("DS_COR_RACA"),
            "DS_GRAU_INSTRUCAO": c.get("DS_GRAU_INSTRUCAO"),
            "VOTOS_TURNO_1": res.get("VOTOS_TURNO_1") if res else None,
            "VOTOS_TURNO_2": res.get("VOTOS_TURNO_2") if res else None,
            "TEM_PROPOSTA_DE_GOVERNO": idx is not None,
            "N_PALAVRAS_PROPOSTA": idx.get("N_PALAVRAS") if idx else None,
            # NOTA (09/10/2026): TEXTO_EXTRAIVEL distingue "entregou PDF mas não conseguimos
            # ler o texto nem com OCR" (N_PALAVRAS==0 — 3 casos: 2 PDFs corrompidos sem
            # trailer/xref válido + 1 PDF do Word sem texto nem imagem extraível) de um
            # índice genuinamente zero. Não forçamos INDICE_BASE_EMPIRICA para None nesses
            # casos (manter o valor que o motor calculou, por disciplina de nunca
            # sobrescrever silenciosamente) — mas qualquer agregação (média, mediana) deve
            # filtrar por TEXTO_EXTRAIVEL==True antes de usar o índice, senão esses 3 casos
            # de dado faltante são contados como "zero empírico" por engano.
            "FONTE_TEXTO": idx.get("FONTE_TEXTO") if idx else None,
            "TEXTO_EXTRAIVEL": (idx.get("N_PALAVRAS", 0) > 0) if idx else None,
            "INDICE_BASE_EMPIRICA": idx.get("indice") if idx else None,
            "INDICE_LEGADO": idx.get("indice_legado") if idx else None,
            "N_PILAR_A_DIAGNOSTICO": idx.get("n_pilar_a_diagnostico") if idx else None,
            "N_PILAR_B_EFEITO": idx.get("n_pilar_b_efeito") if idx else None,
            "N_PILAR_C_EVIDENCIA": idx.get("n_pilar_c_evidencia_causal") if idx else None,
            "CLUSTER_TEXTO_ID": clusters_texto.get(f"{ano}_{sq}"),
        }
        painel.append(linha)

print(f"=== Painel multiciclo — governador, {ANOS[0]}–{ANOS[-1]} ===")
print(f"Total de candidaturas: {len(painel)}")
por_ano = {}
for l in painel:
    por_ano.setdefault(l["ANO"], []).append(l)
for ano in ANOS:
    linhas = por_ano[ano]
    com_proposta = sum(1 for l in linhas if l["TEM_PROPOSTA_DE_GOVERNO"])
    sem_texto = sum(1 for l in linhas if l["TEM_PROPOSTA_DE_GOVERNO"] and l["TEXTO_EXTRAIVEL"] is False)
    com_indice = [l["INDICE_BASE_EMPIRICA"] for l in linhas
                  if l["INDICE_BASE_EMPIRICA"] is not None and l["TEXTO_EXTRAIVEL"] is not False]
    media = sum(com_indice) / len(com_indice) if com_indice else 0
    n_incumb = sum(1 for l in linhas if l["INCUMBENTE"] is True)
    print(f"  {ano}: {len(linhas)} candidaturas, {com_proposta} com proposta "
          f"({sem_texto} sem texto extraível mesmo c/ OCR, excluídos da média), "
          f"índice médio {media:.1f}, {n_incumb} incumbentes identificados")

out_csv = f"{BASE}/analise/painel_governador_2014_2026.csv"
out_json = f"{BASE}/analise/painel_governador_2014_2026.json"
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

campos = list(painel[0].keys()) if painel else []
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campos)
    writer.writeheader()
    writer.writerows(painel)

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(painel, f, ensure_ascii=False, indent=2)

print(f"\nSalvo em: {out_csv}")
print(f"Salvo em: {out_json}")
