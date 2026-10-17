"""
Rede candidato <-> fornecedor de campanha (2026, piloto), a partir do dataset de
prestação de contas do TSE ("documentos fiscais de despesa",
despesa_documento_2026.zip, resource "Candidatos").

Pergunta: candidatos a governador que contratam o MESMO fornecedor (por CNPJ/CPF)
em categorias de despesa ligadas a marketing/consultoria política (produção de
programas de rádio/TV, criação de site, impulsionamento de conteúdo,
jingles/vinhetas/slogans, pesquisas eleitorais, serviços prestados por terceiros)
têm índices de base empírica parecidos entre si? Isso testaria se parte da
variação do índice vem de quem escreveu o material de campanha, não só do
partido ou do candidato.

Fonte bruta: CSV extraído do zip baixado pelo usuário (ver CLAUDE.md, seção
"rede candidato-consultoria"), em
/tmp/.../scratchpad/despesa_2026/despesa_candidato_documento_2026_BRASIL.csv
(ISO-8859-1, ';'-delimitado). Esse arquivo não foi commitado ao projeto (é
grande e específico do piloto) -- ajustar CAMINHO_CSV se reprocessar.

Uso: python3 build_rede_fornecedores.py
"""
import csv
import json
from collections import defaultdict

BASE = "/home/claude/brasil_multiciclo"
CAMINHO_CSV = "/tmp/claude-0/-home-claude/0fc5a4d6-a5e8-5caf-b591-b610e5c5099f/scratchpad/despesa_2026/despesa_candidato_documento_2026_BRASIL.csv"

CATEGORIAS_MARKETING = {
    "Produção de programas de rádio, televisão ou vídeo",
    "Criação e inclusão de páginas na internet",
    "Despesa com Impulsionamento de Conteúdos",
    "Produção de jingles, vinhetas e slogans",
    "Pesquisas ou testes eleitorais",
    "Serviços prestados por terceiros",
    "Serviços próprios prestados por terceiros",
    "Eventos de promoção da candidatura",
}


def main():
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)
    painel_2026 = {r["SQ_CANDIDATO"]: r for r in painel if r["ANO"] == 2026}
    print(f"Candidatos a governador no painel 2026: {len(painel_2026)}")

    despesas_gov = []
    with open(CAMINHO_CSV, encoding="ISO-8859-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["DS_CARGO"] != "Governador":
                continue
            despesas_gov.append(row)

    print(f"Linhas de despesa de candidatos a GOVERNADOR em todo o Brasil: {len(despesas_gov)}")
    sqs_com_despesa = {r["SQ_CANDIDATO"] for r in despesas_gov}
    sqs_no_painel = sqs_com_despesa & set(painel_2026.keys())
    print(f"Desses, candidatos que batem com SQ_CANDIDATO do nosso painel: {len(sqs_no_painel)}")

    # fornecedor (CNPJ/CPF) -> set de candidatos (SQ_CANDIDATO) que pagaram esse fornecedor
    # em categoria de marketing/consultoria
    fornecedor_candidatos = defaultdict(set)
    fornecedor_nome = {}
    for r in despesas_gov:
        if r["DS_DRD"] not in CATEGORIAS_MARKETING:
            continue
        sq = r["SQ_CANDIDATO"]
        if sq not in painel_2026:
            continue
        cnpj = r["NR_CPF_CNPJ_FORNECEDOR"]
        fornecedor_candidatos[cnpj].add(sq)
        fornecedor_nome[cnpj] = r["NM_FORNECEDOR"]

    compartilhados = {cnpj: sqs for cnpj, sqs in fornecedor_candidatos.items() if len(sqs) >= 2}
    print(f"\nFornecedores de marketing/consultoria pagos por 2+ candidatos a governador diferentes: {len(compartilhados)}")

    for cnpj, sqs in sorted(compartilhados.items(), key=lambda kv: -len(kv[1])):
        candidatos = [painel_2026[sq] for sq in sqs]
        nome_forn = fornecedor_nome[cnpj]
        print(f"\n  Fornecedor: {nome_forn} (CNPJ/CPF {cnpj}) -- {len(sqs)} candidatos a governador:")
        for c in candidatos:
            print(f"    {c['SG_UF']} {c.get('NM_URNA_CANDIDATO')} ({c.get('SG_PARTIDO')}) -- índice={c.get('INDICE_BASE_EMPIRICA')}")

    out = {
        "n_candidatos_2026_com_despesa": len(sqs_no_painel),
        "n_fornecedores_compartilhados": len(compartilhados),
        "fornecedores_compartilhados": [
            {
                "cnpj_cpf": cnpj,
                "nome_fornecedor": fornecedor_nome[cnpj],
                "candidatos": [
                    {"sq": sq, "uf": painel_2026[sq]["SG_UF"], "nome": painel_2026[sq].get("NM_URNA_CANDIDATO"),
                     "partido": painel_2026[sq].get("SG_PARTIDO"), "indice": painel_2026[sq].get("INDICE_BASE_EMPIRICA")}
                    for sq in sqs
                ],
            }
            for cnpj, sqs in sorted(compartilhados.items(), key=lambda kv: -len(kv[1]))
        ],
    }
    out_path = f"{BASE}/analise/rede_fornecedores_2026.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo em: {out_path}")


if __name__ == "__main__":
    main()
