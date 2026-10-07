# Nota sobre o uso de Inteligência Artificial neste estudo

Esta nota descreve, de forma direta, onde e como um assistente de IA
(Claude, da Anthropic) foi usado na produção do estudo comparativo sobre os
planos de governo dos candidatos a governador do Nordeste em 2026, para que
leitores, revisores e coautores possam avaliar o material com essa
informação em mãos.

## O que foi feito com apoio de IA

- **Extração e limpeza de texto** dos PDFs de planos de governo para os
  arquivos `.txt` usados na análise.
- **Desenho e refinamento das heurísticas léxicas/regex** que compõem o
  Índice de Base Empírica, a distribuição temática e a densidade de jargão
  — incluindo as correções documentadas em `METODOLOGIA.md` (Seção 7),
  encontradas por rodadas de auditoria independente conduzidas pela própria
  IA a pedido do pesquisador responsável.
- **Escrita dos scripts** de análise (Python), consolidação de dados,
  geração de gráficos e montagem dos dashboards HTML.
- **Redação do texto narrativo** dos relatórios (este pacote de replicação
  incluído), a partir dos números já calculados.
- **Verificação técnica**: checagem automatizada de dashboards (ausência de
  erros de console, de chamadas de rede externas, de valores "undefined"/
  "NaN" visíveis) via automação de navegador.

## O que foi decisão humana

- A **seleção dos candidatos e estados** incluídos no estudo.
- Toda **classificação de categoria política** (incumbente pleno/por
  sucessão, candidato de continuidade, desafiante) — incluindo os dois casos
  de fronteira discutidos em `METODOLOGIA.md` (Cadu Xavier e Felipe
  Camarão), que foram sinalizados, investigados (com busca externa de
  fontes jornalísticas) e resolvidos a pedido explícito do pesquisador
  responsável, Felipe Braga.
- A **interpretação** dos achados (o que o padrão de índice mais baixo em
  candidaturas de continuidade significa, os limites dessa leitura, as
  hipóteses alternativas consideradas) e a decisão de quais extensões
  metodológicas perseguir (ex.: a análise de densidade de jargão
  "fortalecer"/"ampliar" nasceu de uma pergunta específica do pesquisador).
- A **revisão e aprovação de cada etapa**: nenhum resultado foi publicado
  sem checagem humana; as correções metodológicas da Seção 7 do
  `METODOLOGIA.md`, por exemplo, só entraram no estudo depois de validação
  manual dos exemplos de frases capturados por cada versão da heurística.

## Por que isso importa e o que este pacote resolve

Análises assistidas por IA levantam uma preocupação legítima de "caixa
preta": como saber se os números publicados realmente vêm da metodologia
descrita, e não de um erro silencioso ou de um viés não documentado? Este
pacote de replicação existe justamente para responder a essa pergunta sem
exigir confiança cega — ele contém os 21 textos brutos, o código exato que
gerou os números publicados (`codigo/python/`), uma reimplementação
independente em outra linguagem (`codigo/R/`) que recalcula tudo do zero e
confere contra o publicado, e a documentação completa de cada decisão
editorial (`METODOLOGIA.md`). Qualquer divergência entre o texto do plano de
um candidato e a métrica calculada pode ser rastreada, sentença por
sentença, até a regra exata que a gerou.

## Recomendação

Publicações, artigos ou apresentações que citem números deste estudo devem
divulgar que a análise foi assistida por IA sob supervisão humana, na linha
de normas crescentes de transparência acadêmica e jornalística sobre uso de
IA em pesquisa. Esta nota pode ser adaptada livremente para esse fim.
