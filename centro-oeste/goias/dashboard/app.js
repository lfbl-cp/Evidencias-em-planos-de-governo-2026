(function () {
  "use strict";

  var DATA = JSON.parse(document.getElementById('data-bundle').textContent);

  var CAND_ORDER = ['daniel_vilela', 'marconi_perillo'];
  var CAND_COLOR_VAR = {
    'daniel_vilela': '--cand-1',
    'marconi_perillo': '--cand-2'
  };
  var THEME_ORDER = ['saude', 'seguranca', 'educacao', 'infraestrutura', 'meio_ambiente', 'economia', 'gestao_publica', 'assistencia_social', 'outros'];
  var THEME_COLOR_VAR = {
    saude: '--theme-saude',
    seguranca: '--theme-seguranca',
    educacao: '--theme-educacao',
    infraestrutura: '--theme-infra',
    meio_ambiente: '--theme-ambiente',
    economia: '--theme-economia',
    gestao_publica: '--theme-gestao',
    assistencia_social: '--theme-social',
    outros: '--theme-outros'
  };
  var THEME_LABEL = {
    saude: 'Saúde',
    seguranca: 'Segurança',
    educacao: 'Educação',
    infraestrutura: 'Infraestrutura',
    meio_ambiente: 'Meio Ambiente',
    economia: 'Economia e Trabalho',
    gestao_publica: 'Gestão Pública',
    assistencia_social: 'Assist. Social, DH, Cultura',
    outros: 'Outros (aberturas, encerramento)'
  };

  var candBySlug = {};
  DATA.candidatos.forEach(function (c) { candBySlug[c.slug] = c; });

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function fmtPct(v) { return (Math.round(v * 10) / 10).toFixed(1) + '%'; }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ---------- tiny markdown renderer ----------
  function inlineMd(s) {
    s = esc(s);
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    return s;
  }
  function mdToHtml(md) {
    var lines = md.split('\n');
    var html = '';
    var inList = false;
    var paraBuf = [];
    function flushPara() {
      if (paraBuf.length) {
        html += '<p>' + inlineMd(paraBuf.join(' ')) + '</p>';
        paraBuf = [];
      }
    }
    function closeList() {
      if (inList) { html += '</ul>'; inList = false; }
    }
    lines.forEach(function (raw) {
      var line = raw.trim();
      var m;
      if (line === '') { flushPara(); closeList(); return; }
      if (line === '---') { flushPara(); closeList(); html += '<hr>'; return; }
      if ((m = line.match(/^####\s+(.*)/))) { flushPara(); closeList(); html += '<h5>' + inlineMd(m[1]) + '</h5>'; return; }
      if ((m = line.match(/^###\s+(.*)/))) { flushPara(); closeList(); html += '<h4>' + inlineMd(m[1]) + '</h4>'; return; }
      if ((m = line.match(/^##\s+(.*)/))) { flushPara(); closeList(); html += '<h3>' + inlineMd(m[1]) + '</h3>'; return; }
      if ((m = line.match(/^#\s+(.*)/))) { flushPara(); closeList(); html += '<h3>' + inlineMd(m[1]) + '</h3>'; return; }
      // ALL-CAPS short line used as a section heading in the article outline
      if (/^[A-ZÀ-Ý0-9À-Ÿ ,.:\-–—'"]{6,}$/.test(line) && line === line.toUpperCase() && /[A-ZÀ-Ý]/.test(line) && line.split(' ').length <= 12) {
        flushPara(); closeList(); html += '<h4>' + inlineMd(line) + '</h4>'; return;
      }
      if ((m = line.match(/^-\s+(.*)/))) {
        flushPara();
        if (!inList) { html += '<ul>'; inList = true; }
        html += '<li>' + inlineMd(m[1]) + '</li>';
        return;
      }
      paraBuf.push(line);
    });
    flushPara();
    closeList();
    return html;
  }

  // ---------- tooltip ----------
  var tooltipEl = document.getElementById('tooltip');
  function attachTooltip(el, textFn) {
    el.addEventListener('mouseenter', function () {
      tooltipEl.textContent = typeof textFn === 'function' ? textFn() : textFn;
      tooltipEl.classList.add('show');
    });
    el.addEventListener('mousemove', function (e) {
      tooltipEl.style.left = e.clientX + 'px';
      tooltipEl.style.top = e.clientY + 'px';
    });
    el.addEventListener('mouseleave', function () {
      tooltipEl.classList.remove('show');
    });
  }

  // ---------- header meta ----------
  document.getElementById('meta-row').textContent =
    'Gerado em ' + DATA.gerado_em + '  ·  2 candidatos analisados, ambos com fonte 100% oficial (proposta de governo registrada no TSE)  ·  Goiás — projeto Centro-Oeste 2026';

  document.getElementById('callout-text-1').textContent =
    'Os dois textos foram extraídos diretamente dos PDFs oficiais de proposta de governo registrados no TSE. A distribuição temática (%) classifica o texto inteiro de cada plano, trecho a trecho, em vez de uma amostra — mas os planos têm tamanhos diferentes (~18,8 mil palavras no de Daniel Vilela contra ~24,1 mil no de Marconi Perillo), então trate os percentuais como indicativos de ênfase relativa dentro de cada plano, não como comparação de volume absoluto entre candidatos. O plano de Daniel Vilela é organizado em 6 Eixos Estratégicos subdivididos em Diretrizes; o de Marconi Perillo é organizado em 10 Áreas Temáticas numeradas com 55 compromissos — perfis de redação diferentes, o que também é relevante ao comparar os dois.';
  document.getElementById('callout-text-2').textContent =
    'O Índice de Base Empírica é uma heurística lexical assistida por leitura humana: conta um trecho como fundamentado quando traz dado de diagnóstico, efeito/resultado mensurável esperado ou referência a evidência/mecanismo causal externo, frente aos trechos que usam jargão de gestão genérico sem nenhuma dessas âncoras. Não avalia mérito, viabilidade orçamentária, nem a veracidade dos dados citados pelos candidatos. O PDF de origem do plano de Daniel Vilela apresenta um forte artefato de extração de colunas entrelaçadas ao longo de quase todo o documento, que pode adicionar pequeno ruído às fronteiras exatas dos segmentos temáticos (sem afetar a contagem total de palavras nem a detecção de frases para este índice); o plano de Marconi Perillo foi extraído em coluna única e ordem de leitura correta, sem esse artefato — ver nota de metodologia.';

  // ---------- KPI cards ----------
  (function renderKpis() {
    var grid = document.getElementById('kpi-grid');
    CAND_ORDER.forEach(function (slug) {
      var c = candBySlug[slug];
      if (!c) return;
      var color = cssVar(CAND_COLOR_VAR[slug]);
      var topTheme = null, topVal = -1;
      THEME_ORDER.forEach(function (t) {
        if (t === 'outros') return;
        var v = c.distribuicao_tematica_pct[t] || 0;
        if (v > topVal) { topVal = v; topTheme = t; }
      });
      var card = document.createElement('div');
      card.className = 'kpi-card';
      card.innerHTML =
        '<div><span class="swatch" style="background:' + color + '"></span>' +
        '<span class="name">' + esc(c.nome) + '</span><span class="party">' + esc(c.partido) + '</span></div>' +
        '<div class="value" style="color:' + color + '">' + fmtPct(c.indice_base_empirica_pct) + '</div>' +
        '<div class="label">Índice de base empírica</div>' +
        '<div class="topic">Tema mais destacado (relativo): <strong>' + THEME_LABEL[topTheme] + '</strong> (' + fmtPct(topVal) + ')</div>' +
        '<div class="topic">' + c.total_palavras.toLocaleString('pt-BR') + ' palavras · fonte: PDF oficial (TSE)</div>';
      grid.appendChild(card);
    });
  })();

  // ---------- word clouds ----------
  (function renderWordclouds() {
    var grid = document.getElementById('wc-grid');
    CAND_ORDER.forEach(function (slug) {
      var c = candBySlug[slug];
      if (!c) return;
      var color = cssVar(CAND_COLOR_VAR[slug]);
      var card = document.createElement('div');
      card.className = 'wc-card';
      card.innerHTML =
        '<div class="wc-head"><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:' + color + ';margin-right:6px;"></span>' +
        '<strong style="font-size:13.5px;">' + esc(c.nome) + '</strong><span style="color:var(--text-muted);font-size:12px;margin-left:4px;">' + esc(c.partido) + '</span></div>' +
        '<img src="data:image/png;base64,' + c.wordcloud_png_b64 + '" alt="Nuvem de palavras — ' + esc(c.nome) + '">' +
        '<div class="wc-foot">' + c.total_palavras.toLocaleString('pt-BR') + ' palavras analisadas (PDF oficial).</div>';
      grid.appendChild(card);
    });
  })();

  // ---------- frequency chart ----------
  (function renderFreq() {
    var tabsEl = document.getElementById('freq-tabs');
    var chartEl = document.getElementById('freq-chart');
    var tableEl = document.getElementById('freq-table');

    var tabs = [{ key: 'agregado', label: 'Agregado (2 planos)' }].concat(
      CAND_ORDER.map(function (slug) { return { key: slug, label: candBySlug[slug].nome }; })
    );

    function dataFor(key) {
      if (key === 'agregado') return (DATA.top_palavras_agregado || []).slice(0, 15);
      return (candBySlug[key].top_palavras || []).slice(0, 15);
    }
    function colorFor(key) {
      return key === 'agregado' ? cssVar('--accent-finding') : cssVar(CAND_COLOR_VAR[key]);
    }

    function draw(key) {
      var items = dataFor(key);
      var color = colorFor(key);
      var max = items.reduce(function (m, it) { return Math.max(m, it.freq); }, 1);
      var html = '';
      items.forEach(function (it) {
        var w = Math.round((it.freq / max) * 100);
        html += '<div class="bar-row">' +
          '<div class="label">' + esc(it.palavra) + '</div>' +
          '<div class="bar-track"><div class="bar-fill" data-tip="' + esc(it.palavra) + ': ' + it.freq + ' ocorrências" style="width:' + w + '%;background:' + color + '"></div></div>' +
          '<div class="val">' + it.freq + '</div>' +
          '</div>';
      });
      chartEl.innerHTML = html;
      Array.prototype.forEach.call(chartEl.querySelectorAll('.bar-fill'), function (el) {
        attachTooltip(el, el.getAttribute('data-tip'));
      });

      var tHtml = '<table class="data-table"><thead><tr><th>Palavra</th><th>Frequência</th></tr></thead><tbody>';
      items.forEach(function (it) { tHtml += '<tr><td>' + esc(it.palavra) + '</td><td>' + it.freq + '</td></tr>'; });
      tHtml += '</tbody></table>';
      tableEl.innerHTML = tHtml;
    }

    tabsEl.innerHTML = '';
    tabs.forEach(function (t, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tab-btn' + (i === 0 ? ' active' : '');
      btn.textContent = t.label;
      btn.addEventListener('click', function () {
        Array.prototype.forEach.call(tabsEl.children, function (b) { b.classList.remove('active'); b.style.background = ''; b.style.borderColor = ''; });
        btn.classList.add('active');
        var c = colorFor(t.key);
        btn.style.background = c; btn.style.borderColor = 'transparent';
        draw(t.key);
      });
      tabsEl.appendChild(btn);
    });
    tabsEl.children[0].style.background = colorFor('agregado');
    tabsEl.children[0].style.borderColor = 'transparent';
    draw('agregado');
  })();

  // ---------- thematic distribution (stacked bars) ----------
  (function renderTheme() {
    var legendEl = document.getElementById('theme-legend');
    var chartEl = document.getElementById('theme-chart');
    var tableEl = document.getElementById('theme-table');

    legendEl.innerHTML = THEME_ORDER.map(function (t) {
      return '<div class="legend-item"><span class="dot" style="background:' + cssVar(THEME_COLOR_VAR[t]) + '"></span>' + THEME_LABEL[t] + '</div>';
    }).join('');

    var html = '';
    CAND_ORDER.forEach(function (slug) {
      var c = candBySlug[slug];
      html += '<div class="stack-row">' +
        '<div class="label">' + esc(c.nome) + '<span class="party"> ' + esc(c.partido) + '</span></div>' +
        '<div class="stack-track" data-slug="' + slug + '">';
      THEME_ORDER.forEach(function (t) {
        var pct = c.distribuicao_tematica_pct[t] || 0;
        if (pct <= 0) return;
        var showLabel = pct >= 8;
        html += '<div class="stack-seg" data-tip="' + esc(THEME_LABEL[t]) + ': ' + fmtPct(pct) + ' — ' + esc(c.nome) + '" style="width:' + pct + '%;background:' + cssVar(THEME_COLOR_VAR[t]) + '">' +
          (showLabel ? '<span class="seg-label">' + fmtPct(pct) + '</span>' : '') +
          '</div>';
      });
      html += '</div></div>';
    });
    chartEl.innerHTML = html;
    Array.prototype.forEach.call(chartEl.querySelectorAll('.stack-seg'), function (el) {
      attachTooltip(el, el.getAttribute('data-tip'));
    });

    var tHtml = '<table class="data-table"><thead><tr><th>Candidato</th>' +
      THEME_ORDER.map(function (t) { return '<th>' + THEME_LABEL[t] + '</th>'; }).join('') + '</tr></thead><tbody>';
    CAND_ORDER.forEach(function (slug) {
      var c = candBySlug[slug];
      tHtml += '<tr><td>' + esc(c.nome) + '</td>' +
        THEME_ORDER.map(function (t) { return '<td>' + fmtPct(c.distribuicao_tematica_pct[t] || 0) + '</td>'; }).join('') + '</tr>';
    });
    tHtml += '</tbody></table>';
    tableEl.innerHTML = tHtml;
  })();

  // ---------- índice de base empírica ----------
  (function renderConcrecao() {
    var chartEl = document.getElementById('concrecao-chart');
    var tableEl = document.getElementById('concrecao-table');

    var rows = CAND_ORDER.map(function (slug) { return candBySlug[slug]; })
      .slice()
      .sort(function (a, b) { return b.indice_base_empirica_pct - a.indice_base_empirica_pct; });

    var html = '';
    rows.forEach(function (c) {
      var color = cssVar(CAND_COLOR_VAR[c.slug]);
      var pct = c.indice_base_empirica_pct;
      var barWidth = pct <= 0 ? 0 : Math.max(pct, 1.2); // largura mínima visível para valores muito baixos
      html += '<div class="bar-row" style="grid-template-columns:190px 1fr 74px;">' +
        '<div class="label"><span class="dot" style="background:' + color + '"></span>' + esc(c.nome) + ' <span style="color:var(--text-muted);font-weight:400;">' + esc(c.partido) + '</span></div>' +
        '<div class="bar-track"><div class="bar-fill" data-tip="' + esc(c.nome) + ': ' + fmtPct(pct) + '" style="width:' + barWidth + '%;min-width:' + (pct > 0 ? '3px' : '0') + ';background:' + color + '"></div></div>' +
        '<div class="val">' + fmtPct(pct) + '</div>' +
        '</div>';
    });
    chartEl.innerHTML = html;
    Array.prototype.forEach.call(chartEl.querySelectorAll('.bar-fill'), function (el) {
      attachTooltip(el, el.getAttribute('data-tip'));
    });

    var tHtml = '<table class="data-table"><thead><tr><th>Candidato</th><th>Partido</th><th>Índice de base empírica</th><th>Trechos fundamentados</th><th>(a) Dado diagnóstico</th><th>(b) Efeito mensurável</th><th>(c) Evidência/causal externa</th><th>Retórica sem evidência</th></tr></thead><tbody>';
    rows.forEach(function (c) {
      var d = c.indice_base_empirica_detalhe || {};
      tHtml += '<tr><td>' + esc(c.nome) + '</td><td>' + esc(c.partido) + '</td><td>' + fmtPct(c.indice_base_empirica_pct) + '</td>' +
        '<td>' + (d.n_trechos_com_base_empirica || 0) + '</td>' +
        '<td>' + (d.n_pilar_a_diagnostico || 0) + '</td>' +
        '<td>' + (d.n_pilar_b_efeito_mensuravel || 0) + '</td>' +
        '<td>' + (d.n_pilar_c_evidencia_causal_externa || 0) + '</td>' +
        '<td>' + (d.n_trechos_retorica_sem_evidencia || 0) + '</td></tr>';
    });
    tHtml += '</tbody></table>';
    tableEl.innerHTML = tHtml;
  })();

  // ---------- examples (base empírica vs retórica quotes) ----------
  (function renderExamples() {
    var tabsEl = document.getElementById('examples-tabs');
    var gridEl = document.getElementById('examples-grid');

    var PILAR_LABEL = {
      pilar_a_dado_diagnostico: '(a) Dado de diagnóstico',
      pilar_b_efeito_mensuravel: '(b) Efeito mensurável esperado',
      pilar_c_evidencia_ou_mecanismo_causal: '(c) Evidência / mecanismo causal externo'
    };

    function draw(slug) {
      var c = candBySlug[slug];
      var be = c.base_empirica_exemplos || {};
      var retorica = c.retorica_exemplos_sem_evidencia || [];
      var pilaresHtml = Object.keys(PILAR_LABEL).map(function (key) {
        var items = be[key] || [];
        if (!items.length) return '';
        return '<h4 style="margin-top:14px;">' + PILAR_LABEL[key] + '</h4>' +
          items.map(function (q) { return '<div class="quote concrete">' + esc(q) + '</div>'; }).join('');
      }).join('');
      var hasAnyEvidence = Object.keys(PILAR_LABEL).some(function (k) { return (be[k] || []).length; });
      gridEl.innerHTML =
        '<div><h4>Com base empírica</h4>' +
        (hasAnyEvidence ? pilaresHtml : '<div class="quote">Nenhum trecho com base empírica identificado neste plano.</div>') +
        '</div>' +
        '<div><h4>Retórica sem evidência</h4>' +
        retorica.map(function (q) { return '<div class="quote jargon">' + esc(q) + '</div>'; }).join('') +
        (retorica.length === 0 ? '<div class="quote">Nenhum exemplo identificado.</div>' : '') +
        '</div>';
    }

    tabsEl.innerHTML = '';
    CAND_ORDER.forEach(function (slug, i) {
      var c = candBySlug[slug];
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tab-btn' + (i === 0 ? ' active' : '');
      btn.textContent = c.nome;
      btn.addEventListener('click', function () {
        Array.prototype.forEach.call(tabsEl.children, function (b) { b.classList.remove('active'); b.style.background = ''; b.style.borderColor = ''; });
        btn.classList.add('active');
        btn.style.background = cssVar(CAND_COLOR_VAR[slug]); btn.style.borderColor = 'transparent';
        draw(slug);
      });
      tabsEl.appendChild(btn);
    });
    tabsEl.children[0].style.background = cssVar(CAND_COLOR_VAR[CAND_ORDER[0]]);
    tabsEl.children[0].style.borderColor = 'transparent';
    draw(CAND_ORDER[0]);
  })();

  // ---------- methodology ----------
  (function renderMetodologia() {
    var el = document.getElementById('metodologia-content');
    var html = '';
    html += '<h4>Nota geral</h4><p>' + inlineMd(DATA.metodologia_nota) + '</p>';
    html += '<h4>Frequência de palavras</h4><p>' + inlineMd(DATA.metodologia_frequencia_palavras) + '</p>';
    html += '<h4>Distribuição temática</h4><p>' + inlineMd(DATA.metodologia_distribuicao_tematica) + '</p>';
    html += '<h4>Índice de Base Empírica</h4><p>' + inlineMd(DATA.metodologia_indice_base_empirica) + '</p>';
    html += '<h4>Categoria de cada candidato</h4><p>' +
      DATA.candidatos.map(function (c) { return '<strong>' + esc(c.nome) + '</strong> (' + esc(c.partido) + '): ' + inlineMd(c.categoria); }).join('</p><p>') +
      '</p>';
    html += '<h4>Lista de jargão utilizada</h4><p>' + DATA.lista_jargao_utilizada.map(esc).join(', ') + '</p>';
    el.innerHTML = html;
  })();

  // ---------- theme toggle (light/dark) ----------
  (function () {
    var btns = document.querySelectorAll('[data-theme-btn]');
    document.documentElement.setAttribute('data-theme', 'light');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var mode = b.getAttribute('data-theme-btn');
        document.documentElement.setAttribute('data-theme', mode);
        btns.forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
      });
    });
  })();

  // ---------- PDF export ----------
  document.getElementById('export-pdf').addEventListener('click', function () {
    var el = document.getElementById('capture-root');
    var opt = {
      margin: [10, 10],
      filename: 'planos-de-governo-goias-2026.pdf',
      image: { type: 'jpeg', quality: 0.95 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: getComputedStyle(document.body).getPropertyValue('--page') || '#ffffff' },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'] }
    };
    if (window.html2pdf) {
      window.html2pdf().set(opt).from(el).save();
    } else {
      window.print();
    }
  });

})();
