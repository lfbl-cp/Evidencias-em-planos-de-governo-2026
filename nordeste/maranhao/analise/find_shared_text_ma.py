#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

PLANOS_DIR = Path("/home/claude/brasil_2026/nordeste/maranhao/planos")
OUT_DIR = Path("/home/claude/brasil_2026/nordeste/maranhao/analise")

WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9][a-zA-ZÀ-ÖØ-öø-ÿ0-9\-]*")

def strip_header(text):
    marker = "\n---\n"
    idx = text.find(marker)
    return text[idx+len(marker):] if idx != -1 else text

def load(slug):
    raw = (PLANOS_DIR / f"{slug}.txt").read_text(encoding="utf-8")
    return strip_header(raw)

def tokenize_with_pos(text):
    return [(m.group(0).lower(), m.start(), m.end()) for m in WORD_RE.finditer(text)]

N = 8
MIN_CHARS = 150

def find_shared_blocks(text_a, text_b, n=N, min_chars=MIN_CHARS):
    toks_a = tokenize_with_pos(text_a)
    toks_b = tokenize_with_pos(text_b)
    words_a = [t[0] for t in toks_a]
    words_b = [t[0] for t in toks_b]

    index_a = {}
    for i in range(len(words_a) - n + 1):
        gram = tuple(words_a[i:i+n])
        index_a.setdefault(gram, []).append(i)

    matches = []
    i = 0
    while i <= len(words_b) - n:
        gram = tuple(words_b[i:i+n])
        candidates = index_a.get(gram)
        if candidates:
            best_len = 0
            best_a = None
            for a_start in candidates:
                length = 0
                while (a_start + length < len(words_a) and i + length < len(words_b)
                       and words_a[a_start+length] == words_b[i+length]):
                    length += 1
                if length > best_len:
                    best_len = length
                    best_a = a_start
            matches.append((best_a, i, best_len))
            i += best_len
        else:
            i += 1

    blocks = []
    for a_start, b_start, length in matches:
        if length < n:
            continue
        a_char_start = toks_a[a_start][1]
        a_char_end = toks_a[a_start + length - 1][2]
        b_char_start = toks_b[b_start][1]
        b_char_end = toks_b[b_start + length - 1][2]
        size = a_char_end - a_char_start
        if size >= min_chars:
            blocks.append({
                "a_char_start": a_char_start, "a_char_end": a_char_end,
                "b_char_start": b_char_start, "b_char_end": b_char_end,
                "size_a": size, "size_b": b_char_end - b_char_start,
            })
    return blocks

def merge_close_blocks(blocks, gap_tolerance=5):
    if not blocks:
        return blocks
    blocks = sorted(blocks, key=lambda x: x["a_char_start"])
    merged = [blocks[0]]
    for b in blocks[1:]:
        last = merged[-1]
        if (b["a_char_start"] - last["a_char_end"] <= gap_tolerance and
                b["b_char_start"] - last["b_char_end"] <= gap_tolerance and
                b["b_char_start"] >= last["b_char_end"] - gap_tolerance):
            last["a_char_end"] = max(last["a_char_end"], b["a_char_end"])
            last["b_char_end"] = max(last["b_char_end"], b["b_char_end"])
            last["size_a"] = last["a_char_end"] - last["a_char_start"]
            last["size_b"] = last["b_char_end"] - last["b_char_start"]
        else:
            merged.append(b)
    return merged

SLUGS = ["orleans-brandao", "eduardo-braide", "felipe-camarao"]
texts = {s: load(s) for s in SLUGS}
total_words = {s: len(tokenize_with_pos(texts[s])) for s in SLUGS}

pairs = [
    ("orleans-brandao", "eduardo-braide"),
    ("orleans-brandao", "felipe-camarao"),
    ("eduardo-braide", "felipe-camarao"),
]

report = {}
for s1, s2 in pairs:
    a, b = texts[s1], texts[s2]
    blocks = find_shared_blocks(a, b, n=N, min_chars=MIN_CHARS)
    blocks = merge_close_blocks(blocks, gap_tolerance=3)
    blocks = [x for x in blocks if x["size_a"] >= MIN_CHARS]
    blocks.sort(key=lambda x: -x["size_a"])
    total_shared_a = sum(x["size_a"] for x in blocks)
    total_shared_b = sum(x["size_b"] for x in blocks)
    print(f"\n=== {s1} x {s2} ===")
    print(f"len_chars({s1})={len(a)}  len_chars({s2})={len(b)}")
    print(f"num blocks: {len(blocks)}  total shared chars (side {s1}): {total_shared_a}  (side {s2}): {total_shared_b}")
    for x in blocks[:10]:
        snippet_a = a[x["a_char_start"]:x["a_char_start"]+150].replace("\n", " ")
        print(f"  size_a={x['size_a']:5d} size_b={x['size_b']:5d}  a@{x['a_char_start']:6d}-{x['a_char_end']:6d}  b@{x['b_char_start']:6d}-{x['b_char_end']:6d}")
        print(f"    snippet: {snippet_a!r}")
    report[f"{s1}_x_{s2}"] = {
        "blocks": blocks, "total_shared_a": total_shared_a, "total_shared_b": total_shared_b,
        "len_a": len(a), "len_b": len(b),
    }

Path(OUT_DIR / "texto_compartilhado_raw.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("\ntotal_words:", total_words)
