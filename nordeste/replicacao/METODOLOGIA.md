# Metodologia — Planos de Governo, Candidatos a Governador do Nordeste 2026

Este documento descreve, passo a passo, tudo o que foi feito para produzir o
Índice de Base Empírica, a distribuição temática, a densidade de jargão e as
demais métricas usadas no `RELATORIO_COMPARATIVO.md` e nos 9 dashboards
estaduais (Paraíba, Maranhão, Piauí, Ceará, Pernambuco, Rio Grande do Norte,
Alagoas, Sergipe, Bahia), cobrindo 21 candidatos a governador. O objetivo é
que qualquer pessoa — sem ter acompanhado o processo original — consiga
entender exatamente o que foi calculado, como, e reproduzir os números por
conta própria usando os dados e o código desta pasta.

## 1. Escopo e fontes

O estudo cobre 21 candidatos a governador em 9 estados do Nordeste com
eleição em outubro de 2026, restrito a candidaturas competitivas (ver
critério de seleção no arquivo `nordeste_2026_candidatos_competitivos.md` do
projeto original, na Paraíba). Para cada candidato foi coletado o plano de
governo oficial de campanha — o documento formal que, no Brasil, é
registrado junto à Justiça Eleitoral (TSE) e frequentemente também
divulgado pela própria campanha.

Cada plano foi convertido de PDF para texto simples (`.txt`), com um
cabeçalho padronizado no topo do arquivo (candidato, partido, vice, fonte,
status) separado do corpo do documento por uma linha `---`. Dois planos
exigiram reconhecimento óptico de caracteres (OCR) por serem PDFs
escaneados/em imagem: Felipe Camarão (MA) e Raquel Lyra (PE) — ambos têm
ruído de OCR residual documentado nas limitações (Seção 8 abaixo e Seção 9
do relatório principal).

Os 21 textos brutos estão em `dados/planos/<estado>/<slug>.txt`.

## 2. Tokenização e frequência de palavras

Cada texto (após remover o cabeçalho) é tokenizado com a expressão regular
`[a-zA-ZÀ-ÖØ-öø-ÿ][a-zA-ZÀ-ÖØ-öø-ÿ\-]*`, que captura sequências de letras
(incluindo acentuadas) e hífens internos, em minúsculas. O total de tokens
é o campo `total_palavras` usado em todo o estudo (inclui o corpo inteiro do
plano, sem excluir sumário/capa). Uma lista de stopwords (artigos,
preposições, pronomes, e termos estruturais específicos como "candidato",
"governo", o nome do estado etc.) é removida apenas para a nuvem de
palavras/top-20 — não afeta o Índice de Base Empírica nem a densidade de
jargão, que usam o texto completo.

## 3. Distribuição temática exaustiva

Cada plano foi segmentado manualmente em blocos correspondentes às suas
seções/eixos temáticos reais (lidos e mapeados um a um por quem conduziu a
análise), e cada bloco foi classificado em um de 9 temas: saúde, segurança,
educação, infraestrutura, meio ambiente, economia, gestão pública,
assistência social, outros. O percentual de cada tema é a proporção de
tokens do plano dentro dos blocos daquele tema.

Essa classificação **não é mecânica** — é uma leitura humana de cada
documento, documentada dentro de cada script Python (`codigo/python/`, listas
`MARCADORES`), para que decisões de fronteira específicas (ex.: "Cultura"
classificada como assistência social e não como um tema próprio) possam ser
auditadas e contestadas por qualquer leitor. A distribuição temática é usada
apenas como contexto complementar no relatório (Seção 6.1) — nenhuma
conclusão central do estudo depende dela.

## 4. Índice de Base Empírica

Esta é a métrica central do estudo. A pergunta que ela tenta responder,
sentença por sentença: **quando o plano faz uma afirmação/promessa, essa
afirmação vem amarrada a algum tipo de base factual, ou é só retórica de
gestão pública genérica?**

### 4.1 Segmentação em sentenças

O corpo do texto é dividido em sentenças por uma expressão regular que
quebra em pontuação final (`.`, `!`, `?`), ponto e vírgula, quebras de linha,
e início de itens com marcador de lista (`-`). Cada fragmento resultante
passa por uma limpeza (remove aspas/parênteses soltos nas pontas, remove
prefixos de marcador de lista e de numeração de seção) e é descartado se:
- for identificado como um título/cabeçalho solto (todo em maiúsculas, uma
  linha de data isolada, ou uma sequência curta de palavras majoritariamente
  capitalizadas sem pontuação final — heurística para excluir títulos de
  seção que a extração de PDF deixou soltos no meio do texto corrido); ou
- tiver menos de 5 palavras.

### 4.2 Os três pilares de "base empírica"

Cada sentença sobrevivente é testada contra três critérios independentes
(uma sentença pode satisfazer mais de um):

- **Pilar A — diagnóstico com dado**: a sentença contém um número (`R$`,
  percentual, ou qualquer dígito) OU as palavras "maior"/"menor", **E** contém
  uma expressão de diagnóstico factual (ex.: "segundo dados", "de acordo com
  o sistema", "taxa de analfabetismo", "abaixo da linha de pobreza", "IBGE",
  "censo", "posição no ranking").
- **Pilar B — efeito/meta mensurável**: a sentença contém um verbo/expressão
  de variação de indicador (reduzir, aumentar, elevar, diminuir, "meta de",
  "trajetória de") **E** (contém um número OU uma expressão comparativa como
  "entre as cinco melhores").
- **Pilar C — evidência ou mecanismo causal externo**: a sentença cita um
  modelo já adotado em outro lugar, um estudo/pesquisa de uma instituição
  nomeada (IBGE, IPEA, INPE, universidade, instituto), organismos como
  OMS/Banco Mundial/BNDES/BNB, uma lei nomeada, ou expressões como "baseado
  em dados/estudos/evidências", "com base em [dados/estudos/...]",
  "comprovad-", "evidênci-".

Se a sentença satisfaz A, B ou C, ela conta como **"com base empírica"**.

### 4.3 O denominador: retórica sem evidência

Se a sentença **não** satisfaz nenhum dos três pilares, ela é testada contra
uma lista de ~44 termos de jargão de gestão pública genérica (“eficiência”,
“fortalecimento”, “modernização”, “sinergia”, “governança”, “políticas
públicas”, “desenvolvimento sustentável” etc. — lista completa em
`codigo/R/replicar_analise.R`, variável `JARGAO_TERMOS`, idêntica à dos
scripts Python). Se contém pelo menos um desses termos, conta como
**"retórica sem evidência"**.

Sentenças que não satisfazem nenhum pilar **e** não contêm jargão da lista
não entram em nenhum dos dois grupos — são simplesmente neutras (não contam
nem a favor nem contra o índice). Isso é proposital: o índice mede a razão
entre afirmações fundamentadas e afirmações que soam a promessa de gestão
mas não têm nada por trás, não o texto inteiro do plano.

### 4.4 A fórmula

```
Índice de Base Empírica (%) = trechos_com_base_empirica
                               ────────────────────────────────────────── × 100
                               trechos_com_base_empirica + trechos_retorica_sem_evidencia
```

Um plano que não tem nenhuma sentença em nenhum dos dois grupos (nem base
empírica nem retórica jargão-carregada) recebe índice 0,0% por convenção
(ver `n_trechos_com_base_empirica + n_trechos_retorica_sem_evidencia == 0`) —
foi o caso de Lucas Ribeiro (PB), Ciro Gomes (CE) e Renan Filho (AL): seus
planos são curtos e telegráficos o bastante para não conterem nenhuma
sentença detectável em nenhum dos dois grupos.

### 4.5 Exclusão de capa/sumário

Antes de rodar essa análise, o texto de cada candidato é cortado a partir da
2ª ocorrência do primeiro marcador de seção usado na distribuição temática
(ver Seção 3) — a 1ª ocorrência costuma estar dentro do sumário/índice do
documento, não no corpo real. Isso evita que fragmentos de sumário sejam
contados como "retórica sem evidência" (bug encontrado e corrigido durante
a produção deste estudo — ver Seção 7). Para 13 dos 21 candidatos esse corte
é zero (o primeiro marcador só aparece uma vez, tipicamente porque o
documento não tem um sumário separado do corpo). Os valores exatos de corte
(em caracteres) estão em `dados/candidatos_config.csv`,
coluna `cursor_inicial_caracteres`.

## 5. Densidade de jargão "fortalecer" / "ampliar"

Adição posterior ao estudo original, motivada por uma pergunta específica do
pesquisador responsável: será que as famílias de palavras "fortalec-"
(fortalecer, fortalecimento, fortalecido...) e "ampli-" (ampliar, ampliação,
amplo...) — dois dos termos mais genéricos da lista de jargão do Pilar
"retórica" — aparecem proporcionalmente mais em candidatos incumbentes/de
continuidade?

Essa métrica é puramente mecânica: conta ocorrências das expressões
regulares `\bfortalec\w*` e `\bampli\w*` (case-insensitive) no corpo inteiro
do plano (sem excluir capa/sumário, ao contrário do Índice de Base Empírica),
normalizado por mil palavras (`total_palavras` da Seção 2). O resultado está
na Seção 6.2 do relatório principal: o sinal é real mas moderado (r ≈ -0,50
com o Índice de Base Empírica) e mais forte entre incumbentes plenos do que
entre candidatos de continuidade — nuance que qualifica, mas não invalida, a
hipótese original.

## 6. Classificação incumbente / desafiante / continuidade

Diferente das métricas acima, a categoria de cada candidato **não é
derivada do texto do plano** — é um julgamento humano sobre a situação
político-eleitoral de cada candidatura, com 4 valores possíveis:

- **incumbente pleno**: governador em exercício buscando reeleição direta.
- **incumbente por sucessão**: assumiu o cargo durante o mandato atual (por
  sucessão) e concorre à reeleição no cargo que já ocupa.
- **candidato de continuidade**: não é o titular do cargo, mas é o candidato
  indicado e/ou publicamente apoiado pelo governador em exercício que não
  concorre à reeleição — a campanha se posiciona explicitamente como
  continuação do governo atual.
- **desafiante**: todos os demais — oposição ao governo atual, sem indicação
  do titular.

Essa classificação foi checada candidato a candidato e, em dois casos,
levou a decisões editoriais não óbvias, documentadas para auditoria:

- **Cadu Xavier (RN)** foi inicialmente classificado como desafiante (por o
  RN não ter um incumbente pleno concorrendo) e depois **reclassificado
  para candidato de continuidade**, após confirmação de que a governadora
  Fátima Bezerra (PT, não concorre à reeleição) o apoia publicamente
  ("Vamos eleger Cadu Xavier governador") e de que seu próprio plano cita o
  "legado" do governo Fátima dezenas de vezes — ao contrário dos outros 2
  candidatos do RN (Allyson Bezerra, Álvaro Dias), cujos planos têm zero
  menções a Fátima Bezerra. Fontes: agorarn.com.br e diariodorn.com.br
  (links completos no relatório principal, Seção 3).
- **Felipe Camarão (MA)** permanece classificado como desafiante (é
  formalmente oposição ao governador Brandão), mas é, na prática, o
  vice-governador em exercício licenciado do cargo — um caso de fronteira
  discutido na Seção 8 do relatório principal como uma "quinta categoria"
  não usada por não haver outro caso equivalente no estudo.

O arquivo `dados/candidatos_config.csv` traz a categoria de cada um dos 21
candidatos.

## 7. Correções metodológicas aplicadas durante o estudo

Duas rodadas de auditoria independente (ver Seção 9 do relatório principal
para o texto completo) encontraram e corrigiram três problemas que afetavam
o Índice de Base Empírica:

1. **Gatilhos genéricos demais no Pilar C.** A primeira versão da expressão
   regular de evidência aceitava "conforme o/a" e "baseado em"/"com base em"
   sem exigir um substantivo evidencial em seguida — disparando o pilar C em
   frases sem nenhuma evidência real (ex.: "baseado em gestão qualificada,
   inovação..."). Corrigido exigindo que esses conectores sejam seguidos de
   um substantivo evidencial específico (dados, estudos, indicadores,
   diagnóstico, etc.).
2. **Gatilho específico do Maranhão inflando o pilar C.** Menções a "plano
   Lula"/"plano nacional" contavam como evidência causal externa mesmo
   quando eram apenas alinhamento político declarado, não citação de
   estudo/dado. Removido.
3. **Cálculo do índice não excluía a mesma região de capa/sumário** que a
   distribuição temática já excluía (ver Seção 4.5) — corrigido aplicando o
   mesmo corte (`cursor_inicial`) ao cálculo do índice.

Essas três correções foram aplicadas de forma centralizada aos 9 scripts
(8 do Nordeste + retroativamente à Paraíba, o estudo original que deu
origem à metodologia) para preservar comparabilidade entre os 21
candidatos. Os números usados neste relatório e nesta replicação já
refletem a versão corrigida.

## 8. Limitações conhecidas, não corrigidas nesta rodada

- **Fragmentação de sentenças por quebra de linha física do PDF.** A
  heurística de segmentação trata toda quebra de linha como um possível fim
  de frase — em textos extraídos com quebra de linha física preservada
  (comum em PDFs de colunas ou copiados sem reflow), isso fragmenta frases
  no meio, o que pode inflar o denominador (mais fragmentos curtos sem
  pilar nem jargão detectável) ou, ocasionalmente, quebrar uma frase que
  teria pilar em dois pedaços que isoladamente não têm. Efeito estimado em
  pelo menos um caso (Pernambuco) e provavelmente presente, em grau menor,
  em outros. Ver `codigo/R/replicar_analise.R`, candidato Álvaro Dias (RN),
  para um exemplo replicável desse efeito (diferença de 0,3 ponto
  percentual entre o índice publicado e uma segmentação alternativa).
- **Ruído de OCR** em Felipe Camarão (MA) e Raquel Lyra (PE).
- **Granularidade temática não é estritamente uniforme** entre estados (ver
  Seção 3) — não afeta o Índice de Base Empírica.
- **A categorização incumbente/desafiante/continuidade é uma simplificação**
  da realidade política de cada candidatura (ver Seção 6) — checada caso a
  caso, mas outros casos de fronteira podem existir sem terem sido
  sinalizados.

## 9. Consolidação, estatísticas e gráficos

Os resultados por candidato de todos os 9 estados são consolidados em
`dados/dados_consolidados.csv`/`.json` (21 linhas). A partir dessa tabela:

- **Estatísticas descritivas por categoria** (média, desvio padrão
  populacional — não amostral, já que os 21 candidatos são o universo
  completo de planos oficiais disponíveis, não uma amostra de uma população
  maior —, mediana, mínimo, máximo) são calculadas para o Índice de Base
  Empírica e para a densidade de jargão, agrupadas pelas 4 categorias da
  Seção 6.
- **Correlação de Pearson** entre densidade de jargão e Índice de Base
  Empírica.
- **Gráficos comparativos** (barras horizontais, ordenados pelo valor,
  coloridos por categoria) são gerados a partir da mesma tabela — em HTML
  interativo no projeto original (`analise_geral_ne/grafico_comparativo.html`)
  e, aqui, em PNG estático via R base (`saida/*.png`, gerados por
  `codigo/R/replicar_analise.R`).

## 10. Sobre esta pasta de replicação

Esta pasta (`replicacao/`) foi construída para permitir que qualquer pessoa
reproduza os números publicados de forma independente, sem depender do
ambiente original de análise. Ver `LEIA-ME.md` para instruções de uso e a
seção "Limites da replicação em R" para uma discussão honesta de onde o
recálculo em R diverge, por poucas décimas, dos números publicados (2 de 21
candidatos) e por quê.
