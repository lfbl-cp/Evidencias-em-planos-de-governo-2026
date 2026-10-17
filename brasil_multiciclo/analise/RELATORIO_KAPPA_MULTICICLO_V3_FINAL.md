# Relatório de Confiabilidade — Pilar B, Validação Final Independente (v3)

**Validador:** agente independente, 3ª camada do pipeline (codificador cego → revisor adversarial →
**este relatório**). **Data:** 2026-10-09.
**Insumos (lidos e recalculados do zero, nenhum número dos relatórios anteriores foi reutilizado sem
reconferir):** `analise/kappa_gabarito_v3.json` (N=204, motor final, campos `pilar_b` e
`pilar_b_antigo`), `analise/kappa_codificador_llm.json` (N=204, LLM cego, inalterado desde 25/09),
`programs/motor_indice_base_empirica.py` (lido integralmente, não só os trechos citados em relatórios
anteriores), `analise/RELATORIO_KAPPA_MULTICICLO.md` e `analise/REVISAO_ADVERSARIAL_V2.md` (tratados
como alegações a confirmar), e os PDFs originais das 7 frases remanescentes mais relevantes (contexto
completo, não só o fragmento da amostra).

---

## 1. Resumo executivo

- **Confirmo de forma independente, recalculando do zero a partir dos rótulos brutos**, os três
  números centrais da cadeia: κ=0,469 (motor original, bug sistemático) → κ=0,769 (1ª correção,
  tempo verbal + numeração de lista) → **κ=0,769 (2ª correção, `ano_ciclo`)**. A matriz de confusão
  completa está na seção 2.
- **A 2ª correção (`ano_ciclo`) funciona para o que foi desenhada**: testei eu mesmo, com frases
  construídas fora da amostra de 204 (seção 4), o cenário exato que motivou a correção ("Em ANO
  futuro, [verbo no futuro]...") e variantes de fronteira (ano igual ao próprio ciclo, intervalo
  "entre ANO e ANO" cruzando o ano do ciclo). Todos os 6 casos construídos se comportam como
  esperado. O risco de regressão que o revisor adversarial apontou (Padrão D) está, de fato,
  neutralizado.
- **Mas a 2ª correção não é um ganho líquido nesta amostra — é uma troca 1-por-1.** Ao reler as 8
  discordâncias remanescentes frase a frase (não só os 8 já citados no relatório anterior), encontrei
  que a correção do `ano_ciclo` **resolveu S0156** (o caso "apontou"/"censo escolar" documentado pelo
  revisor) mas **introduziu um caso novo, não documentado em nenhum relatório anterior: S0064**. O
  κ do Pilar B nesta amostra de 204 frases é **matematicamente idêntico** antes e depois da correção
  do `ano_ciclo` (0,7689 nos dois casos) porque uma discordância foi trocada por outra. Isso não
  invalida a correção (ela resolve um risco real e maior fora da amostra, ver §4), mas significa que
  **"0,769" não deve ser lido como "a 2ª rodada melhorou o número"** — ela resolveu um risco
  sistêmico sem piorar nem melhorar o desempenho medido nesta amostra específica.
- **Os 15 casos de verdadeiro-positivo do Pilar B auditados no relatório original permanecem 100%
  verdadeiros na versão final do motor** (seção 6) — zero regressão confirmada.
- **Achado novo (S0064, severidade média, 1 caso nesta amostra):** descrito em detalhe na seção 5.
  Resumo: uma frase que descreve uma **projeção demográfica externa** (envelhecimento da população,
  fonte indireta, não é compromisso do candidato) foi truncada pela quebra de linha do PDF exatamente
  no meio de uma frase mais longa, deixando um fragmento com números reais (percentuais) adjacentes à
  palavra-gatilho "redução de". Antes da correção do `ano_ciclo`, esse caso era (coincidentemente)
  classificado certo, porque o bug antigo tratava **qualquer** "em ANO" como passado — inclusive
  "em 2030" nesta frase, que também era usado (incorretamente, pelos motivos errados) para suprimir o
  falso-positivo. Com a correção, "em 2030" só é tratado como passado quando 2030 é anterior ao ano do
  ciclo (2018) — o que é o comportamento *correto* em geral — mas aqui expõe que a frase nunca deveria
  ter sido capturada por `EFEITO_RE`/`has_real_number` em primeiro lugar: é o mesmo bug catalogado como
  "Padrão B / #3" pelo revisor adversarial (número presente que não é a magnitude da promessa),
  nunca corrigido em nenhuma das duas rodadas.
- **Pilar A (κ=0,3661) e Pilar C (κ=0,6806) recalculados do zero e idênticos aos relatórios
  anteriores** — confirmam que a correção do Pilar B não teve efeito colateral mensurável nesses
  pilares (controle negativo esperado, já que `is_diagnostico`/`is_evidencia` não foram tocados).
- **Achado novo de distribuição (não estava em nenhum relatório anterior): as 8 discordâncias
  remanescentes do Pilar B não estão distribuídas igualmente entre ciclos.** 5 das 8 são do ciclo
  2018 (κ de 2018 sobe de 0,258 para só 0,408 — ainda "moderada", o único ciclo que não chega a
  "substancial"); 2014 tem κ=1,0 (perfeito, 0 discordâncias); 2022 vai a 0,790; 2026 vai a 0,835. Ver
  tabela na seção 2.2.
- **Parecer final (seção 7): pronto para uso no painel/artigo COM ressalvas documentadas, não
  "problema encerrado".** Ver seção 7 para a recomendação completa.

---

## 2. Matriz de confusão recalculada (Pilar B, motor final v3 × LLM, N=204)

Recalculada do zero em Python a partir dos dois arquivos de rótulos brutos (fórmula padrão de Cohen,
p_o/p_e manual, sem depender de biblioteca para a lógica — só para conferência cruzada).

### 2.1 Agregado (4 ciclos)

|                        | LLM = True | LLM = False | Total |
|---|---|---|---|
| **Motor final = True**  | 15 | 8 | 23 |
| **Motor final = False** | 0  | 181 | 181 |
| **Total**               | 15 | 189 | 204 |

- p_o (concordância bruta) = 0,9608
- p_e (esperada ao acaso) = 0,8303
- **κ = 0,7689 ≈ 0,769**
- Padrão direcional **preservado**: 8 falso-positivos do motor (motor=True, LLM=False), **0
  falso-negativos** (motor nunca deixa de capturar uma promessa que o LLM capturou). Era 27→0 antes
  da correção; agora é 8→0. A assimetria é a mesma, só menor em magnitude.

Para comparação, a mesma matriz usando `pilar_b_antigo` (motor original, sem nenhuma correção desta
rodada) — reproduz exatamente o número do relatório de 25/09:

|                          | LLM = True | LLM = False | Total |
|---|---|---|---|
| **Motor original = True**  | 15 | 27 | 42 |
| **Motor original = False** | 0  | 162 | 162 |

p_o=0,8676, p_e=0,7509, **κ=0,4687 ≈ 0,469**.

### 2.2 Por ciclo (motor final v3 × LLM, N=51 cada)

| Ciclo | TP | FP (motor=T,LLM=F) | FN | TN | κ final | κ original (`pilar_b_antigo`) |
|---|---|---|---|---|---|---|
| 2014 | 5 | 0 | 0 | 46 | **1,000** (perfeita) | 0,617 (substancial) |
| 2018 | 2 | 5 | 0 | 44 | **0,408** (moderada — pior dos 4) | 0,258 (razoável) |
| 2022 | 2 | 1 | 0 | 48 | **0,790** (substancial) | 0,287 (razoável) |
| 2026 | 6 | 2 | 0 | 43 | **0,835** (quase perfeita) | 0,653 (substancial) |

Achado: **2018 concentra 5 das 8 discordâncias remanescentes** e é o único ciclo que não passa de
"moderada" depois da correção. Não investiguei a fundo por que 2018 é pior (os PDFs de 2018 citados
nas discordâncias — GO, PI, RS, DF — não têm nada em comum óbvio de formato), mas registro o padrão
para quem for decidir se vale investir mais correção especificamente nesse ciclo antes de reportar
comparação temporal no artigo.

---

## 3. Confirmação do mecanismo de código (`ano_ciclo`)

Li a função `is_efeito` e as auxiliares (`_tem_marcador_temporal_passado`, `EM_ANO_RE`,
`ENTRE_ANOS_RE`) diretamente em `programs/motor_indice_base_empirica.py` (linhas 251–325), não só o
comentário que as descreve. Confirmo que:

- `PASSADO_RE` continua cobrindo verbos/citações datadas independentemente de `ano_ciclo` (ex.:
  "houve", "perdeu", "caiu", "pnad 20XX", "censo (escolar) 20XX" — a lista fixa de gatilhos).
- O gatilho genérico de ano (`EM_ANO_RE` = `em (?:19|20)\d{2}`, `ENTRE_ANOS_RE` = `entre ANO e ANO`)
  só conta como passado quando `ano_ciclo` é passado como argumento **e** o(s) ano(s) citado(s)
  é/são estritamente anterior(es) ao ano do ciclo. Sem `ano_ciclo` (ex.: uso avulso/teste direto da
  função), esse gatilho específico fica **desativado** — comportamento conservador correto (prefere
  não suprimir a arriscar suprimir uma promessa genuína).
- Confirmei em `build_indice_base_empirica.py` (linha 60) que `ano_ciclo=int(ano)` é de fato
  propagado em todo ponto de chamada real do pipeline (`base_empirica_analise(texto,
  ano_ciclo=int(ano))`), não é um parâmetro morto.

---

## 4. Testes próprios (fora da amostra de 204) do mecanismo `ano_ciclo`

Construí 6 frases de teste (nenhuma reaproveitada do revisor adversarial) chamando `is_efeito()`
diretamente, cobrindo o cenário original do Padrão D e casos de fronteira que o revisor não testou:

| # | Frase (resumida) | `ano_ciclo` | Esperado | Obtido | OK? |
|---|---|---|---|---|---|
| 1 | "Em 2030, aumentaremos a cobertura vacinal para 95%..." | 2026 | True | True | ✅ (reconfirma o Padrão D do revisor, agora corrigido) |
| 2 | "Em 2010, a cobertura vacinal era de apenas 60%, segundo dados do Datasus." | 2014 | False | False | ✅ (ano passado + verbo no passado — continua suprimido corretamente) |
| 3 | "Entre 2026 e 2030, aumentaremos a cobertura em 10 p.p." | 2026 | True | True | ✅ (ano inicial = próprio ano do ciclo — fronteira tratada como "não passado", correto) |
| 4 | "Entre 2010 e 2013, a cobertura cresceu 10 p.p." | 2014 | False | False | ✅ (intervalo inteiramente no passado — suprimido corretamente, é Pilar A, não B) |
| 5 | "Em 2018, vamos aumentar o investimento em educação em 20%." | 2018 | True | True | ✅ (ano igual ao ciclo + verbo futuro "vamos" — não suprime) |
| 6 | "Em 2014, quando assumimos, o estoque da dívida era de R$ 4 bi." | 2014 | False | False | ✅ (ano igual ao ciclo, mas "era" já está em `PASSADO_RE` — suprime pelo verbo, não pelo ano; o teste confirma que o mecanismo de verbo e o de ano operam independentemente, como o código sugere) |

**Conclusão dos meus próprios testes: a correção do `ano_ciclo` funciona corretamente, inclusive nos
casos de fronteira (ano igual ao próprio ciclo, intervalo cruzando o ano do ciclo) que nenhum
relatório anterior tinha testado.** Não encontrei, nos cenários que construí, nenhuma regressão nova
*desse tipo específico* (ano futuro sendo tratado como passado). A regressão nova que encontrei (S0064,
seção 5) é de natureza diferente — não é o mecanismo de ano que falha, é um bug pré-existente e já
catalogado (número irrelevante) que só ficou visível de novo porque o bug do ano parou de
"mascará-lo" por acidente.

---

## 5. Achado novo: S0064 — a troca 1-por-1 que explica por que κ não subiu

**Frase (fragmento da amostra, ciclo 2018, PR):** *"número de idosos dos atuais 9,2% para quase 20%
em 2030 e a redução de"*

**Contexto completo, recuperado do PDF original** (`propostas/2018/PR/2018PR160000609226.pdf`,
linhas 946–950 do `pdftotext -layout`):

> "A projeção populacional do Estado traz dois pontos de atenção: a concentração de pessoas nas
> regiões de Curitiba, Londrina e Maringá e o envelhecimento da população, com crescimento percentual
> projetado do número de idosos dos atuais 9,2% para quase 20% em 2030 e a redução de população de 0
> a 14 anos de 20,8% para 14,6% em 2030."

**O que isso realmente é:** uma projeção demográfica (provavelmente de fonte externa, estilo
IBGE/IPARDES, não citada explicitamente no trecho disponível) apresentada como "ponto de atenção" —
ou seja, **diagnóstico/contexto do problema, não uma meta ou efeito que o candidato se compromete a
entregar.** O trecho inteiro é uma única frase lógica no PDF, mas a quebra de linha do `pdftotext`
faz `split_sentences` (que separa em `\n+`) cortá-la em pelo menos três fragmentos — o fragmento da
amostra é só o do meio, sem o "A projeção populacional..." que dá o enquadramento de diagnóstico, e
sem o trecho final ("de população de 0 a 14 anos de 20,8% para 14,6% em 2030") que mostra a que a
"redução de" de fato se refere (não é uma meta do candidato, é a mesma projeção demográfica, para
outra faixa etária).

**Por que o motor erra, e por que só passou a errar agora:**
- `EFEITO_RE` dispara em "redução de" (presente no fragmento, mesmo cortado antes do número real).
- `has_real_number` encontra números reais no fragmento ("9,2%", "20%" — percentuais não são
  rótulo de lista) e retorna `True`.
- `_tem_marcador_temporal_passado`: não há nenhum verbo de `PASSADO_RE` no fragmento; o único
  candidato a marcador de passado é "em 2030" via `EM_ANO_RE` — mas 2030 **não é anterior** a
  2018 (`ano_ciclo` deste documento), então, corretamente segundo a nova regra, não é tratado como
  passado.
- Resultado: `is_efeito()` retorna `True` → motor classifica como Pilar B. LLM (corretamente, lendo
  o fragmento isolado como uma afirmação neutra de contexto demográfico, sem verbo de compromisso)
  classificou como `False`.

**Por que isso é diferente do Padrão D que o revisor caçou:** não é um caso de "ano futuro tratado
como passado" (o comportamento do `ano_ciclo` aqui está correto — 2030 de fato não é passado em
relação a 2018). É o **Padrão B/#3 já catalogado pelo revisor** ("número presente na frase que não é
a magnitude da promessa") — aqui a forma específica é "número de uma projeção demográfica externa
citada perto de uma palavra-gatilho de efeito, mas o número não quantifica a promessa do candidato,
quantifica uma tendência populacional". **O motivo de este caso não ter aparecido nos relatórios
anteriores** é que, na versão do motor usada para gerar aquele relatório (`v2`, sem `ano_ciclo`), o
gatilho antigo e incondicional "em (?:19\|20)\d{2}" tratava "em 2030" como passado de qualquer forma
— **pelo motivo errado** (o mesmo bug genérico que o revisor chamou de Padrão D) — e isso
"mascarava" acidentalmente este outro bug, fazendo o motor dar a resposta certa por um caminho
errado. Corrigir o Padrão D corretamente removeu essa máscara acidental e expôs o Padrão B/#3 de
novo, nesta frase específica.

**Classificação do caso:** `llm_correto` (o motor erra). Severidade: média — é 1 caso em 204, mas é
exatamente o tipo de caso (projeção/estatística externa perto de palavra-gatilho de efeito) que
"Padrão B/#3" já havia identificado como uma classe inteira de erro não corrigida; não é incidente
isolado, é uma amostra concreta de uma classe de bug já conhecida e documentada, ainda aberta.

---

## 6. As 8 discordâncias remanescentes, veredito próprio (não copiado)

Reli os 8 casos com o contexto completo do PDF original sempre que isso mudava a leitura do
fragmento isolado (6 dos 8; S0067 e S0115 já tinham contexto suficiente no próprio fragmento/no
trecho citado). Formei veredito antes de comparar com o do revisor adversarial, e só então comparei.

| id | ciclo | Frase (fragmento da amostra) | Meu veredito | Mecanismo técnico exato | Concorda com revisor v2? |
|---|---|---|---|---|---|
| S0062 | 2018 | "Ofertar mamografia... na faixa etária maior de 40 anos para redução do [câncer de mama]" | **llm_correto** | "40" é critério de elegibilidade (idade), não magnitude; frase cortada antes do número de meta real (que nem existe no texto — é proposta sem número). | Sim |
| **S0064** | 2018 | "...dos atuais 9,2% para quase 20% em 2030 e a redução de" | **llm_correto — achado novo, não documentado antes** | Projeção demográfica externa (não é compromisso do candidato); "em 2030" corretamente não tratado como passado agora, mas número nunca devia ter sido lido como magnitude de uma promessa em 1º lugar. Ver seção 5. | Não se aplica (caso não existia na lista do revisor v2) |
| S0065 | 2018 | "humanidade, tenha a redução do número de visitantes, de mais de 60% a cada ano." | **llm_correto** (refino: contexto completo do PDF mostra claramente fato passado — "Em 2016 foram 25.000 turistas, e em 2017, apenas 16.000" é a frase seguinte, cortada pela mesma quebra de linha), mas **o fragmento isolado, sem esse contexto, é genuinamente mais difícil de decidir que os outros 7** — concordo com o revisor que, tomado só o fragmento (sem ir ao PDF original), "ambíguo" é defensável; com o PDF original a mão, eu mesmo pendo para `llm_correto` sem reserva. | Marginal — revisor disse "ambíguo", eu digo "llm_correto" ao checar o PDF original, mas reconheço a razão de ele ter hesitado |
| S0067 | 2018 | "seja, redução de R$ 17 bilhões." | **ambíguo** (mantenho) — o PDF original mostra que a frase completa ("podemos estimar que chegaremos ao final de 2018 com uma redução...") É uma promessa/projeção futura genuína do governo, mas essa informação nunca chega ao codificador (motor ou LLM): a quebra de linha do PDF corta a frase exatamente antes do verbo "chegaremos". Como unidade de codificação isolada (que é o que de fato é avaliado), o fragmento não tem verbo nem sujeito — é indecidível por desenho, não por falha de julgamento de nenhum dos dois lados. | Sim |
| S0070 | 2018 | "mulheres não negras Queda de 10,8%." | **llm_correto** | PDF original mostra "o DF **registrou** os seguintes índices" (verbo de diagnóstico explícito) numa frase anterior, cortada pelo `;` do `SENT_SPLIT_RE`. É claramente Pilar A (dado histórico já registrado), não B. | Sim |
| S0115 | 2022 | "meta de transformação através de um governo Inovativo - 360 º." | **llm_correto** | "360º" é o clichê retórico "governo 360 graus" (confirmado por trechos repetidos do mesmo documento: "visão de 360 graus", "Governo Inovativo"), não uma magnitude; "12" (pilares) é numeração de lista, já coberto por outro mecanismo mas não pelo específico deste caso. | Sim |
| S0169 | 2026 | "Restauração... da PR-170, entre o Rio Jordão e a BR-153" | **llm_correto** | "170"/"153" são códigos de rodovia dentro de um item de lista de obras — confirmado no PDF (lista de 7+ itens idênticos, cada um "Restauração com aumento de capacidade da PR-XXX, entre Y e Z"); nenhum tem magnitude numérica real da "capacidade" prometida. | Sim |
| S0172 | 2026 | "...temperatura global deve aumentar entre 2,5°C e 2,9°C até o fim do século" | **llm_correto** | PDF confirma: é citação de relatório do PNUMA (ONU) sobre aquecimento global, contexto científico internacional, não compromisso do candidato; "até o fim do século" até reforça o falso-positivo ao disparar `FUTURO_RE`. | Sim |

**Resumo do veredito:** 7 de 8 `llm_correto` (motor erra), 1 de 8 `ambíguo` por desenho (fragmento sem
verbo/sujeito), **0 de 8 `motor_correto`**. A assimetria direcional do bug original (motor só infla,
nunca perde) permanece 100% presente nos casos remanescentes — não há nenhum caso, nem na amostra de
204 nem nos meus testes construídos, em que o motor tenha passado a **perder** uma promessa genuína
por causa de qualquer uma das duas correções.

**Padrão transversal que encontrei ao buscar o contexto completo (não estava explicitado assim em
nenhum relatório anterior):** 3 dos 8 casos remanescentes (S0065, S0067, S0070) são causados
especificamente pela forma como `split_sentences` quebra frases em `\n+` (quebra de linha do PDF) ou
em `;` — não por uma falha de `is_efeito` em si, mas por a "unidade de codificação" chegar até
`is_efeito` já mutilada, sem o verbo ou o sujeito que desambiguaria o tempo verbal. Isso é uma classe
de erro estrutural diferente das duas já corrigidas (tempo verbal explícito; numeração de lista) —
nenhuma correção de regex dentro de `is_efeito` consegue resolver isso; precisaria de uma correção em
`split_sentences` (ex.: não quebrar em quebra de linha simples quando a linha anterior não termina em
pontuação de fim de frase) ou de olhar a frase vizinha antes de classificar.

---

## 7. Auditoria dos 15 verdadeiro-positivos originais — confirmação de zero regressão

Recuperei do `kappa_gabarito.json` original os 15 casos em que motor=True **e** LLM=True (a base
usada no relatório de 25/09 para dizer "0 falso-negativo introduzido pela correção"). Confirmei
individualmente, pelo campo `pilar_b` em `kappa_gabarito_v3.json`, que **todos os 15 continuam
`True`** na versão final do motor (nenhum foi lido só como "número do relatório", reconferido um a
um):

S0012, S0013, S0014, S0018, S0019, S0066, S0069, S0116, S0119, S0164, S0165, S0166, S0167, S0168,
S0170 — **15/15 preservados, 0 regressões**, nas duas rodadas de correção combinadas.

---

## 8. Controle negativo: Pilares A e C

Recalculados do zero a partir dos mesmos dois arquivos (`pilar_a`, `pilar_c`), sem depender de
nenhum número do relatório de 25/09:

| Pilar | κ (recalculado agora) | κ (relatório 25/09) | Idêntico? |
|---|---|---|---|
| A — diagnóstico | 0,3661 | 0,366 | Sim |
| C — evidência externa | 0,6806 | 0,681 | Sim |

Como esperado — nenhuma das duas correções tocou `is_diagnostico`/`is_evidencia` — confirma que a
correção do Pilar B não teve efeito colateral mensurável nos outros dois pilares.

**Nota lateral sobre `com_base` (A∨B∨C):** recalculado também, dá κ=0,6184 com o Pilar B final,
contra 0,621 (relatório original, calculado com `pilar_b_antigo`) — uma queda de ~0,003, não um ganho.
Isso **não é uma regressão real**: `com_base` é dominado por A e C, que são os dois pilares com mais
ruído (κ 0,366 e 0,681) e não mudaram; a pequena queda vem de casos em que o motor original acertava
`com_base=True` "pelo motivo errado" (via o falso-positivo de B, que coincidia por acaso com um
acerto genuíno de A ou C do LLM) e deixou de acertar por esse caminho quando B foi corrigido. Não
reportar `com_base` como "melhorou" por causa da correção de B — ele é essencialmente insensível a
essa correção porque A e C dominam sua variância.

---

## 9. Parecer final: pronto para publicar?

**Resposta: pronto para uso provisório no painel/artigo, com três ressalvas explícitas a documentar
no texto — não é "problema encerrado".**

**O que está, de fato, resolvido e pode ser afirmado no artigo sem ressalva:**
- A correção do Pilar B (as duas rodadas combinadas) é uma melhora real, grande e verificada de forma
  totalmente independente (κ 0,469 → 0,769), não um artefato de arredondamento ou erro de cálculo —
  recalculei do zero, a partir dos rótulos brutos, por conta própria, e obtive exatamente os mesmos
  números dos dois relatórios anteriores.
- O viés direcional original (motor só infla, nunca perde uma promessa genuína) permanece, mas
  diminuiu de 27 para 8 casos em 204 (13,2% → 3,9% das frases da amostra) — uma redução real de
  ~70% no volume de erro, não zero.
- A correção do `ano_ciclo` resolve corretamente o risco de regressão "ano futuro tratado como
  passado" que o revisor adversarial identificou — testei isso eu mesmo com 6 frases novas, incluindo
  casos de fronteira que nenhum relatório anterior cobriu, e todos passam.
- Os 15 casos de verdadeiro-positivo conhecidos permanecem 100% intactos nas duas rodadas de
  correção — zero regressão nesse conjunto.

**O que NÃO está resolvido e deve ser documentado como limitação conhecida antes de publicar (ou
corrigido antes, se o tempo permitir):**
1. **Padrão B/#3 (número irrelevante perto de palavra-gatilho) continua inteiramente aberto.**
   Responde por 5 das 8 discordâncias remanescentes (S0062, S0064 [achado novo desta rodada], S0115,
   S0169, S0172) e tem formas concretas e diversas: idade de elegibilidade ("40 anos"), código de
   rodovia ("PR-170"), clichê retórico com número ("360º"), estatística científica externa ("2,5°C"),
   e — o achado novo — número de uma projeção demográfica externa citada perto do gatilho. Não é um
   padrão único e fácil de regexar (ao contrário dos Padrões #1/#2 já corrigidos); provavelmente exige
   uma heurística de proximidade/contexto mais robusta que um ajuste pontual de regex.
2. **A fragmentação de frase por quebra de linha do PDF (`split_sentences`, regra `\n+`) é uma fonte
   estrutural de erro independente de `is_efeito`**, responsável por 3 dos 8 casos remanescentes
   (S0065, S0067, S0070) e por pelo menos parte do caso novo S0064. Nenhuma correção de regex dentro
   de `is_efeito`/`PASSADO_RE`/`FUTURO_RE` resolve isso — o problema é que a "frase" que chega à
   função de classificação já perdeu o verbo/sujeito que desambiguaria o caso. Vale investigar, antes
   de tentar mais correções de regex em `is_efeito`, se `split_sentences` pode ser menos agressivo ao
   quebrar em quebra de linha simples (ex.: só tratar `\n+` como fim de frase quando o trecho anterior
   já termina em pontuação de fim de frase).
3. **2018 concentra 5 das 8 discordâncias remanescentes e é o único ciclo que não passa de "moderada"
   (κ=0,408) depois da correção** — achado novo desta rodada, não investigado a fundo aqui (não achei
   uma causa estrutural óbvia comum aos PDFs envolvidos: GO, PI, RS, DF), mas registrado para quem for
   comparar ciclos no artigo: **não tratar o Pilar B como igualmente confiável nos 4 ciclos** — 2018 é
   sistematicamente mais fraco.
4. **O Pilar A (κ=0,366, "razoável") não foi tocado por nenhuma das duas rodadas de correção e
   continua o elo mais fraco dos três pilares** — isso já estava no relatório original e permanece
   inalterado; não é um achado novo, mas reforço que ele não deve ser esquecido só porque o Pilar B
   recebeu toda a atenção recente.

**Recomendação prática:**
- **Pode reportar κ=0,769 (substancial) para o Pilar B no artigo**, com uma nota metodológica
  explícita cobrindo os quatro pontos acima (especialmente o nº 1 e 2, que são mecanismos técnicos
  específicos, não "ruído genérico").
- **Não é necessário reprocessar o painel de novo antes de publicar** só por causa dos achados desta
  rodada — nenhum dos problemas remanescentes é tão grave quanto o bug original (nenhum caso é
  catastrófico; o volume residual, ~4% das frases de Pilar B, é da ordem de grandeza que qualquer
  classificador lexical determinístico vai ter contra um codificador LLM em texto de PDF real).
- **Se houver tempo antes da submissão**, o investimento com melhor retorno marginal é (1) fechar o
  Padrão B/#3 (número irrelevante) e (2) revisitar a regra de quebra de linha em `split_sentences` —
  nessa ordem, porque (1) tem mecanismo mais claro e (2) é uma mudança estrutural que pode afetar
  todos os pilares, não só B, e merece sua própria rodada de validação de kappa antes de ser adotada.
