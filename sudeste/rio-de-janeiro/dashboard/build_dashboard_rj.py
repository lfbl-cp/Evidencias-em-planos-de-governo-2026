#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o dashboard.html final do Rio de Janeiro embutindo o data_bundle
(analise.json), o app.js e o html2pdf vendorizado, dentro do template.html —
mesmo processo usado nos 9 estados do Nordeste, no Tocantins e em Mato
Grosso do Sul (ver
/home/claude/brasil_2026/centro-oeste/mato-grosso-do-sul/dashboard/build_dashboard_ms.py).

Caso especial do RJ: esta rodada tem apenas 1 candidato (Douglas Ruas) — o
template.html e o app.js já foram adaptados para esse layout de candidato
único; este script apenas monta o pacote final, sem lógica adicional.
"""
import json
from pathlib import Path

DASH_DIR = Path("/home/claude/brasil_2026/sudeste/rio-de-janeiro/dashboard")
ANALISE_PATH = Path("/home/claude/brasil_2026/sudeste/rio-de-janeiro/analise/analise.json")

template = (DASH_DIR / "template.html").read_text(encoding="utf-8")
app_js = (DASH_DIR / "app.js").read_text(encoding="utf-8")
html2pdf_js = (DASH_DIR / "vendor_html2pdf.bundle.min.js").read_text(encoding="utf-8")
analise = json.loads(ANALISE_PATH.read_text(encoding="utf-8"))

data_bundle_json = json.dumps(analise, ensure_ascii=False).replace("</script", "<\\/script")
app_js_safe = app_js.replace("</script", "<\\/script")
html2pdf_js_safe = html2pdf_js.replace("</script", "<\\/script")

out = template.replace("__DATA_BUNDLE_JSON__", data_bundle_json)
out = out.replace("__APP_JS__", app_js_safe)
out = out.replace("__HTML2PDF_JS__", html2pdf_js_safe)

out_path = DASH_DIR / "dashboard.html"
out_path.write_text(out, encoding="utf-8")
print(f"Salvo em {out_path}  ({len(out):,} bytes)")
