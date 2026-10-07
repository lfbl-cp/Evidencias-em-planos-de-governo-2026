# Base empírica nos planos de governo do Norte 2026: o que os dados mostram

*Análise comparativa de 14 planos de governo, 6 estados (AC, AM, AP, PA, RO, TO), eleição 2026. Mesma metodologia usada na análise dos 9 estados do Nordeste — ver ressalvas metodológicas ao final, sobretudo sobre o tamanho pequeno da amostra desta rodada. **Atualização (25/08/2026)**: total elevado de 12 para 14 candidatos com a adição de Hildon Chaves (RO) e David Almeida (AM) como candidatos plenos — ver seções 7 e 8.*

---

## 1. Escopo desta rodada

Esta é a segunda etapa do projeto de análise de planos de governo estaduais, depois do Nordeste (21 candidatos, 9 estados). Cobre os candidatos mais competitivos, segundo pesquisas, em cada um dos 6 estados da região Norte: Acre, Amazonas, Amapá, Pará, Rondônia e Tocantins — originalmente 2 por estado (12 planos de governo no total); **atualização (25/08/2026)**: o critério de seleção passou a cobrir todos os candidatos competitivos nas pesquisas, não um número fixo por estado, e Rondônia e Amazonas passaram a ter 3 candidatos cada (Hildon Chaves e David Almeida, respectivamente — ver seções 7 e 8), elevando o total desta rodada para 14 planos de governo. **Roraima ficou de fora desta rodada.** **Correção (25/08/2026)**: a justificativa original aqui ("eleição suplementar com calendário próprio, diferente dos demais 26 estados") estava imprecisa e desatualizada. A eleição suplementar de Roraima (para preencher o mandato-tampão após a cassação de Antonio Denarium) já se encerrou em junho/2026, com Arthur Henrique (PL) declarado o mais votado (resultado sub judice à época). Roraima **também** tem eleição regular no mesmo calendário nacional de 4 de outubro de 2026 (2º turno em 25/10, se necessário) para o mandato pleno de 4 anos, com 5 candidatos já registrados (Arthur Henrique/PL, Clébio Genuíno/PCO, Farah Mesquita/Solidariedade, Rosi Aires/PSOL, Soldado Sampaio/Republicanos) — ou seja, Roraima não é estruturalmente diferente dos demais 26 estados nesta rodada regular. A exclusão do estado desta análise do Norte não tem, portanto, justificativa metodológica sólida a essa altura; foi simplesmente uma lacuna de cobertura desta rodada, ainda não corrigida, que fica registrada aqui para decisão em uma futura atualização (levantar os 2 candidatos mais competitivos entre os 5 registrados e aplicar a mesma metodologia usada nos demais estados do Norte).

**Nota sobre a segunda rodada de correção do índice (25/08/2026)**: todos os números deste relatório já refletem a validação estatística e a migração do Índice de Base Empírica para a definição de "índice de cobertura", aplicada de forma centralizada aos 6 estados do Norte junto com todo o resto do projeto — ver o relatório do Nordeste, Seção 9, para o detalhamento completo (validação por segundo codificador, correções de regex, e a razão para a mudança de denominador). O índice pela fórmula anterior (já com o regex corrigido) foi preservado em `indice_base_empirica_legado_pct`, ao lado do novo `indice_base_empirica_pct`, em `dados_consolidados_norte.json` e em cada `analise.json` estadual.

Importante fixar de saída: **esta é uma amostra muito menor que a do Nordeste** — 2 candidatos por estado, ante 2–3 no Nordeste, mas aqui aplicados a apenas 6 estados em vez de 9, o que deixa a maioria das categorias políticas (incumbente pleno, incumbente por sucessão, candidato de continuidade) com 1 a 3 observações. Qualquer leitura de "padrão" nesta seção deve ser lida como **descritiva desta amostra específica**, não como um achado estatisticamente robusto — o valor está mais em preparar o terreno para a análise nacional (27 estados, quando os quatro grupos terão de 15 a 40+ observações cada) do que em tirar conclusões definitivas já aqui.

---

## 2. Estatísticas descritivas por categoria

| Categoria | n | Média | Desvio padrão | Mediana | Mín. | Máx. |
|---|---|---|---|---|---|---|
| Desafiante | 8 | 5,96% | 7,34 | 2,75% | 0,5% | 23,8% |
| Candidato de continuidade | 3 | 2,10% | 0,67 | 2,30% | 1,2% | 2,8% |
| Incumbente por sucessão | 2 | 1,35% | 0,75 | 1,35% | 0,6% | 2,1% |
| Incumbente pleno | 1 | 0,6% | — | 0,6% | 0,6% | 0,6% |
| **Total (14 candidatos)** | **14** | **4,09%** | **5,98** | **2,15%** | **0,5%** | **23,8%** |

*(Desvio padrão populacional. Tabela recalculada em 25/08/2026 com os 14 candidatos já incluindo Hildon Chaves e David Almeida (seções 7 e 8) e a segunda rodada de correção do índice — ver relatório do Nordeste, Seção 9, para o detalhamento da correção. "Incumbente pleno" tem n=1 — Clécio Luís, único governador do Norte buscando reeleição direta entre os 14 analisados — e "incumbente por sucessão" tem n=2: qualquer estatística de dispersão nesses grupos deve ser lida com essa limitação em mente, mais ainda do que no relatório do Nordeste.)*

O padrão de ordenação entre categorias lembra o do Nordeste (continuidade/sucessão mais baixo que desafiante), mas aqui a diferença entre grupos é menor e um único candidato — Omar Aziz — domina boa parte da média do grupo "desafiante": sem ele, a média de desafiantes cai de 5,96% para **3,41%**, ainda acima de "candidato de continuidade", mas por margem bem mais estreita. Isso é tratado em detalhe na Seção 4.

---

## 3. Um outlier estrutural: o plano de Omar Aziz (AM)

Antes de qualquer leitura comparativa, é preciso registrar um fato que não tem equivalente em nenhum dos 21 planos do Nordeste: o plano de governo de Omar Aziz (PSD, Amazonas) tem **1.552 páginas e cerca de 433 mil palavras** — mais de cinco vezes o segundo maior documento já analisado no projeto inteiro (ACM Neto, Bahia, ~75 mil palavras) e mais de 24 vezes a média dos outros 11 candidatos do Norte (~18 mil palavras). É um documento em estilo quase acadêmico, com referências bibliográficas numeradas espalhadas ao longo de várias seções — não um anexo isolado — e citações de estudos e fontes institucionais nacionais e internacionais. A extração confirmou que o conteúdo é genuíno (não é ruído de OCR nem duplicação de páginas), mas o arquivo fundido a partir das 8 partes em que o TSE distribuiu o PDF não preserva a ordem de leitura original — o script de análise precisou segmentar por títulos de capítulo reais, na ordem em que aparecem no arquivo, com uma granularidade mais grossa que o padrão do projeto (documentado em detalhe no script `build_analysis_am.py` e no arquivo de auditoria `_debug_segmentos_omar-aziz.txt`).

Esse tamanho atípico tem uma consequência direta sobre o índice: Omar Aziz tem o maior Índice de Base Empírica de toda a região Norte (23,8%) — mecanicamente esperado, já que um documento 24 vezes maior tem 24 vezes mais oportunidades estatísticas de conter uma frase de diagnóstico, efeito mensurável ou citação de fonte (o mesmo confundidor de tamanho já documentado no relatório do Nordeste, Seção 7). A correlação entre número de palavras e índice nos 14 candidatos do Norte é **r ≈ 0,93** — muito mais forte que a do Nordeste (r ≈ 0,73) — precisamente porque Omar Aziz é um outlier tão extremo que domina o cálculo. Excluindo-o, a correlação cai para **r ≈ 0,51**, moderada, mas em linha com o padrão já visto no Nordeste.

**Recomendação de leitura**: trate o índice de Omar Aziz como não comparável em pé de igualdade com os outros 13 candidatos desta rodada — ele reflete, em boa parte, a escala do documento, não necessariamente um plano proporcionalmente mais rigoroso. Nas subseções seguintes, quando relevante, os números são reportados com e sem ele.

---

## 4. Continuidade/sucessão volta a pontuar mais baixo — mas com margem estreita

Cinco dos 12 candidatos do Norte concorrem como parte de uma continuidade de governo — dois por sucessão dentro do próprio mandato (assumiram quando o titular saiu) e três como candidatos de continuidade apoiados pelo governador em exercício:

| Candidato | Partido | Estado | Situação | Índice de Base Empírica |
|---|---|---|---|---|
| Adailton Fúria | PSD | Rondônia | Candidato de continuidade (apoiado pelo governador Marcos Rocha) | **2,8%** |
| Professora Dorinha | União | Tocantins | Candidata de continuidade (apoiada pelo governador Wanderlei Barbosa) | **2,3%** |
| Hana Ghassan | MDB | Pará | Incumbente por sucessão (assumiu com a renúncia de Helder Barbalho) | **2,1%** |
| Alan Rick¹ | Republicanos | Acre | — ver nota ¹ | 2,1% |
| Roberto Cidade | União | Amazonas | Candidato de continuidade (indicado por Wilson Lima) | **1,2%** |
| Mailza Assis | PP | Acre | Incumbente por sucessão (assumiu com a renúncia de Gladson Cameli) | **0,6%** |

*¹ Alan Rick foi classificado como "desafiante" pela verificação do estado do Acre — embora do mesmo campo político de Gladson Cameli, ele concorre como opositor à candidata de continuidade (Mailza Assis) numa disputa interna à direita. Está listado aqui só para contexto de proximidade política, não como parte do grupo "continuidade" nas contagens.*

Média do grupo de continuidade/sucessão (5 candidatos, excluindo Alan Rick): **1,80%**, desvio padrão populacional 0,79 — mais baixo que a média geral da região (4,09%), replicando na direção o achado central do relatório do Nordeste, mas com margem mais estreita: no Nordeste, o grupo de continuidade tinha média 0,50%, menos de um terço da encontrada aqui. Uma leitura possível é que a amostra do Norte simplesmente não tem um caso tão extremo quanto Renan Filho (0,0%, 1.129 palavras) ou Lucas Ribeiro (0,0%, 3.837 palavras) — os dois candidatos mais curtos do Nordeste inteiro; os cinco candidatos de continuidade/sucessão do Norte têm documentos de tamanho mais convencional (7 mil a 31 mil palavras).

---

## 5. O único incumbente pleno da rodada: Clécio Luís (AP)

Com n=1, não há como calcular dispersão ou tirar uma conclusão de grupo — mas vale registrar o caso individual: Clécio Luís, governador em exercício do Amapá buscando reeleição direta, tem um dos índices mais baixos de toda a região Norte (0,6%) — só Hildon Chaves (RO, 0,5%) fica abaixo dele, e ele empata com Mailza Assis (AC) e Dr. Daniel Santos (PA), também em 0,6%. Isso destoa do padrão observado no Nordeste, onde o grupo de incumbentes plenos tinha a segunda maior média (3,92%) entre as quatro categorias, com Rafael Fonteles (Piauí) isoladamente pontuando 7,4%. Um único caso não permite generalizar — mas é um contraponto que a análise nacional, com mais incumbentes plenos na amostra, poderá esclarecer se é um caso isolado ou parte de um padrão diferente do Nordeste.

---

## 6. Densidade de jargão "fortalecer"/"ampliar": um padrão invertido em relação ao Nordeste

A mesma métrica de densidade de jargão calculada para o Nordeste (ocorrências das famílias "fortalec-"/"ampli-" por mil palavras) foi recalculada para os 14 candidatos do Norte:

| Categoria | n | Média (/mil palavras) | Desvio padrão | Mediana | Mín. | Máx. |
|---|---|---|---|---|---|---|
| Incumbente pleno | 1 | 19,34 | — | 19,34 | 19,34 | 19,34 |
| Incumbente por sucessão | 2 | 18,61 | 0,20 | 18,61 | 18,41 | 18,81 |
| Desafiante | 8 | 9,31 | 4,26 | 9,51 | 3,57 | 15,45 |
| Candidato de continuidade | 3 | 9,01 | 2,40 | 8,99 | 6,08 | 11,96 |
| **Total (14 candidatos)** | **14** | **11,29** | **5,22** | **10,84** | **3,57** | **19,34** |

A direção do achado do Nordeste se confirma com folga: candidatos ligados à situação (incumbente pleno + sucessão) usam mais ou menos o dobro do jargão "fortalecer/ampliar" que desafiantes e candidatos de continuidade — 18,6%–19,3/mil contra 9,0–9,3/mil. É, na verdade, um contraste **mais nítido** que no Nordeste (17,34 contra 10,08/mil para os mesmos dois grupos-tipo). Curiosamente, Omar Aziz — o candidato com o maior índice de base empírica da região — tem também a **menor densidade de jargão de toda a amostra do Norte** (3,57/mil), reforçando o padrão já visto no Nordeste de que essas duas métricas capturam sinais relacionados, mas não idênticos: a correlação entre índice e densidade de jargão nos 14 candidatos do Norte é **r ≈ -0,58** (r ≈ -0,57 sem Omar Aziz) — moderada, negativa como esperado, em linha com o r ≈ -0,48 encontrado no Nordeste. A correlação entre densidade de jargão e tamanho do documento é **r ≈ -0,45** — candidatos com planos mais longos tendem a usar levemente menos jargão por mil palavras, mesma direção (mas magnitude bem menor) da relação entre índice e tamanho.

---

## 7. Uma nota sobre Roberto Cidade e Wilson Lima

O caso de Roberto Cidade (União, Amazonas) merece registro à parte porque a verificação da categoria política exigiu checar uma linha do tempo específica: Wilson Lima, governador em exercício do Amazonas, concluiu seus dois mandatos consecutivos permitidos e renunciou em abril de 2026 para concorrer ao Senado — deixando o cargo antes do fim do mandato para viabilizar a candidatura. Roberto Cidade foi indicado e publicamente apoiado por ele como sucessor. Diferente do caso de Mailza Assis (AC) e Hana Ghassan (PA) — que já assumiram o cargo de governador por sucessão e concorrem como titulares em exercício —, Roberto Cidade concorre como candidato de continuidade sem jamais ter ocupado o cargo de governador. A distinção entre "incumbente por sucessão" (já é governador) e "candidato de continuidade" (indicado pelo titular, mas nunca ocupou o cargo principal) foi mantida consistente com o critério já usado no Nordeste para casos como Cadu Xavier (RN) e Renan Filho (AL).

**Nota sobre David Almeida (atualização de 25/08/2026)**: David Almeida (Avante), prefeito de Manaus licenciado, é o 3º nome competitivo na corrida ao governo do Amazonas e não está coberto nesta análise (que segue o padrão de 2 candidatos por estado do projeto). Pesquisas de 2026 mostram Roberto Cidade geralmente à frente de Almeida na disputa pelo 2º lugar atrás de Omar Aziz, mas com margens que variam de folgadas (Instituto Projeta, junho: Cidade 22,4% x Almeida 17,1%) a tecnicamente empatadas (Direto ao Ponto, junho: Almeida 21% x Cidade 20%) conforme o instituto — diferente do empate técnico mais consistente observado em Rondônia (ver nota acima), mas próximo o suficiente para merecer registro. A escolha de Roberto Cidade como 2º candidato do Amazonas não muda de recomendação com os dados disponíveis, mas o leitor deve estar ciente de que Almeida é um competidor real, não marginal.

**Atualização (25/08/2026): David Almeida foi adicionado como candidato pleno.** A pedido do pesquisador responsável, o critério de seleção do projeto passou a cobrir todos os candidatos competitivos nas pesquisas, não um número fixo por estado — e a nota acima já registrava que Almeida é "um competidor real, não marginal". Seu plano de governo ("Pra Cima, Amazonas", 76 páginas, ~18,8 mil palavras, 9 Eixos Estratégicos) tem Índice de Base Empírica de 5,1% — acima de Roberto Cidade (1,2%) mas bem abaixo de Omar Aziz (23,8%, o outlier de escala já discutido na Seção 3). Cerca de metade do documento (52%) é front matter (introdução, diagnóstico SWOT do Estado e dados gerais) classificado como "outros" na distribuição temática — proporção atipicamente alta porque esse front matter é, ele próprio, incomumente rico em dados quantitativos (IDHM, PIB, indicadores com fonte citada), o que também contribui para o índice acima da mediana da amostra; entre os temas substantivos, economia (14,1%) é o mais presente, refletindo a ênfase do plano em bioeconomia, Zona Franca de Manaus e desenvolvimento do interior. Ver `dados_consolidados_norte.json` e `../amazonas/analise/analise.json` para os números completos.

---

## 8. Limitações desta rodada

- **Amostra pequena.** 2 candidatos por estado, 6 estados — a maioria das categorias políticas tem entre 1 e 3 observações. Nenhuma das leituras acima deve ser tratada como um achado estatisticamente robusto; são descrições desta amostra específica, preparatórias para a análise nacional.
- **Outlier de escala não neutralizado.** O plano de Omar Aziz é grande o bastante para distorcer qualquer estatística agregada que o inclua sem ressalva — reportamos os números com e sem ele quando relevante, mas o leitor deve ter isso em mente ao interpretar qualquer média desta rodada.
- **Mesmas limitações estruturais já documentadas no Nordeste**: fragmentação de sentenças por quebra de linha física do PDF (afeta a segmentação de frases, já observado nos textos de Rondônia e Tocantins, entre outros), variação editorial na granularidade da classificação temática, e um resíduo de defeito de extração de PDF no plano de Dr. Furlan (AP) — um pequeno conjunto de caracteres corrompidos (ligadura "fi" tipográfica), documentado e não corrigido, seguindo o mesmo princípio de transparência do projeto.
- **Defeito de extração corrigido nesta rodada, e correção retificada numa auditoria posterior**: em Mailza Assis (AC, defeito mais severo) e Marcos Rogério (RO, "bene cios"→"benefícios", 4 ocorrências) a ligadura tipográfica "fi" havia sido extraída como um espaço em branco no meio da palavra (ex.: "pro ssionais" em vez de "profissionais"). Um reparo automatizado baseado em padrões radical+sufixo foi aplicado — mas numa auditoria de qualidade posterior, verificamos que duas dessas regras (`"de " + palavra começada em "ne-"/"ni-"` e `"de ciência"`) eram amplas demais e, ao serem aplicadas aos 12 candidatos, fundiram indevidamente palavras legítimas e distintas em 10 dos 12 planos — por exemplo "de negócios"→"definegócios" e, em dois candidatos (Dr. Furlan e Omar Aziz), "de ciência [e tecnologia]"→"deficiência" (trocando uma menção real a Ciência&Tecnologia pelo tema Deficiência/Inclusão). Essas regras foram corrigidas (restringidas ao contexto onde o defeito é genuíno — ex. "de ciência" só é tratado como "deficiência" quando precedido de "com") e todos os 12 textos foram reextraídos e reprocessados do zero; os índices de base empírica publicados não mudaram (a heurística é insensível a essas poucas dezenas de palavras por candidato), mas as nuvens de palavras e os rankings de termos mais frequentes de 10 candidatos foram regenerados livres da distorção. Ver `_repair/reparar_ligadura_fi.py` para o histórico completo da correção.
- **Categorização política checada estado a estado**, com busca externa por notícias recentes (agosto de 2026), mas sem o mesmo processo de verificação adversarial por dois agentes independentes usado para a seleção inicial dos 12 candidatos — a classificação de categoria (incumbente/desafiante/continuidade) foi feita por um único agente por estado, com fontes citadas em cada `analise.json`. Recomenda-se checagem adicional antes de qualquer publicação, sobretudo nos casos de fronteira (Alan Rick, seção 4).
- **Seleção de candidatos de Rondônia, desatualizada (atualização de 25/08/2026)**: a inclusão de Adailton Fúria como 2º colocado (atrás de Marcos Rogério, líder isolado) refletia as pesquisas disponíveis no momento da seleção original. Pesquisas mais recentes (ex.: Phoenix, 22/08/2026) mostram Adailton Fúria e Hildon Chaves em empate técnico genuíno pela 2ª colocação e pela vaga no 2º turno — situação estruturalmente parecida com o empate técnico do Paraná (ver relatório do Sul), mas aqui documentada sem uma arbitragem dedicada equivalente. A inclusão de Fúria não está mais claramente justificada como "o 2º mais competitivo" isoladamente; Hildon Chaves deveria, no mínimo, ser mencionado como alternativa igualmente defensável, e uma futura atualização desta rodada deveria considerar refazer essa escolha com uma arbitragem formal (nos moldes da usada no PR) ou reavaliar se ambos merecem ser cobertos.

  **Atualização (25/08/2026): Hildon Chaves foi adicionado como candidato pleno.** Em vez de refazer a escolha entre Fúria e Chaves, o pesquisador responsável decidiu, para esta rodada, cobrir ambos — mesmo critério agora aplicado ao caso de David Almeida (AM, ver seção 7). O plano de Hildon Chaves (138 páginas, ~33,3 mil palavras, 14 Eixos de Governo + apêndice "Plano Tático dos 100 Primeiros Dias") tem Índice de Base Empírica de 0,5% — o mais baixo dos 3 candidatos de Rondônia, abaixo até de Adailton Fúria (2,8%) e Marcos Rogério (10,1%), refletindo um texto com grande volume de propostas descritas em linguagem genérica ("fortalecer", "modernizar", "ampliar") e relativamente poucas frases com dado de diagnóstico, efeito mensurável ou evidência causal explícita nos moldes que a heurística do projeto reconhece. O tema dominante de seu plano é assistência social (22,6%), à frente de infraestrutura (14,8%) e segurança (12,6%). Ver `dados_consolidados_norte.json` e `../rondonia/analise/analise.json` para os números completos.

---

## 9. Nota sobre o uso de IA

Este estudo foi produzido com apoio de um assistente de IA (Claude, da Anthropic), sob supervisão direta do pesquisador responsável, Felipe Braga, seguindo o mesmo processo já documentado para a análise do Nordeste (ver `../nordeste/replicacao/NOTA_SOBRE_USO_DE_IA.md`, que se aplica igualmente a esta rodada). Adicionalmente nesta rodada: os planos de governo oficiais dos 6 estados foram baixados diretamente do CDN do TSE via automação de navegador (Claude em Chrome, no navegador do próprio pesquisador), e a seleção final dos 12 candidatos mais competitivos foi verificada por um processo de dois agentes de pesquisa independentes com o mesmo prompt, mais um terceiro agente de arbitragem para resolver os pontos específicos de divergência encontrados entre os dois primeiros — mesmo padrão de rigor já usado para o caso de Cadu Xavier na análise do Nordeste, agora formalizado como processo padrão do projeto.

---

## Arquivos desta pasta

- `dados_consolidados_norte.json` — tabela completa dos 14 candidatos (estado, partido, categoria, índice de base empírica, contagens/densidade das famílias de palavras "fortalec-"/"ampli-"). **Atualização (25/08/2026)**: originalmente 12 candidatos; Hildon Chaves (RO) e David Almeida (AM) foram adicionados como candidatos plenos — ver seções 7 e 8.
- `grafico_comparativo_norte.html` — página única e interativa com os dois gráficos comparativos desta rodada (Índice de Base Empírica e densidade de jargão), mesmo padrão visual do gráfico do Nordeste.
- Este relatório (`RELATORIO_COMPARATIVO_NORTE.md`).
- `../<estado>/analise/` e `../<estado>/dashboard/` (uma pasta por estado) — script de análise, `analise.json`, wordclouds e dashboard interativo de cada um dos 6 estados, mesmo padrão usado nos 9 estados do Nordeste.
