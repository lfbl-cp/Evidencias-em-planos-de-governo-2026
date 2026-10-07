# Índice de Base Empírica — diagnóstico e propostas de robustecimento metodológico

Documento de trabalho, 25/08/2026. Objetivo: revisar o Índice de Base Empírica com ferramentas de estatística e análise de conteúdo, separando o que já é defensável do que precisa de reforço, e propor um plano concreto — com achados empíricos já rodados sobre os dados reais do projeto (57 candidatos, 26 estados/piloto), não apenas considerações abstratas.

## 0. Resumo executivo

O índice, como está hoje, é **metodologicamente honesto na sua concepção** (heurística lexical transparente + revisão manual documentada, replicada de forma quase idêntica entre estados) mas tem **quatro pontos frágeis** que um parecerista de ciência política cobraria: (1) nunca foi validado contra um segundo codificador independente — não existe nenhuma medida de confiabilidade (kappa, precisão/recall); (2) os números publicados não vêm com intervalo de confiança, e ao recalculá-los agora, **73% das comparações par-a-par dentro do mesmo estado têm IC95% sobrepostos** — ou seja, na maioria dos casos não dá para afirmar com confiança estatística que um candidato tem "mais base empírica" que o outro, mesmo quando os pontos percentuais publicados diferem; (3) o denominador do índice (frases-com-base ÷ (frases-com-base + retórica-com-jargão)) ignora toda frase que não é nem uma coisa nem outra, o que é uma escolha de constructo válida mas não testada contra alternativas; (4) o pilar C (evidência/mecanismo causal externo) responde por **69% das classificações positivas**, contra 26% do pilar A e 18% do pilar B — o índice está, na prática, medindo majoritariamente "menciona uma instituição/lei nomeada", não o mix balanceado de diagnóstico+efeito+evidência que a definição promete.

Nenhum desses pontos invalida o trabalho já feito — mas todos são corrigíveis com esforço moderado, e a Seção 3 propõe como.

## 1. O que já está bem fundamentado (não mexer)

- **Transparência da heurística**: cada frase é classificada por regras explícitas (regex), não por um modelo opaco — qualquer pessoa pode auditar por que uma frase caiu num pilar. Isso é uma vantagem real sobre um classificador de caixa-preta, especialmente para um projeto que se propõe replicável (o pacote `replicacao_R/` da Paraíba já reflete essa preocupação).
- **Consistência entre estados**: rodei agora um diff estrutural das 5 regex centrais (`NUM_ANY`, `DIAG_KEYWORDS_RE`, `EFEITO_RE`, `EVIDENCIA_RE`, `JARGAO_TERMOS`) e do filtro de sentenças (`SENT_SPLIT_RE`, `BULLET_RE`, `MIN_SENTENCE_WORDS`) nos 26 scripts `build_analysis_*.py` do projeto. Resultado: **idênticas em 25-26 dos 26 casos**, com só duas exceções, ambas já documentadas em comentário no próprio código-fonte (não são inconsistências acidentais): a Bahia estende `BULLET_RE` para reconhecer o glifo `\x90` como marcador de lista (defeito real de extração do PDF de Jerônimo Rodrigues, 275 ocorrências) e o piloto da Paraíba (`build_analysis_v3.py`) usa uma versão ligeiramente anterior de `DIAG_KEYWORDS_RE`/`EVIDENCIA_RE` — a versão "rascunho" da qual a versão "final" replicada nos outros 25 estados derivou. Isso é uma boa notícia: a comparabilidade entre estados (fora a Paraíba) é real, não presumida.
- **Revisão manual documentada**: os blocos `REVISAO_MANUAL` (Paraíba) e os comentários equivalentes nos demais scripts registram ajustes de regex motivados por leitura humana (ex.: remoção do gatilho genérico "experiência de/do/da" que capturava retórica turística como se fosse evidência). Isso é o começo de um processo de validação, só que documentado como *justificativa de decisão*, não como *medida de acordo* entre dois julgamentos independentes — ver Seção 2.2.

## 2. Vulnerabilidades — com achados empíricos

Rodei os cálculos abaixo agora, sobre os `analise.json` publicados de todos os 57 candidatos do projeto (54 do rollout regional + 3 da Paraíba).

### 2.1 Confiabilidade (inter-rater): nunca medida

O processo de "leitura manual de amostra generosa, nos dois sentidos" é real, mas foi feito por um único leitor (eu, em sessões distintas), sem um segundo codificador cego e sem nenhuma estatística de concordância. Para um parecer/publicação, isso é o primeiro ponto que qualquer revisor de ciência política vai cobrar — é o equivalente, em análise de conteúdo, de reportar um coeficiente sem erro-padrão.

**O que isso significa na prática**: não temos como saber se um segundo leitor, aplicando a mesma definição dos 3 pilares, chegaria às mesmas classificações. A regex pode estar sistematicamente errando de um jeito que "faz sentido" para quem escreveu as regras, mas que outro leitor razoável discordaria.

### 2.2 Robustez estatística: os números publicados não têm margem de erro

Tratando `indice_base_empirica_pct` como uma proporção binomial (frases-com-base entre frases-classificadas), calculei o **intervalo de Wilson (IC95%)** para os 57 candidatos — Wilson em vez de Wald/normal porque lida corretamente com proporções perto de 0% ou 100% e com denominadores pequenos (vários candidatos têm índice = 0,0%, onde um IC normal geraria limite inferior negativo, sem sentido).

- **Largura média do IC95%: 5,3 pontos percentuais** (mediana 4,6 p.p.); casos com denominador pequeno chegam a 17,6 p.p. de largura (Renan Filho/AL, n=18; Eduardo Braide/MA, n=27).
- **Achado mais importante**: comparando os 37 pares de candidatos do mesmo estado (37 pares em 26 unidades eleitorais), **73% (27 de 37) têm IC95% sobrepostos** — ou seja, na maioria dos estados, a diferença publicada entre os dois candidatos ("X% vs Y%") não é estatisticamente distinguível dado o tamanho da amostra de frases classificadas naquele documento. Exemplos de pares que SÃO estatisticamente distintos (não sobrepõem): ACM Neto (25,6% [21,5–30,2]) vs. Jerônimo Rodrigues (2,8% [1,4–5,5]) na Bahia; Omar Aziz (18,5% [17,5–19,7]) vs. os dois rivais no Amazonas. Exemplos que NÃO são distintos apesar de parecerem diferentes à primeira vista: Marcos Rogério (8,1%) vs. Adailton Fúria (3,9%) em Rondônia — os ICs se tocam.

Isso não significa que os números estejam errados — significa que **os relatórios comparativos, ao dizerem "candidato X tem mais base empírica que Y", estão fazendo uma afirmação mais forte do que os dados sustentam na maioria dos casos**, porque nunca reportamos a incerteza amostral.

### 2.3 Validade de constructo: o problema do denominador

O índice = frases-com-base ÷ (frases-com-base + frases-retórica-com-jargão) × 100. Isso **exclui do cálculo qualquer frase que não seja nem uma coisa nem outra** — descrições de procedimento, cronogramas, frases de transição, promessas sem jargão de gestão pública nem evidência ("Vamos construir 40 novas escolas"). Essas frases não entram no denominador nem no numerador.

Isso é uma decisão de constructo defensável (o índice mede "entre as frases que fazem algum tipo de afirmação carregada — seja com evidência, seja com retórica vazia —, qual fração tem lastro empírico"), mas é uma decisão, não um dado — e nunca foi testada contra a alternativa óbvia: um índice de **cobertura**, com denominador = todas as frases que fazem algum tipo de proposta/compromisso (identificáveis por verbos de compromisso: "implementar", "criar", "ampliar", "garantir" etc.), não só as que carregam jargão. Sob essa definição alternativa, um plano telegráfico e enxuto (como o de Lucas Ribeiro na Paraíba — "texto mais telegráfico e enxuto dos três", conforme o próprio comentário no script) poderia ter um índice bem diferente do publicado, porque hoje ele é penalizado/beneficiado apenas em relação às frases com jargão, que são poucas nesse tipo de texto.

### 2.4 Os 3 pilares não pesam igual — e isso nunca foi reportado

Somando os pilares acionados em todas as frases classificadas como "com base empírica" do projeto inteiro (uma frase pode acionar mais de um pilar):

| Pilar | Nº de acionamentos | % das frases-com-base que o acionam |
|---|---|---|
| (a) dado de diagnóstico | 362 | 25,6% |
| (b) efeito/resultado mensurável | 249 | 17,6% |
| (c) evidência/mecanismo causal externo | 976 | **69,0%** |

O pilar (c) domina o índice — quase 7 em cada 10 frases classificadas como "com base empírica" chegam lá só por citar uma instituição nomeada (IBGE, IPEA, DATASUS, SINISA, MapBiomas, INPE, OMS, Banco Mundial, BNDES, BNB) ou "lei nº", não por apresentar um diagnóstico numérico (a) ou uma meta de efeito mensurável (b). Isso é esperado dado como o pilar (c) foi desenhado (a regex tem uma lista de nomes de instituição, que é mecânica de detectar), mas significa que o "Índice de Base Empírica" divulgado hoje é, na prática, **muito mais um índice de "cita instituição/lei nomeada" do que um índice equilibrado dos três tipos de evidência** que o nome sugere. Isso não foi comunicado nos relatórios publicados.

### 2.5 Confound de tamanho do documento

Calculei a correlação entre `indice_base_empirica_pct` e `total_palavras` nos 57 candidatos: **Pearson r = 0,48 (p = 0,0002)**, moderada e estatisticamente significativa — planos mais longos tendem a ter índice mais alto. A correlação de postos de Spearman é bem mais fraca (rho = 0,23, p = 0,08, não significativa), o que sugere que a relação não é monotônica limpa e é parcialmente puxada por casos extremos — meu suspeito principal é o plano de Omar Aziz (AM), com **432.989 palavras / 1.552 páginas**, mais de 7× o segundo maior documento do projeto (Sandro Alex/PR, ~59 mil palavras). Removendo Omar Aziz da amostra, a correlação praticamente não muda (r = 0,41, p = 0,002) — então não é só ele, mas ele é um outlier de alavancagem que merece um olhar à parte (não necessariamente um defeito de extração — o PDF genuinamente tem 1.552 páginas — mas vale checar se boa parte disso são anexos/tabelas orçamentárias que diluem o texto narrativo e não deveriam ser comparados nos mesmos termos que os planos de 15-300 páginas dos demais candidatos).

De qualquer forma, o padrão pede uma checagem formal: sem controlar por tamanho do documento, comparações "brutas" do índice entre candidatos com planos de tamanhos muito diferentes correm risco de confundir "documento mais longo" com "mais base empírica".

## 3. Plano de melhorias propostas

Organizado por esforço, do que dá para fazer imediatamente sobre os dados já coletados até o que exige uma decisão sua sobre redesenho.

### Fase 1 — Robustecimento estatístico (baixo esforço, não muda a metodologia de classificação)

1. **Reportar IC95% (Wilson) ao lado de cada índice publicado**, nos `analise.json`, dashboards e relatórios comparativos — e, nas comparações entre candidatos, marcar explicitamente quando os ICs se sobrepõem (não afirmar diferença onde ela não é estatisticamente sustentada). Já tenho o código pronto (rodado nesta análise) — é só integrar ao pipeline.
2. **Reportar a contribuição de cada pilar separadamente** (não só o índice agregado) — pelo menos nos dashboards, para deixar claro que "base empírica" hoje é majoritariamente pilar (c). Alternativa mais forte: recalibrar o índice para dar peso menor ao pilar (c) sozinho, ou exigir que uma citação institucional venha acompanhada de um número/dado para contar como pilar (c) — isso vai reduzir os índices de todo mundo, mas de forma mais fiel ao que o nome do índice promete.
3. **Análise de sensibilidade da lista de jargão** (`JARGAO_TERMOS`): recalcular o índice removendo/adicionando termos (leave-one-out ou variações de ±20% da lista) para quantificar o quanto o resultado depende dessa lista específica, e reportar a faixa de variação como uma segunda camada de incerteza (além do IC amostral).
4. **Índice de cobertura alternativo** (denominador = frases de compromisso/proposta, não só frases-com-jargão) como medida de validade convergente — calcular os dois índices para todo o corpus e reportar a correlação entre eles. Se forem fortemente correlacionados, reforça a robustez do índice atual; se não, expõe que a escolha do denominador importa mais do que parece.

### Fase 2 — Confiabilidade via segundo codificador (esforço médio)

5. **Validação com classificador independente em amostra estratificada**: desenhar uma amostra estratificada (por pilar/retórica/estado — algo como 200-300 frases) e submetê-la a uma segunda classificação cega, feita por um LLM instruído com a mesma definição operacional dos 3 pilares (sem ver o rótulo da regex). Calcular **precisão, recall e F1** da regex contra esse segundo codificador, e **Cohen's kappa** para a concordância bruta. Isso é executável agora, sem depender de terceiros, e dá o primeiro número de confiabilidade que o projeto jamais teve. Se você preferir, também dá para rodar em 100% do corpus (não só a amostra) e comparar candidato a candidato — mais caro em tokens, mas viável.
6. **Codebook formal**: consolidar as definições operacionais de cada pilar + os casos de fronteira já documentados em `REVISAO_MANUAL`/comentários espalhados pelos 26 scripts num único documento com exemplos e contraexemplos — isso profissionaliza a reprodutibilidade (inclusive por um codificador humano futuro) e é pré-requisito natural para o item 5.

### Fase 3 — Decisões que são suas (redesenho, não só validação)

7. **Segundo codificador humano de verdade** (você ou um(a) assistente de pesquisa) sobre a mesma amostra estratificada da Fase 2, para comparar concordância humano-humano vs. humano-regex vs. humano-LLM — o padrão-ouro em análise de conteúdo assistida por IA na ciência política atual é reportar as três concordâncias, não só uma.
8. **Decidir se o índice recalibrado (pilares ponderados, ou denominador de cobertura) substitui o publicado, ou se os dois passam a ser reportados lado a lado** como visões complementares (constructo é uma escolha teórica, não um fato a ser "descoberto").
9. **Checagem específica do outlier Omar Aziz** (1.552 páginas): decidir se o texto deveria ser segmentado (narrativa vs. anexos) antes de entrar nas comparações agregadas de tamanho/índice do projeto.

## 4. O que eu preciso que você decida para seguir

- Prioridade: seguir pela Fase 1 primeiro (rápido, sem mudar números publicados, só adiciona contexto de incerteza) e decidir depois sobre Fase 2/3? Ou já quer que eu monte a validação por segundo codificador (Fase 2, item 5) em paralelo?
- Escopo da amostra de validação (Fase 2): amostra estratificada (~200-300 frases) ou corpus inteiro (mais caro, mais robusto)?
- Quer que eu já recalcule e publique o índice com IC95% nos dashboards/relatórios existentes, ou isso fica para depois de decidirmos se o índice em si muda (Fase 3)?
