#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o dashboard.html final de Minas Gerais embutindo o data_bundle
(analise.json), o app.js e o html2pdf vendorizado, dentro do template.html —
mesmo processo usado nos demais estados do projeto (ver
/home/claude/brasil_2026/centro-oeste/mato-grosso-do-sul/dashboard/build_dashboard_ms.py).
"""
import json
from pathlib import Path

DASH_DIR = Path("/home/claude/brasil_2026/sudeste/minas-gerais/dashboard")
ANALISE_PATH = Path("/home/claude/brasil_2026/sudeste/minas-gerais/analise/analise.json")

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
