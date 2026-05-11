"""
Etape 5 du pipeline : Uniformisation de la structure juridique.

Les arretes prefectoraux suivent une structure codifiee :
    - Un en-tete (titre, visas, considerants)
    - Le mot "ARRETE" (ou "DECIDE", "ORDONNE")
    - Des articles numerotes sequentiellement
    - Une formule d'execution finale

Cette etape normalise :
    1. Le titre de l'acte : "ARRETE" → "ARRETE" (en majuscules centrees)
    2. La numerotation des articles :
       - "ARTICLE PREMIER" / "Art. 1" / "Article 1er" → "Article 1"
       - "ARTICLE 2" / "Art.2" / "ART. DEUX" → "Article 2"
    3. Le separateur article-contenu :
       - ":" / "-" / "." → " — " (tiret cadratin)
    4. Les alineas et paragraphes
    5. Les formules "Vu" et "Considerant"

Principe fondamental : on ne modifie JAMAIS le contenu juridique,
uniquement la FORME de presentation (numerotation, separateurs,
mise en forme).
"""

import re


# =================================================================
# BLOC : Constantes de structure
# =================================================================
MDASH = '\u2014'     # Tiret cadratin —
NBSP = '\u00a0'      # Espace insecable


# =================================================================
# BLOC : Suppression des numéros de page
# =================================================================
# Formes détectées et supprimées :
#
#   PAGE 3          → supprimé
#   Page 3/12       → supprimé
#   - 3 -           → supprimé
#   — 3 —           → supprimé
#   3/12            → supprimé (seul sur sa ligne)
#   p. 3            → supprimé
#   p3              → supprimé
# =================================================================

RE_PAGE = re.compile(
    r'^\s*'
    r'(?:'
    # ===== PAGE 1 =====
    r'=+\s*(?:PAGE|Page|page)\s*\d+\s*=+'

    r'|'

    # Page 3 / Page 3/12 / Page 3 sur 12
    r'(?:PAGE|Page|page)\s*\d+(?:\s*/\s*\d+)?(?:\s+sur\s+\d+)?'

    r'|'

    # p. 3 / p3
    r'(?:P\.?|p\.?)\s*\d+'

    r'|'

    # 1/12 (avec espaces)
    r'\d+\s*/\s*\d+'

    r'|'

    # - 3 - ou — 3 —
    r'[-—–]\s*\d+\s*[-—–]'

    r'|'

    # numéro seul
    r'\d+'
    r')'
    r'(?:\s*)$',
    re.MULTILINE
)


def remove_page_numbers(text: str) -> dict:
    """
    Supprime les numéros de page d'un texte brut issu d'un fichier TXT.

    Paramètres :
        text : Le texte brut (str)

    Retourne :
        dict avec 'text', 'corrections', 'stats'

    Exemple :
        >>> r = remove_page_numbers("PAGE 3\\nVu le décret...\\n1/12")
        >>> r['text']
        'Vu le décret...'
    """
    corrections = []
    page_count = 0

    def _remove_page(match):
        nonlocal page_count
        page_count += 1
        return ''

    text_result = RE_PAGE.sub(_remove_page, text)

    text_result = re.sub(
        r'\b[Pp]age\s*\d+\b',
        '',
        text_result
    )
    
    text_result = re.sub(r'^=+\s*=+$', '', text_result, flags=re.MULTILINE)
    
    # Nettoyer les lignes vides multiples laissées par les suppressions
    text_result = re.sub(r'\n{3,}', '\n\n', text_result)
    text_result = text_result.strip()
    
    
 
    if page_count > 0:
        corrections.append({
            "type": "pagination",
            "description": "Suppression de {} numéro(s) de page".format(page_count),
            "count": page_count,
        })

    return {
        "text": text_result,
        "corrections": corrections,
        "stats": {
            "total_suppressions": page_count,
        },
    }


def process_txt_file(filepath: str) -> dict:
    """
    Lit un fichier TXT et supprime les numéros de page.

    Paramètres :
        filepath : Chemin vers le fichier TXT

    Retourne :
        dict avec 'text', 'corrections', 'stats'
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    result = remove_page_numbers(text)

    # Sauvegarder le fichier nettoyé
    output_path = filepath.replace('.txt', '_cleaned.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result['text'])

    print(f"✅ Fichier nettoyé sauvegardé : {output_path}")
    print(f"📄 {result['stats']['total_suppressions']} numéro(s) de page supprimé(s)")

    return result




# =================================================================
# BLOC : Patterns de detection des articles
# =================================================================
# Les articles apparaissent sous des formes tres variees dans les
# RAA selon la prefecture d'origine, l'epoque, et l'outil de
# production du document.
#
# Formes rencontrees (exemples reels) :
#   ARTICLE PREMIER    → Article 1
#   ARTICLE 1er        → Article 1
#   Article Premier    → Article 1
#   Art. 1             → Article 1 (si premier article)
#   Art.1              → Article 1
#   ART. 2             → Article 2
#   ARTICLE 2 :        → Article 2 —
#   Article 2 -        → Article 2 —
#   Article 2.         → Article 2 —
#   ARTICLE DEUX       → Article 2
#   Art 3eme           → Article 3
#   ARTICLE UNIQUE     → Article unique
# =================================================================

# ── Mots francais pour les nombres ordinaux ──
ORDINAL_WORDS = {
    "premier": 1, "premi\u00e8re": 1, "premiere": 1,
    "un": 1, "une": 1,
    "deux": 2, "deuxi\u00e8me": 2, "deuxieme": 2, "second": 2, "seconde": 2,
    "trois": 3, "troisi\u00e8me": 3, "troisieme": 3,
    "quatre": 4, "quatri\u00e8me": 4, "quatrieme": 4,
    "cinq": 5, "cinqui\u00e8me": 5, "cinquieme": 5,
    "six": 6, "sixi\u00e8me": 6, "sixieme": 6,
    "sept": 7, "septi\u00e8me": 7, "septieme": 7,
    "huit": 8, "huiti\u00e8me": 8, "huitieme": 8,
    "neuf": 9, "neuvi\u00e8me": 9, "neuvieme": 9,
    "dix": 10, "dixi\u00e8me": 10, "dixieme": 10,
    "onze": 11, "douze": 12, "treize": 13, "quatorze": 14,
    "quinze": 15, "seize": 16,
}

# =================================================================
# Regex principale de detection des articles.
#
# Decompositon :
#   ^                    : debut de ligne
#   \s*                  : espaces optionnels en debut
#   (?:ARTICLE|Article|article|ART\.?|Art\.?)
#                        : le mot "article" sous toutes ses formes
#   \s*                  : espaces optionnels
#   (                    : GROUPE 1 — le "numero" de l'article
#     PREMIER|premier|...  mots ordinaux
#     |\d+\s*(?:er|ère|e|ème|eme)?  chiffre + suffixe ordinal optionnel
#     |UNIQUE|unique       article unique
#   )
#   \s*                  : espaces optionnels
#   [:\-\.—–]?           : separateur optionnel (: - . — –)
#   \s*                  : espaces apres separateur
# =================================================================

# Construction dynamique du pattern des mots ordinaux
_ordinal_words_pattern = '|'.join(
    re.escape(w) for w in sorted(ORDINAL_WORDS.keys(), key=len, reverse=True)
)

RE_ARTICLE = re.compile(
    r'^(\s*)'                              # Groupe 1 : indentation
    r'(?:ARTICLE|Article|article|ART\.?\s*|Art\.?\s*)'  # Mot "article"
    r'\s*'
    r'('                                   # Groupe 2 : numero
    + _ordinal_words_pattern +             #   mots ordinaux
    r'|\d+\s*(?:er|[eè]re|[eè]me|e)?'     #   ou chiffres + suffixe
    r'|UNIQUE|unique|Unique'               #   ou "unique"
    r')'
    r'\s*'
    r'[:.\u2014\u2013-]?'                   # Separateur optionnel (: . — – -)
    r'\s*',                                # Espaces apres separateur
    re.IGNORECASE | re.MULTILINE
)


# =================================================================
# Regex pour le mot "ARRETE" (titre de l'acte)
# =================================================================
# Detecte les variations du mot cle central de l'arrete :
#   ARRETE, ARRÊTE, Arrête, ARRETE, DECIDE, ORDONNE
#
# Le mot doit etre seul sur sa ligne (ou quasi seul).
# =================================================================
RE_TITLE_KEYWORD = re.compile(
    r'^(\s*)(ARR[ÊE\u00ca]T[ÉE\u00c9]|DECIDE|D[ÉE\u00c9]CIDE|ORDONNE)(\s*)$',
    re.IGNORECASE | re.MULTILINE
)


# =================================================================
# Regex pour les formules "Vu" et "Considerant"
# =================================================================
# Normalise la presentation des visas et considerants :
#   VU → Vu
#   CONSIDERANT → Considérant
#   ATTENDU → Attendu
# =================================================================
RE_VU = re.compile(
    r'^(\s*)(VU|Vu|vu)\b',
    re.MULTILINE
)

RE_CONSIDERANT = re.compile(
    r'^(\s*)(CONSID[ÉE\u00c9]RANT|Consid[ée\u00e9]rant|consid[ée\u00e9]rant)\b',
    re.MULTILINE
)

RE_ATTENDU = re.compile(
    r'^(\s*)(ATTENDU|Attendu|attendu)\b',
    re.MULTILINE
)


def fix_structure(text: str) -> dict:
    """
    Uniformise la structure juridique d'un arrete prefectoral.

    Parametres :
        text : Le texte a structurer (str)

    Retourne :
        dict avec 'text', 'corrections', 'stats'

    Exemple :
        >>> r = fix_structure("ARTICLE PREMIER: Le PREFET decide...")
        >>> r['text']
        'Article 1er — Le PREFET decide...'
    """
    corrections = []
    
    text = remove_page_numbers(text)['text']
    
   
    # =================================================================
    # Etape 1 : Normaliser le titre "ARRETE" / "ARRÊTE"
    # =================================================================
    # Le mot-cle central de l'arrete est toujours en majuscules,
    # seul sur sa ligne, avec "ARRÊTE" accentue.
    # =================================================================
    def _fix_title(match):
        indent = match.group(1)
        keyword = match.group(2).upper()
        trailing = match.group(3)
        # Normaliser : ARRETE → ARRÊTE, DECIDE → DÉCIDE
        normalized = keyword
        if keyword in ('ARRETE', 'ARR\u00caTE', 'ARRÊTE'):
            normalized = 'ARR\u00caTE'
        elif keyword in ('DECIDE', 'D\u00c9CIDE', 'DÉCIDE'):
            normalized = 'D\u00c9CIDE'
        return indent + normalized + trailing

    text_before = text
    text = RE_TITLE_KEYWORD.sub(_fix_title, text)
    if text != text_before:
        corrections.append({
            "type": "structure_title",
            "description": "Normalisation du titre de l\u2019acte",
            "count": 1,
        })

    # =================================================================
    # Etape 2 : Normaliser les articles
    # =================================================================
    # Chaque article est reformate en :
    #   "Article N — " (avec tiret cadratin)
    #
    # Le numero est normalise :
    #   - Mots ordinaux → chiffres (PREMIER → 1er)
    #   - Suffixes uniformises (1er, 2, 3, etc.)
    #   - "UNIQUE" preserve tel quel
    # =================================================================
    article_count = 0

    def _fix_article(match):
        nonlocal article_count
        article_count += 1
        indent = match.group(1)
        raw_number = match.group(2).strip()

        # Determiner le numero
        number = _parse_article_number(raw_number)

        # Formater le numero
        if isinstance(number, int):
            if number == 1:
                num_str = str(number)
            else:
                num_str = str(number)
        else:
            # "unique" ou autre texte special
            num_str = number
 
        return indent + '\n' + 'Article ' + num_str + ' ' + MDASH + ' '

    text = RE_ARTICLE.sub(_fix_article, text)

    if text != text_before:
        corrections.append({
            "type": "structure_articles",
            "description": "Normalisation de {} article(s)".format(article_count),
            "count": article_count,
        })

    # =================================================================
    # Etape 3 : Normaliser les formules "Vu" et "Considerant"
    # =================================================================

    text_before = text
    vu_count = 0

    def _fix_vu(match):
        nonlocal vu_count
        vu_count += 1
        return match.group(1) + 'Vu'

    text = RE_VU.sub(_fix_vu, text)

    if vu_count > 0:
        corrections.append({
            "type": "structure_vu",
            "description": "Normalisation de {} visa(s) (Vu)".format(vu_count),
            "count": vu_count,
        })

    cons_count = 0

    def _fix_considerant(match):
        nonlocal cons_count
        cons_count += 1
        return match.group(1) + 'Consid\u00e9rant'

    text = RE_CONSIDERANT.sub(_fix_considerant, text)

    if cons_count > 0:
        corrections.append({
            "type": "structure_considerant",
            "description": "Normalisation de {} consid\u00e9rant(s)".format(cons_count),
            "count": cons_count,
        })

    att_count = 0

    def _fix_attendu(match):
        nonlocal att_count
        att_count += 1
        return match.group(1) + 'Attendu'

    text = RE_ATTENDU.sub(_fix_attendu, text)

    if att_count > 0:
        corrections.append({
            "type": "structure_attendu",
            "description": "Normalisation de {} attendu(s)".format(att_count),
            "count": att_count,
        })

    # =================================================================
    # Construction du resultat
    # =================================================================
    total_corrections = sum(c.get("count", 0) for c in corrections)

    return {
        "text": text,
        "corrections": corrections,
        "stats": {
            "total_corrections": total_corrections,
            "categories": len(corrections),
        },
    }


def _parse_article_number(raw: str):
    """
    Parse le numero d'un article depuis sa forme brute.

    Parametres :
        raw : le texte du numero ("PREMIER", "2", "3ème", "UNIQUE", etc.)

    Retourne :
        int si c'est un nombre, str si c'est un texte special ("unique")
    """
    raw_lower = raw.lower().strip()

    # Cas "unique"
    if raw_lower == 'unique':
        return 'unique'

    # Cas mot ordinal (PREMIER, DEUX, etc.)
    if raw_lower in ORDINAL_WORDS:
        return ORDINAL_WORDS[raw_lower]

    # Cas chiffre avec suffixe optionnel ("2", "3ème", "1er")
    match = re.match(r'(\d+)', raw)
    if match:
        return int(match.group(1))

    # Cas inconnu : retourner tel quel
    return raw

"""
fix_raa.py — Corrige les retours à la ligne intempestifs dans un fichier texte RAA.

Logique :
- Une ligne qui se termine par un mot (sans ponctuation forte) et dont
  la suivante commence par une minuscule (ou un chiffre) est considérée
  comme la continuation de la même phrase → on les fusionne.
- Les vrais séparateurs de paragraphe (ligne vide, ligne de titre en
  majuscules, ligne commençant par "Article", "•", "-", un chiffre suivi
  d'un point, etc.) sont TOUJOURS conservés.

Usage :
    python fix_raa.py input.txt output.txt
"""

import re
import sys


# ---------------------------------------------------------------------------
# Heuristiques pour détecter un début de nouveau bloc logique
# ---------------------------------------------------------------------------
BLOC_PATTERNS = [
    r"^\s*$",                          # ligne vide
    r"^Article\s+\d",                  # Article 1, Article 2…
    r"^ARTICLE\s+\d",
    r"^\d+[\.\)]\s+\S",               # 1. texte  /  1) texte
    r"^[A-ZÀÂÉÈÊÎÔÙÛ]{3,}",          # ligne tout en MAJUSCULES (titre)
    r"^[\-\•\*►]\s+",                 # liste à puces
    r"^Vu\b",                          # considérants juridiques
    r"^Considérant\b",
    r"^Le\s+(Préfet|Maire|Président)", # formule d'autorité
    r"^ARRÊTÉ",
    r"^DÉCISION",
    r"^ANNEXE",
]

BLOC_RE = re.compile("|".join(BLOC_PATTERNS))

# Ponctuation forte → la ligne suivante commence forcément un nouveau bloc
STRONG_PUNCT = re.compile(r"[.;:!?»]\s*$")


def is_new_block(line: str) -> bool:
    """Renvoie True si la ligne doit impérativement démarrer un nouveau bloc."""
    return bool(BLOC_RE.match(line))


def fix_line_breaks(text: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    buffer = ""

    for raw_line in lines:
        line = raw_line.rstrip()

        # --- Ligne vide : vide le buffer et ajoute un séparateur ---
        if line.strip() == "":
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append("")
            continue

        # --- Ligne qui commence un nouveau bloc logique ---
        if is_new_block(line):
            if buffer:
                result.append(buffer)
                buffer = ""
            buffer = line
            continue

        # --- Continuation ou nouvelle phrase ? ---
        if buffer:
            prev_ends_strongly = bool(STRONG_PUNCT.search(buffer))
            next_starts_upper = line[0].isupper() if line else False

            if prev_ends_strongly or next_starts_upper:
                # Nouveau bloc : on flush et on commence une nouvelle ligne
                result.append(buffer)
                buffer = line
            else:
                # Même phrase → on fusionne avec un espace
                buffer = buffer + " " + line
        else:
            buffer = line

    # Ne pas oublier le dernier buffer
    if buffer:
        result.append(buffer)

    return "\n".join(result)


def main():
    if len(sys.argv) < 3:
        print("Usage : python fix_raa.py <input.txt> <output.txt>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        original = f.read()

    fixed = fix_line_breaks(original)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(fixed)

    # Statistiques rapides
    orig_lines = original.count("\n")
    fixed_lines = fixed.count("\n")
    print(f"✅ Terminé.")
    print(f"   Lignes avant : {orig_lines}")
    print(f"   Lignes après : {fixed_lines}")
    print(f"   Lignes fusionnées : {orig_lines - fixed_lines}")
    print(f"   Fichier sauvegardé : {output_path}")


if __name__ == "__main__":
    main()
