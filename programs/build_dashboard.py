#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o dashboard.html de um estado embutindo o data_bundle (analise.json), o
app.js e o html2pdf vendorizado dentro do template.html. Driver genérico —
extraído em 28/08/2026 (reorganização v2) dos 23 `build_dashboard_<uf>.py`
originais, que eram idênticos entre si a menos dos caminhos (`DASH_DIR`/
`ANALISE_PATH`) e do texto do docstring. `template.html` e `app.js` continuam
por estado (`<estado>/dashboard/`): contêm prosa e cores específicas de cada
estado, não são mecânicos — só o empacotamento é.

Uso: python3 build_dashboard.py <estado_dir>
onde <estado_dir> contém dashboard/{template.html,app.js} e
analise/analise.json. O html2pdf vendorizado (idêntico em todos os 24 estados
com dashboard — verificado por hash) vem de programs/vendor/, não mais
duplicado por estado.
"""
import json
import sys
from pathlib import Path

PROGRAMS_DIR = Path(__file__).resolve().parent
VENDOR_HTML2PDF = PROGRAMS_DIR / "vendor" / "vendor_html2pdf.bundle.min.js"


def build_dashboard(estado_dir: Path):
    dash_dir = estado_dir / "dashboard"
    analise_path = estado_dir / "analise" / "analise.json"

    template = (dash_dir / "template.html").read_text(encoding="utf-8")
    app_js = (dash_dir / "app.js").read_text(encoding="utf-8")
    html2pdf_js = VENDOR_HTML2PDF.read_text(encoding="utf-8")
    analise = json.loads(analise_path.read_text(encoding="utf-8"))

    data_bundle_json = json.dumps(analise, ensure_ascii=False).replace("</script", "<\\/script")
    app_js_safe = app_js.replace("</script", "<\\/script")
    html2pdf_js_safe = html2pdf_js.replace("</script", "<\\/script")

    out = template.replace("__DATA_BUNDLE_JSON__", data_bundle_json)
    out = out.replace("__APP_JS__", app_js_safe)
    out = out.replace("__HTML2PDF_JS__", html2pdf_js_safe)

    out_path = dash_dir / "dashboard.html"
    out_path.write_text(out, encoding="utf-8")
    print(f"Salvo em {out_path}  ({len(out):,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 build_dashboard.py <estado_dir>")
        sys.exit(1)
    build_dashboard(Path(sys.argv[1]).resolve())
