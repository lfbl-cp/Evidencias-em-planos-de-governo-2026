"""
Painel individual: usa NR_CPF_CANDIDATO (identifica a MESMA PESSOA entre ciclos,
ao contrário de SQ_CANDIDATO que é por registro/ciclo) para comparar o índice de
base empírica do mesmo candidato consigo mesmo em ciclos diferentes -- uma
identificação mais forte do efeito de incumbência do que a comparação
cross-sectional (incumbentes vs. desafiantes, pessoas diferentes) já usada no
dashboard.

Pergunta: quando a MESMA pessoa concorre de novo, e numa dessas vezes está na
condição de incumbente e na outra de desafiante, o índice dela muda?

Uso: python3 analise_candidato_mesmo.py
Saída: analise/painel_candidato_mesmo.json/csv (trajetória por pessoa) +
resumo impresso no terminal.
"""
import csv
import json
from collections import defaultdict

BASE = "/home/claude/brasil_multiciclo"


def main():
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)

    por_cpf = defaultdict(list)
    for r in painel:
        cpf = r.get("NR_CPF_CANDIDATO")
        if cpf:
            por_cpf[cpf].append(r)

    trajetorias = []
    for cpf, regs in por_cpf.items():
        validos = [r for r in regs if r.get("INDICE_BASE_EMPIRICA") is not None]
        if len(validos) < 2:
            continue
        validos.sort(key=lambda r: r["ANO"])
        nome = validos[-1].get("NM_URNA_CANDIDATO")
        trajetorias.append({
            "NR_CPF_CANDIDATO": cpf,
            "NOME": nome,
            "N_CANDIDATURAS_COM_INDICE": len(validos),
            "CICLOS": [r["ANO"] for r in validos],
            "UFS": [r["SG_UF"] for r in validos],
            "PARTIDOS": [r["SG_PARTIDO"] for r in validos],
            "INDICES": [r["INDICE_BASE_EMPIRICA"] for r in validos],
            "INCUMBENTE": [r["INCUMBENTE"] for r in validos],
            "RESULTADO": [r["DS_SIT_TOT_TURNO"] for r in validos],
        })

    print(f"=== Painel individual (mesma pessoa, CPF) ===")
    print(f"Pessoas com índice válido em 2+ ciclos: {len(trajetorias)}")

    # --- 1. tendência within-person: índice sobe ou desce entre a 1a e a última candidatura? ---
    deltas = [t["INDICES"][-1] - t["INDICES"][0] for t in trajetorias]
    sobe = sum(1 for d in deltas if d > 0)
    desce = sum(1 for d in deltas if d < 0)
    igual = sum(1 for d in deltas if d == 0)
    media_delta = sum(deltas) / len(deltas)
    print(f"\nTendência (1ª vs. última candidatura de cada pessoa, N={len(trajetorias)}):")
    print(f"  sobe: {sobe} ({100*sobe/len(trajetorias):.0f}%) | desce: {desce} ({100*desce/len(trajetorias):.0f}%) | igual: {igual}")
    print(f"  delta médio: {media_delta:+.2f} pontos percentuais")

    # --- 2. efeito de incumbência, mesma pessoa: casos onde a mesma pessoa é incumbente numa
    #    candidatura e desafiante em outra (dentro das suas 2+ candidaturas com índice válido) ---
    pares_incumb = []  # (indice_como_desafiante, indice_como_incumbente, cpf, nome)
    for t in trajetorias:
        inc = t["INCUMBENTE"]
        idx = t["INDICES"]
        # pega o par mais direto: primeira vez como desafiante (False) e primeira como incumbente (True)
        try:
            i_des = inc.index(False)
            i_inc = inc.index(True)
        except ValueError:
            continue
        pares_incumb.append((idx[i_des], idx[i_inc], t["NR_CPF_CANDIDATO"], t["NOME"]))

    print(f"\nPessoas com registro de AMBAS as condições (desafiante numa candidatura, "
          f"incumbente em outra): {len(pares_incumb)}")
    if pares_incumb:
        media_des = sum(p[0] for p in pares_incumb) / len(pares_incumb)
        media_inc = sum(p[1] for p in pares_incumb) / len(pares_incumb)
        sobe_ao_ficar_incumb = sum(1 for p in pares_incumb if p[1] > p[0])
        desce_ao_ficar_incumb = sum(1 for p in pares_incumb if p[1] < p[0])
        print(f"  índice médio como desafiante: {media_des:.2f}")
        print(f"  índice médio como incumbente: {media_inc:.2f}")
        print(f"  diferença (incumbente - desafiante), mesma pessoa: {media_inc-media_des:+.2f}")
        print(f"  sobe ao virar incumbente: {sobe_ao_ficar_incumb}/{len(pares_incumb)} | "
              f"desce: {desce_ao_ficar_incumb}/{len(pares_incumb)}")
        print(f"\n  Casos individuais:")
        for des, inc_, cpf, nome in sorted(pares_incumb, key=lambda p: p[1]-p[0]):
            print(f"    {nome:<28} desafiante={des:>5.1f}  incumbente={inc_:>5.1f}  delta={inc_-des:+.1f}")

    # --- 3. quantos trocaram de partido entre candidaturas? ---
    trocou_partido = sum(1 for t in trajetorias if len(set(t["PARTIDOS"])) > 1)
    print(f"\nPessoas que trocaram de partido entre candidaturas: {trocou_partido}/{len(trajetorias)} "
          f"({100*trocou_partido/len(trajetorias):.0f}%)")

    out_json = f"{BASE}/analise/painel_candidato_mesmo.json"
    out_csv = f"{BASE}/analise/painel_candidato_mesmo.csv"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(trajetorias, f, ensure_ascii=False, indent=2)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NR_CPF_CANDIDATO", "NOME", "N_CANDIDATURAS", "CICLOS", "UFS", "PARTIDOS", "INDICES", "INCUMBENTE", "RESULTADO"])
        for t in trajetorias:
            writer.writerow([t["NR_CPF_CANDIDATO"], t["NOME"], t["N_CANDIDATURAS_COM_INDICE"],
                              "|".join(map(str, t["CICLOS"])), "|".join(t["UFS"]), "|".join(t["PARTIDOS"]),
                              "|".join(f"{x:.1f}" for x in t["INDICES"]),
                              "|".join(str(x) for x in t["INCUMBENTE"]),
                              "|".join(str(x) for x in t["RESULTADO"])])
    print(f"\nSalvo em: {out_json}")
    print(f"Salvo em: {out_csv}")


if __name__ == "__main__":
    main()
