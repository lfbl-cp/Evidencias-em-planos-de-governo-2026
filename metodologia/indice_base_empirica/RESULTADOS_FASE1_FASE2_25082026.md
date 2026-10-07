# Índice de Base Empírica — resultados da Fase 1 (robustez estatística) e Fase 2 (validação por segundo codificador)

25/08/2026. Segue o plano proposto em `INDICE_BASE_EMPIRICA_MELHORIAS.md`. Nenhum número já publicado (`analise.json`, dashboards, relatórios comparativos) foi alterado — tudo aqui é análise nova, sobre um dataset sentença-a-sentença reconstruído a partir dos 26 scripts `build_analysis_*.py` publicados (mais o piloto da Paraíba), sem modificar nenhum deles.

## Como os dados foram gerados

`extrair_frases_classificadas.py` importa dinamicamente cada `build_analysis_<uf>.py` já publicado e reaplica a mesma lógica de classificação sentença-a-sentença (reaproveitando os objetos de regex de cada módulo — inclusive as 2 exceções documentadas, Bahia e o piloto da Paraíba), produzindo **133.139 frases classificadas** em 57 candidatos. Diferença deliberada: usei o corpo inteiro de cada plano (sem replicar o corte de front matter específico de cada estado), o que adiciona um número pequeno de frases de capa/sumário à base — os totais aqui (n_base=1.416, n_retórica=18.941) batem com os publicados (1.415 e 18.868) com menos de 0,5% de diferença, confirmando a fidelidade da reconstrução.

## Fase 1 — achados de robustez estatística

### 1. O denominador atual cobre só 15,3% do texto substantivo

Das 133.139 frases classificáveis (após filtro de cabeçalho/tamanho mínimo), **apenas 20.357 (15,3%) entram no denominador do índice atual** (1.416 com base empírica + 18.941 retórica-com-jargão). As outras **112.782 frases (84,7%) não entram em lugar nenhum** — não são nem "com base" nem "retórica com jargão". Isso é mais extremo do que eu estimei na primeira leitura do problema (Seção 2.3 do documento de diagnóstico) e é o achado mais importante desta rodada para a validade de constructo: o índice publicado descreve uma fração pequena e não aleatória de cada plano.

### 2. Índice de cobertura alternativo: forte validade convergente

Um índice alternativo (denominador = frases com verbo de compromisso/proposta, não só frases com jargão) tem correlação **muito alta** com o índice atual: Pearson r = 0,952, Spearman ρ = 0,924 (ambos p < 0,0001), com média quase idêntica (3,75% vs. 3,91%). **Isso é uma boa notícia**: apesar da preocupação teórica sobre o denominador, uma definição de constructo bem diferente reproduz essencialmente o mesmo ranking entre candidatos. Reduz (mas não elimina — ver achado 1) a preocupação de que a escolha do denominador esteja distorcendo as comparações entre candidatos.

### 3. Sensibilidade à lista de jargão: moderada, com exceções concentradas nos índices mais altos

Rodando o índice sob 200 subamostras aleatórias (80% da lista de 41 termos de jargão), a faixa de variação típica é pequena (largura mediana 1,6 p.p., média 2,5 p.p.), mas concentrada de forma desigual: os candidatos com **maior variação são exatamente os de índice mais alto e mais citado nos relatórios** — Felipe Camarão/MA (19,3% publicado, faixa de 15,4 p.p. sob subamostragem), ACM Neto/BA (25,6%, faixa 10,2 p.p.), Cícero Lucena/PB (15,1%, faixa 7,3 p.p.), Rafael Fonteles/PI (10,0%, faixa 6,9 p.p.). Recomendo tratar esses 4 números específicos com uma nota de cautela adicional nos relatórios (são os "recordes" mais citados, e são também os que mais dependem da lista de jargão escolhida).

## Fase 2 — validação por segundo codificador (LLM, cego, mesma definição operacional)

Amostra estratificada de 265 frases (7 estratos: só-pilar-A, só-pilar-B, só-pilar-C, multi-pilar, retórica-com-jargão, "neutra com verbo de compromisso", "neutra pura"), classificada por um segundo codificador sem acesso ao rótulo da regex, usando o mesmo codebook operacional (definições de A/B/C/jargão idênticas às do regex, para testar reprodutibilidade da REGRA, não uma regra diferente).

### Concordância (Cohen's kappa, escala de Landis & Koch: <0=nenhuma, 0-0,20=leve, 0,21-0,40=razoável, 0,41-0,60=moderada, 0,61-0,80=substancial, 0,81-1=quase perfeita)

| Critério | Concordância bruta | Kappa | Interpretação | Precisão (regex vs. LLM) | Recall |
|---|---|---|---|---|---|
| **com_base (o que vira o índice)** | 88,3% | **0,767** | substancial | 0,82 | 0,95 |
| pilar C (evidência externa) | 89,4% | 0,733 | substancial | 0,84 | 0,77 |
| retórica-sem-evidência (jargão) | 95,8% | 0,861 | quase perfeita | 0,96 | 0,83 |
| pilar A (diagnóstico) | 84,2% | 0,513 | moderada | 0,55 | 0,69 |
| pilar B (efeito mensurável) | 90,9% | 0,525 | moderada | 0,44 | 0,80 |

**Leitura**: o índice agregado (`com_base`) tem confiabilidade **substancial** (kappa 0,767) — um número defensável para publicação, na faixa que a literatura de análise de conteúdo considera aceitável para relatar sem ressalva grave. O pilar que mais pesa no índice (C, 69% das classificações positivas) é também o mais confiável dos três isoladamente. Mas os pilares A e B, vistos separadamente, têm confiabilidade só **moderada** — se algum relatório futuro quiser destacar "candidato X tem mais dados de diagnóstico que Y" (pilar A isolado) ou "mais metas mensuráveis" (pilar B isolado), isso merece bem mais cautela do que o índice agregado.

### Por que a regex diverge do segundo codificador — padrões específicos e corrigíveis

Lendo as divergências caso a caso (arquivo `comparacao_regex_llm.csv`), aparecem 4 padrões recorrentes e específicos, não ruído aleatório:

1. **Pilar B "solta" o número da frase**: o regex confere `EFEITO_RE` (verbo de efeito) E `NUM_ANY` (algum número) na mesma frase, mas não confirma que o número pertence à MESMA proposta/efeito — ex.: "apoiar tecnicamente as 223 prefeituras e modernizar a SEFAZ" foi contado como pilar B (tem "modernizar" + o número "223"), mas o número descreve o ALCANCE da ação, não uma magnitude de efeito esperado. É a causa provável da baixa precisão do pilar B (0,44 — mais da metade dos positivos do regex não se sustentam).
2. **"Linha de base" como gatilho ambíguo**: `DIAG_KEYWORDS_RE` inclui a frase "linha de base" para capturar diagnóstico (ex.: "taxa de X, linha de base Y"), mas ela também aparece em descrições de sistema de monitoramento futuro ("painel de indicadores... com linha de base, meta intermediária") — que não é um diagnóstico existente, é uma promessa de acompanhamento. Puxa a precisão do pilar A para baixo (0,55).
3. **`EVIDENCIA_RE` (pilar C) tem falsos positivos em uso técnico não político**: o gatilho genérico "evidênci" casa até em jargão técnico de mineração ("evidências indiretas — geofísicas...") sem relação com evidência causal de política pública.
4. **`EVIDENCIA_RE` (pilar C) tem falsos negativos em citações de estudo não hard-coded**: a lista de instituições é fixa (IBGE, IPEA, DATASUS etc.) — um estudo citado por nome mas de instituição fora da lista (ex.: "O estudo Cartografias da Violência na Amazônia (FBSP, 2025)") não é capturado, mesmo sendo uma citação de evidência genuína e específica.

Esses 4 pontos são **achados acionáveis**, não só uma nota de "o classificador não é perfeito" — dá para corrigir a regex de forma dirigida (ex.: exigir que o número do pilar B esteja a poucas palavras do verbo de efeito, não em qualquer lugar da frase; remover "linha de base" isolado do pilar A ou exigir que venha acompanhado de um valor numérico já observado; restringir `EVIDENCIA_RE` para o domínio de política pública; ampliar a lista de instituições/expressões-gatilho do pilar C para reduzir falso negativo).

## Avaliação geral

O índice publicado é **defensável na sua forma agregada** (kappa substancial, 0,767, contra um segundo codificador cego e independente — é a primeira vez que o projeto tem essa medida) — mas a validação também encontrou 4 pontos de correção concretos na regex e confirmou que **85% do texto de cada plano nunca entra no cálculo**. Recomendo: (a) publicar o kappa e as ressalvas por pilar junto com o índice, (b) considerar as 4 correções de regex acima como próxima rodada de ajuste fino (Fase 3), e (c) decidir, com base no achado 1 (denominador cobre só 15%) e no achado 2 (índice de cobertura alternativo bate com o atual), se vale a pena migrar o índice principal para a definição de cobertura — que tem a vantagem de ser mais interpretável ("dentre as frases que fazem uma proposta, quantas têm lastro") e não muda substancialmente os números.

## Arquivos desta pasta

- `extrair_frases_classificadas.py` — reconstrói o dataset sentença-a-sentença a partir dos scripts publicados (sem alterá-los)
- `frases_classificadas.jsonl` — as 133.139 frases classificadas (dataset completo; grande, ~40MB, comprimido no zip)
- `analise_sensibilidade_cobertura.py` — sensibilidade ao jargão + índice de cobertura
- `indice_cobertura_alternativo.csv` — índice atual vs. índice de cobertura, por candidato
- `amostra_validacao.jsonl` — a amostra estratificada de 265 frases enviada para o segundo codificador
- `comparacao_regex_llm.csv` / `.json` — comparação frase-a-frase regex vs. segundo codificador (a base de todos os números da Fase 2 acima)
