"""
Modelo multinível (hierárquico) para o Índice de Base Empírica, substituindo a
ideia inicial de "efeito fixo simples" por partido/estado isolado.

Pedido do usuário (15/10/2026): "multilevel/hierarchical model (candidato
dentro de estado dentro de região dentro de ciclo) em vez de efeito fixo
simples -- mais apropriado dado que o N por estado varia bastante."

DECISÃO METODOLÓGICA (documentada aqui e em CLAUDE.md): a estrutura pedida tem
4 níveis (candidato < estado < região < ciclo), mas região (5 categorias) e
ciclo (4 categorias) têm grupos DEMAIS DE POUCOS para estimar uma variância de
efeito aleatório com alguma confiabilidade -- a literatura de modelos
multinível (ex. Gelman & Hill 2007; regra prática comum: >=5-10 grupos como
mínimo absoluto, >=20-30 como confortável) recomenda tratar fatores com poucos
níveis como efeito FIXO, não aleatório, quando o objetivo é inferência sobre a
variância entre grupos. Região e ciclo entram aqui como efeitos fixos
(dummies); estado (27 grupos -- N adequado) entra como intercepto aleatório,
aninhado dentro de região automaticamente (toda UF pertence a exatamente 1
região, então a variância de estado capta variação DENTRO de região, já tendo
região like controlada como efeito fixo). Isso é estatisticamente equivalente
a aninhamento candidato < estado < região, só que região entra como fixo em
vez de aleatório -- a escolha certa dado o N de grupos disponível, não um
atalho.

Partido fica DE FORA da estrutura aleatória deste modelo de propósito: já tem
análise própria (dashboard "por partido", N efetivo por cluster de texto --
ver CLAUDE.md "duplicação de template"), e com 49 partidos de N muito
desigual um efeito cruzado partido x estado é um passo natural de robustez
FUTURO, não deste primeiro modelo.

Dois modelos (ver print no final):
  M1: todos os 4 ciclos, sem incumbência (2014 não tem essa variável).
  M2: só 2018-2026 (3 ciclos), com incumbência -- checagem de robustez.
Ambos: indice ~ C(ano) + C(regiao) + C(genero) + log1p(n_palavras) + (1|estado)
M2 adiciona: + incumbente

Uso: python3 modelo_multinivel.py
Saída: analise/modelo_multinivel_resultados.txt (sumário completo dos 2
modelos) + analise/modelo_multinivel_icc.json (variância entre estados, ICC)
"""
import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

BASE = "/home/claude/brasil_multiciclo"

REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def main():
    with open(f"{BASE}/analise/painel_governador_2014_2026.json", encoding="utf-8") as f:
        painel = json.load(f)

    df = pd.DataFrame(painel)
    df = df[df["TEXTO_EXTRAIVEL"] != False]  # noqa: E712 -- None (sem proposta) também cai fora, igual ao dashboard
    df = df[df["INDICE_BASE_EMPIRICA"].notna()].copy()
    df["regiao"] = df["SG_UF"].map(REGIAO)
    df["ano"] = df["ANO"].astype(int).astype(str)  # categórico
    df["estado"] = df["SG_UF"]
    df["genero"] = df["DS_GENERO"].fillna("NÃO INFORMADO")
    df["log_palavras"] = np.log1p(df["N_PALAVRAS_PROPOSTA"].fillna(0))
    df["indice"] = df["INDICE_BASE_EMPIRICA"].astype(float)

    print(f"N total no modelo (com índice válido): {len(df)}")
    print(f"Estados: {df['estado'].nunique()} | Regiões: {df['regiao'].nunique()} | Ciclos: {df['ano'].nunique()}")
    print(f"Índice -- média: {df['indice'].mean():.2f}, mediana: {df['indice'].median():.2f}, "
          f"% de zeros: {100*(df['indice']==0).mean():.1f}%")
    print()

    saida = []

    # --- M1: todos os 4 ciclos, sem incumbência ---
    m1 = smf.mixedlm(
        "indice ~ C(ano) + C(regiao) + C(genero) + log_palavras",
        data=df,
        groups=df["estado"],
    )
    r1 = m1.fit(reml=True)
    print("=== M1: todos os 4 ciclos (N=%d), (1|estado) aninhado em região (fixa) ===" % len(df))
    print(r1.summary())
    saida.append("=== M1: todos os 4 ciclos ===\n" + str(r1.summary()))

    var_estado_m1 = float(r1.cov_re.iloc[0, 0])
    var_resid_m1 = float(r1.scale)
    icc_m1 = var_estado_m1 / (var_estado_m1 + var_resid_m1)
    print(f"\nVariância entre estados: {var_estado_m1:.3f} | Variância residual: {var_resid_m1:.3f}")
    print(f"ICC (fração da variância, após controlar ano/região/gênero/tamanho, que é 'do estado'): {icc_m1:.3f}")

    # --- M2: 2018-2026, com incumbência (robustez) ---
    df2 = df[df["ANO"] != 2014].copy()
    df2 = df2[df2["INCUMBENTE"].notna()]
    df2["incumbente"] = df2["INCUMBENTE"].astype(bool)
    m2 = smf.mixedlm(
        "indice ~ C(ano) + C(regiao) + C(genero) + log_palavras + incumbente",
        data=df2,
        groups=df2["estado"],
    )
    r2 = m2.fit(reml=True)
    print("\n\n=== M2: 2018-2026 (N=%d), com incumbência ===" % len(df2))
    print(r2.summary())
    saida.append("\n\n=== M2: 2018-2026 com incumbência ===\n" + str(r2.summary()))

    var_estado_m2 = float(r2.cov_re.iloc[0, 0])
    var_resid_m2 = float(r2.scale)
    icc_m2 = var_estado_m2 / (var_estado_m2 + var_resid_m2)
    print(f"\nVariância entre estados: {var_estado_m2:.3f} | Variância residual: {var_resid_m2:.3f}")
    print(f"ICC: {icc_m2:.3f}")

    # --- comparação com OLS simples (sem estrutura hierárquica) para referência ---
    # AIC de MixedLM só é comparável ao de OLS quando ambos ajustados por máxima
    # verossimilhança (ML), não REML -- reajusta M1 com reml=False só para esta
    # comparação (os coeficientes reportados acima continuam vindo do fit REML,
    # preferível para os componentes de variância em si).
    m_ols = smf.ols("indice ~ C(ano) + C(regiao) + C(genero) + log_palavras", data=df).fit()
    r1_ml = m1.fit(reml=False)
    print(f"\n\nComparação (ambos por ML) -- OLS simples (sem efeito aleatório): AIC={m_ols.aic:.1f} | "
          f"Mixed (M1, estado aleatório): AIC={r1_ml.aic:.1f}")
    print("AIC menor é melhor -- diferença pequena/negativa aqui é esperada dado ICC baixo (abaixo).")

    with open(f"{BASE}/analise/modelo_multinivel_resultados.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(saida))

    icc_out = {
        "m1_todos_ciclos": {"n": len(df), "var_estado": var_estado_m1, "var_residual": var_resid_m1, "icc": icc_m1},
        "m2_2018_2026_com_incumbencia": {"n": len(df2), "var_estado": var_estado_m2, "var_residual": var_resid_m2, "icc": icc_m2},
    }
    with open(f"{BASE}/analise/modelo_multinivel_icc.json", "w", encoding="utf-8") as f:
        json.dump(icc_out, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em: {BASE}/analise/modelo_multinivel_resultados.txt")
    print(f"Salvo em: {BASE}/analise/modelo_multinivel_icc.json")


if __name__ == "__main__":
    main()
