# Revisão Adversarial da Correção do Pilar B — 2ª Rodada

**Revisor:** agente adversarial, 2ª rodada do pipeline de validação (codificador cego → revisor
adversarial → validador independente). **Data:** 2026-10-09.
**Insumos:** `kappa_gabarito_v2.json` (N=204, motor corrigido), `kappa_codificador_llm.json`
(N=204, LLM cego, inalterado desde 25/09), `kappa_relatorio_falhas.json` (relatório da 1ª rodada,
usado como referência de padrões, não como verdade assumida), e leitura direta de
`programs/motor_indice_base_empirica.py` (`is_efeito`, `PASSADO_RE`, `FUTURO_RE`,
`has_real_number`, `_is_list_marker_match`).

---

## 1. Kappa recalculado: confirmação independente

Antes de julgar a correção, verifiquei que a base de comparação está correta:
- `kappa_gabarito_v2.json.pilar_b_antigo` é byte-a-byte idêntico ao `pilar_b` do
  `kappa_gabarito.json` original (0 divergências em 204) — e as 204 frases não mudaram
  (0 divergências de texto). Ou seja, a comparação "antes × depois" é sobre a mesma amostra,
  mesmo texto, só a lógica do motor mudou.
- Recalculando o kappa do zero a partir de `pilar_b_antigo` × LLM, obtive **p_o=0,868, p_e=0,751,
  κ=0,4688 ≈ 0,469** — reproduz exatamente o número do relatório de 25/09. Isso confirma que meu
  método de cálculo está correto antes de aplicá-lo ao motor novo.

**Pilar B, motor corrigido × LLM (N=204): p_o=0,961, p_e=0,830, κ=0,7689 ≈ 0,769.**

Isso **confirma de forma independente** o número que você reportou ter medido (0,769) — não é
coincidência de arredondamento, é o mesmo valor calculado do zero, por outro caminho. A melhora é
real: de 0,469 ("moderada") para 0,769 ("substancial" na escala de Landis & Koch, mas abaixo do
limiar de 0,81 para "quase perfeita"). A matriz de confusão foi de 27 falso-positivos/0
falso-negativos para **8 falso-positivos/0 falso-negativos** — nenhum caso passou a ser
"motor=False quando LLM=True" (nenhuma promessa que o motor parou de capturar), que é o tipo de
regressão mais perigoso e que a tarefa pedia para procurar especificamente. Pilar A e Pilar C
permanecem com os mesmos números do relatório de 25/09 (0,366 e 0,681) — controle negativo
confirmando que a correção não teve efeito colateral em outro pilar.

## 2. As 8 discordâncias remanescentes, uma a uma

Reli as 8 frases completas (não uma amostra — é o universo inteiro de discordâncias restantes) e
formei veredito independente antes de olhar qualquer categorização prévia.

| id | Frase | Veredito | Por quê |
|---|---|---|---|
| S0062 | "Ofertar mamografia a todas as mulheres goianas na faixa etária maior de 40 anos para redução do" | llm_correto | "40" é critério de elegibilidade (idade), não a magnitude da meta; frase cortada antes do número real. |
| S0065 | "humanidade, tenha a redução do número de visitantes, de mais de 60% a cada ano." | ambíguo | "tenha" (subjuntivo) não é claramente passado nem futuro; fragmento cortado no início — genuinamente indecidível, mesma categoria do "frases cortadas" do relatório original. |
| S0067 | "seja, redução de R$ 17 bilhões." | ambíguo | Fragmento mínimo, sem verbo; o relatório original já havia marcado este mesmo caso como ambíguo — mantenho o veredito. |
| S0070 | "mulheres não negras Queda de 10,8%." | llm_correto | Legenda telegráfica de tabela/gráfico, sem nenhum verbo — o mecanismo de tempo verbal (PASSADO_RE/FUTURO_RE) é estruturalmente incapaz de ajudar aqui, porque não há verbo para checar. |
| S0115 | "meta de transformação através de um governo Inovativo - 360 º." | llm_correto | "360º" é o clichê retórico "governo 360 graus", não uma magnitude de meta; o filtro de rótulo de lista não cobre números de 3 dígitos sem contexto de lista. |
| S0156 | "O Censo escolar 2025 apontou uma redução de 38,4 mil matrículas na educação básica do RS." | llm_correto | **O achado mais importante.** Claro diagnóstico histórico ("apontou uma redução de"), mas "apontou" não está na lista fixa de `PASSADO_RE`, e "censo (?:19\|20)\d{2}" exige adjacência direta que "Censo **escolar** 2025" quebra. O motor volta a classificar como B=True. |
| S0169 | "Restauração com aumento de capacidade da PR-170, entre o Rio Jordão e a BR-153" | llm_correto | "170"/"153" são códigos de rodovia (PR-170, BR-153), não a magnitude do "aumento" prometido; o filtro de rótulo de lista não reconhece esse formato. |
| S0172 | "global deve aumentar entre 2,5°C e 2,9°C até o fim do século – um patamar considerado extremamente" | llm_correto | Projeção científica de aquecimento global (contexto, não compromisso do candidato); "até o fim do século" até dispara `FUTURO_RE`, reforçando o falso-positivo. |

**6 de 8 são llm_correto (motor erra), 2 de 8 são ambíguos (fragmentação do PDF), 0 de 8 são
motor_correto.** O viés direcional do Pilar B (motor sempre infla, nunca "perde" uma promessa)
continua presente nos casos remanescentes — não é ruído aleatório recém-introduzido, é a mesma
assinatura de bug de antes, só que uma fatia menor dela.

## 3. Padrões generalizados (o que sobrou e o que a correção não viu)

**Padrão A — Verbo de passado fora da lista fixa (1 caso, S0156, severidade alta).**
`PASSADO_RE` é uma lista de verbos específicos, não um detector de tempo verbal. "Apontou" não
está nela (nem "revelou", "indicou", "mostrou", "demonstrou", "constatou" — nenhum destes é
testado na amostra, mas por extensão do mesmo mecanismo, provavelmente têm o mesmo problema).
Isso é o próprio Padrão #1 do relatório original, só que para um verbo que não estava entre os
8 exemplos efetivamente lidos antes da correção.

**Padrão B — Número irrelevante não coberto (4 casos: S0062, S0115, S0169, S0172, severidade
média-alta).** Já era o **Padrão #3 do relatório de 25/09**, documentado lado a lado com os
Padrões #1 e #2 que foram corrigidos — mas o comentário no código-fonte da correção (linhas
~205-236 de `motor_indice_base_empirica.py`) menciona explicitamente só "Padrões #1 e #2". O
Padrão #3 foi deixado de lado inteiro, apesar de estar catalogado na mesma fonte que motivou a
correção. É evidência direta de que a correção resolveu os bugs mais fáceis de descrever com uma
lista de palavras-gatilho, não a classe inteira de "número presente na frase que não é a
magnitude da promessa".

**Padrão C — Fragmento tipo legenda sem verbo (1 caso, S0070, severidade média).** Subtipo
novo, não previsto no relatório original: frases telegráficas de tabela/gráfico, sem sujeito nem
verbo flexionado, onde o próprio mecanismo de tempo verbal é inaplicável por falta de verbo.

**Padrão D — Risco de regressão latente: "em ANO futuro" sem "até" (0 casos na amostra, mas
confirmado por teste direto do mecanismo; severidade alta como risco).** Este é o achado que
justifica a desconfiança pedida pela tarefa. `PASSADO_RE` inclui `em (?:19|20)\d{2}` para capturar
referências a anos passados ("em 2021"), mas essa expressão regular **não diferencia ano passado
de ano futuro**. Testei diretamente contra `is_efeito()` (fora da amostra de 204, frase construída
para teste de estresse):

```
"Em 2030, aumentaremos a cobertura vacinal para 95% da população."
EFEITO_RE: match | PASSADO_RE: match ("em 2030") | FUTURO_RE: NENHUM match
is_efeito() => False   <- FALSO NEGATIVO
```

```
"Até 2030, aumentaremos a cobertura vacinal para 95% da população."
is_efeito() => True   <- correto, só porque troquei "Em" por "Até"
```

Essa é uma frase de Pilar B genuína e inequívoca — verbo no futuro, meta numérica clara, ano-alvo
explícito — classificada como falso-negativo só porque usa "Em 2030" em vez de "Até 2030".
`FUTURO_RE` só reconhece `até (?:19|20)\d{2}`, não `em (?:19|20)\d{2}`. Como "Em AAAA, [verbo no
futuro]..." é uma forma natural e comum de expressar metas em português, é muito provável que essa
construção apareça no corpus completo (~900 candidaturas, 4 ciclos) mesmo não tendo aparecido
nesta amostra de 204 frases. **Isto é exatamente o tipo de regressão que a tarefa pediu para caçar
ativamente — um verdadeiro-positivo que pode virar falso-negativo indevido — só que não é visível
nesta amostra específica, e só foi encontrado testando o mecanismo diretamente, não auditando as
204 frases.**

## 4. A correção "overfitou"?

**Parcialmente, de forma mensurável.** Dos 27 falso-positivos originais do Pilar B: os 8 exemplos
citados do Padrão #1 e os 8 do Padrão #2 (os 16 efetivamente lidos e citados no comentário da
correção) foram 100% corrigidos. Mas o Padrão #1 tinha `n_casos=14`, não 8 — dos 6 casos do mesmo
padrão que não estavam entre os exemplos citados, 3 foram corrigidos "de brinde" (por outros
gatilhos de `PASSADO_RE` coincidirem) e **3 continuam quebrados** (S0065, S0070, S0156) por usarem
formas fora da lista testada. O Padrão #3 inteiro (4 casos) não foi tocado, apesar de estar
documentado na mesma fonte. Isso é um padrão reconhecível: a correção generalizou bem para os
casos citados e para vizinhos próximos por coincidência, mas não para variações de vocabulário
fora da lista nem para a classe de erro estruturalmente diferente que já estava catalogada e foi
deixada de lado.

## 5. Conclusão e recomendação

- **Reportar o Pilar B com o kappa novo (0,769, substancial) é defensável e é uma melhora real e
  grande** sobre o 0,469 original — não é um artefato de arredondamento nem um erro de cálculo.
- **Não tratar 0,769 como "problema resolvido".** Há 8 discordâncias remanescentes em 204 frases
  (6 bugs reais do motor + 2 ambíguos), um padrão já catalogado (Padrão #3) que não foi corrigido,
  e um risco de regressão confirmado por teste direto (Padrão D) que não aparece nesta amostra mas
  é estruturalmente real e provável no corpus completo.
- **Antes de reprocessar o painel multiciclo inteiro**, pelo menos tratar o Padrão D (maior risco,
  porque pode suprimir promessas futuras genuínas) — por exemplo, fazendo `FUTURO_RE` reconhecer
  também `em (?:19|20)\d{2}` e dando precedência a futuro quando o próprio verbo-gatilho já está
  conjugado no futuro (`-emos`, `-eremos`, `-aremos`, já presentes em `EFEITO_RE`).
- Dados os achados de 25/09 e desta rodada, fica reforçada a prática do projeto: nenhuma correção
  de regex nesse motor deve ser considerada "fechada" sem reler o universo completo das
  discordâncias remanescentes (não só os exemplos citados) e sem testar o mecanismo com casos
  construídos fora da amostra, exatamente o que esta rodada fez.

---

### Arquivos desta rodada
- Dados estruturados: `analise/kappa_relatorio_falhas_v2.json`
- Este resumo em prosa: `analise/REVISAO_ADVERSARIAL_V2.md`
