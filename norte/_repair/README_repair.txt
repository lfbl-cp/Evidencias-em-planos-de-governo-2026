"""
Repara o defeito de extração de PDF em que as ligaduras tipográficas 'fi' e 'fl'
foram substituídas por um único espaço em branco no texto extraído (mesmo defeito
confirmado tanto via pdftotext quanto via PyMuPDF -- portanto está no PDF fonte,
não na ferramenta de extração). Ex.: "profissionais" -> "pro ssionais",
"eficiência" -> "e ciência", "confiança" -> "con ança", "fluxos" -> " uxos".

Abordagem: lista curada de substituições regex, construída a partir da análise de
frequência dos pares "palavra espaço palavra" no texto de cada candidato afetado
(caso mais severo: Mailza Assis, AC, 166 ocorrências). Cada regra corrige um
radical+sufixo específico e documentado, evitando "consertar" espaços legítimos
(ex.: "e a", "de vida", que são combinações reais de palavras, não foram tocadas).
"""
import re

_RULES = [
    # (regex, replacement)  -- 'fi' inserida
    (r'\b([Cc])on (ança\w*|ável\w*|aram\w*|amos\w*|ei\b|a\b|ar\b)\b', r'\1onfi\2'),
    (r'\b([Pp])ro (ssion\w*)\b', r'\1rofi\2'),
    (r'\b([Qq])uali (c\w*)\b', r'\1ualifi\2'),
    (r'\b([Rr])equali (c\w*)\b', r'\1equalifi\2'),
    (r'\b([Mm])ultipro (ssion\w*)\b', r'\1ultiprofi\2'),
    (r'\b([Dd])iversi (c\w*)\b', r'\1iversifi\2'),
    (r'\b([Dd])esa (fios?|os?)\b', r'\1esafi\2'),
    (r'\b([Ss])igni (c\w*|que\w*|cado\w*)\b', r'\1ignifi\2'),
    (r'\b([Ee])speci (cidades?\w*|c\w*)\b', r'\1specifi\2'),
    (r'\b([Bb])ene (ci\w*)\b', r'\1enefi\2'),
    (r'\b([Vv])eri (c\w*)\b', r'\1erifi\2'),
    (r'\b([Jj])usti (c\w*)\b', r'\1ustifi\2'),
    (r'\b([Dd])e (ne\w*|ni[çc]\w*|nid\w*|nir\w*)\b', r'\1efi\2'),
    (r'\b([Dd])e (ciência\w*)\b', r'\1efi\2'),  # "de ciência" (sem acento) = "deficiência"; "da/à/a ciência" (= "science") não é tocado
    (r'\b([Ii])denti (c\w*)\b', r'\1dentifi\2'),
    (r'\b([Cc])erti (c\w*)\b', r'\1ertifi\2'),
    (r'\b([Ss])impli (c\w*)\b', r'\1implifi\2'),
    (r'\b([Ee]) (ciência\w*|ciente\w*|cácia\w*|caz\w*)\b', r'\1fi\2'),
    (r'\bAo (nal\w*)\b', r'Ao fi\1'),
    (r'\bao (nal\w*)\b', r'ao fi\1'),
    # 'fl' inserida
    (r'\b([Cc])on (itos?\w*)\b', r'\1onfl\2'),
    (r'\b([Rr])e (etem\w*|ete\w*|exã?o\w*|exiv\w*)\b', r'\1efl\2'),
    (r'\b(uxos?)\b', r'fl\1'),
]

def reparar(texto):
    for pat, repl in _RULES:
        texto = re.sub(pat, repl, texto)
    return texto

if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    with open(path, encoding='utf-8') as f:
        original = f.read()
    reparado = reparar(original)
    n_changes = sum(1 for a, b in zip(original, reparado) if a != b)
    print(f"{path}: {len(original)-len(reparado)} caracteres removidos (repair aplicado)")
    if len(sys.argv) > 2 and sys.argv[2] == '--write':
        with open(path, 'w', encoding='utf-8') as f:
            f.write(reparado)
        print("  escrito.")
CORRIGIDO em auditoria pós-Norte (25/08/2026): a afirmação original abaixo
era FALSA e o script acima está desatualizado (ver reparar_ligadura_fi.py,
o arquivo real usado, para a versão corrigida com as notas completas).

"Repair already applied to mailza_assis.txt (and harmlessly to all others).
Do not re-apply." — NÃO era inofensivo: duas regras (linha 30, alternativa
"ne\w*"; e linha 31, "de ciência" sem contexto) produziram 92 fusões
espúrias de palavras legítimas ("de negócios"->"definegócios", "de
ciência"->"deficiência" trocando Ciência&Tecnologia por Deficiência) em
10 dos 12 candidatos do Norte quando aplicadas via --write. Todos os 12
textos foram reextraídos e reprocessados após a correção das regras.
Consulte `reparar_ligadura_fi.py` (versão corrigida) antes de reaplicar
qualquer reparo — e sempre faça um dry-run comparando antes/depois por
candidato antes de escrever, mesmo com regras "documentadas".
