import json
from pathlib import Path

DASH_DIR = Path("/home/claude/brasil_2026/nordeste/piaui/dashboard")
ANALISE_DIR = Path("/home/claude/brasil_2026/nordeste/piaui/analise")

template = (DASH_DIR / "template.html").read_text(encoding="utf-8")
app_js = (DASH_DIR / "app.js").read_text(encoding="utf-8")
html2pdf_js = (DASH_DIR / "vendor_html2pdf.bundle.min.js").read_text(encoding="utf-8")
analise = json.loads((ANALISE_DIR / "analise.json").read_text(encoding="utf-8"))

data_bundle_json = json.dumps(analise, ensure_ascii=False)

def esc_script_close(s):
    return s.replace("</script", "<\\/script")

out = template
out = out.replace("__HTML2PDF_JS__", lambda_safe := esc_script_close(html2pdf_js))
out = out.replace("__DATA_BUNDLE_JSON__", esc_script_close(data_bundle_json))
out = out.replace("__APP_JS__", esc_script_close(app_js))

out_path = DASH_DIR / "dashboard.html"
out_path.write_text(out, encoding="utf-8")
print("Salvo em", out_path, "tamanho:", len(out), "bytes")
