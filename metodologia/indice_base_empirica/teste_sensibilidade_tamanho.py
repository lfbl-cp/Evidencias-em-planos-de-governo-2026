import json, glob, random, importlib.util, statistics
from pathlib import Path
from collections import defaultdict

random.seed(42)

# --- carrega frases ja segmentadas (segmentacao nao mudou na correcao Fase 3) ---
by_slug = defaultdict(list)
with open("/home/claude/brasil_2026/metodologia/indice_base_empirica/frases_classificadas.jsonl", encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        by_slug[d["slug"]].append(d["frase"])

nat = json.load(open("/home/claude/brasil_2026/nacional/dados_nacionais.json", encoding="utf-8"))
nat_by_slug = {r["slug"]: r for r in nat}

FILES = sorted(glob.glob("/home/claude/brasil_2026/*/*/analise/build_analysis_*.py")) + \
    ["/home/claude/pb2026_v2/analise/build_analysis_v3.py"]
FILES = [f for f in FILES if "/replicacao/" not in f]

def load_module(path):
    spec = importlib.util.spec_from_file_location(f"mod_{Path(path).stem}_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# mapeia slug -> modulo (para reclassificar com a regex CORRIGIDA atual)
slug_to_mod = {}
for f in FILES:
    try:
        mod = load_module(f)
    except Exception as e:
        print("erro import", f, e)
        continue
    for c in getattr(mod, "CANDIDATOS", []):
        slug_to_mod[c.get("slug")] = mod

def reclassifica(slug):
    """Reclassifica as frases de um candidato com a logica CORRIGIDA atual (pos-Fase 3)."""
    mod = slug_to_mod.get(slug)
    if mod is None:
        return None
    frases = by_slug.get(slug)
    if not frases:
        return None
    out = []
    for s in frases:
        s_low = s.lower()
        pa = bool(mod.is_diagnostico(s_low))
        pb = bool(mod.is_efeito(s_low))
        try:
            pc = bool(mod.is_evidencia(s.strip(), s_low))   # assinatura corrigida (2 args)
        except TypeError:
            pc = bool(mod.is_evidencia(s_low))               # fallback (piloto PB, se ainda 1 arg)
        com_base = pa or pb or pc
        compromisso = False
        if not com_base:
            try:
                compromisso = bool(mod.PROPOSAL_RE.search(s))
            except AttributeError:
                compromisso = False
        out.append({"com_base": com_base, "compromisso": compromisso})
    return out

def indice_cobertura(labels):
    n_base = sum(1 for l in labels if l["com_base"])
    n_comp = sum(1 for l in labels if l["compromisso"])
    denom = n_base + n_comp
    return (n_base / denom * 100) if denom else None, n_base, n_comp, len(labels)

# --- candidatos-alvo: espectro de tamanho ---
ALVOS = ["omar-aziz", "acm-neto", "felipe-camarao", "marcos-rogerio", "joao-rodrigues", "renan-filho"]
# normaliza slugs conhecidos (checagem)
for a in ALVOS:
    if a not in by_slug:
        # tenta achar variantes
        cands = [s for s in by_slug if a.split("-")[0] in s]
        print(f"aviso: slug '{a}' nao encontrado direto, candidatos parecidos: {cands[:5]}")

print("="*100)
print("TESTE A -- convergencia por subamostragem aleatoria (precisao vs vies)")
print("="*100)
FRACOES = [0.05, 0.10, 0.25, 0.50, 0.75, 1.0]
B = 300
resultados_A = {}
for slug in ALVOS:
    labels = reclassifica(slug)
    if not labels:
        continue
    n_total = len(labels)
    idx_full, nb, nc, nt = indice_cobertura(labels)
    nome = nat_by_slug.get(slug, {}).get("nome", slug)
    palavras = nat_by_slug.get(slug, {}).get("total_palavras", "?")
    print(f"\n{nome} ({palavras} palavras, {n_total} frases) -- indice full (reclassificado)={idx_full:.2f}%  [publicado={nat_by_slug.get(slug,{}).get('indice_base_empirica_pct')}]")
    row = {}
    for frac in FRACOES:
        k = max(5, int(n_total * frac))
        if frac == 1.0:
            vals = [idx_full]
        else:
            vals = []
            for _ in range(B):
                sample = random.sample(labels, k)
                v, _, _, _ = indice_cobertura(sample)
                if v is not None:
                    vals.append(v)
        mean = statistics.mean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        row[frac] = (mean, sd)
        print(f"  frac={frac:.2f} (n~{k:6d})  media={mean:6.2f}%  desvio={sd:5.2f}  [{mean-1.96*sd:6.2f}, {mean+1.96*sd:6.2f}]")
    resultados_A[slug] = row

print("\n" + "="*100)
print("TESTE B -- perfil posicional (indice por decil do documento, ordem original)")
print("="*100)
for slug in ALVOS:
    labels = reclassifica(slug)
    if not labels:
        continue
    n_total = len(labels)
    nome = nat_by_slug.get(slug, {}).get("nome", slug)
    deciles = []
    for i in range(10):
        lo = int(n_total * i / 10)
        hi = int(n_total * (i+1) / 10)
        chunk = labels[lo:hi]
        v, nb, nc, nt = indice_cobertura(chunk)
        deciles.append(v)
    dstr = "  ".join(f"{v:5.1f}" if v is not None else "   NA" for v in deciles)
    print(f"{nome:20s} decis 1-10: {dstr}")
