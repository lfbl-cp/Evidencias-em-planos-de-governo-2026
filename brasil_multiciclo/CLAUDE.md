# Projeto: Base Empírica nos Planos de Governo — Painel Multi-Ciclo (2014–2026)

Este é um projeto **separado** do `brasil_2026` (o levantamento de um único ciclo, 58 candidatos
curados por posição nas pesquisas, com saída em imprensa/op-ed). Este projeto aqui existe para
transformar aquele achado pontual em uma contribuição acadêmica de verdade: mesma pergunta, mas
ao longo do tempo, com população completa em vez de amostra curada, e desenho pensado para
submissão a periódico de Ciência Política.

Se os dois projetos divergirem em algum número (por exemplo, o índice médio de 2026 aqui vs. lá),
a causa mais provável é a mudança de população (censo vs. top-3 por pesquisa) — não um erro. Ver
seção "Diferenças deliberadas em relação ao brasil_2026" abaixo antes de assumir inconsistência.

## Pergunta de pesquisa

O padrão observado em 2026 (média de ~3,9% de base empírica nas promessas de campanha; candidatos
de continuidade com índice sistematicamente mais baixo que desafiantes) é uma característica
estável do jogo eleitoral brasileiro, ou uma particularidade daquele ciclo? O índice está subindo,
caindo, ou estagnado ao longo do tempo? Ele se relaciona com o resultado eleitoral (eleito, foi a
2º turno, votação obtida)?

## Escopo

- **Cargo:** governador (mesma obrigação legal de "propostas defendidas" vale para presidente e
  prefeito, mas não é o foco aqui — decidir depois se vale a pena replicar).
- **Ciclos:** 2014, 2018, 2022, 2026. **2010 é meta esticada**, não faz parte do escopo inicial —
  não encontramos o dataset "Proposta de Governo" de 2010 no Portal de Dados Abertos do TSE
  (o portal, no formato atual, parece cobrir só a partir de 2014); precisaria de fonte alternativa
  (sistema legado do TSE) e isso é trabalho à parte.
- **Estados:** todos os 26 dos 27 estados cobertos no `brasil_2026` (Roraima ficou de fora lá por
  falta de plano de governo disponível no momento da coleta; reavaliar Roraima em cada ciclo
  antigo, pode ter dados completos nos anos passados mesmo que não em 2026).

## Diferenças deliberadas em relação ao brasil_2026

1. **População: censo, não amostra.** Em vez de "3 candidatos mais bem colocados nas pesquisas"
   por estado, este projeto pega **todos os candidatos com candidatura deferida que chegaram à
   urna** (majoritária, governador) em cada estado e ciclo. Motivo: elimina viés de seleção,
   elimina a dependência de achar pesquisas eleitorais confiáveis para ciclos antigos, e é
   exatamente a população que a exigência legal (Lei 12.034/2009, art. 11 §1º IX da Lei 9.504/97)
   cobre.
   - **Candidaturas indeferidas/cassadas/renunciadas antes da eleição ficam de fora** — não
     chegaram a fazer campanha de verdade, não é o fenômeno que queremos medir.
   - **Candidaturas cassadas depois da eleição ficam dentro** — a proposta de governo foi
     apresentada e a campanha aconteceu; o desfecho jurídico posterior é outra variável, não um
     motivo de exclusão retroativa.
2. **Classificação automatizada, não biográfica.** No `brasil_2026`, `categoria` (desafiante,
   incumbente pleno, incumbente por sucessão, candidato de continuidade) veio de apuração manual
   em fontes jornalísticas por candidato — não escala para um censo de múltiplos ciclos. Aqui,
   `categoria` deve ser **derivada mecanicamente** dos próprios dados do TSE:
   - incumbência: candidato ocupava o cargo de governador no momento do registro (cruzar com o
     resultado do ciclo anterior — quem venceu ou assumiu por sucessão);
   - resultado: `DS_SIT_TOT_TURNO` / situação de totalização (eleito, eleito por QP, 2º turno,
     não eleito) do dataset de resultados de cada ciclo;
   - votos: total de votos e % de votos válidos, do dataset de resultados.
   - Isso é uma trade-off consciente: perdemos a granularidade fina do `categoria_raw` (ex.: "era
     vice-governador, assumiu por renúncia do titular para concorrer à Presidência") que o
     `brasil_2026` capturava com apuração jornalística. Para um artigo com N grande, a variável
     estrutural (situação de totalização do ciclo anterior) é o que dá pra defender de forma
     reprodutível; detalhe biográfico fica para notas de rodapé/estudos de caso, se necessário,
     não para a variável de regressão.
3. **Alvo de publicação: periódico acadêmico com modelo em painel** (efeitos fixos por estado e/ou
   ciclo), não imprensa. O texto para imprensa, se vier, é um subproduto depois do artigo
   acadêmico, não o objetivo principal deste projeto.
4. **Ruído da cauda é dado, não erro.** Candidaturas nanicas/partido de aluguel tendem a entregar
   propostas de governo curtas ou genéricas só para cumprir a exigência formal. Não excluir esses
   casos por critério ad hoc (reintroduziria viés de seleção) — reportar a distribuição completa e
   rodar o modelo principal com e sem um piso de palavras como checagem de robustez (o piso exato
   é decisão a tomar quando os dados estiverem em mãos, olhando a distribuição real).

## Fontes de dados (Portal de Dados Abertos do TSE — dadosabertos.tse.jus.br)

Por ciclo (2014, 2018, 2022, 2026), três datasets por estado:
- **Candidatos** (`candidatos-AAAA`, arquivo `consulta_cand_AAAA.zip`, um CSV por UF + um
  `consulta_cand_AAAA_BRASIL.csv` consolidado): registro, partido, situação de candidatura.
- **Proposta de Governo** (`candidatos-AAAA` → recurso "Proposta de Governo", um zip de PDFs por
  UF): os documentos em si — matéria-prima para rodar o índice de base empírica. Já tínhamos
  alguns desses zips de 2026 baixados de sessão anterior (`proposta_governo_2026_AM.zip`,
  `proposta_governo_2026_RO.zip`, no Downloads do usuário) — confirma o formato esperado.
- **Resultados/Votação**: totais de voto por candidato, situação de totalização por turno.

**Schema confirmado nesta sessão** (baixei e abri `consulta_cand_2026.zip` de verdade — não é mais
suposição): CSV `;`-delimitado, encoding ISO-8859-1 (latin1), CRLF, 50 campos. Os que importam para
este projeto:

| Campo | Uso aqui |
|---|---|
| `SG_UF` | filtro de estado |
| `DS_CARGO` | filtrar `"GOVERNADOR"` (valores possíveis incluem também PRESIDENTE, VICE-GOVERNADOR, SENADOR, DEPUTADO ESTADUAL/FEDERAL/DISTRITAL, 1º/2º SUPLENTE) |
| `SQ_CANDIDATO` | chave única do candidato — usar para casar com o arquivo de proposta de governo e com o de resultados |
| `NM_CANDIDATO`, `NM_URNA_CANDIDATO` | nome |
| `SG_PARTIDO`, `NM_PARTIDO` | partido |
| `CD_SITUACAO_CANDIDATURA` / `DS_SITUACAO_CANDIDATURA` | situação do registro (deferido/indeferido/etc.) — **importante: o próprio dicionário do TSE (leiame.pdf) diz que este campo só é aplicável a eleições até 2022.** Para 2026 vem sempre `#NE` (não estabelecido) até a Justiça Eleitoral concluir o julgamento dos registros — não é um bug nosso, é o dado ainda não existir nesta fase do ciclo. |
| `CD_SIT_TOT_TURNO` / `DS_SIT_TOT_TURNO` | situação de totalização (eleito, não eleito, 2º turno etc.) — só populado depois da eleição acontecer; em 2026 vem `#NULO` porque a eleição (4/10/2026) ainda não ocorreu no momento desta checagem (22/09/2026). Para 2014/2018/2022 deve vir preenchido de verdade. |
| `DT_NASCIMENTO`, `DS_GENERO`, `DS_GRAU_INSTRUCAO`, `DS_COR_RACA` | variáveis de controle, se o modelo precisar |

**Contagem real de candidatos a governador em 2026 (censo, não amostra):** 201 candidatos
registrados nacionalmente, contra os 58 curados por posição nas pesquisas no `brasil_2026`. Isso
confirma na prática o que discutimos: o censo é ~3,5x maior só em 2026; em 4 ciclos a base deve
ficar na casa de 700–900 candidaturas, não umas centenas — dimensionar processamento (extração de
PDF + índice lexical) para essa escala, não para 58×4.

**Padrões de URL confirmados de verdade (não suposição) — atualização desta sessão, via WebFetch:**

| Dataset | Padrão de URL | Confirmado para |
|---|---|---|
| Candidatos (censo) | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_AAAA.zip` | 2014, 2018, 2022, 2026 (as 4 checadas via WebFetch na página do dataset `candidatos-AAAA`; padrão idêntico nas 4) |
| Proposta de Governo (por UF) | `https://cdn.tse.jus.br/estatistica/sead/odsele/proposta_governo/proposta_governo_AAAA_UF.zip` | 2026, testado para PB, PR e RR (as 3 responderam com dados binários reais, não erro) — muito provável que valha para as 27 UFs e para os outros ciclos também, mas só ciclos/UFs testados de fato contam como "confirmado" |
| Resultados/Votação nominal | `https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_AAAA.zip` | 2022 (confirmado via página do dataset `resultados-2022`) |

**Nota operacional sobre a rede (atualizada):** `cdn.tse.jus.br` e `dadosabertos.tse.jus.br`
continuam bloqueados para **download real** tanto pelo `Bash` do container de nuvem quanto pelo
terminal que rodo na máquina do usuário (`device_bash`) — confirmado de novo nesta sessão
(`curl` retorna 403, "blocked-by-allowlist"). **Porém**, a ferramenta `WebFetch` consegue alcançar
esses domínios (rota de rede diferente, não passa pelo mesmo proxy do container) — só que ela
converte a resposta para texto/markdown e descarta conteúdo binário, então serve para **descobrir a
URL exata de um recurso** (abrindo a página do dataset ou do recurso no `dadosabertos.tse.jus.br` e
pedindo o link de download), mas não serve para baixar o zip de verdade. Ou seja: o `WebFetch`
elimina a necessidade de o usuário navegar manualmente pela interface do CKAN para achar cada
recurso, mas o clique final para baixar o arquivo continua sendo do usuário, no navegador dele.
Fluxo atual: eu descubro/confirmo a URL exata via `WebFetch` → mando o link pronto → usuário clica e
baixa → eu leio depois pela ponte com o computador.

**Como os PDFs de "Proposta de Governo" foram obtidos no `brasil_2026` (verificado nos arquivos
originais, não suposição):** o método variou por região, e isso importa para decidir o método
deste projeto.
- **Norte (AC, AP, AM, PA, RO, TO), Centro-Oeste (DF, GO, MT, MS) e Sudeste (ES, MG, RJ, SP):**
  baixados **em lote por estado**, via o zip oficial `proposta_governo_2026_XX.zip` do dataset
  "Proposta de Governo" do TSE. Evidência: cada estado tem uma pasta com PDFs de nome numérico no
  padrão do próprio TSE (ex.: `2026AM40002532272_01.pdf`) e um `leiame.pdf` byte-idêntico (162.759
  bytes) em todos eles — assinatura inconfundível do zip oficial extraído.
- **Nordeste:** método diferente, candidato por candidato. Evidência clara na Paraíba, o único
  estado da região com PDF sobrevivente: nomes de arquivo legíveis e não-padronizados
  (`Plano_Cicero_Lucena.pdf`, `Plano_Efraim_Filho.pdf`) — claramente baixados um a um, não do zip
  em lote. Os demais estados do Nordeste não têm PDF nem zip sobrevivente para confirmar, mas o
  padrão bate com o relato do usuário.
- **Sul:** sem PDF nem zip sobrevivente em nenhum dos três estados — método não verificável pelos
  arquivos que restaram.

**Implicação para este projeto:** o download em lote por estado (zip oficial "Proposta de
Governo") é o caminho comprovadamente viável e muito mais rápido — e com a escala aqui (censo
completo, ~700–900 candidaturas em 4 ciclos, não 58 curados), é o método a priorizar por padrão.
Baixar candidato por candidato como foi feito no Nordeste do `brasil_2026` não escala para este
projeto.

## Metodologia (herdada do brasil_2026, a validar de novo por ciclo)

- Mesmo índice lexical determinístico (3 pilares: A. diagnóstico com dado numérico, B. efeito
  mensurável projetado, C. referência a evidência/mecanismo causal externo) aplicado à mesma regra
  para todos os candidatos, em todos os ciclos — é o que garante comparabilidade ao longo do
  tempo.
- **Validar kappa por ciclo, não só reusar o kappa de 2026** (lá foi 0,80 em amostra de 265
  frases). Qualidade/formato do PDF pode variar bastante entre 2014 e 2026 (OCR mais necessário em
  documentos antigos, por exemplo) — checar antes de confiar no número.
- Índice dual (o "legado" vs. o "de base empírica" que o `brasil_2026` mantinha para auditoria) —
  manter os dois campos aqui também, mesma lógica de nunca sobrescrever silenciosamente uma
  reclassificação.

## Disciplina de verificação (carregada do projeto anterior)

- Nunca reescrever/reclassificar em silêncio — toda correção registrada com o que mudou e por quê.
- Verificação por reprodutibilidade: outro codificador (humano ou segundo LLM independente) numa
  amostra, kappa reportado.
- Antes de confiar numa pasta local ou num arquivo consolidado, checar tamanho/contagem contra a
  fonte, não confiar em nome de pasta ou data de modificação.

## Estado atual (nesta sessão)

- Estrutura de pastas criada (`dados_tse/`, `propostas/`, `codificacao/`, `analise/`, `docs/`).
- **`brasil_2026` re-sincronizado parcialmente**: o workspace de nuvem tinha sido reiniciado entre
  sessões e a pasta original tinha sumido daqui. Recuperei do computador do usuário (pasta
  `Downloads\brasil_2026`, que ele mantém como cópia íntegra) o motor do índice
  (`programs/motor_indice_base_empirica.py`), `programs/build_dashboard.py`, as notas
  metodológicas (`metodologia/NOTA_METODOLOGICA.md`, `metodologia/INDICE_BASE_EMPIRICA_MELHORIAS.md`,
  `NOTAS_METODOLOGICAS_PENDENTES.md`) e os dados nacionais consolidados de 2026
  (`nacional/RELATORIO_NACIONAL.md`, `dados_nacionais.csv/json`, `build_dados_nacionais.py`,
  `build_site_data.py`) para `/home/claude/brasil_2026/` nesta nuvem. **Não trouxe os PDFs dos 58
  planos nem os dashboards estaduais** (não precisamos deles para este projeto agora, e são
  pesados) — se algum dia precisar, o zip completo está em `Downloads\brasil_2026.zip` /
  `brasil_2026 (2).zip` no computador do usuário, ou no OSF.
- **`consulta_cand_2026.zip` baixado e aberto de verdade** (usuário baixou manualmente pelo
  navegador dele, contornando o bloqueio de rede do ambiente automatizado — ver nota operacional
  acima). Confirmei o schema real (tabela na seção anterior) e contei 201 candidatos a governador
  registrados nacionalmente em 2026, contra os 58 curados do `brasil_2026`. Uma cópia do CSV
  nacional e do `leiame.pdf` (dicionário de dados oficial do TSE) está salva em
  `dados_tse/2026/`.
- Ainda não baixamos os arquivos de 2014/2018/2022 nem o arquivo de resultados/votação de nenhum
  ciclo.
- **Os 11 estados que faltavam para o censo de "Proposta de Governo" 2026 foram baixados pelo
  usuário e já processados** (AL, BA, CE, MA, PE, PI, RN, SE, RS, SC, RR — extraídos e organizados
  em `propostas/2026/<UF>/`). Auditoria feita cruzando `SQ_CANDIDATO` de cada PDF contra o censo
  (`censo_governador_2026.json`): cobertura de **100% dos 83 candidatos a governador desses 11
  estados** (zero candidato do censo sem proposta de governo). Achado sistemático: em CE, MA, PE e
  PI aparece exatamente **1 PDF a mais por estado** cujo `SQ_CANDIDATO` não bate com nenhum
  candidato a `GOVERNADOR` no censo (4 "órfãos" no total) — não investigado a fundo, mas como o
  cruzamento é feito a partir do censo (não do PDF), esses órfãos são automaticamente ignorados e
  não afetam a cobertura.
- **Os outros 15 estados (Norte, Centro-Oeste, Sudeste, Sul restante) foram recuperados da pasta
  `brasil_2026` antiga no computador do usuário** (alguns estavam em subpastas `_to_delete`, mas
  íntegros) e agora também extraídos/auditados: AC, AM, AP, DF, ES, GO, MG, MS, MT, PA, PR, RJ, RO,
  SP, TO. **26 de 27 estados cobertos — só falta Paraíba (PB)**, que no `brasil_2026` original foi
  baixada candidato por candidato (não em lote), então ainda não temos um zip oficial completo dela.
  - **Achado da auditoria (versão inicial, 26 UFs):** os zips reaproveitados do `brasil_2026` antigo
    foram baixados há várias semanas (~19/08), enquanto o período de registro de candidatura ainda
    estava/está em andamento, deixando alguns candidatos sem proposta correspondente.
  - **Paraíba baixada em lote e MG/PA/RJ/SP/TO re-baixados frescos** (a pedido, pelos links diretos
    do CDN do TSE) e reprocessados. **Auditoria final: 27 de 27 estados, 201 candidatos no censo,
    205 PDFs encontrados.** Restam apenas **2 candidatos sem proposta correspondente** (RJ:
    `SQ_CANDIDATO` 190002550196; SP: `SQ_CANDIDATO` 250002548080) — mesmo baixando fresco, o
    registro de candidatura para 2026 segue aberto até perto da eleição (4/10), então é esperado que
    esses 2 tenham registrado depois do download de hoje (23/09); revisitar antes de fechar o
    corpus definitivo. Seguem **6 PDFs "órfãos"** (sem match no censo de governador) em CE, ES, MA,
    PE, PI (1 cada, mesmo fenômeno de defasagem temporal ou candidatura de outro cargo agrupada no
    zip) — não afetam a cobertura porque o join parte do censo.
- **Estrutura de diretórios organizada** (`/home/claude/brasil_multiciclo/`):
  - `dados_tse/<ano>/` — `consulta_cand_<ano>_BRASIL.csv` + `leiame_consulta_cand.pdf` (dicionário
    oficial) + `derivados/censo_governador_<ano>.csv|json` (censo de governador já filtrado/limpo).
    Ciclos presentes: 2014, 2018, 2022, 2026.
  - `propostas/2026/<UF>/` — PDFs de "Proposta de Governo" por estado, direto do zip oficial do TSE
    (nome de arquivo no padrão `2026<UF><SQ_CANDIDATO>_01.pdf`) + `leiame.pdf` de cada zip. 27 UFs
    completas.
  - `programs/` — scripts de processamento (`build_censo_governador.py`; mais scripts do índice
    lexical virão aqui depois de re-sincronizados/recriados).
  - `codificacao/`, `analise/`, `docs/` — reservadas, ainda vazias (próximas etapas: join
    censo+proposta+índice, modelo em painel, e o texto do artigo).
- **Censo de candidatos a governador confirmado para os 4 ciclos** (rodei
  `build_censo_governador.py` para cada um, usando os `consulta_cand_AAAA_BRASIL.csv` reais).
  `DS_SITUACAO_CANDIDATURA` (APTO/INAPTO) e `DS_SIT_TOT_TURNO` (ELEITO/NÃO ELEITO) vêm de fato
  preenchidos para 2014/2018/2022, confirmando a nota do schema (só 2026 vem `#NE`/`#NULO` porque a
  eleição ainda não ocorreu).
  - **Bug real encontrado e corrigido: candidato que vai a 2º turno aparece em DUAS linhas no CSV do
    TSE** (uma por `NR_TURNO`, cada uma com seu próprio `DS_SIT_TOT_TURNO` — a do turno 1 sempre
    "2º TURNO", a do turno 2 com o resultado definitivo "ELEITO"/"NÃO ELEITO"). A primeira versão do
    script contava as duas linhas como dois candidatos. **Corrigido**: agora dedup por
    `SQ_CANDIDATO`, mantendo a linha de `NR_TURNO` mais alto (resultado final) e marcando
    `FOI_A_2_TURNO` (SIM/NÃO) como campo derivado. Contagens corretas (candidatos únicos): **2014 =
    192** (32 foram a 2º turno), **2018 = 204** (28), **2022 = 228** (24), **2026 = 201** (0, eleição
    ainda não ocorreu). **Total corrigido do painel: 825 candidaturas em 4 ciclos** (não 909 como
    calculado antes de corrigir o bug) — ainda assim ~4x maior que os 58 curados do `brasil_2026`.

- **Proposta de Governo de 2014 baixada (27/27 estados) e processada** em
  `propostas/2014/<UF>/`. Padrão de nome do PDF é diferente de 2026: `2014<UF><SQ_CANDIDATO>.pdf`
  (sem sufixo `_01`) — script de auditoria ajustado para reconhecer os dois padrões. Auditoria contra
  o censo corrigido (192 candidatos): **206 PDFs encontrados, 6 candidatos do censo sem proposta**
  (AL, AM, AP, MG, RJ, TO — 1 cada) e **20 PDFs "órfãos"** (bem mais que em 2026; esperado, já que
  documentos de 2014 são mais antigos e o esquema de nomeação do TSE nessa época era menos
  padronizado — DF sozinho tem 9 órfãos). Não investigado a fundo ainda; não bloqueia o uso do corpus
  porque o join parte do censo.
- **Proposta de Governo de 2018 baixada (27/27 estados) e processada** em `propostas/2018/<UF>/`.
  **Achado de nomenclatura: nem todo zip do mesmo ciclo usa o mesmo padrão de nome de arquivo** — a
  maioria de 2018 segue `2018<UF><SQ_CANDIDATO>.pdf` (como 2014), mas o zip de SP especificamente usa
  `proposta_governo_2018_SP_<SQ_CANDIDATO>.pdf`. A auditoria/join não deve mais depender de um regex
  fixo por ano — passei a extrair qualquer sequência de 9–14 dígitos do nome do arquivo e casar
  contra `SQ_CANDIDATO`, o que funciona para os três padrões vistos até agora.
  - **Auditoria contra o censo (204 candidatos, já com o bug de 2º turno corrigido): 179 PDFs
    casados, 31 candidatos do censo sem proposta correspondente.** Investigando por quê: **20 desses
    31 têm `DS_SITUACAO_CANDIDATURA = INAPTO`** (candidatura indeferida) — e candidatura indeferida
    já está fora do escopo da população deste projeto (ver "Diferenças deliberadas", item 1), então
    não é uma lacuna real para a análise. Sobram **11 candidatos `APTO` genuinamente sem proposta no
    zip oficial** — limitação real dos dados de 2018 (possivelmente arquivo não digitalizado/incluído
    pelo TSE nessa época), registrar como limitação conhecida do painel, não tentar preencher
    manualmente por ora. 6 PDFs "órfãos" de novo (mesmo fenômeno de defasagem/nomeação já visto).
- **Proposta de Governo de 2022 baixada (27/27 estados) e processada** em `propostas/2022/<UF>/`.
  Auditoria (regex genérico de dígitos): 228 candidatos no censo, 235 PDFs casados, **só 4 sem
  proposta** (3 `APTO` genuinamente sem PDF, 1 `INAPTO` já fora do escopo) e 11 órfãos. De longe o
  ciclo com melhor cobertura dos quatro — coerente com ser o mais recente antes de 2026.
- **Painel de Proposta de Governo fechado para os 4 ciclos (2014, 2018, 2022, 2026), 27 estados cada.**
  Resumo da auditoria censo × proposta de governo:

  | Ciclo | Candidatos (censo) | PDFs casados | Sem proposta (real, após excluir INAPTO) | Órfãos |
  |---|---|---|---|---|
  | 2014 | 192 | 206 | 6 | 20 |
  | 2018 | 204 | 179 | 11 | 6 |
  | 2022 | 228 | 235 | 3 | 11 |
  | 2026 | 201 | 205 | 2 (registro ainda aberto) | 6 |

  Cobertura é boa em todos os ciclos (regra geral >95% dos candidatos `APTO`); os poucos residuais
  "sem proposta" ficam documentados como limitação conhecida dos dados de origem, não como falha do
  pipeline — não vale a pena caçar manualmente candidato por candidato para uma fração tão pequena.
- **Padrão de URL da Proposta de Governo confirmado também para 2014 e 2018** (via `WebFetch` na
  página do dataset `candidatos-AAAA`, mesmo método usado para 2026): idêntico ao de 2026,
  `proposta_governo_AAAA_UF.zip`, com recurso existindo para as 27 UFs nos três ciclos. Gerei uma
  página (`docs/links_download_propostas_historicas.html`, entregue ao usuário) com os 81 links
  diretos (27 estados × 2014/2018/2022) para ele ir baixando aos poucos, mesmo fluxo usado para 2026.

## Achado novo (14/10/2026): duplicação de template infla N de alguns partidos

Checagem rápida pedida pelo usuário ("como podemos melhorar essa análise? análise de redes
talvez?") — testei se candidatos do mesmo partido reaproveitam o mesmo texto de proposta
(hipótese: template nacional do partido, não documento escrito por cada candidato). Método:
shingles de 12 palavras + similaridade de Jaccard par a par dentro de cada partido (n≥5,
763 candidaturas, 36 partidos), depois clusterização por componente conexo (limiar 0,85) para
estimar o "N efetivo" de textos distintos por partido.

**Resultado: PCO é um outlier isolado.** 42 candidaturas nominais → **apenas 7 textos
distintos** (83% de redução) — um cluster de 18 candidaturas (2026) e outro de 13 (2022) são
texto **idêntico** (mesmo índice calculado, óbvio já que é o mesmo texto) espalhado por 13+
estados diferentes em cada ciclo. Ou seja: a média de 7,10% reportada para o PCO não vem de 42
observações independentes — vem essencialmente de **4 documentos** (um template nacional por
ciclo), cada um "votado" várias vezes pelos estados que o reusaram. Todos os outros 35 partidos
checados (incluindo PSTU, PT, PSOL, PSB, MISSÃO, UP, NOVO) têm 0–5% de redução — **duplicação
não é um fenômeno geral, é específico do PCO**. Isso reforça (não enfraquece) a conclusão
anterior sobre o PSTU: seu índice alto é genuíno, candidato a candidato (59 de 60 textos únicos).

**Implicação para qualquer análise/regressão que use partido como variável**: tratar o PCO com
N=42 (erro padrão como se fossem observações independentes) é estatisticamente errado — na
prática o desvio-padrão entre estados do PCO é quase zero por construção (é o mesmo texto). Antes
de reportar qualquer coisa sobre o PCO no artigo, decidir entre: (a) excluir o PCO de comparações
entre partidos por N efetivo baixo demais, (b) colapsar duplicatas exatas para 1 observação por
cluster antes de calcular médias/erro padrão por partido, ou (c) usar erro padrão clusterizado
por "texto único" (não por estado) em qualquer regressão que inclua partido. Script de checagem
(não definitivo, não salvo como parte do pipeline principal) em
`/tmp/.../scratchpad/full_sweep.py` desta sessão — reescrever como script do projeto
(`programs/`) se a decisão for aplicar a correção.

**Correção aplicada em 15/10/2026** (opção b, colapsar duplicatas antes da média): o método de
detecção (shingles+Jaccard+union-find) foi formalizado para **todos os 49 partidos** do painel
(não só os 36 com n≥5 testados na checagem original) em `programs/detectar_duplicatas_texto.py`
→ `analise/clusters_texto.json` (mapa `"{ano}_{sq}" → cluster_id`) e
`analise/resumo_duplicatas_por_partido.json`. O painel completo (`build_painel_multiciclo.py`)
ganhou o campo `CLUSTER_TEXTO_ID` por linha (não destrutivo — o dado nominal cru continua
intacto, auditável). O agregado "por partido" do dashboard (`build_dashboard_data.py`) passou a
agrupar por `(partido, cluster_id)`: `n` agora é **N efetivo** (textos únicos, não candidaturas
nominais) e `media` é a média das médias por cluster (não a média nominal das 42 linhas cruas no
caso do PCO) — campos `n_nominal`/`media_nominal` preservados à parte para quem quiser comparar.
Corte de inclusão no card trocado de `n nominal ≥ 15` para `n_efetivo ≥ 10`, o que **exclui o PCO**
do gráfico "por partido" (n_efetivo=7) sem tirar nenhum partido genuinamente bem representado —
ele continua visível candidato a candidato na tabela completa. Confirmado: nenhum outro partido
precisou de ajuste por esse motivo (maior caso fora do PCO é PCB, 30→26, 13,3% de redução — bem
abaixo do 83,3% do PCO).

## Achado novo (15/10/2026): o efeito de incumbência desaparece quando comparado dentro da mesma pessoa

A pedido do usuário ("também gostei da ideia do candidato com ele mesmo"), montei um painel
individual via `NR_CPF_CANDIDATO` (`programs/analise_candidato_mesmo.py`,
`analise/painel_candidato_mesmo.json|csv`): 108 pessoas aparecem em 2+ ciclos com índice válido;
26 delas têm registro de **ambas** as condições — foram desafiante numa candidatura e incumbente
em outra.

**O dashboard atual mostra, de forma cross-sectional (pessoas diferentes), desafiante=4,9% vs.
incumbente=2,8%** (diferença grande, "contraintuitivo" — ver card do dashboard). **Comparando a
MESMA pessoa consigo mesma (N=26), o efeito quase desaparece e inverte de sinal**: desafiante=2,38
vs. incumbente=2,78 (+0,40 ao virar incumbente), 13 sobem e 12 descem. Isso é evidência de que o
padrão cross-sectional é majoritariamente **seleção** (quem chega a ser incumbente já era, em
média, um tipo de candidato com índice mais baixo) e não um **efeito causal** de ocupar o cargo
sobre o estilo retórico da pessoa. N=26 é pequeno — não dá para cravar "não há efeito", mas dá
para dizer que a magnitude do efeito cross-sectional não se sustenta within-person, o que é
material o bastante para mudar a redação do achado no artigo (de "incumbência reduz a base
empírica" para algo como "a diferença observada entre incumbentes e desafiantes é em grande parte
composicional, não um efeito do cargo em si — ver robustez via comparação intra-candidato").

Achado secundário da mesma checagem: a tendência de alta ao longo dos ciclos (3,8%→5,6%) **não é
um efeito de aprendizado dos mesmos políticos ficando melhores com o tempo** — entre quem repete
candidatura, a variação 1ª→última candidatura é basicamente plana (47 sobem, 50 descem, delta
médio +0,26). A alta observada no painel completo é mais provável de vir de **composição**
(entrada de candidatos novos com perfil diferente a cada ciclo) do que de mudança de
comportamento dos mesmos indivíduos — outro ponto a qualificar na redação do achado central.

Também: 35% dos que repetem candidatura trocam de partido entre uma e outra — relevante para
qualquer modelo que use partido como variável (o "mesmo partido" nem sempre é o mesmo político, e
vice-versa).

**Ainda não incorporado ao dashboard nem ao texto do artigo** — só a análise e os dados brutos
estão prontos; a decisão de como reescrever os cards "Desafiante vs. incumbente" e "índice sobe de
ciclo em ciclo" à luz disso é próximo passo.

## Investigação (15/10/2026): viabilidade de rede candidato↔empresa de consultoria política

A pedido do usuário, investiguei se dá para montar uma rede bipartida candidato↔consultoria de
marketing político usando o dataset de prestação de contas do TSE (`dadosabertos.tse.jus.br`,
dataset `prestacao-de-contas-eleitorais-<ano>`, mesmo portal usado para censo/proposta de
governo). **Confirmado que o dado existe, mas o formato muda bastante entre ciclos**:

| Ciclo | Recurso mais promissor | Observação |
|---|---|---|
| 2026 | `despesa_documento_2026.zip` ("Documentos fiscais de despesa", candidato e partido) — URL: `https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/despesa_documento_2026.zip` | Parece ser o nível mais granular (documento fiscal individual, provavelmente com nome/CNPJ do fornecedor) — formato novo, não existia nos ciclos anteriores com esse nome. |
| 2022, 2018 | `prestacao_de_contas_eleitorais_candidatos_<ano>.zip` | Só "Candidatos" — não confirmado se é por documento/fornecedor ou já agregado por candidato; TSE não descreve os campos na página do dataset. |
| 2014 | `prestacao_final_2014.zip` / `primeira_parcial_2014.zip` / `segunda_parcial_2014.zip` (formato antigo do SPCE, TXT) | Schema provavelmente bem diferente dos ciclos mais recentes — maior risco de retrabalho. |

**Nenhum desses zips foi aberto ainda** — `cdn.tse.jus.br` continua bloqueado para download direto
(mesma limitação de rede documentada para os outros datasets); preciso que o usuário baixe pelo
navegador dele, como fizemos para censo/proposta de governo/votação. Tamanho é desconhecido mas
provavelmente grande (prestação de contas é por TODOS os cargos, não só governador — pode repetir
o problema de tamanho que tivemos com `votacao_candidato_munzona`, resolvido ali com filtro via
`device_bash`/`awk` direto de dentro do zip antes de extrair).

**Decisão do usuário**: pilotar só 2026 primeiro. Resultado do piloto (15/10/2026):

- Baixei `despesa_documento_2026.zip` (5MB, bem menor do que o temido) e abri
  `despesa_candidato_documento_2026_BRASIL.csv` (consolidado nacional, `;`-delimitado,
  ISO-8859-1). Schema confirmado: `SQ_CANDIDATO`, `DS_CARGO`, `NR_CPF_CNPJ_FORNECEDOR`,
  `NM_FORNECEDOR`, `DS_DRD` (categoria da despesa), `VR_DESPESA` — exatamente o que precisávamos
  para montar a rede bipartida candidato↔fornecedor. Script:
  `programs/build_rede_fornecedores.py` (lê o CSV de um caminho de scratchpad, não commitado —
  arquivo bruto não faz parte do projeto, só o script e a saída agregada).
- **Problema real, não bug**: de 201 candidatos a governador do painel 2026, só **13** têm
  qualquer despesa registrada em todo o arquivo nacional (confirmado que não é erro de join —
  contei `SQ_CANDIDATO` únicos com `DS_CARGO=='Governador'` direto no CSV, deu 13 também). Causa:
  é uma **prestação de contas PARCIAL** (a notícia do TSE que achou o dataset já avisava disso) —
  a eleição foi em 4/10/2026, a prestação final só fecha algumas semanas depois. Hoje o dado está
  cedo demais para ser útil.
  - Dos poucos fornecedores compartilhados entre 2+ candidatos a governador que apareceram, a
    maioria é plataforma genérica de baixo valor informativo (Facebook Serviços Online — qualquer
    campanha moderna compra anúncio lá; um gateway de pagamento). O único caso com cara de
    consultoria de verdade foi "ALMEIDA & GALVÃO ASSOCIADOS LTDA", ligando Patrus Ananias
    (PT/MG) e Gabriel (MDB/MG) — mas N=2, não dá pra tirar conclusão.
- **Decisão (15/10/2026): pausar e voltar a baixar depois que a prestação final de 2026 fechar.**
  Quando o usuário trouxer essa linha de volta, o fluxo já está pronto: baixar o mesmo
  `despesa_documento_2026.zip` atualizado (URL não muda), restagear, e rodar
  `build_rede_fornecedores.py` de novo — não precisa reconstruir nada.

## Achado novo (15/10/2026): auditoria do índice para o PSTU — bug real encontrado e corrigido, mas o índice elevado continua majoritariamente genuíno

O usuário levantou a suspeita, no mesmo pedido que priorizou o ajuste do PCO: "tenho algumas
ressalvas com o PSTU aparecendo tão bem. talvez nosso próprio índice os esteja superestimando."
Fiz uma auditoria manual dos **73 exemplos de Pilar B** do PSTU (`exemplos_pilar_b` em
`codificacao/indice_base_empirica_<ano>.json`, todos os ciclos).

**Achado: havia um bug real, não é só percepção.** ~44% desses exemplos eram falso-positivo, todos
do mesmo padrão: a frase descreve um **resultado passado/atual negativo** (estilo retórico de
crítica estrutural, comum no material do PSTU — "atingiu menos de 15% da meta de reduzir a
mortalidade infantil"), mas continha a palavra "meta de", que estava na lista `FUTURO_RE` e
cancelava a exclusão de passado em `is_efeito()` — classificando como projeção futura (Pilar B
positivo) algo que na verdade é diagnóstico de fracasso passado. Root cause isolado e documentado
em `programs/motor_indice_base_empirica.py` (comentário datado acima de `PASSADO_RE`).

**Correção**: removida a condição "meta (?:de|:)" de `FUTURO_RE` (meta por si só não indica tempo
verbal — outros gatilhos de `FUTURO_RE` como "até <ano>" continuam cobrindo metas genuinamente
prospectivas); adicionados a `PASSADO_RE` os padrões de comparação/crítica estrutural que também
apareciam nos falso-positivos ("em relação a `<ano>`", "no mesmo período de `<ano>`", "já
está/estão", "que existe hoje", "sofrendo", "fez aumentar/diminuir/com que", "privatizou").
Validação: 10/24 falso-positivos curados corrigidos, 0/10 verdadeiro-positivos regredidos; contra a
amostra formal de 204 frases (`kappa_gabarito_v3.json`), **0 frases mudaram de classificação,
kappa do Pilar B inalterado em 0,769** — ou seja, a amostra estratificada original não continha
esse padrão específico (concentrado no estilo retórico do PSTU), então a correção é estritamente
aditiva sobre a validação existente.

**Impacto real, reprocessando os 4 ciclos inteiros**: a média do PSTU (por texto único, já
descontando duplicação — ver achado do PCO acima) caiu de **11,33% para 10,95%** (nominal: 11,56%
→ 11,17%). Uma redução real, mas modesta (~3,4%). **O índice médio geral do painel não mudou
visivelmente ciclo a ciclo** (2014=3,8 / 2018=3,7 / 2022=5,1 / 2026=5,6 — idênticos ao valor
pré-correção na precisão de uma casa decimal), porque o bug afeta uma fração pequena do corpus
total concentrada num estilo retórico específico.

**Conclusão para o artigo**: a ressalva do usuário estava parcialmente certa — havia, sim, um bug
de classificação, e ele foi corrigido. Mas ele não explica a maior parte da diferença: mesmo depois
da correção, o PSTU continua **~2x acima do segundo partido mais alto** (PCB, 5,63%) e muito acima
da média geral de cada ciclo. Isso é evidência de que o índice elevado do PSTU é **majoritariamente
genuíno** (texto de fato mais carregado de diagnóstico numérico/evidência causal, estilo
característico da retórica do partido), não um artefato do motor — mas vale registrar no artigo,
como limitação de escopo, que o motor passou por uma correção específica após auditoria de um
partido com estilo retórico atípico, e que **não se pode descartar a priori** que outros estilos
retóricos minoritários no painel tenham vieses residuais não detectados pela amostra de validação
de 204 frases (que foi estratificada por ciclo/resultado, não por partido ou estilo retórico).

## Achado novo (17/10/2026): modelo multinível — variação por estado é desprezível depois de controlar ano/região/gênero/tamanho do texto

A pedido do usuário (prioridade antes de qualquer análise de rede): "multilevel/hierarchical model
(candidato dentro de estado dentro de região dentro de ciclo) em vez de efeito fixo simples — mais
apropriado dado que o N por estado varia bastante."

**Decisão metodológica (documentada em `programs/modelo_multinivel.py`)**: a estrutura de 4 níveis
pedida (candidato < estado < região < ciclo) foi implementada como **candidato < estado (aleatório)
aninhado em região (fixo)**, com **ciclo também fixo**. Região (5 categorias) e ciclo (4 categorias)
têm grupos de menos para estimar uma variância de efeito aleatório com confiabilidade (regra prática
usual: mínimo ~5–10 grupos, confortável 20+); estado (27 grupos) tem N suficiente. Isso ainda é um
modelo hierárquico de verdade — a variância de estado é estimada **depois de condicionar em
região**, o que equivale a "aninhado em região" — só que região entra como efeito fixo em vez de
aleatório, pela razão estatística acima, não por atalho.

Dois modelos ajustados (`analise/modelo_multinivel_resultados.txt`, sumário completo;
`analise/modelo_multinivel_icc.json`, componentes de variância):
- **M1** (todos os 4 ciclos, N=779): `indice ~ C(ano) + C(região) + C(gênero) + log(palavras) + (1|estado)`
- **M2** (2018–2026, N=593, robustez com incumbência): idem + `incumbente`

**Achado central: a variância entre estados é essencialmente nula.** ICC (fração da variância total
atribuível ao estado, depois de controlar ano/região/gênero/tamanho do texto) = **0,6% em M1, 1,1%
em M2**. Comparação de AIC confirma: o modelo com efeito aleatório de estado (ajustado por máxima
verossimilhança para comparação justa) tem AIC levemente PIOR que o OLS simples sem estrutura
hierárquica (5167,8 vs. 5163,8) — i.e., adicionar o intercepto aleatório por estado não melhora o
ajuste, porque praticamente não há variância sistemática entre estados para capturar. A variância
residual (candidato a candidato, dentro do mesmo estado) é ~43 em ambos os modelos — ordens de
grandeza maior que a variância entre estados (0,26–0,50).

**Implicação para o artigo**: isto não invalida o modelo multinível — ao contrário, é exatamente o
tipo de achado que justifica tê-lo rodado: agora há evidência formal, não só suposição, de que
clustering por estado não é uma ameaça relevante aos erros-padrão de uma regressão mais simples
(efeito fixo ou nem isso). A heterogeneidade do índice é, na prática, quase toda **individual**
(candidato a candidato), não geográfica — reforça o enquadramento já sugerido pelos achados de
13–15/10 (duplicação de template no PCO, seleção/composição no efeito de incumbência): **o índice
varia muito mais por quem escreve o quê do que por padrões estruturais de partido, região ou
ciclo**. Efeitos fixos/significativos que sobrevivem nos dois modelos: ano (2026 > 2014, mesmo
controlando composição), região Nordeste (mais alto que Centro-Oeste, a referência), tamanho do
texto (textos maiores têm índice um pouco maior, esperado), e incumbência em M2 (incumbente ~2,1
p.p. mais baixo, mesmo controlando ano/região — consistente com o achado de seleção do painel
CPF-comparável de 15/10, mas aqui em nível populacional, não só nos 26 casos comparáveis).

**Limitações a registrar no artigo**: (1) o índice é um percentual limitado a [0,100] com massa em
zero (27,3% das candidaturas têm índice=0) — este modelo usa regressão linear padrão (Gaussiana) por
simplicidade/interpretabilidade; um robustness check com Tobit ou regressão Beta inflacionada em
zero (mais apropriado à distribuição) é um próximo passo natural, ainda não feito. (2) Partido foi
deliberadamente deixado de fora da estrutura aleatória deste primeiro modelo (já tem o dashboard
"por partido" dedicado); um efeito aleatório cruzado estado × partido é a extensão óbvia de
robustez. (3) O ajuste por ML de M1 (só para comparação de AIC) não convergiu de forma limpa
(ConvergenceWarning) — não afeta os coeficientes/variâncias reportados acima, que vêm do fit REML
(convergiu normalmente), só a comparação de AIC lateral.

## Estudo (17/10/2026, atualizado 17/10/2026): índice por área de política pública

**Posicionamento explícito (pedido do usuário)**: este NÃO é o artigo principal do projeto — é um
estudo entre vários que o painel `brasil_multiciclo` sustenta (ver lista completa na seção "Próximos
passos combinados" e no doc `Índice de Base Empírica por Área de Política Pública — Esboço de
Estudo`, https://claude.ai/artifact/VYgWauwS37ZRZ3KAip7qsC). Decidir com o usuário, mais adiante, se
vira seção do artigo principal ou paper à parte.

Pedido original: "topic modeling do texto das propostas para quebrar o índice por área de política
pública (saúde, educação, segurança, economia) ... segunda dimensão de achado ... sem precisar de
dado novo, só reaproveitar o texto que você já extraiu." Decisão de método perguntada ao usuário
(AskUserQuestion): classificação por dicionário (escolhida) vs. LDA/NMF não-supervisionado — dicionário
mantém a mesma disciplina determinística/auditável do motor principal. Em 17/10/2026 o usuário pediu
para (a) validar por kappa e (b) adicionar uma 5ª área: **meio ambiente**.

**Método** (`programs/classificar_dominio_politica.py`): reextrai o texto de cada candidatura (834
com texto), quebra em frases, e cada frase "com base empírica" (pilar A/B/C) ou "compromisso sem
base" é testada contra um dicionário de termos por área (5 dicionários, ~25–30 termos/regex cada).
Multi-rótulo permitido. índice por área usa a mesma fórmula do índice geral, particionada:
`n_base_área / (n_base_área + n_compromisso_área) × 100`; candidato que nunca menciona uma área fica
com índice ausente (não zero) nessa área.

**Validação por kappa** (`programs/build_amostra_kappa_dominio.py`): amostra de 154 frases (reservoir
sampling — 25 por área entre as que o dicionário classificou + 30 que não classificou em nenhuma, para
checar falso-negativo). Um agente separado, sem acesso aos rótulos do dicionário, rotulou as mesmas
154 frases de forma independente (`Agent` subagent, "codificador cego" — mesmo papel que o LLM cego do
motor principal). Kappa de Cohen por área, binário (presença/ausência):

| Área | Kappa (1ª rodada) | Kappa (depois do ajuste) |
|---|---|---|
| Saúde | 0,726 | **0,940** |
| Segurança | 0,934 | 0,934 |
| Educação | 0,857 | 0,857 |
| Meio ambiente | 0,649 | **0,799** |
| Economia | 0,770 | 0,770 |

**Ajuste aplicado**: a inspeção das discordâncias achou uma causa concentrada — o termo "saneamento"
estava no dicionário de **saúde**, mas o codificador cego classificava a maioria das frases sobre
saneamento básico/marco legal do saneamento como **meio ambiente** (infraestrutura hídrica, não
assistência médica). Corrigido (termo movido de saúde para meio_ambiente) e revalidado contra os
MESMOS rótulos cegos (sem recoletar amostra) — kappa de saúde e meio ambiente sobem para 0,940 e
0,799. Todas as 5 áreas ficam em concordância substancial a quase perfeita (κ ≥ 0,77), no mesmo
patamar do motor principal (Pilar B = 0,77, Pilar C = 0,79). Economia (0,770) e meio ambiente (0,799)
são os kappa mais baixos restantes — próximos candidatos a auditoria, sem causa única identificada
ainda.

**Resultado final (pós-ajuste), todos os ciclos agregados** (`analise/resumo_dominio_politica.json`):

| Área | % que fala do tema | Índice médio | Índice mediano |
|---|---|---|---|
| Segurança | 75,1% | **6,03** | 0,0 |
| Meio ambiente | 66,2% | 4,90 | 0,0 |
| Economia | 91,0% | 4,07 | 0,0 |
| Saúde | 84,9% | 4,06 | 0,0 |
| Educação | 87,8% | **3,29** | 0,0 |

**Achado central: educação é a área com menor base empírica, agregando os 4 ciclos**, e é a mais
fraca isoladamente em 2014 (2,02), 2018 (2,34) e 2022 (4,22). Em 2026 a ordem muda: saúde cai para o
último lugar (3,38) e educação sobe para 4,12 (2ª mais baixa) — mencionar essa inversão recente no
artigo, não só o agregado. Mediana=0,0 em todas as áreas (mesmo padrão do índice geral — distribuição
concentrada em zero, cauda longa).

**Achado lateral não esperado, concentrado em meio ambiente**: índice médio salta de quase
irrelevante para a 2ª área mais bem fundamentada — 2014=0,92; 2018=1,14; 2022=4,36; **2026=11,58**.
Hipótese (ainda não confirmada por leitura direta de amostra — próximo passo): o **Marco Legal do
Saneamento Básico** (Lei nº 14.026/2020), que criou metas numéricas obrigatórias de universalização
(99% água, 90% esgoto até 2033) citadas literalmente em muitos planos a partir de 2022 — um efeito de
política federal sobre o conteúdo estadual, distinto da tendência geral gradual do índice.

**Limitações a registrar no artigo**: (1) `n_candidatos_total`=834 (todos com N_PALAVRAS>0 nos 4
ciclos), levemente diferente do N=825/779 do painel principal/modelo multinível — population base
distinta, registrar se citar os números juntos. (2) Multi-rótulo: uma frase pode contar para mais de
uma área, não somar as colunas de "% que fala do tema" como mutuamente exclusivas. (3) Amostra de
kappa (154 frases) é menor e deliberadamente estratificada (não aleatória simples) — comparável, mas
não idêntica em desenho, à amostra de 204 do motor principal. (4) Hipótese do Marco Legal do
Saneamento ainda não confirmada por leitura direta. (5) Ainda não incorporado ao dashboard — decisão
de visualizar (card "por área de política pública") é próximo passo, não feito nesta sessão.

## Estudo (17/10/2026): índice por área x ideologia partidária (BLS Zucco & Power) — sem relação robusta, achado é PSTU isolado

Pedido do usuário: "vamos verificar se a base empírica por área varia conforme o partido. Use o BLS
de Zucco e Power mais recente para classificar as ideologias partidárias." Extensão direta do estudo
"índice por área" acima — mesmo doc (`programs/ideologia_partidaria_bls.py`,
`programs/analise_indice_por_ideologia.py`).

**Fonte da ideologia**: Zucco & Power (2024), "The Ideology of Brazilian Parties and Presidents...",
*Latin American Politics and Society* 66(1) — Tabela C1 do material suplementar, 9 ondas do BLS
(1990–2021). Escala contínua ~-1 (esquerda) a +1 (direita). Lida por extração de PDF via WebFetch (não
houve acesso à planilha de replicação original no Harvard Dataverse, bloqueada neste ambiente) —
**revisar os números contra a fonte primária antes de publicar**.

**Cobertura**: 31/49 siglas do painel têm score BLS (605/825 candidaturas, 73%). O BLS só entrevista
deputados federais eleitos — partidos que nunca elegeram bancada federal ficam sem score, o que inclui
justamente **PCB, PCO e UP** (3 dos 4 partidos de esquerda marginal centrais ao achado de 15/10 sobre
duplicação de template e índice elevado). **PSTU tem uma única observação em toda a série 1990–2021**
(-0,826) — tratar como estimativa muito incerta, não uma medida robusta.

**Resultado — correlação ao nível de partido (N≥5 candidaturas, score BLS disponível, 25 partidos,
571 candidaturas)**:

| Área | r (com PSTU) | r (sem PSTU) | ρ (com PSTU) | ρ (sem PSTU) |
|---|---|---|---|---|
| Índice geral | -0,26 | +0,19 | +0,02 | +0,15 |
| Saúde | -0,05 | +0,11 | -0,20 | -0,12 |
| Educação | +0,01 | +0,14 | 0,00 | +0,11 |
| Segurança | -0,41 | -0,18 | -0,22 | -0,13 |
| Economia | -0,16 | -0,11 | -0,15 | -0,06 |
| Meio ambiente | +0,02 | +0,08 | -0,15 | -0,12 |

**Achado central: não há relação robusta entre ideologia partidária e o índice, geral ou por área.**
A correlação negativa aparente no índice geral (r=-0,26) depende quase inteiramente do PSTU — um único
ponto, N=1 na série BLS. Removendo-o, r vira +0,19 (fraco, sinal invertido) e Pearson/Spearman
discordam de sinal em metade das áreas, assinatura clássica de resultado puxado por outlier, não
tendência monotônica real. **Conclusão: o índice parece ortogonal à posição ideológica do partido** —
reforça o achado já registrado na auditoria do PSTU (15/10): aquele padrão retórico é um caso
específico do partido, não um gradiente esquerda-direita geral do painel.

**Limitações**: (1) crosswalk sigla→linhagem histórica (PMDB=MDB, PR=PL, PPS=Cidadania, PRB=
Republicanos, PTN/PHS=Podemos etc. — ver `RENOMEACOES` no script) montado por pesquisa, não auditado
por segunda fonte. (2) Tabela C1 lida por extração de PDF, não planilha original — conferir antes de
publicar. (3) O próprio resultado-chave ("é só o PSTU") fica mais frágil sabendo que a posição
ideológica do PSTU também vem de N=1. (4) 224 candidaturas (27%) ficam fora por partido sem score BLS,
incluindo justamente PCB/PCO/UP — não dá para saber se eles seguiriam o padrão do PSTU ou não.

Gráfico de dispersão (índice geral × ideologia, PSTU destacado) e tabela completa no doc
[Índice de Base Empírica por Área de Política Pública — Esboço de Estudo](https://claude.ai/artifact/VYgWauwS37ZRZ3KAip7qsC),
nova seção "Variação por ideologia partidária".

## Convenção (17/10/2026): versionamento e sincronização com o GitHub

Pedido do usuário: "vamos subir sempre o que estamos fazendo para cá:
https://github.com/lfbl-cp/Evidencias-em-planos-de-governo-2026".

Configuração feita nesta sessão: repositório git local inicializado em
`/home/claude/brasil_multiciclo` (branch `main`), remote `origin` apontando
para o repositório acima. `.gitignore` exclui `propostas/` (PDFs originais,
~1GB) e `dados_tse/` (microdados brutos do TSE, ~127MB) — dados de origem,
grandes e reobteníveis nas fontes oficiais, não produto do projeto. Tudo o
mais (código em `programs/`, dados derivados em `analise/` e `codificacao/`,
este `CLAUDE.md`, `docs/`) é versionado.

Acesso ao GitHub exigiu dois passos fora do meu controle (ambos concluídos
pelo usuário): (1) conectar a conta GitHub `felipe-braga-cp` à sessão via
`https://claude.ai/customize/connectors` e (2) autorizar especificamente este
repositório na tela de instalação do GitHub App (`Settings → Applications →
Installed GitHub Apps → Configure → Repository access`).

**Cadência combinada (resposta do usuário a "faça assim", 17/10/2026):**
commit + push **ao final de cada sessão de trabalho**, não a cada achado ou
a cada arquivo alterado. Ou seja: trabalhar normalmente ao longo da sessão
(editar scripts, reprocessar dados, atualizar este arquivo) e, antes de
encerrar ou quando o usuário sinalizar que vai parar por ora, rodar
`git add` + `git commit` (mensagem descrevendo o que mudou na sessão) +
`git push origin main`. Isso evita poluir o histórico com micro-commits a
cada etapa intermediária, mantendo ainda a garantia de que nada do trabalho
fica só na sessão.

**Bloqueio permanente, não resolvido (confirmado de novo em 17/10/2026):** o
`git push`/`gh api` desta sessão de nuvem (`/home/claude/brasil_multiciclo`)
contra `lfbl-cp/Evidencias-em-planos-de-governo-2026` **sempre** falha com
"access denied by the git proxy: ...not in this session's authorized
repository set" — testado repetidas vezes, inclusive depois de (1) a conta
GitHub do usuário (`felipe-braga-cp`) conectada à sessão, (2) o app do GitHub
liberado para "All repositories", (3) o usuário confirmado como colaborador
com Write access de verdade no repo (`lfbl-cp` é de outro laboratório; precisou
aceitar um convite de colaborador). Nenhuma dessas mudanças teve efeito no erro
do proxy — é uma limitação da plataforma Cowork (sem ferramenta `add_repo`
disponível), não um problema de permissão do GitHub. **Não vale a pena tentar
de novo `git push` direto desta sessão** — ir direto para a solução abaixo.

**Solução estabelecida (17/10/2026) — GitHub Codespace como ponte de push:**
como o `git push` do container de nuvem nunca funciona, mas o usuário não sabe
rodar comandos de terminal no próprio computador, o mecanismo de sincronização
daqui pra frente é:

1. No fim da sessão (ou quando o usuário pedir), usar as ferramentas do Chrome
   (`mcp__claude-in-chrome__*`) para abrir `github.com/codespaces` (ou o botão
   "Code → Codespaces" do repositório) e criar/reabrir um Codespace em
   `lfbl-cp/Evidencias-em-planos-de-governo-2026` — **pedir confirmação ao
   usuário antes de criar um novo** (é cobrado na conta `felipe-braga-cp`
   enquanto ativo).
2. O Codespace abre um VS Code + terminal já autenticado com o GitHub do
   usuário — `git push` funciona nativamente ali, sem o proxy bloqueado desta
   sessão.
3. Como não dá para copiar o conteúdo local do container de nuvem direto para
   o Codespace, o caminho que funcionou foi: gerar um zip do conteúdo
   (`git archive` ou zip simples), entregar via `SendUserFile`, o usuário sobe
   pela interface web do GitHub (upload de arquivos) ou — melhor, já testado —
   **digitar os comandos git diretamente no terminal do Codespace** (clonar,
   copiar/reorganizar arquivos com `git mv`/heredoc, commitar, `git push`).
   Preferir sempre reorganizar dentro do próprio Codespace quando possível, em
   vez de depender do upload web (que tem limite de ~100 arquivos por lote e
   achata a estrutura de pastas se não for um drag-and-drop de pasta real).
4. **Ao terminar, parar o Codespace** (`github.com/codespaces` → "..." →
   "Stop codespace") para não deixar rodando à toa (cobrança). Ele tem
   auto-delete configurado por inatividade, então não precisa apagar na mão.

Essa foi a rota usada para corrigir um upload anterior que tinha ido parar
solto na raiz do repo em vez de dentro de `brasil_multiciclo/` (109 arquivos
reorganizados via `git mv` num único commit, mais um arquivo `.gitignore`
perdido — virou `download` por bug de upload de dotfile no navegador — removido
depois). Resultado confirmado em 17/10/2026 (via WebFetch e screenshot do
GitHub): `brasil_multiciclo/` correto na raiz, nada do site antigo
(`centro-oeste/`, `metodologia/`, `nacional/`, `nordeste/`, `norte/`,
`programs/` antigo, `sudeste/`, `sul/`, `index.html`, `.nojekyll`, `.gitignore`
antigo) foi alterado, deployment do GitHub Pages seguiu verde.

## Próximos passos combinados

1. ~~Confirmar o schema exato dos arquivos de candidatos/proposta de governo/resultados do TSE para
   os quatro ciclos~~ — **feito**: censo e proposta de governo confirmados e auditados nos 4 ciclos
   (2014, 2018, 2022, 2026), 27 estados cada. Falta só o arquivo de **resultados/votação**
   (`votacao_candidato_munzona_AAAA.zip`) — padrão de URL já confirmado (via WebFetch em
   `resultados-2022`), mas nenhum arquivo baixado/aberto ainda.
2. ~~Baixar e abrir o arquivo de resultados/votação~~ — **feito para os 3 ciclos históricos (2014,
   2018, 2022)**. Diferença importante em relação aos outros arquivos: `votacao_candidato_munzona`
   é **um zip nacional único por ciclo** (não por estado), mas cada zip tem um CSV por UF (nível
   candidato × município × zona — nada de arquivo consolidado utilizável, o `..._BRASIL.csv` de
   dentro do zip é a soma de tudo e passa de 3GB, inviável). Zips inteiros vieram grandes (2014:
   494MB, 2018: 395MB, 2022: 643MB) — **acima do limite de 400MB por arquivo do `device_stage_files`**
   para os de 2014 e 2022. Solução: usei `device_bash` (roda na VM Linux local do usuário) para
   filtrar `CD_CARGO==3` (Governador) direto de dentro do zip com `unzip -p | awk`, sem nunca
   extrair o zip inteiro em disco, produzindo um CSV filtrado de ~19–28MB por ciclo — só então
   staged para a nuvem. Isso evita o limite de tamanho e é a técnica a repetir sempre que um
   dataset bruto do TSE for grande demais para stage direto.
   - Schema do arquivo mudou entre ciclos (2014 tem menos colunas que 2018/2022 — sem
     situação de julgamento/cassação/diploma/federação), mas `CD_CARGO` fica estável na coluna 17
     nos três, então o filtro funcionou sem ajuste manual por ano.
   - Script `programs/build_resultados_governador.py`: agrega as linhas (por município×zona) somando
     `QT_VOTOS_NOMINAIS` por `SQ_CANDIDATO`/turno, e extrai o resultado final
     (`DS_SIT_TOT_TURNO`) do turno mais alto (mesmo tratamento de 2º turno do censo). Salvo em
     `dados_tse/<ano>/derivados/resultados_governador_<ano>.csv|json`.
   - Resultados: 2014 = 181 candidatos com voto (27 eleitos), 2018 = 184 (27 eleitos), 2022 = 213
     (27 eleitos) — sempre 27 eleitos por ciclo, como esperado (1 por estado). Diferença para o total
     do censo (192/204/228) é candidato que não chegou a receber voto (indeferido/cassado antes da
     eleição, fora do escopo do projeto de qualquer forma).
   - **Validação cruzada**: `DS_SIT_TOT_TURNO` calculado aqui a partir do arquivo de votação bate
     **100%** (0 divergências, nos 3 ciclos) com o mesmo campo já existente no censo
     (`consulta_cand`) — confirma que os dois arquivos do TSE são consistentes entre si e que o
     pipeline de dedup por turno está correto nos dois lados.
   - 2026 não tem esse arquivo ainda (eleição não ocorreu).
3. ~~Re-sincronizar o script do índice lexical do `brasil_2026`~~ — **feito**: `motor_indice_base_empirica.py`
   recuperado de `brasil_2026` (sem alterações no motor em si) e copiado para
   `programs/motor_indice_base_empirica.py` (precisou instalar `wordcloud` via pip só porque o módulo
   importa isso no topo do arquivo, mesmo sem usar a word cloud para o índice). Script novo
   `programs/build_indice_base_empirica.py` roda `pdftotext -layout` + `base_empirica_analise()` sobre
   todos os PDFs de `propostas/<ano>/<UF>/`, casando cada PDF ao `SQ_CANDIDATO` pelo mesmo regex
   genérico de dígitos (`\d{9,14}`) já usado na auditoria de cobertura. Saída por ciclo em
   `codificacao/indice_base_empirica_<ano>.csv|json`.
   - Resultados (todos os PDFs casados, sem ainda restringir a piso de palavras):

     | Ciclo | PDFs processados | Sem texto extraível (pdftotext) | Índice médio | Índice mediano |
     |---|---|---|---|---|
     | 2014 | 206 | 21 | 4.3 | 2.5 |
     | 2018 | 179 | 9 | 4.7 | 3.1 |
     | 2022 | 235 | 18 | 5.8 | 3.3 |
     | 2026 | 218 | 6 | 7.9 | 3.8 |

     Tendência de alta monotônica no índice médio ao longo dos ciclos — resultado relevante para a
     pergunta de pesquisa central (o padrão é estável ou específico de um ciclo?), mas ainda **não**
     controlado por nada (partido, incumbência, tamanho do estado, piso de palavras) — é só o dado
     bruto por enquanto.
   - **Pendência de qualidade de dado**: 54 PDFs (entre os 4 ciclos: 21+9+18+6) retornaram zero texto
     via `pdftotext` — provavelmente PDFs escaneados/imagem. Hoje entram no índice com valor 0.0 (o
     motor trata "sem frases" como índice zero, não como dado faltante), o que pode enviesar médias se
     não for tratado. Opções: rodar OCR (skill `pdf` do Claude suporta) ou marcar/excluir
     explicitamente antes de qualquer análise — **ainda não decidido**.
4. ~~Montar a tabela final que junta censo + proposta de governo (índice) + resultado, por
   candidato, nos 4 ciclos~~ — **feito**: `programs/build_painel_multiciclo.py`, saída em
   `analise/painel_governador_2014_2026.csv|json`, 825 linhas (uma por candidatura, todos os ciclos).
   - Campos principais: identificação (`SQ_CANDIDATO`, `NR_CPF_CANDIDATO`, nome, partido, UF, ano),
     situação (`DS_SITUACAO_CANDIDATURA`, `DS_SIT_TOT_TURNO`, `FOI_A_2_TURNO`), demografia (gênero,
     raça/cor, escolaridade), votos por turno, `INCUMBENTE` (ver abaixo), e os campos do índice de
     base empírica (`INDICE_BASE_EMPIRICA`, `INDICE_LEGADO`, contagens por pilar A/B/C, `N_PALAVRAS_PROPOSTA`).
   - Contagem de "com proposta" no painel é um pouco menor que "PDFs casados" da tabela de cobertura
     acima porque aqui só entra proposta vinculada a um `SQ_CANDIDATO` que existe no censo (exclui os
     PDFs "órfãos" que não batem com nenhum candidato) — por isso o índice médio recalculado aqui
     (4.3 / 4.5 / 5.9 / 6.9) difere um pouco do bruto acima para 2018/2022/2026: é o valor mais
     correto, restrito à população do estudo.
   - **Incumbência**: adicionei `NR_CPF_CANDIDATO` (identificador estável de pessoa, ao contrário do
     `SQ_CANDIDATO` que é por registro/ciclo) ao censo (`build_censo_governador.py`) e reprocessei os
     4 anos (totais confirmados inalterados: 192/204/228/201). Verifiquei que o CPF publicado pelo TSE
     nesse dataset tem sempre 11 dígitos numéricos e é único por candidato em 2022 — é um CPF completo,
     não mascarado, bom o suficiente para join exato. `INCUMBENTE` é derivado automaticamente no
     script do painel: para (ano, UF), busca quem foi `ELEITO` no ciclo anterior (ano-4) no mesmo
     estado e compara o CPF. 2014 fica com `INCUMBENTE = None` (sem dado de 2010 no escopo). Resultado:
     15 incumbentes concorrendo de novo em 2018, 16 em 2022, 9 em 2026 (validado manualmente contra
     casos conhecidos: Reinaldo Azambuja/MS, Rui Costa/BA, Wellington Dias/PI, Waldez Góes/AP — todos
     batem).
5. Decidir o piso de palavras (ou critério equivalente) para a checagem de robustez de candidaturas
   nanicas — a distribuição real já está disponível (`N_PALAVRAS_PROPOSTA` no painel, ex: 2026 vai de
   0 a 76.571 palavras, média 13.839), mas o piso em si ainda não foi escolhido.
6. Tratar os 54 PDFs sem texto extraível (ver item 3) antes de finalizar qualquer análise que dependa
   do índice.
7. ~~Re-visitar o kappa de confiabilidade entre codificadores do índice lexical, nos 4 ciclos~~ —
   **feito, via pipeline de 3 agentes** (codificador cego → revisor adversarial → validador
   independente), a pedido explícito do usuário ("use agents para isso. rode um, outro para achar
   falhas, e um terceiro para validar tudo depois"), em 25/09/2026.
   - **Amostra**: `programs/build_amostra_kappa.py` extrai frases de todos os PDFs, classifica com o
     motor determinístico, e monta amostra estratificada de 204 frases (51/ciclo, cobrindo pilares
     A/B/C + retórica/compromisso/neutro). Gabarito do motor em `analise/kappa_gabarito.json`
     (não mostrado ao codificador), versão cega em `analise/kappa_amostra_cega.json`.
   - **Agente 1 (codificador cego)**: classificou as 204 frases independentemente (sem ver a saída
     do motor nem tentar reconstruir a regex), usando só o codebook dos 3 pilares. Saída em
     `analise/kappa_codificador_llm.json`.
   - **Agente 2 (revisor adversarial)**: comparou motor × LLM, achou 92 discordâncias (de 612
     células = 204 frases × 3 pilares), deu veredito frase a frase e generalizou 11 padrões
     recorrentes de falha. Saída em `analise/kappa_relatorio_falhas.json`.
   - **Agente 3 (validador independente)**: NÃO confiou no relatório do agente 2 — recalculou o
     kappa do zero a partir dos rótulos brutos, auditou 25/92 discordâncias formando veredito
     próprio antes de olhar o do revisor (92% de concordância, 23/25), e releu as frases de 3 dos
     11 padrões recorrentes para confirmar que os exemplos realmente sustentam a descrição (todos
     confirmados). Relatório final em `analise/RELATORIO_KAPPA_MULTICICLO.md`.
   - **Resultado (kappa de Cohen, motor × LLM, N=204)**:

     | Pilar | κ agregado (4 ciclos) | Interpretação | κ por ciclo (2014/2018/2022/2026) |
     |---|---|---|---|
     | A — diagnóstico numérico | 0,366 | Razoável | 0,369 / 0,274 / 0,289 / 0,548 |
     | B — efeito mensurável | 0,469 | Moderada | 0,617 / 0,258 / 0,287 / 0,653 |
     | C — evidência causal externa | 0,681 | Substancial | 0,719 / 0,783 / 0,648 / 0,568 |
     | com_base (A ou B ou C) | 0,621 | Substancial | 0,622 / 0,617 / 0,658 / 0,587 |

   - **Achado principal (validado, não é só ruído)**: o **Pilar B tem um bug sistemático e
     direcional** — nas 27 discordâncias de B na amostra, 100% são falso-positivo do motor (motor
     conta como promessa quantificada o que o LLM não conta; zero casos no sentido oposto). Duas
     causas identificadas e confirmadas por releitura de frase: (1) `EFEITO_RE`/`is_efeito` não
     verifica tempo verbal, então confunde estatística histórica já ocorrida ("houve uma queda de
     6%", "perdeu 388 mil empregos") com promessa futura; (2) `NUM_ANY` captura número de
     numeração de lista/seção/objetivo ("1)", "9.6.1", "Objetivo 11") como se fosse a magnitude da
     meta prometida. Taxa de base de B no motor (20,6%) é quase 3x a do LLM (7,4%) nesta amostra —
     **risco real de superestimar a base empírica das propostas**, mais em documentos com listas
     numeradas de objetivos (formato comum).
   - **Achado secundário (validado, efeito menor)**: Pilar C também infla (18 falso-positivo vs. 7
     falso-negativo) por disparar em jargão vazio tipo "baseado em evidências"/"com base em
     indicadores" sem nomear fonte real — mas o kappa de C já é o mais alto dos três (a maioria dos
     acertos é sólida). Pilar A é o mais ruidoso em kappa mas SEM viés direcional claro (21
     falso-positivo vs. 19 falso-negativo) — mais "régua grosseira" (lista de gatilhos rígida
     demais) que bug sistemático.
   - **Achado que DERRUBA uma hipótese registrada neste arquivo**: não há gradiente temporal
     monotônico de confiabilidade ligado à idade do documento — 2014 tem os MELHORES kappas de B e
     C entre os 4 ciclos, não os piores. **Não afirmar no artigo que a confiabilidade cai em
     documentos mais antigos** — não sustentado pelos dados.
   - **Recomendação do validador, ainda não executada**: corrigir `EFEITO_RE`/`NUM_ANY` (Pilar B) e
     a lista de jargão de `EVIDENCIA_RE` (Pilar C) no motor antes de reportar o índice no artigo —
     Pilar B é o bloqueador mais claro (viés limpo e fácil de corrigir/demonstrar). Depois da
     correção, re-rodar `build_indice_base_empirica.py` nos 4 ciclos e reconstruir o painel
     (`build_painel_multiciclo.py`). Só então vale re-testar o kappa por ciclo e qualquer
     comparação temporal do índice.
8. ~~Corrigir os bugs de regex do motor (Pilar B: tempo verbal + numeração de lista)~~ — **feito,
   em 09/10/2026, só a parte do Pilar B** (Pilar C/jargão vazio continua pendente, não fazia parte
   do pedido desta rodada). Ver comentário versionado em cima de `PASSADO_RE`/`FUTURO_RE` em
   `programs/motor_indice_base_empirica.py` para o histórico completo. Resumo:
   - **Correção 1**: `is_efeito` não contava mais como Pilar B frases com marcador de tempo passado
     (verbo no passado, citação de PNAD/Censo datado, `-X%` com sinal) sem marcador de futuro/meta
     sobrepondo, e passou a ignorar números que são rótulo de lista/seção/objetivo do PDF (não a
     magnitude real de uma promessa).
   - **Pipeline de validação (3 "agentes", como no `brasil_2026`)**: (a) reaproveitei o codificador
     LLM cego já existente (`analise/kappa_codificador_llm.json` — o texto das 204 frases não mudou,
     só a lógica do motor, então não precisava recodificar); (b) um agente revisor adversarial
     auditou a correção (`analise/REVISAO_ADVERSARIAL_V2.md`) e confirmou o kappa (0,469 → 0,769),
     mas achou uma **regressão real**: o gatilho "em ANO" tratava qualquer ano citado como passado,
     inclusive ano futuro de meta ("Em 2030, aumentaremos..." virava falso-negativo) — caso que não
     estava na amostra de 204, mas plausível no corpus completo.
   - **Correção 2** (mesmo dia, em resposta ao achado do revisor): o gatilho "em ANO"/"entre ANO e
     ANO" só conta como passado se o ano citado for anterior ao ano do próprio ciclo eleitoral do
     documento (`ano_ciclo`, novo parâmetro de `is_efeito`/`base_empirica_analise`, propagado a
     partir de `build_indice_base_empirica.py`, que já sabe qual ciclo está processando).
   - **Validador independente final** (`analise/RELATORIO_KAPPA_MULTICICLO_V3_FINAL.md`): recalculou
     tudo do zero, confirmou κ final = 0,769 (substancial), os 15 verdadeiro-positivos originais
     100% preservados, Pilares A/C inalterados (controle negativo correto). Achado adicional não
     documentado antes: a correção do `ano_ciclo` é uma troca ~1-por-1 no kappa desta amostra — corrige
     um caso (censo escolar) mas expõe outro já catalogado (número irrelevante tipo projeção externa
     perto do gatilho, "Padrão B/#3", ainda não corrigido). **2018 é o ciclo com pior kappa (0,408)**
     dos quatro, achado novo a investigar se o painel for usado para comparação entre ciclos.
     **Parecer do validador: pronto para uso no artigo, com essas ressalvas documentadas, não
     bloqueantes.**
   - **4 ciclos reprocessados e painel reconstruído** com o motor final (`codificacao/
     indice_base_empirica_<ano>.*`, `analise/painel_governador_2014_2026.*`). Índices médios por
     ciclo (população do painel, pós-correção): 2014 = 3,9; 2018 = 4,2; 2022 = 5,4; 2026 = 6,2 —
     **a tendência de alta monotônica ao longo dos ciclos sobrevive à correção** (números um pouco
     mais baixos que a versão provisória anterior, como esperado ao remover inflação de falso-
     positivo, mas o padrão central da pergunta de pesquisa não muda).
   - **Ainda pendente, fora do escopo desta rodada**: Pilar C (jargão vazio de "evidência"), o
     "Padrão B/#3" (número irrelevante tipo código de rodovia/temperatura/idade perto do gatilho de
     efeito), fragmentação de frase por `split_sentences` perto de quebras de linha do PDF, e
     decidir o piso de palavras (item 5 abaixo) e os 54 PDFs sem texto extraível (item 6 abaixo).
9. ~~Investigar anomalia PSTU/PCO e corrigir Pilar C (jargão vazio de evidência)~~ — **feito em
   09/10/2026**, a pedido explícito ("vamos fazer as correções metodologicas. Explorar essas
   inconsistencias de partidos como PSTU/PCO").
   - **Investigação PSTU/PCO**: puxei as frases realmente casadas (campo `_exemplos`, mais um
     re-scan completo do corpus, não só as 5 primeiras em cache) nas propostas desses dois partidos.
     Conclusão: a maior parte do índice alto é **achado genuíno, não bug** — PSTU e PCO (esquerda
     pequena, tradição trotskista) escrevem propostas com citação intensa de estatística oficial
     (dados de desigualdade, dívida pública, indicadores de educação/saúde) para sustentar uma
     crítica estrutural — exatamente o padrão que o Pilar C/A deveria capturar. Havia, porém, um
     artefato real sobreposto: a construção "a exemplo de [Nome Próprio]" (citar um caso concreto
     como ilustração, não como evidência causal) disparava `EVIDENCIA_RE` antiga por engano — 22/22
     ocorrências no corpus PSTU/PCO eram falso-positivo (e 7/11 na amostra geral de 204 frases).
   - **Correção do Pilar C**: `EVIDENCIA_RE` (monolítica) foi substituída por `INSTITUICAO_RE`
     (nomes de instituição/lei reais — IBGE, IPEA, Datasus, Sinisa, Mapbiomas, INPE, OMS, Banco
     Mundial, BNDES, BNB, "lei nº" etc. — gatilho incondicional), `JARGAO_EVIDENCIA_RE` (frases
     genéricas como "baseado em evidências"/"com base em indicadores"/"conforme dados"/"modelo já
     adotado" — agora só conta se **também** houver instituição nomeada, número real, ou citação no
     mesmo período) e `EXEMPLO_RE` + `_exemplo_cita_precedente` (a construção "a exemplo de" só
     conta como evidência se o nome citado for de fato um precedente/instituição, não qualquer nome
     próprio). Ver comentário versionado datado em `motor_indice_base_empirica.py`.
   - **Validação (kappa, mesma amostra de 204 frases, mesmo par codificador-cego × motor)**: κ do
     Pilar C passou de **0,681 → 0,794** (substancial → quase perfeito) sem alterar A/B (controle
     negativo correto).
   - **Resultado pós-correção (painel final, após também o item 10 abaixo)**: PSTU n=60 média=11,56
     (era 12,33 antes da correção); PCO n=42 média=7,10 (praticamente inalterado — o artefato "a
     exemplo de" era mais raro nas propostas do PCO que nas do PSTU). **O achado sobrevive à
     correção**: PSTU e PCO continuam no topo entre os partidos com n≥5 (MISSÃO tem média maior,
     16,18, mas n=9, instável). Conclusão de pesquisa a registrar no artigo: índice alto nesses
     partidos é majoritariamente genuíno (estilo retórico denso em estatística oficial para
     sustentar crítica estrutural), não artefato de medição — vale nota metodológica explicando o
     "a exemplo de" como limitação conhecida e corrigida.
10. ~~Tratar os 54 PDFs sem texto extraível (OCR) e decidir o piso de palavras~~ — **feito em
    09/10/2026**.
    - **OCR**: `extrair_texto()` em `build_indice_base_empirica.py` agora tenta `pdftotext -layout`
      primeiro e cai para OCR (`pdftoppm -r 200 -gray` + `tesseract -l por --psm 6`, página a
      página) só quando o resultado vem vazio. Cache em disco por candidato
      (`ocr_cache/<ano>_<uf>_<sq>.txt`) para nunca re-OCRizar o mesmo PDF duas vezes — necessário
      porque OCR é ordens de magnitude mais lento que `pdftotext` (script auxiliar
      `programs/ocr_backfill.py`, rodado uma vez em background com 2 processos paralelos, ~33min
      para as 54 páginas pendentes, 1037 páginas no total somando os ciclos onde pdftotext falhou).
      Cada linha do painel ganhou o campo `FONTE_TEXTO` (`pdftotext` | `ocr` | `sem_texto`) e
      `TEXTO_EXTRAIVEL` (bool) para auditoria — nunca sobrescrevemos silenciosamente.
    - **Resultado**: dos 54 PDFs que `pdftotext` não conseguia ler, **50 foram recuperados via
      OCR** (qualidade boa no spot-check manual — texto corrido, pontuação e acentuação
      preservadas). **4 continuam genuinamente ilegíveis**: 3 PDFs corrompidos de verdade
      (`pdfinfo` reporta "Couldn't find trailer dictionary"/"Couldn't read xref table" — arquivo
      truncado no download, não um problema do nosso pipeline) e 1 PDF gerado pelo Word sem texto
      nem imagem extraível (página em branco ou só elementos vetoriais, `pdfimages -list` não lista
      nenhuma imagem). Esses 4 ficam com `N_PALAVRAS_PROPOSTA=0` e `TEXTO_EXTRAIVEL=False` — **são
      tratados como dado faltante, não como índice zero**, nas médias que o script
      `build_painel_multiciclo.py` imprime (e devem ser excluídos do mesmo jeito em qualquer
      análise/regressão downstream — ver o campo `TEXTO_EXTRAIVEL`).
    - **Piso de palavras (robustez)**: distribuição real (N=779 propostas com texto): mínimo 6,
      p5=988, p10=1388, p25=2800, mediana=7150 palavras. Só 18 candidaturas (2,3%) têm menos de 500
      palavras — cauda natural de candidatura nanica/partido de aluguel (a maioria com índice=0,
      coerente com texto curto demais pra ter diagnóstico/meta/evidência). **Decisão: piso de
      robustez = 500 palavras**, usado só como checagem de sensibilidade (não para excluir do
      modelo principal, que usa a população completa por desenho — ver "Diferenças deliberadas",
      item 4). Testado nos 4 ciclos: índice médio com vs. sem piso varia **no máximo 0,13 ponto**
      (ex.: 2014 vai de 3,80 para 3,74 excluindo 10 casos; 2026 de 5,60 para 5,72 excluindo 4) —
      **resultado robusto ao piso**, pode reportar no artigo que a tendência central não depende
      dessa escolha.
    - **4 ciclos reprocessados e painel reconstruído** com motor final (Pilar B + Pilar C + OCR).
      Índices médios finais por ciclo (excluindo os 3 casos `TEXTO_EXTRAIVEL=False` de 2022; 2014 e
      2018 e 2026 não tiveram nenhum caso remanescente): **2014 = 3,8; 2018 = 3,7; 2022 = 5,1; 2026
      = 5,6**. A tendência de alta ao longo dos ciclos **sobrevive** a todas as correções (Pilar B,
      Pilar C, OCR), embora 2014→2018 agora apareça praticamente estável (3,8→3,7) em vez da leve
      alta vista nas versões provisórias anteriores — ajustar a frase do achado central no rascunho
      do artigo para refletir isso (quebra mais visível é 2018→2022, não um crescimento linear
      desde 2014).
    - **Todas as 3 correções metodológicas do item "próximos passos" (5, 6, e Pilar C) estão agora
      concluídas.** Dashboard republicado com os dados finais (mesmo link:
      `https://claude.ai/artifact/PnejBDSrzRLTS2kTtdNa4Z`, versão 2) — `programs/build_dashboard_data.py`
      é o script reprodutível que gera `data.json`/`aggregates.json` a partir do painel final (antes
      esse passo tinha sido feito à mão, sem script salvo). Falta: decidir com o usuário os próximos
      passos de ampliação da análise (regressão em painel com efeitos fixos, etc. — decisão conjunta,
      ainda não tomada).
