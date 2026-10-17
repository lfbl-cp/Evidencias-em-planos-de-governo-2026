# Relatório de Confiabilidade Inter-Codificador (Cohen's Kappa) — Painel Multiciclo 2014–2026

**Validador:** agente independente, cego à cadeia de raciocínio do revisor adversarial.
**Data:** 2026-09-25.
**Insumos:** `kappa_gabarito.json` (motor, N=204), `kappa_codificador_llm.json` (LLM cego, N=204),
`kappa_relatorio_falhas.json` (92 discordâncias + 11 padrões, produzidos por um terceiro agente).

**Resumo do método:** (1) recalculei o kappa do zero a partir dos dois arquivos de rótulos, sem
usar nenhum número do relatório de falhas como insumo; (2) sorteei 25 das 92 discordâncias
(`random.seed(7)`) e formei veredito próprio antes de olhar a justificativa do revisor; (3) reli as
frases citadas como `exemplos_ids` em 3 dos 11 padrões recorrentes para checar se sustentam a
descrição do padrão.

---

## 1. Kappa por pilar e por ciclo

Fórmula padrão de Cohen (via `sklearn.metrics.cohen_kappa_score`, conferida manualmente com
p_o/p_e). N=204 no agregado (51 por ciclo, distribuição estratificada confirmada).

### 1.1 Agregado (4 ciclos, N=204)

| Pilar | p_o (concordância bruta) | p_e (esperada ao acaso) | κ | Interpretação (Landis & Koch) |
|---|---|---|---|---|
| A — diagnóstico numérico | 0,804 | 0,691 | **0,366** | Razoável |
| B — efeito mensurável | 0,868 | 0,751 | **0,469** | Moderada |
| C — evidência/mecanismo causal | 0,877 | 0,616 | **0,681** | Substancial |
| **com_base** (A ou B ou C) | 0,804 | 0,483 | **0,621** | Substancial |

### 1.2 Por ciclo (N=51 cada)

| Ciclo | κ Pilar A | κ Pilar B | κ Pilar C | κ com_base |
|---|---|---|---|---|
| 2014 | 0,369 (razoável) | 0,617 (substancial) | 0,719 (substancial) | 0,622 (substancial) |
| 2018 | 0,274 (razoável) | 0,258 (razoável) | 0,783 (substancial) | 0,617 (substancial) |
| 2022 | 0,289 (razoável) | 0,287 (razoável) | 0,648 (substancial) | 0,658 (substancial) |
| 2026 | 0,548 (moderada) | 0,653 (substancial) | 0,568 (moderada) | 0,587 (moderada) |

**Leituras principais:**

- **Não há tendência secular clara e monotônica** ligada à idade do documento/qualidade de PDF. A
  hipótese registrada no `CLAUDE.md` ("2014 pode ser pior por causa de OCR/formato antigo") **não
  se confirma nos dados**: 2014 tem os melhores kappas de B e C entre os quatro ciclos; 2018 e 2022
  são os piores em A e B; 2026 é o melhor em A mas moderado em C. A variação parece dirigida mais
  por peculiaridades de regex/amostra do que por um gradiente temporal de qualidade de digitalização.
- **Pilar C é consistentemente o mais confiável** (substancial/quase-substancial em todos os 4
  ciclos), apesar de ser o pilar com mais bugs de falso-positivo identificados pelo revisor (ver
  §3) — o volume de acertos verdadeiros (institutições/leis citadas corretamente) é grande o
  suficiente para manter o kappa alto mesmo com ruído.
- **Pilar A é o elo mais fraco em 3 dos 4 ciclos** (2014/2018/2022 na faixa "razoável", a pior
  categoria fora de "leve/nula"), mesmo com concordância bruta relativamente alta (78–86%). Isso é
  em parte um **paradoxo do kappa com prevalência baixa e desbalanceada**: como só ~20% das frases
  são Pilar A=True para os dois codificadores, grande parte da concordância bruta vem de acertar o
  "False" fácil, e isso é descontado pesadamente por p_e. Ou seja, o número "razoável" não deve ser
  lido como "os dois codificadores discordam quase tanto quanto concordariam ao acaso" no sentido
  ingênuo — mas também não deve ser descartado: 40 das 92 discordâncias auditadas pertencem ao
  Pilar A, o maior bloco dos três.
- **Pilar B tem um padrão de erro estruturalmente assimétrico**: nas 27 discordâncias do Pilar B,
  **100% são motor=True/LLM=False** (zero casos do tipo oposto). Ou seja, o motor nunca "perde"
  uma promessa quantificada que o LLM capturou — ele só "inventa" excesso. Isso é consistente com
  bug técnico sistemático (não ruído aleatório) e é discutido em §3.

---

## 2. Auditoria independente do revisor adversarial

### 2.1 Amostra de 25 discordâncias (seed=7)

Formei veredito próprio (motor_certo / llm_certo / ambiguo) para cada uma das 25 frases sorteadas,
relendo a frase e aplicando o codebook — incluindo a leitura do motor de regex real
(`programs/motor_indice_base_empirica.py`, `DIAG_KEYWORDS_RE`, `EFEITO_RE`, `EVIDENCIA_RE`) para
entender por que o motor disparou — **antes** de olhar o veredito/justificativa do revisor.

**Taxa de concordância comigo: 23/25 = 92%.**

Dois casos de discordância, ambos de fronteira genuína (não erro grosseiro de nenhum dos lados):

| id | pilar | Frase | Meu veredito | Veredito do revisor | Comentário |
|---|---|---|---|---|---|
| S0111 | a | "Conforme o IBGE, a população de Alagoas foi estimada para 2021 em 3.365.351" | ambíguo (pendia para motor_certo: é estatística real, com fonte nomeada, número completo) | llm_certo | O revisor argumenta que uma estimativa populacional bruta não é "diagnóstico de um problema" — leitura defensável, mas o codebook também aceita "estatística... idealmente com fonte" sem exigir explicitamente que seja enquadrada como "problema". Não é um erro do revisor, é um limite de precisão do próprio codebook nesse ponto. |
| S0007 | a | "Na definição do IBGE, aglomerado subnormal é um conjunto de, no mínimo, 51 unidades habitacionais carentes," | llm_certo (motor errou: é definição metodológica, não diagnóstico do estado hoje) | ambíguo | O revisor reconheceu explicitamente a mesma tensão que eu vi ("defensável ler como diagnóstico com fonte ou como definição metodológica"), só que classificou como "ambíguo" em vez de decidir por "llm_certo". Diferença de threshold, não de leitura da frase. |

**Avaliação:** 92% de concordância em uma amostra de 25 é uma taxa alta para julgamento
qualitativo de frases fragmentadas e ambíguas (muitas cortadas por extração de PDF). As duas
discordâncias não indicam viés sistemático do revisor a favor do LLM nem do motor — nos dois
casos o revisor e eu concordamos sobre *os fatos* da frase, discordamos só sobre onde traçar a
linha "problema genuíno" vs. "dado demográfico neutro"/"definição vs. diagnóstico". Isso reforça
que o relatório do revisor é **majoritariamente confiável como leitura de conteúdo**, mas também
mostra que uma fração pequena (aqui, 2/25 ≈ 8%) dos 92 vereditos originais provavelmente teria
sido chamada de forma diferente por outro leitor cuidadoso — não porque o revisor "errou", mas
porque o próprio codebook deixa uma zona cinzenta em torno de "estatística demográfica neutra" e
"definição metodológica com número".

### 2.2 Verificação dos padrões recorrentes (3 de 11 checados)

Reli as frases de `exemplos_ids` para os padrões #1, #2 e #5 (os três com maior `n_casos`
declarado: 14, 8 e 16 respectivamente) diretamente no gabarito, sem depender da descrição do
relatório.

- **Padrão #1 (diagnóstico histórico confundido com promessa futura, Pilar B).** Confirmado nos 8
  exemplos citados. Todos usam claramente tempo passado/fato consumado: "o estado **perdeu**
  388.031 empregos... uma redução de", "com **queda** de -11,9%... seguido por", "Esse valor
  **corresponde** a um aumento de 9,5%", "A redução da taxa de analfabetismo em comparação com a
  gestão Vilela **foi** de 0,6%, segundo dados da PNAD 2016", "**houve** uma queda de 6%". Nenhuma
  dessas frases é uma promessa de política ("reduziremos", "meta de"); todas relatam algo que já
  aconteceu, com fonte/data no passado. O padrão está corretamente descrito e é um bug real de
  `EFEITO_RE`/`is_efeito`, que não verifica tempo verbal.

- **Padrão #2 (numeração de lista/seção contada como magnitude, Pilar B).** Confirmado nos 8
  exemplos. Ex.: `"1.5 1) Reduzir a desigualdade de gênero no mundo"`, `"12 • Reduzir a níveis
  satisfatórios..."`, `"Objetivo 11: Reduzir o impacto financeiro..."`, `"9.6.1 Dar continuidade
  às ações de redução do déficit..."`, `"2) gestão por resultados, para aumentar..."`. Em nenhum
  desses 8 casos há de fato um número que quantifique a *magnitude* da promessa — o único número
  presente é rótulo de seção/objetivo/bullet. Isso bate exatamente com o mecanismo técnico descrito
  (`NUM_ANY` capturando qualquer dígito solto, incluindo numeração de lista) e é o mesmo bug, visto
  de outro ângulo, do Padrão #3 do relatório (não verificado aqui em detalhe, mas a mecânica é
  idêntica).

- **Padrão #5 (jargão vazio "baseado em evidências" disparando Pilar C sem fonte nomeada).**
  Confirmado nos 10 exemplos. Frases como "planejamento **baseado em evidências** e avaliação de
  impacto", "decisão **baseada em evidências** pelos gestores públicos", "projetos **com base em
  indicadores** de resultados e de desempenho", "a exemplo de todos os modelos aqui apresentados",
  "a exemplo **do** [frase cortada]" — nenhuma nomeia um estudo, instituição real ou lei específica
  no fragmento disponível; são exatamente o jargão genérico que o próprio codebook diz que **não**
  deveria contar como Pilar C. Um caso (S0023, "disputa por um **BNDES popular**") é interessante:
  o revisor descreve corretamente que aqui o nome da instituição é sujeito de uma reivindicação
  política ("queremos que o BNDES seja diferente"), não uma citação do BNDES como fonte/mecanismo
  — distinção sutil que o regex simples não capta, e que de fato é jargão/retórica, não evidência.

**Conclusão da auditoria de padrões:** os três padrões checados (que somados cobrem 38 dos 92
casos, ~41%) são descritos com precisão e sustentados pelas frases citadas. Não achei nenhum
exemplo que contradissesse a descrição do padrão ou que parecesse "forçado" para caber na
narrativa.

---

## 3. O motor tem bugs reais? Isso muda a conclusão do artigo?

**Sim, os bugs são reais — a auditoria independente não encontrou motivo para descartá-los.**
Meus próprios vereditos concordaram com o revisor em 23/25 (92%) da amostra, e os 3 padrões
recorrentes que reli são sustentados palavra por palavra pelas frases citadas. O relatório do
revisor não parece inflado nem seletivo (não achei "exemplo ruim" nos 3 padrões nem no 1 caso de
"motor_certo" — que é raríssimo, só 1 em 92).

**Mas a magnitude do problema precisa ser lida com cautela, pilar por pilar, e não generalizada
para "o índice inteiro é pouco confiável":**

1. **Pilar B (efeito mensurável) é o caso mais claro para correção antes de publicar.** Todas as
   27 discordâncias de B nesta amostra de 204 frases são falso-positivo do motor (motor=True,
   LLM=False; 0 no sentido oposto), e ~14 dos 92 casos auditados batem exatamente no padrão
   "passado confundido com promessa futura" e outros ~8 no padrão "numeração de lista". Isso é um
   **viés direcional, não ruído**: o motor tende a inflar sistematicamente a contagem de "promessas
   quantificadas" — que é exatamente o componente do índice que mede se o candidato assume um
   compromisso numérico verificável. Como a taxa de base de B no gabarito (20,6%) é quase 3x a do
   LLM (7,4%) nesta amostra, um índice que usa o motor como está corre risco real de **superestimar**
   a base empírica das propostas, especialmente em documentos cheios de listas numeradas de
   objetivos (formato comum em planos de governo).

2. **Pilar C (jargão vazio) também é real, mas o efeito líquido é menor.** 18 falsos-positivos
   contra 7 falsos-negativos — inflação também, mas menos assimétrica que B, e o kappa de C já é o
   mais alto dos três (substancial em 3 dos 4 ciclos). Corrigir a lista de jargão ("a exemplo de"
   sem objeto nomeado, "baseado em evidências" genérico) é uma correção de regex relativamente
   barata e de baixo risco de quebrar os acertos verdadeiros.

3. **Pilar A é o mais ruidoso em kappa, mas o erro é mais equilibrado (21 falso-positivo vs. 19
   falso-negativo)** — sugere um problema de **lista de palavras-chave rígida demais** (perde
   diagnósticos legítimos que não usam os gatilhos fixos, como "IPEA", "queda de", "aumento de" sem
   as palavras exatas do `DIAG_KEYWORDS_RE`) somado a falsos-positivos em citações de rodapé/tabela
   e definições metodológicas. Não há um viés direcional claro aqui — é mais "o motor é uma régua
   grosseira" do que "o motor está sistematicamente inflando ou subestimando".

**Recomendação prática:**

- **Não reportar o índice atual no artigo sem, no mínimo, corrigir os bugs do Pilar B** (checagem
  de tempo verbal antes de `EFEITO_RE`, e excluir dígitos que são claramente numeração de
  lista/seção/objetivo do `NUM_ANY` usado como gatilho de B). Esse é o pilar com o viés mais
  limpo e mais fácil de demonstrar/corrigir, e é o que mais distorce direcionalmente o índice.
- **Vale corrigir a lista de jargão do Pilar C** (padrão #5) antes de publicar — correção de baixo
  custo, efeito moderado.
- **Para o Pilar A, a correção de regex tem retorno menor** (o erro já é mais simétrico) — melhor
  investimento aqui seria expandir a lista de gatilhos (padrão #7, "lista rígida demais") do que
  tentar eliminar falso-positivos pontuais, mas isso é um refinamento, não um bloqueador.
- **Depois de corrigir B e C, re-rodar o kappa por ciclo antes de reportar qualquer comparação
  temporal.** Como os kappas por ciclo não seguem um gradiente monotônico claro ligado à idade do
  documento (§1.2), a alegação "a confiabilidade cai em documentos mais antigos" **não está
  sustentada pelos dados atuais** — evitar essa afirmação no artigo a menos que o padrão mude após
  a correção do motor.
- **Não superestimar a confiança do resultado apenas porque a auditoria bateu 92%.** Uma amostra
  de 25 com 2 casos de fronteira é compatível tanto com "o revisor é confiável" quanto com "ainda
  há uma margem de ~5-10% de decisões subjetivas em qualquer leitura humana/LLM desse codebook,
  inclusive a minha". O LLM cego também não é gabarito absoluto — kappa mede concordância entre
  dois codificadores imperfeitos, não acerto contra uma verdade externa. A conclusão "o motor tem
  bugs identificáveis e corrigíveis" é sólida; a conclusão "depois de corrigir, o índice será
  perfeitamente confiável" não foi testada aqui e não deve ser assumida.

---

## 4. Limitações desta validação

- A amostra de 25/92 discordâncias (27%) é suficiente para estimar uma taxa de concordância
  aproximada, mas um intervalo de confiança formal (binomial, n=25) em torno de 92% é largo
  (aprox. 74%–99% a 95%); não tratar "92%" como uma medida de precisão.
- Só 3 dos 11 padrões recorrentes foram verificados por releitura de frases; os outros 8 (números
  soltos sem sentido, frases cortadas, lista de instituições incompleta do Pilar C, gatilhos
  rígidos do Pilar A, "maior/menor índice" ambíguo, citação de rodapé/tabela, casos genuinamente
  indecidíveis) não foram auditados aqui e devem ser tratados como reportados pelo revisor, não
  como confirmados de forma independente.
- Frases nesta amostra são frequentemente fragmentos cortados por segmentação de sentença/extração
  de PDF — isso por si só é uma fonte de discordância genuína entre qualquer par de codificadores
  (padrão #4 do relatório, "frases cortadas"), não necessariamente um "bug" corrigível no sentido
  de regex.
