# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

Análise comparativa (em português) dos planos de governo dos candidatos a governador em 2026, por estado → região → Brasil. Para cada candidato mede: **Índice de Base Empírica** (parcela de trechos com diagnóstico numérico, efeito mensurável ou evidência externa vs. retórica genérica), **distribuição temática exaustiva** (9 temas), **densidade de jargão** ("fortalecer"/"ampliar" por mil palavras), frequência de palavras/nuvem e texto compartilhado entre planos. Atualmente 58 candidatos em 26 estados (Roraima e Garotinho/RJ fora — ver `metodologia/NOTA_METODOLOGICA.md`). Não há build system, testes, linter nem `requirements.txt`: é um pipeline de scripts Python que lê textos e gera JSON/HTML/Markdown.

Dependências Python usadas: biblioteca padrão + `wordcloud` (nuvens de palavras). Neste PC (Windows) `python` não está no PATH (só o atalho da Microsoft Store) — localize o interpretador real antes de rodar scripts. Todos os arquivos são UTF-8; use `-Encoding utf8` ao ler/escrever pelo PowerShell, senão os acentos corrompem.

## Layout

```
<regiao>/<estado>/
  <UF>/            PDFs originais do TSE (2026<UF>...pdf + leiame.pdf)
  planos/<slug>.txt   texto extraído; cabeçalho CANDIDATO/PARTIDO/VICE/FONTE/STATUS, depois "---", depois o corpo
  analise/build_analysis_<uf>.py  →  analise/analise.json, wordclouds/, _debug_segmentos_<slug>.txt
  dashboard/{template.html, app.js, build_dashboard_<uf>.py}  →  dashboard.html (autocontido)
<regiao>/analise_geral_<regiao>/   build_dados_consolidados.py → dados_consolidados_*.json/.csv
                                    grafico_comparativo_*.py → .html;  RELATORIO_COMPARATIVO_*.md (escrito/atualizado à mão a partir dos dados)
nacional/    build_dados_nacionais.py → dados_nacionais.json/.csv → build_site_data.py → site_data.json → build/panorama_nacional.html; RELATORIO_NACIONAL.md
programs/    motor_indice_base_empirica.py + build_dashboard.py + vendor/ (motor compartilhado, ver abaixo)
metodologia/ NOTA_METODOLOGICA.md (documento vivo, histórico datado), INDICE_BASE_EMPIRICA_MELHORIAS.md, indice_base_empirica/ (validação estatística, Fases 1–3)
nordeste/replicacao/   pacote de replicação do Nordeste (cópias dos scripts + R); não é a fonte de trabalho
_to_delete/, norte/_repair/, sudeste/rio-de-janeiro/_v1_backup/   arquivos descartáveis/históricos — não editar
```

## Fluxo de dados (a ordem importa)

1. PDF do TSE → `planos/<slug>.txt` (extração manual; ver defeito de ligaduras `fi`/`fl` em `norte/_repair/`, que usa regras curadas por candidato — regras genéricas demais já corromperam 10 planos).
2. `build_analysis_<uf>.py` → `analise/analise.json` (**fonte da verdade** de cada estado).
3. `build_dashboard.py <estado_dir>` (ou o `build_dashboard_<uf>.py` do estado) injeta `analise.json` + `app.js` + html2pdf no `template.html` via placeholders `__DATA_BUNDLE_JSON__`, `__APP_JS__`, `__HTML2PDF_JS__` → `dashboard.html`.
4. `build_dados_consolidados.py` de cada região lê todos os `analise.json` e reconstrói `dados_consolidados_*.json/.csv`, **preservando** `categoria`/`categoria_raw` já publicados (a categoria é julgamento editorial humano, não calculada).
5. Gráfico comparativo regional e `nacional/build_dados_nacionais.py` → `build_site_data.py` → painel nacional.
6. `RELATORIO_*.md` são atualizados a partir dos dados recalculados — números nunca ajustados à mão.

Ao adicionar/alterar um candidato, percorra todos os passos 2→6 e confira por diff campo-a-campo que os outros candidatos do estado ficaram idênticos.

## Arquitetura do motor e armadilhas

- **`programs/motor_indice_base_empirica.py`** concentra tokenização, stopwords, os 3 pilares do índice (`is_diagnostico`, `is_efeito`, `is_evidencia`), `PROPOSAL_RE` (denominador de cobertura), `distribuicao_tematica_exaustiva`, `base_empirica_analise` e geração de nuvem. Só `build_analysis_rj.py` e `build_analysis_pb.py` já o importam (`sys.path.insert(0, PROJECT_ROOT / "programs")`, caminhos via `Path(__file__)`); os outros ~22 `build_analysis_*.py` ainda carregam uma **cópia colada** da lógica e caminhos absolutos `/home/claude/brasil_2026/...` do ambiente original — para rodá-los aqui é preciso ajustar `PLANOS_DIR`/`ANALISE_DIR`. O mesmo vale para `build_dashboard_<uf>.py`, `build_dados_consolidados.py` e `nacional/*.py` (que ainda usam `/home/claude/...` e `/tmp/br_map_paths.json`).
- Ao migrar um estado para o motor, o PNG/números já publicados não podem mudar. Desvios reais entre estados viram **parâmetros opcionais** do motor (`bullet_re` para a Bahia/`\x90`, `max_words=20` para AL/BA/RN, `gerar_wordcloud_png_b64_legacy_pi` para o Piauí) — nunca um fork nem normalização silenciosa. Documente o novo desvio no docstring do motor.
- **Cada `build_analysis_*.py` mantém só o específico do estado**: `CANDIDATOS` (incluindo `categoria` e fontes), `MARCADORES_*` (segmentação temática mapeada **à mão** lendo o plano) e `metodologia_nota`. Rodar o script deve ser idempotente e reproduzir o JSON publicado: o padrão é `analise = {**analise_anterior, **analise}` e truncar blocos "ATUALIZAÇÃO" num marcador antes de reanexá-los (PE/PI/SE já perderam campos e a PB já duplicou notas por não fazerem isso). Sempre compare com o `analise.json` anterior antes de sobrescrever.
- `indice_base_empirica_pct` (denominador de cobertura, número de manchete) coexiste com `indice_base_empirica_legado_pct` (fórmula original) — mantenha os dois; nunca apague a fórmula antiga.
- Em `analise.json`, `categoria` é a forma masculina normalizada para agrupamento (incumbente pleno / incumbente por sucessão / candidato de continuidade / desafiante); `categoria_raw` preserva a redação natural com justificativa.
- Pernambuco não tem `build_dashboard_pe.py`: o dashboard é atualizado editando o bundle JSON embutido em `dashboard.html`. O dashboard da Paraíba tem 2 erros de console pré-existentes conhecidos.
- Seleção de candidatos: incluir todos os competitivos nas pesquisas, não um número fixo por estado (regra de 25/08/2026). Planos com proveniência atípica (ex.: Eduardo Paes/RJ, versão preliminar não confirmada no TSE) são tratados pela mesma metodologia mas com nota de transparência.

## Convenções de documentação (importantes)

- **Nunca sobrescrever silenciosamente** número, texto ou campo já publicado. Mudanças metodológicas ganham uma entrada **datada** em `metodologia/NOTA_METODOLOGICA.md` (Seção 3) e marcação inline datada nos relatórios afetados; números recalculados vêm sempre dos dados, não de edição manual. Tabelas estatísticas fechadas de rodadas antigas dos relatórios regionais são preservadas de propósito.
- `NOTAS_METODOLOGICAS_PENDENTES.md` lista decisões **não tomadas** (sensibilidade do índice ao tamanho do documento, r≈0,58 nacional; o diagnóstico de 28/08 conclui que não é artefato de medição e recomenda reportar índice bruto + IC de Wilson, sem normalizar). Não implementar nada ali sem decisão do pesquisador responsável (Felipe Braga).
- Validação habitual dos dashboards/gráficos: Playwright headless checando erros de console novos, requisições externas e `undefined`/`NaN` (não há script no repositório).
- Texto de relatórios e comentários do código são em português; manter o idioma e o tom (rastreabilidade, fontes com URL e data).
