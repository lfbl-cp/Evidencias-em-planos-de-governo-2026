# Planos de Governo — Região Sul (RS, SC, PR), Eleições 2026

**Relatório comparativo | Rio Grande do Sul, Santa Catarina e Paraná**
Preparado para: Felipe (UFPE) — Projeto de análise de planos de governo, ciclo eleitoral 2026
Data da coleta: agosto de 2026

## 1. Escopo e metodologia

Este relatório cobre os 6 candidatos a governador mais competitivos nas pesquisas eleitorais mais recentes (agosto de 2026) nos 3 estados da Região Sul — Rio Grande do Sul, Santa Catarina e Paraná — a partir dos textos oficiais de "proposta de governo" registrados no Tribunal Superior Eleitoral (TSE). A seleção de candidatos seguiu o mesmo processo adversarial de duas rodadas de pesquisa independente usado nas regiões anteriores (Nordeste, Norte, Centro-Oeste, Sudeste): dois agentes pesquisaram de forma independente os candidatos mais competitivos de cada estado via múltiplas pesquisas eleitorais recentes, com posterior verificação cruzada contra o cadastro oficial de candidaturas do TSE (número de sequência do candidato, partido e vice confirmados nominalmente).

A extração de texto dos PDFs, a tokenização, as stopwords, a segmentação temática exaustiva por marcadores de seção reais de cada documento, e o cálculo do Índice de Base Empírica (heurística de três pilares — diagnóstico com dado numérico, efeito mensurável projetado, e evidência causal externa citada — aplicada via expressões regulares sobre trechos de texto) são **idênticos, sem nenhuma alteração de código**, aos usados desde a primeira rodada (Nordeste). Isso garante que os números entre regiões sejam comparáveis.

Uma particularidade importante desta rodada: em **2 dos 3 estados (RS e PR), o governador atual não é candidato à reeleição**, por limite constitucional de mandatos já cumpridos — Eduardo Leite (PSDB, RS) e Ratinho Junior (PSD, PR) disputam, respectivamente, o Senado e permanecem fora da disputa estadual. Isso torna essas duas corridas "sem incumbente", com os dois principais concorrentes classificados como "desafiante" em ambos os casos — um padrão distinto das rodadas anteriores, que em geral opuseram um governador em exercício a um desafiante. Apenas Santa Catarina segue o padrão mais comum, com Jorginho Mello (PL) como incumbente pleno buscando reeleição.

### 1.1 Caso especial — Paraná: empate técnico pelo 2º lugar

No Paraná, Sergio Moro (PL) lidera isoladamente as pesquisas de agosto/2026 (37%–46%, conforme o instituto), mas o **2º lugar foi objeto de empate técnico genuíno** entre Requião Filho (PDT) e Sandro Alex (PSD, candidato ligado ao grupo do governador Ratinho Junior). Como apenas um dos dois poderia ser incluído na análise (mantendo o padrão de 2 candidatos por estado usado em toda a série), foi feita uma arbitragem dedicada: um agente de pesquisa levantou 8 pesquisas eleitorais distintas publicadas entre julho e agosto de 2026 (Genial/Quaest, Neokemp ×2, IRG Pesquisas ×2, Paraná Pesquisas, Real Time Big Data, Alfa Inteligência) e aplicou um critério objetivo e reprodutível: **menor número de derrotas estatisticamente significativas (fora da margem de erro) contra o rival direto**. Resultado: Requião Filho venceu 4 pesquisas e perdeu 2 (com 2 empates técnicos), contra 2 vitórias e 4 derrotas de Sandro Alex — robusto mesmo excluindo a única pesquisa com contratante partidário (Paraná Pesquisas, contratada pelo PL, partido do próprio Moro).

**Nota de transparência metodológica**: um recorte considerando só as pesquisas mais recentes (as de agosto) inverteria esse resultado a favor de Sandro Alex, que venceu 2 das 4 pesquisas de agosto contra 1 de Requião Filho (a única favorável a Requião no período foi justamente a pesquisa com viés partidário potencial). Trata-se, portanto, de um empate técnico genuíno que poderia razoavelmente ter sido resolvido em qualquer direção — a escolha de Requião Filho reflete o critério de "desempenho agregado ao longo de todo o período disponível" em vez de "tendência mais recente", uma decisão explícita, não uma constatação inequívoca. **Correção de contagem (25/08/2026)**: a arbitragem original citou "8 pesquisas", mas uma reverificação encontrou pelo menos uma 9ª pesquisa elegível no período (Paraná Pesquisas, início de julho, distinta da pesquisa Paraná Pesquisas de agosto já contabilizada) que não entrou no cômputo original — não foi reincorporada retroativamente ao critério objetivo desta arbitragem (o que exigiria repetir o levantamento completo), mas fica registrado que "8" subestima ligeiramente o universo de pesquisas disponíveis à época.

**Atualização (25/08/2026)**: pesquisas publicadas nas duas semanas seguintes ao fechamento desta arbitragem (ex.: TMC/Instituto Alfa, 24/08: Sandro Alex 26% x Requião Filho 20%; Paraná Pesquisas, 17/08: cenário semelhante) mostram Sandro Alex consolidando — não apenas mantendo — a vantagem sobre Requião Filho que já aparecia no recorte "só agosto" citado acima. A tendência que a nota de transparência original já sinalizava como possível parece estar se confirmando. Por consistência metodológica com a decisão já tomada e documentada (critério de desempenho agregado no período da arbitragem, não o mais recente ponto de pesquisa), este relatório mantém Requião Filho como o candidato analisado; mas o pesquisador responsável pelo projeto deve considerar, para rodadas futuras ou atualizações do PR, refazer a arbitragem com o conjunto de pesquisas atualizado — o resultado hoje provavelmente favoreceria Sandro Alex.

**Nota (25/08/2026) — Sandro Alex adicionado como 3º candidato pleno do PR**: a pedido do pesquisador responsável pelo projeto, que revisou o critério de seleção de candidatos para cobrir TODOS os candidatos competitivos nas pesquisas (em vez de um número fixo por estado), Sandro Alex passou a ser analisado como candidato pleno na análise específica do Paraná (`parana/analise/analise.json` e `parana/dashboard/dashboard.html`), ao lado de Sergio Moro e Requião Filho — ver `metodologia_nota` do JSON do PR para o detalhe completo da decisão. Seu plano de governo (274 páginas, 59.301 palavras de corpo) é de longe o mais extenso dos três do PR (Sergio Moro: 23.134 palavras; Requião Filho: 3.885 palavras) e também registra o maior Índice de Base Empírica da rodada (6,6%, contra 1,2% de Moro e 0,0% de Requião Filho); seu tema dominante na distribuição temática exaustiva é "outros" (33,1%, refletindo a extensa seção de fundamentos conceituais do Plano — visão, método, arquitetura das "Cinco Pontes" — antes do bloco de propostas), seguido por economia (16,0%) como principal tema substantivo. Esta adição ainda não foi propagada aos agregados estatísticos da Região Sul apresentados nas Seções 2 a 8 abaixo (tabela de candidatos, estatísticas por categoria, correlações e densidade de jargão), que continuam refletindo o recorte original de 6 candidatos (2 por estado) usado para fechar esta rodada do relatório — uma atualização completa desses agregados para 7 candidatos fica para uma rodada futura. O dataset consolidado da região (`dados_consolidados_sul.json`) e o gráfico comparativo (`grafico_comparativo_sul.html`) já foram regenerados e incluem Sandro Alex.

## 2. Os 6 candidatos analisados

*Números recalculados em 25/08/2026 na segunda rodada de correção do Índice de Base Empírica — ver relatório do Nordeste, Seção 9, para o detalhamento completo (validação estatística, correção de regex, migração para o índice de cobertura). O índice pela fórmula anterior (já com o regex corrigido) foi preservado em `indice_base_empirica_legado_pct`, em `dados_consolidados_sul.json` e em cada `analise.json` estadual.*

| Candidato | Estado | Partido | Situação | Palavras (corpo) | Índice de Base Empírica |
|---|---|---|---|---|---|
| Juliana Brizola | RS | PDT | Desafiante (ex-deputada estadual) | 15.780 | 5,7% |
| João Rodrigues | SC | PSD | Desafiante (ex-prefeito de Chapecó) | 6.428 | 4,5% |
| Luciano Zucco | RS | PL | Desafiante (deputado federal) | 28.644 | 3,1% |
| Jorginho Mello | SC | PL | Incumbente pleno (governador em exercício) | 3.353 | 1,8% |
| Sergio Moro | PR | PL | Desafiante (senador, ex-juiz/ex-ministro) | 23.134 | 1,2% |
| Requião Filho | PR | PDT | Desafiante (deputado estadual) | 3.885 | 0,0% |

## 3. Estatísticas por categoria

| Categoria | n | Média | Desvio padrão | Mediana | Mín. | Máx. |
|---|---|---|---|---|---|---|
| Desafiante | 5 | 2,90% | 2,09 | 3,1% | 0,0% | 5,7% |
| Incumbente pleno | 1 | 1,8% | — | 1,8% | 1,8% | 1,8% |
| **Total (6 candidatos)** | **6** | **2,72%** | **1,95** | **2,45%** | **0,0%** | **5,7%** |

Com apenas 1 caso na categoria "incumbente pleno" (Jorginho Mello), qualquer comparação incumbente-vs-desafiante nesta rodada é necessariamente ilustrativa, não estatisticamente robusta. Dito isso, é digno de nota que o único incumbente da rodada tem Índice de Base Empírica abaixo da média dos desafiantes (1,8% vs 2,9%) — nesta amostra pequena, não há sinal de que estar no poder produza planos mais ancorados em evidência do que os de quem desafia; se algo, a leitura é na direção oposta, embora com n=1 no grupo incumbente isso não deva ser lido como um achado robusto.

## 4. Requião Filho: o terceiro caso de Índice de Base Empírica igual a zero

Entre os 57 candidatos analisados em todo o projeto (as 5 regiões concluídas, incluindo Sandro Alex no PR e a Paraíba dentro do recorte do Nordeste), **Requião Filho é um de apenas quatro candidatos a registrar Índice de Base Empírica de exatamente 0,0%**, ao lado de Lucas Ribeiro (PB, Nordeste), Ciro Gomes (CE, Nordeste) e Renan Filho (AL, Nordeste) — nenhum dos trechos analisados em seu plano de 3.885 palavras atendeu a nenhum dos três pilares da heurística (diagnóstico com dado numérico, efeito mensurável projetado, evidência causal externa citada), nem contém frases de "compromisso sem lastro" suficientes para compor sequer o denominador do índice de cobertura. Isso não significa necessariamente que o plano seja de baixa qualidade substantiva — o texto de Requião Filho é estruturado como uma lista de compromissos concretos e específicos ("Zerar a carga estadual de ICMS das micro e pequenas [empresas]", "Criar um centro de governo para coordenar prioridades") — mas sim que esses compromissos são apresentados sem o tipo de embasamento quantitativo (diagnóstico numérico, projeção de efeito, ou citação de fonte externa) que a heurística mede especificamente. É um lembrete importante de que o Índice de Base Empírica mede um tipo específico e estreito de evidenciação textual, não a qualidade geral de uma proposta de governo — e que 0,0% não é um evento isolado no projeto, mas já ocorreu em 4 dos 57 candidatos analisados (≈7% da amostra total).

## 5. Correlações

Com um n pequeno (6 candidatos), os coeficientes abaixo devem ser lidos como descritivos desta amostra específica, não como estimativas robustas de um padrão nacional — mas são registrados aqui para alimentar a discussão metodológica em curso sobre a sensibilidade do Índice de Base Empírica ao tamanho do documento (ver `NOTAS_METODOLOGICAS_PENDENTES.md`). Ao preparar este relatório, recalculamos diretamente os três coeficientes para **todas as 5 regiões já concluídas** (a partir dos datasets consolidados de cada uma) — **tabela atualizada em 25/08/2026** para refletir a segunda rodada de correção do Índice de Base Empírica (ver relatório do Nordeste, Seção 9); os números abaixo substituem os de qualquer versão anterior deste relatório.

| Região (n candidatos) | r(índice, palavras) | r(índice, jargão) | r(jargão, palavras) |
|---|---|---|---|
| Nordeste (21) | +0,73 | −0,48 | −0,46 |
| Norte (14) | +0,93 | −0,58 | −0,43 |
| Centro-Oeste (8) | −0,07 | −0,50 | −0,27 |
| Sudeste (7) | −0,34 | +0,32 | +0,10 |
| **Sul (6)** | **+0,18** | **−0,59** | **+0,22** |

- **r(índice, palavras)**: essa correlação **não** tem sido consistentemente positiva nem negativa — é fortemente positiva no Nordeste (+0,73, muito influenciada por um outlier: ACM Neto/BA, com plano de 75.226 palavras e índice de 29,0%; sem ele, cai para +0,30) e no Norte (+0,93, dominada de forma ainda mais extrema pelo outlier Omar Aziz/AM — ver relatório do Norte, Seção 3), fica próxima de zero no Centro-Oeste (−0,07), negativa moderada no Sudeste (−0,34) e fracamente positiva no Sul (+0,18). Mais uma evidência de que **não existe, nos dados coletados até agora, uma relação estável e unidirecional entre tamanho do documento e Índice de Base Empírica**: ela muda de sinal e de magnitude a cada região, o que é o esperado com amostras de 6 a 21 candidatos e reforça a necessidade de tratar essas correlações regionais como descritivas, não preditivas.
- **r(índice, jargão)**: esta correlação **tem sido consistentemente negativa em 4 das 5 regiões** (Nordeste −0,48, Norte −0,58, Centro-Oeste −0,50, Sul −0,59, todas na faixa moderada), com o Sudeste como única exceção (+0,32, positiva fraca a moderada, amostra pequena e desbalanceada) — um padrão bem mais estável e replicável do que o de r(índice, palavras), e consistente com a análise de sensibilidade feita sobre o projeto inteiro na segunda rodada de correção (ver metodologia).
- **r(jargão, palavras) ≈ +0,22**: fraca e positiva no Sul; nas demais regiões variou entre negativa moderada (Nordeste −0,46, Norte −0,43, Centro-Oeste −0,27) e levemente positiva (Sudeste +0,10) — como esperado, essa correlação não é afetada pela correção do índice (jargão e tamanho do documento são medidas independentes da fórmula do índice), então os números aqui são os mesmos de antes da correção.

## 6. Densidade de jargão ("fortalecer" + "ampliar")

| Categoria | n | Média (/mil) | Desvio padrão | Mediana | Mín. | Máx. |
|---|---|---|---|---|---|---|
| Desafiante | 5 | 11,16 | 2,93 | 11,66 | 6,22 | 14,39 |
| Incumbente pleno | 1 | 10,14 | — | 10,14 | 10,14 | 10,14 |
| **Total (6 candidatos)** | **6** | **10,99** | **2,70** | **10,90** | **6,22** | **14,39** |

*(Densidade de jargão não é afetada pela correção do índice — mesmos números de antes.)* Sergio Moro (PR) tem a maior densidade de jargão da rodada (14,39/mil), acompanhando um Índice de Base Empírica baixo (1,2%) — consistente com a correlação negativa relatada acima. João Rodrigues (SC) tem a menor densidade (6,22/mil) e um dos maiores índices da rodada (4,5%), no extremo oposto do mesmo padrão — embora Juliana Brizola (RS), com densidade de jargão intermediária (11,66/mil), tenha hoje o maior índice da rodada (5,7%), lembrando que a correlação é moderada, não determinística.

## 7. Rio Grande do Sul e Paraná: disputas sem governador candidato

Diferentemente da maioria dos estados já analisados no projeto — em que o governador em exercício concorre à reeleição e compete diretamente com um desafiante —, tanto o RS quanto o PR têm em 2026 disputas **sem nenhum candidato que seja o governador atual**, por limite constitucional de reeleições já esgotado. Isso significa que, nestes 2 estados, a comparação "incumbente vs. desafiante" simplesmente não se aplica: ambos os concorrentes mais competitivos em cada corrida nunca ocuparam o cargo de governador. É um contraste útil frente às rodadas anteriores, em que a maioria dos estados tinha essa dinâmica incumbente-desafiante como eixo central da corrida — aqui, a competição em RS e PR se dá inteiramente entre outsiders do Executivo estadual (deputados federais/estaduais, ex-prefeitos, um senador), o que pode ajudar a explicar por que os planos de RS e PR tendem a ser mais extensos e detalhados (os dois maiores planos da rodada, de Zucco e Moro, vêm justamente desses dois estados) — candidatos sem histórico de governo podem sentir mais necessidade de demonstrar detalhamento programático.

## 8. Limitações

- **Amostra pequena e desbalanceada**: 6 candidatos em 3 estados, com apenas 1 caso na categoria "incumbente pleno" — as estatísticas por categoria (especialmente desvio padrão) devem ser lidas como descritivas desta amostra, não como estimativas populacionais.
- **Correlações instáveis**: com n=6, os coeficientes de correlação relatados na Seção 5 têm intervalos de confiança amplos e podem mudar substancialmente com a adição de poucos casos — devem ser vistos como pontos de dados para o debate metodológico em curso, não como conclusões definitivas.
- **Empate técnico no Paraná**: a inclusão de Requião Filho (em vez de Sandro Alex) no lugar do 2º colocado no PR foi uma decisão de arbitragem sobre um empate técnico genuíno — ver Seção 1.1. Um recorte diferente das pesquisas (por exemplo, priorizando só as mais recentes) teria levado à inclusão de Sandro Alex em seu lugar, com resultados de análise textual necessariamente diferentes.
- **Índice de Base Empírica mede evidenciação textual específica, não qualidade geral do plano**: como discutido na Seção 4 a propósito de Requião Filho, um índice baixo ou zero não implica necessariamente um plano de baixa qualidade substantiva — apenas que o texto não emprega o tipo específico de embasamento quantitativo que a heurística busca.
- **Verificação de vices**: todos os vices relatados neste relatório e nos dashboards individuais foram confirmados contra o cadastro oficial de candidaturas do TSE (mesma sequência de coligação do titular), não apenas contra fontes jornalísticas.
- **Extração de PDF**: nenhum defeito grave de extração foi identificado nos 6 documentos (sem mojibake, sem ligaduras tipográficas fi/fl quebradas de forma significativa, sem colunas fora de ordem generalizadas) — a única ressalva notável está documentada no `metodologia_nota` do JSON de cada estado: rodapés/cabeçalhos repetidos (ex. "ZUCCO GOVERNADOR / SILVANA COVATTI VICE" repetido 96× no plano de Zucco; "COLIGAÇÃO FÉ NO TRABALHO E PÉ NA TÁBUA" repetido 23× no de Jorginho Mello) que inflam artificialmente a frequência de algumas palavras nos rankings de termos mais frequentes, sem afetar o cálculo do Índice de Base Empírica ou da distribuição temática.

## 9. Nota sobre uso de IA

Este relatório foi produzido com apoio de Claude (Anthropic) em um processo supervisionado por Felipe (UFPE): a seleção de candidatos passou por duas pesquisas independentes com citação de fontes e verificação cruzada contra o cadastro oficial do TSE; o empate técnico no Paraná foi resolvido por uma arbitragem dedicada com critério objetivo, declarado e reproduzível (Seção 1.1), incluindo nota explícita de que um critério alternativo teria produzido resultado diferente; o motor de análise textual (tokenização, segmentação temática, Índice de Base Empírica) é código determinístico e idêntico ao usado em todas as rodadas anteriores do projeto, sem intervenção discricionária por estado; e todos os dashboards e o gráfico comparativo foram validados automaticamente (Playwright headless) para garantir ausência de erros de console, de requisições de rede externas, e de valores "undefined"/"NaN" visíveis.

## 10. Arquivos desta rodada

- `dados_consolidados_sul.json` — dataset consolidado dos 7 candidatos (inclui Sandro Alex; ver nota na Seção 1.1), com `indice_base_empirica_legado_pct` preservando a fórmula anterior à segunda rodada de correção de 25/08/2026 — ver relatório do Nordeste, Seção 9
- `grafico_comparativo_sul.html` — gráfico comparativo interativo (Índice de Base Empírica e densidade de jargão), regenerado em 25/08/2026 com os 7 candidatos
- `rio-grande-do-sul/analise/`, `rio-grande-do-sul/dashboard/` — análise e painel individual do RS (Zucco vs. Brizola)
- `santa-catarina/analise/`, `santa-catarina/dashboard/` — análise e painel individual de SC (Jorginho Mello vs. João Rodrigues)
- `parana/analise/`, `parana/dashboard/` — análise e painel individual do PR (Moro, Requião Filho e, desde 25/08/2026, Sandro Alex)
