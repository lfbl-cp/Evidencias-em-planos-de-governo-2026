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
    (r'\b([Dd])e (ni[çc]\w*|nid\w*|nir\w*)\b', r'\1efi\2'),
    # CORRIGIDO (auditoria pós-Norte): a alternativa "ne\w*" foi removida por
    # produzir falsos positivos sistemáticos ("de negócios"->"definegócios",
    # "de necessidade"->"definecessidade", "de neoindustrialização"->
    # "defineoindustrialização") em 10 dos 12 candidatos do Norte -- nenhuma
    # ocorrência genuína de defeito de ligadura foi encontrada nessa forma.
    (r'\bcom de (ciência\w*)\b', r'com defi\1'),
    # CORRIGIDO (auditoria pós-Norte): restrito a exigir "com" imediatamente
    # antes ("pessoas com de ciência" = "pessoas com deficiência"), pois sem
    # essa âncora de contexto "de ciência"/"de ciências" é majoritariamente a
    # frase legítima "de ciência" (= "of science": "feiras de ciências",
    # "ecossistema de ciência e tecnologia", "território de ciência e
    # inovação") -- confirmado em Dr. Furlan e Omar Aziz (Norte), 0/8 eram
    # defeitos genuínos antes desta correção.
    (r'\b([Ii])denti (c\w*)\b', r'\1dentifi\2'),
    (r'\b([Cc])erti (c\w*)\b', r'\1ertifi\2'),
    (r'\b([Ss])impli (c\w*)\b', r'\1implifi\2'),
    (r'\b([Ee]) (ciente\w*|cácia\w*|caz\w*)\b', r'\1fi\2'),
    (r'\bAo (nal\w*)\b', r'Ao fi\1'),
    (r'\bao (nal\w*)\b', r'ao fi\1'),
    # 'fl' inserida
    (r'\b([Cc])on (itos?\w*)\b', r'\1onfl\2'),
    (r'\b([Rr])e (etem\w*|ete\w*|exã?o\w*|exiv\w*)\b', r'\1efl\2'),
    (r'\b(uxos?)\b', r'fl\1'),
]

# Regra separada e NÃO aplicada por padrão: "e ciência" -> "eficiência" é
# ambígua no texto corrido, pois a mesma string "e ciência" também ocorre
# como frase legítima "e ciência" (= "and science": "tradicionais e
# ciência", "empreendedorismo e ciência", "inteligência artificial e
# ciência de dados"). CONFIRMADO (auditoria pós-Norte): das 8 ocorrências
# fora do candidato Mailza Assis (AC) -- Alan Rick, Clécio Luís, Omar Aziz
# (5x), Roberto Cidade --, TODAS eram "and science", 0 genuínas. Já em
# Mailza Assis, as ~18 ocorrências de "e ciência" (não precedidas de "de"/
# "com de") são genuinamente "eficiência" quebrada (ex. "mais e ciência",
# "a e ciência do SUS"). Por não haver uma âncora de contexto confiável que
# separe os dois casos de forma geral, esta regra só deve ser aplicada
# manualmente ao candidato/arquivo específico já verificado (Mailza Assis),
# nunca via reparar() genérico.
_RULE_E_CIENCIA_AMBIGUA = (r'\b([Ee]) (ciência\w*)\b', r'\1fi\2')

def reparar(texto):
    for pat, repl in _RULES:
        texto = re.sub(pat, repl, texto)
    return texto

def reparar_e_ciencia_ambigua(texto):
    """Aplica a regra "e ciência"->"eficiência", ambígua em geral.
    Só deve ser chamada em arquivos onde a ambiguidade já foi verificada
    manualmente (ver nota acima) -- atualmente, apenas Mailza Assis (AC)."""
    pat, repl = _RULE_E_CIENCIA_AMBIGUA
    return re.sub(pat, repl, texto)

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
