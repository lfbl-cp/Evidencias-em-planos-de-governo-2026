# Pacote de Replicação — Planos de Governo, Nordeste 2026

Este pacote permite reproduzir, de forma independente, todos os números
usados no `RELATORIO_COMPARATIVO.md` (análise comparativa dos 21 candidatos
a governador do Nordeste em 2026): o Índice de Base Empírica, a densidade de
jargão "fortalecer"/"ampliar", e as estatísticas descritivas por categoria.

## O que tem aqui

```
replicacao/
├── LEIA-ME.md                    este arquivo
├── METODOLOGIA.md                passo a passo completo de tudo o que foi feito
├── NOTA_SOBRE_USO_DE_IA.md       transparência sobre o uso de IA neste estudo
├── dados/
│   ├── candidatos_config.csv     os 21 candidatos: categoria, arquivo do plano,
│   │                             ponto de corte de capa/sumário, valores publicados
│   ├── dados_consolidados.csv/json   tabela final usada no relatório
│   └── planos/<estado>/<slug>.txt    texto bruto dos 21 planos de governo
├── codigo/
│   ├── python/                   os 9 scripts originais (o código que de fato
│   │                             gerou os números publicados — a fonte da verdade)
│   └── R/replicar_analise.R      script único em R que recalcula tudo do zero
│                                 a partir dos textos brutos e confere contra
│                                 o publicado
└── saida/                        gerado ao rodar o script em R (CSV + 2 PNGs)
```

## Como rodar (R)

Requer apenas R base — nenhum pacote externo (`jsonlite`, `stringr` etc.) é
necessário.

```bash
cd codigo/R
Rscript replicar_analise.R
```

Ou, no RStudio: abra `replicar_analise.R` e rode com Source. O script
detecta sozinho as pastas `dados/` e `saida/` relativas à sua própria
localização.

Se seu sistema não tiver uma locale UTF-8 disponível e o script avisar sobre
isso (ou os acentos aparecerem corrompidos), rode:

```bash
LC_ALL=C.UTF-8 Rscript replicar_analise.R
```

**Tempo de execução**: cerca de 3-4 minutos no total (um candidato — ACM
Neto, o texto mais longo do estudo — sozinho leva ~1 minuto, por causa do
custo de rodar expressões regulares extensas milhares de vezes em R puro;
isso é inerente a como o R base processa laços/regex, não um sinal de
problema).

## O que esperar na saída

Para cada um dos 21 candidatos: o Índice de Base Empírica recalculado, a
densidade de jargão recalculada, e uma linha `OK`/`DIVERGE` comparando cada
métrica com o valor publicado em `dados_consolidados.csv`. Ao final: as
tabelas de estatísticas descritivas por categoria, a correlação de Pearson
entre jargão e índice, e a confirmação de que os 2 gráficos PNG foram
salvos em `saida/`.

Rodando do zero, o resultado esperado é:

```
Resultado da verificação: 162 / 168 métricas batem com o publicado.
```

Ou seja, **20 dos 21 índices batem exatamente**, e as duas exceções são
pequenas (0,3 ponto percentual em um candidato; 5 palavras em 75 mil, sem
nenhum efeito no índice, em outro) e estão explicadas em detalhe na Seção 8
de `METODOLOGIA.md` e na própria saída do script — não são bugs
escondidos, são o resultado, documentado e reproduzível, de um limite
conhecido da heurística de segmentação de sentenças (diferenças sutis de
como R e Python tratam certas quebras de linha/caracteres incomuns em 2 dos
21 textos).

## Como rodar (Python — a fonte da verdade)

Os scripts em `codigo/python/` são cópias exatas dos scripts que geraram os
números publicados nos dashboards e no relatório (não uma reimplementação).
Requerem `pip install wordcloud` (usado apenas para gerar a nuvem de
palavras de cada candidato — pode ser comentado se você só quer os números).
Cada script é autocontido por estado; rodar exige ajustar os caminhos de
entrada/saída no topo do arquivo (`PLANOS_DIR`, `ANALISE_DIR`) para apontar
para as pastas correspondentes desta replicação, já que os scripts
originais referenciam caminhos absolutos do ambiente de análise original.

## Uma nota sobre reprodutibilidade e julgamento humano

A tokenização, a segmentação de sentenças e a aplicação das expressões
regulares do Índice de Base Empírica são 100% mecânicas — sem nenhum ajuste
manual escondido. Já a categoria de cada candidato (incumbente pleno /
incumbente por sucessão / candidato de continuidade / desafiante) e a
classificação temática de cada bloco de texto são julgamentos editoriais
humanos, documentados e justificados em `METODOLOGIA.md` (Seções 3 e 6) para
que qualquer pessoa possa auditar cada decisão e discordar de casos de
fronteira específicos, se quiser.

## Fontes dos textos

Os 21 arquivos em `dados/planos/` foram extraídos dos PDFs oficiais de
planos de governo de cada candidato (registrados junto à Justiça Eleitoral
e/ou divulgados pelas campanhas). Cada arquivo tem um cabeçalho padronizado
(candidato/partido/vice/fonte/status) seguido do corpo integral do plano.
