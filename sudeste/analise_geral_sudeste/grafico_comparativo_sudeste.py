import json
from statistics import mean, median, pstdev

regs = json.load(open("/home/claude/brasil_2026/sudeste/analise_geral_sudeste/dados_consolidados_sudeste.json"))
for r in regs:
    r["uf"] = r["estado"]
    r["per_mil_total"] = r["per_mil_jargao"]

def grupo(r):
    c = r["categoria"]
    if c in ("candidato de continuidade", "incumbente por sucessão"):
        return "continuidade"
    if c == "incumbente pleno":
        return "incumbente"
    return "desafiante"

for r in regs:
    r["grupo"] = grupo(r)

COLOR = {
    "desafiante": "var(--series-1)",
    "incumbente": "var(--series-2)",
    "continuidade": "var(--series-3)",
}

bar_h = 22
gap = 8
row_h = bar_h + gap
top_pad = 46
bottom_pad = 40
left_pad = 300
right_pad = 60
chart_w = 560

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def build_chart(regs_sorted, value_key, max_val, gridvals, fmt, tip_fn, aria_label):
    svg_h = top_pad + len(regs_sorted) * row_h + bottom_pad
    svg_w = left_pad + chart_w + right_pad

    def x(v):
        return left_pad + (v / max_val) * chart_w

    rows = []
    for i, r in enumerate(regs_sorted):
        y = top_pad + i * row_h
        w = x(r[value_key]) - left_pad
        color_var = COLOR[r["grupo"]]
        name_lbl = f"{r['nome']} ({r['uf']})"
        party_lbl = r["partido"]
        val_txt = fmt(r[value_key])
        tip = tip_fn(r, val_txt)
        rows.append(f'''
    <g class="bar-row" data-tip="{esc(tip)}">
      <text x="{left_pad - 12}" y="{y + bar_h/2 + 1}" text-anchor="end" class="row-label">{esc(name_lbl)}</text>
      <text x="{left_pad - 12}" y="{y + bar_h/2 + 13}" text-anchor="end" class="row-party">{esc(party_lbl)}</text>
      <rect x="{left_pad}" y="{y}" width="{max(w,2):.1f}" height="{bar_h}" rx="4" fill="{color_var}"/>
      <text x="{x(r[value_key]) + 8:.1f}" y="{y + bar_h/2 + 4}" class="val-label">{val_txt}</text>
    </g>''')

    gridlines = []
    for gv in gridvals:
        gx = x(gv)
        gridlines.append(f'<line x1="{gx:.1f}" y1="{top_pad-10}" x2="{gx:.1f}" y2="{svg_h - bottom_pad + 6}" class="gridline"/>')
        gridlines.append(f'<text x="{gx:.1f}" y="{svg_h - bottom_pad + 24}" text-anchor="middle" class="axis-label">{fmt(gv)}</text>')

    svg = f'''<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" role="img" aria-label="{esc(aria_label)}">
  {''.join(gridlines)}
  <line x1="{left_pad}" y1="{top_pad-10}" x2="{left_pad}" y2="{svg_h - bottom_pad + 6}" class="axis-line"/>
  {''.join(rows)}
</svg>'''
    return svg


def stats_table(regs_group_source, value_key, fmt, total_label):
    groups = {}
    for r in regs_group_source:
        groups.setdefault(r["categoria"], []).append(r)

    def stats_row(nome, items):
        vals = [i[value_key] for i in items]
        n = len(vals)
        mu = mean(vals)
        dp = pstdev(vals) if n > 1 else None
        md = median(vals)
        dp_txt = f"{dp:.2f}" if dp is not None else "—"
        return f'''<tr>
      <td>{esc(nome)}</td>
      <td class="num">{n}</td>
      <td class="num">{fmt(mu)}</td>
      <td class="num">{dp_txt}</td>
      <td class="num">{fmt(md)}</td>
      <td class="num">{fmt(min(vals))}</td>
      <td class="num">{fmt(max(vals))}</td>
    </tr>'''

    order = ["desafiante", "candidato de continuidade", "incumbente por sucessão", "incumbente pleno"]
    stats_rows = "".join(stats_row(cat, groups[cat]) for cat in order if cat in groups)
    stats_rows_total = stats_row(total_label, regs_group_source)
    return f'''<table class="stats">
    <thead>
      <tr>
        <th>Categoria</th>
        <th class="num">n</th>
        <th class="num">Média</th>
        <th class="num">Desvio padrão</th>
        <th class="num">Mediana</th>
        <th class="num">Mín.</th>
        <th class="num">Máx.</th>
      </tr>
    </thead>
    <tbody>
      {stats_rows}
      <tr class="total">{stats_rows_total[4:]}
    </tbody>
  </table>'''


# ---------------------------------------------------------------------------
# Chart 1 — Índice de Base Empírica
# ---------------------------------------------------------------------------
regs_indice = sorted(regs, key=lambda r: -r["indice_base_empirica_pct"])

def fmt_pct(v):
    return f"{v:.1f}%".replace(".", ",")

def tip_indice(r, val_txt):
    return f"{r['nome']} ({r['uf']}) — {r['partido']} — {r['categoria']} — {val_txt} — {r['total_palavras']:,} palavras".replace(",", ".")

svg_indice = build_chart(
    regs_indice, "indice_base_empirica_pct", 6, [0, 2, 4, 6], fmt_pct, tip_indice,
    "Índice de Base Empírica por candidato, com partido, Sudeste 2026",
)
stats_indice = stats_table(regs, "indice_base_empirica_pct", fmt_pct, "Total (7 candidatos)")

# ---------------------------------------------------------------------------
# Chart 2 — Densidade de jargão "fortalecer" / "ampliar"
# ---------------------------------------------------------------------------
regs_jargao = sorted(regs, key=lambda r: -r["per_mil_total"])

def fmt_mil(v):
    return f"{v:.1f}".replace(".", ",")

def tip_jargao(r, val_txt):
    return (f"{r['nome']} ({r['uf']}) — {r['partido']} — {r['categoria']} — "
            f"{val_txt} ocorrências/mil palavras "
            f"('fortalec*': {r['n_fortalec']}, 'ampli*': {r['n_ampli']}) — "
            f"Índice de Base Empírica: {r['indice_base_empirica_pct']}%")

svg_jargao = build_chart(
    regs_jargao, "per_mil_total", 16, [0, 4, 8, 12, 16], fmt_mil, tip_jargao,
    "Densidade de jargão fortalecer/ampliar por candidato, Sudeste 2026",
)
stats_jargao = stats_table(regs, "per_mil_total", fmt_mil, "Total (7 candidatos)")

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Índice de Base Empírica e densidade de jargão — governos estaduais do Sudeste 2026</title>
<style>
  .viz-root {{
    color-scheme: light;
    --surface-1: #fcfcfb;
    --surface-2: #f3f2ee;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #86847c;
    --border: #e4e2da;
    --gridline: #eceae2;
    --series-1: #2a78d6;
    --series-2: #eb6834;
    --series-3: #1baf7a;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) .viz-root {{
      color-scheme: dark;
      --surface-1: #1a1a19;
      --surface-2: #232320;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #8b897f;
      --border: #33322d;
      --gridline: #2a2a26;
      --series-1: #3987e5;
      --series-2: #d95926;
      --series-3: #199e70;
    }}
  }}
  :root[data-theme="dark"] .viz-root {{
    color-scheme: dark;
    --surface-1: #1a1a19;
    --surface-2: #232320;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #8b897f;
    --border: #33322d;
    --gridline: #2a2a26;
    --series-1: #3987e5;
    --series-2: #d95926;
    --series-3: #199e70;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--surface-1); color: var(--text-primary); }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 28px 24px 48px; }}
  h1 {{ font-size: 19px; margin: 0 0 6px; }}
  p.intro {{ font-size: 13px; color: var(--text-secondary); margin: 0 0 28px; line-height: 1.5; }}
  h2 {{ font-size: 16px; margin: 0 0 6px; }}
  h3 {{ font-size: 14px; margin: 30px 0 10px; }}
  p.sub {{ font-size: 13px; color: var(--text-secondary); margin: 0 0 18px; line-height: 1.5; }}
  section.block {{ margin-bottom: 48px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
  section.block:last-of-type {{ border-bottom: none; }}
  .legend {{ display: flex; gap: 18px; margin-bottom: 12px; font-size: 12.5px; color: var(--text-secondary); flex-wrap: wrap; }}
  .legend .item {{ display: flex; align-items: center; gap: 6px; }}
  .legend .dot {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
  .chart-card {{ background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; overflow-x: auto; }}
  .row-label {{ font-size: 11.5px; fill: var(--text-secondary); }}
  .row-party {{ font-size: 10px; fill: var(--text-muted); }}
  .val-label {{ font-size: 11.5px; fill: var(--text-primary); font-variant-numeric: tabular-nums; }}
  .axis-label {{ font-size: 11px; fill: var(--text-muted); }}
  .gridline {{ stroke: var(--gridline); stroke-width: 1; }}
  .axis-line {{ stroke: var(--border); stroke-width: 1; }}
  .bar-row rect {{ transition: opacity .1s ease; }}
  .bar-row:hover rect {{ opacity: 0.75; }}
  .tooltip {{ position: fixed; pointer-events: none; background: var(--text-primary); color: var(--surface-1); font-size: 12px; padding: 6px 9px; border-radius: 6px; max-width: 300px; line-height: 1.4; opacity: 0; transition: opacity .1s ease; z-index: 10; }}
  .tooltip.show {{ opacity: 1; }}
  .foot {{ font-size: 11.5px; color: var(--text-muted); margin-top: 14px; line-height: 1.5; }}
  table.stats {{ width: 100%; border-collapse: collapse; font-size: 12.5px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-top: 4px; }}
  table.stats th, table.stats td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--border); }}
  table.stats th {{ color: var(--text-muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }}
  table.stats td.num, table.stats th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.stats tr:last-child td {{ border-bottom: none; }}
  table.stats tr.total td {{ font-weight: 600; border-top: 2px solid var(--border); }}
  .callout {{ background: rgba(235,104,52,0.08); border: 1px solid rgba(235,104,52,0.35); border-radius: 10px; padding: 12px 16px; font-size: 12.5px; color: var(--text-secondary); margin: 0 0 22px; line-height: 1.5; }}
</style>
</head>
<body class="viz-root">
<div class="wrap">
  <h1>Governos estaduais do Sudeste 2026 — planos de governo em números</h1>
  <p class="intro">7 planos de governo analisados em 4 estados (SP, RJ, MG, ES). Metodologia idêntica à usada nas rodadas do Nordeste, Norte e Centro-Oeste. Amostra pequena por estado — leia as estatísticas por categoria com cautela, especialmente onde n=1.</p>
  <p class="callout"><strong>Nota sobre o Rio de Janeiro:</strong> esta rodada cobre só 1 candidato no RJ (Douglas Ruas, PL) em vez de 2. Os 2 candidatos mais competitivos nas pesquisas são Eduardo Paes (PSD, líder disparado com 41%) e Anthony Garotinho (Republicanos, 9%) — mas nenhum dos dois havia registrado proposta de governo no TSE até a data de coleta (24/08/2026). O painel será atualizado assim que isso acontecer.</p>

  <div class="legend">
    <span class="item"><span class="dot" style="background:var(--series-1)"></span>Desafiante</span>
    <span class="item"><span class="dot" style="background:var(--series-2)"></span>Incumbente (pleno)</span>
    <span class="item"><span class="dot" style="background:var(--series-3)"></span>Continuidade / sucessão</span>
  </div>

  <section class="block">
    <h2>Índice de Base Empírica por candidato</h2>
    <p class="sub">Proporção de trechos com diagnóstico/efeito mensurável/evidência externa sobre o total de trechos com base empírica + retórica de gestão pública sem evidência.</p>
    <div class="chart-card">
      {svg_indice}
    </div>
    <p class="foot">Fonte: análise dos PDFs oficiais de campanha (proposta de governo registrada no TSE) de cada candidato.</p>

    <h3>Estatísticas descritivas por categoria</h3>
    {stats_indice}
    <p class="foot">Desvio padrão populacional (n no denominador). Amostra do Sudeste é pequena e desbalanceada nesta rodada (RJ com 1 candidato só): "incumbente pleno" e "incumbente por sucessão" têm n=1 cada — desvio padrão não é calculável nesses grupos. Trate estes números como descritivos desta amostra específica, não como estimativas robustas de um padrão nacional.</p>
  </section>

  <section class="block">
    <h2>Densidade de jargão ("fortalec*" + "ampli*") por candidato</h2>
    <p class="sub">Ocorrências das famílias de palavras "fortalec-" (fortalecer, fortalecimento...) e "ampli-" (ampliar, ampliação, amplo...) por mil palavras do corpo do plano. Essas duas famílias fazem parte da lista de termos de retórica de gestão pública genérica usada no cálculo do Índice de Base Empírica.</p>
    <div class="chart-card">
      {svg_jargao}
    </div>
    <p class="foot">Eixo: ocorrências por 1.000 palavras do corpo do plano (após o cabeçalho padronizado). Fonte: contagem direta nos textos extraídos dos PDFs oficiais.</p>

    <h3>Estatísticas descritivas por categoria</h3>
    {stats_jargao}
    <p class="foot">Valores em ocorrências por 1.000 palavras. Desvio padrão populacional.</p>
  </section>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
  var tooltip = document.getElementById('tooltip');
  document.querySelectorAll('.bar-row').forEach(function (el) {{
    el.addEventListener('mousemove', function (e) {{
      tooltip.textContent = el.getAttribute('data-tip');
      tooltip.style.left = (e.clientX + 14) + 'px';
      tooltip.style.top = (e.clientY + 14) + 'px';
      tooltip.classList.add('show');
    }});
    el.addEventListener('mouseleave', function () {{
      tooltip.classList.remove('show');
    }});
  }});
</script>
</body>
</html>'''

open("/home/claude/brasil_2026/sudeste/analise_geral_sudeste/grafico_comparativo_sudeste.html", "w", encoding="utf-8").write(html)
print("merged chart written")
