"""
Etape 3 du pipeline : Reparation des erreurs OCR contextuelles.

Les documents RAA numerises par OCR (reconnaissance optique de
caracteres) contiennent des erreurs specifiques et recurrentes.
L'OCR confond souvent des caracteres visuellement proches :

Confusions les plus frequentes (francais) :
    - "I" (i majuscule) ↔ "l" (L minuscule) ↔ "1" (chiffre un)
    - "O" (o majuscule) ↔ "0" (chiffre zero)
    - "rn" ↔ "m" (deux jambages fusionnes)
    - "c1" ↔ "d" (c + 1 → d)
    - "fi" ↔ ligature "fi"
    - "fl" ↔ ligature "fl"
    - Coupure de mot en fin de ligne ("pré-\\nfecture" → "prefecture")

Cette etape utilise des regles contextuelles (le mot doit exister
en francais ou dans le vocabulaire juridique) pour decider si une
substitution est correcte. On ne corrige que les cas certains
pour eviter d'alterer le sens du texte.
"""

import re


# =================================================================
# BLOC : Vocabulaire juridique et administratif francais
# =================================================================
# Liste des mots frequents dans les RAA qui sont souvent mal
# OCRises. Cette liste sert de reference pour valider les
# corrections contextuelles.
#
# Le principe : si apres substitution le mot appartient a ce
# vocabulaire, la correction est appliquee. Sinon, on laisse
# le texte tel quel (principe de prudence).
# =================================================================

LEGAL_VOCABULARY = {
    # ── Titres et fonctions ──
    "prefet", "pr\u00e9fet", "pr\u00e9f\u00e8te", "sous-pr\u00e9fet", "sous-pr\u00e9f\u00e8te",
    "pr\u00e9fecture", "sous-pr\u00e9fecture",
    "secr\u00e9taire", "g\u00e9n\u00e9ral", "g\u00e9n\u00e9rale",
    "directeur", "directrice", "adjoint", "adjointe",
    "ministre", "pr\u00e9sident", "pr\u00e9sidente",
    "maire", "commissaire", "d\u00e9l\u00e9gu\u00e9", "d\u00e9l\u00e9gu\u00e9e",
    "inspecteur", "inspectrice", "contr\u00f4leur", "contr\u00f4leuse",

    # ── Actes et procedures ──
    "arr\u00eat\u00e9", "arr\u00eat\u00e9s", "d\u00e9cret", "d\u00e9crets",
    "d\u00e9cision", "d\u00e9cisions", "d\u00e9lib\u00e9ration", "d\u00e9lib\u00e9rations",
    "circulaire", "instruction", "notification",
    "abrogation", "modification", "prorogation",
    "publication", "affichage", "ex\u00e9cution",

    # ── Structure des arretes ──
    "article", "articles", "alin\u00e9a", "alin\u00e9as",
    "chapitre", "section", "paragraphe",
    "titre", "annexe", "annexes",
    "pr\u00e9ambule", "dispositif", "consid\u00e9rant",

    # ── Formules juridiques ──
    "consid\u00e9rant", "attendu",
    "code", "loi", "ordonnance", "r\u00e8glement",
    "d\u00e9partement", "d\u00e9partements",
    "commune", "communes", "intercommunal",
    "r\u00e9gion", "r\u00e9gional", "r\u00e9gionale",
    "territoire", "territorial", "territoriale",
    "collectivit\u00e9", "collectivit\u00e9s",
    "administration", "administratif", "administrative",

    # ── Mots courants souvent mal OCRises ──
    "la", "le", "les", "un", "une", "des", "du", "de",
    "il", "elle", "ils", "elles",
    "dans", "pour", "avec", "sans", "sous", "sur",
    "cette", "celui", "celle",
    "faire", "fait", "faite",
    "public", "publique", "publics", "publiques",
    "national", "nationale", "nationaux", "nationales",
}


# =================================================================
# BLOC : Regles de correction OCR contextuelles
# =================================================================
# Chaque regle est un tuple (pattern_regex, remplacement, description).
# Les patterns utilisent des lookbehind/lookahead pour s'assurer
# du contexte (debut/fin de mot, caracteres adjacents).
# =================================================================

OCR_RULES = [
    # ── Confusion I/l (i majuscule / L minuscule) ──
    #
    # "I'article" → "l'article"
    # Contexte : "I" suivi d'une apostrophe puis d'une lettre minuscule
    # C'est un "l" (article defini elide), pas un "I" (pronom anglais).
    #
    # Regex expliquee :
    #   \bI          : "I" en debut de mot
    #   (?=['\u2019]) : suivi d'une apostrophe (droite ou typographique)
    #   (?=..[a-z])  : puis d'une lettre minuscule (apres l'apostrophe)
    (
        re.compile(r"\bI(?=['\u2019][a-z\u00e0-\u00ff])"),
        "l",
        "I majuscule \u2192 l minuscule (article \u00e9lid\u00e9)",
    ),

    # ── "Ia" → "la" (article defini) ──
    # "I" suivi de "a" en debut de mot, puis d'un espace.
    # "Ia prefecture" → "la prefecture"
    (
        re.compile(r"\bIa\b"),
        "la",
        "Ia \u2192 la (article d\u00e9fini)",
    ),

    # ── "Ie" → "le" (article defini) ──
    (
        re.compile(r"\bIe\b"),
        "le",
        "Ie \u2192 le (article d\u00e9fini)",
    ),

    # ── "Ies" → "les" (article defini pluriel) ──
    (
        re.compile(r"\bIes\b"),
        "les",
        "Ies \u2192 les (article d\u00e9fini pluriel)",
    ),

    # ── "Il" en milieu de phrase apres une virgule → "Il" (correct)
    # On ne corrige PAS "Il" car c'est souvent correct (pronom).
    # Seul "Ie", "Ia", "Ies" sont des erreurs certaines.

    # ── Confusion 0/O (zero/O majuscule) ──
    #
    # "n0 2023" → "n° 2023"  — pas directement, mais :
    # "article 1O" → probablement pas une erreur courante
    # On ne corrige que dans les contextes tres surs.

    # ── Coupure de mot en fin de ligne ──
    #
    # "pré-\nfecture" → "préfecture"
    # "adminis-\ntration" → "administration"
    #
    # Regex expliquee :
    #   ([a-z\u00e0-\u00ff])  : lettre minuscule (y compris accentuees)
    #   -\s*\n\s*             : tiret, espaces optionnels, saut de ligne, espaces
    #   ([a-z\u00e0-\u00ff])  : lettre minuscule qui suit
    #
    # On rejoint les deux parties du mot.
    (
        re.compile(r'([a-z\u00e0-\u00ff])-\s*\n\s*([a-z\u00e0-\u00ff])'),
        r'\1\2',
        "R\u00e9paration coupure de mot en fin de ligne",
    ),

    # ── "rn" → "m" dans certains mots connus ──
    #
    # L'OCR confond souvent "m" avec "rn" car les deux ont
    # des formes tres proches dans beaucoup de polices.
    # On ne corrige que les mots du vocabulaire juridique.
    #
    # "cornrnune" → "commune"
    # "adrninistration" → "administration"
    # "norrnalisation" → "normalisation"
    #
    # Ces corrections sont faites par la fonction _fix_rn_to_m()
    # qui verifie le vocabulaire.
]


# =================================================================
# BLOC : Regex pour la detection de "rn" → "m"
# =================================================================
# On cherche les mots contenant "rn" et on teste si le remplacement
# par "m" donne un mot du vocabulaire.
# =================================================================
RE_WORD_WITH_RN = re.compile(r'\b(\w*rn\w*)\b', re.UNICODE)

# Mots ou "rn" est correct et ne doit PAS etre remplace par "m"
RN_EXCEPTIONS = {
    "journal", "journaux", "ourne", "tourner", "retourner",
    "fournir", "fourniture", "gouvernement", "gouverneur",
    "borne", "bornes", "cornet", "corner", "corne",
    "interne", "inernes", "externe", "externes",
    "alterne", "discerne", "concerne",
    "orne", "ornement",
    "urne", "urnes",
    "herne", "verne", "berne",
    "terne", "moderne", "modernes",
    "caserne", "caverne", "citerne", "lanterne",
}


def fix_ocr(text: str) -> dict:
    """
    Repare les erreurs OCR contextuelles dans un texte francais.

    Parametres :
        text : Le texte a reparer (str)

    Retourne :
        Un dictionnaire contenant :
        - 'text'  : le texte repare (str)
        - 'corrections' : liste des corrections effectuees
        - 'stats' : statistiques de l'etape

    Exemples :
        >>> result = fix_ocr("I'arrete prefectoral de Ia prefecture")
        >>> result['text']
        "l'arrete prefectoral de la prefecture"

        >>> result = fix_ocr("pre-\\nfecture du departement")
        >>> result['text']
        "prefecture du departement"
    """
    corrections = []

    # =================================================================
    # Appliquer les regles OCR dans l'ordre
    # =================================================================
    for pattern, replacement, description in OCR_RULES:
        text_before = text
        text, count = pattern.subn(replacement, text)

        if count > 0:
            corrections.append({
                "type": "ocr_rule",
                "description": "{} ({} occurrence(s))".format(description, count),
                "count": count,
            })

    # =================================================================
    # Correction "rn" → "m" contextuelle
    # =================================================================
    text_before_rn = text
    rn_fixes = 0

    def _try_rn_to_m(match):
        nonlocal rn_fixes
        word = match.group(0)
        word_lower = word.lower()

        # Ne pas toucher aux exceptions connues
        if word_lower in RN_EXCEPTIONS:
            return word

        # Tester si le remplacement donne un mot connu
        candidate = word_lower.replace('rn', 'm')
        if candidate in LEGAL_VOCABULARY:
            rn_fixes += 1
            # Preserver la casse d'origine
            return word.replace('rn', 'm').replace('Rn', 'M')

        return word

    text = RE_WORD_WITH_RN.sub(_try_rn_to_m, text)

    if rn_fixes > 0:
        corrections.append({
            "type": "ocr_rn_to_m",
            "description": "Correction rn \u2192 m ({} mot(s) v\u00e9rifi\u00e9(s))".format(rn_fixes),
            "count": rn_fixes,
        })

    # =================================================================
    # Nettoyage des espaces multiples residuels
    # =================================================================
    # Apres la reunion de mots coupes, il peut rester des espaces
    # doubles. On les reduit a un seul espace (sauf en debut de ligne
    # pour preserver l'indentation).
    # =================================================================
    text_before_spaces = text
    # Ne toucher qu'aux espaces en milieu de ligne (pas l'indentation)
    text = re.sub(r'(?<=\S)[ \t]{2,}(?=\S)', ' ', text)

    if text != text_before_spaces:
        diff = len(text_before_spaces) - len(text)
        corrections.append({
            "type": "ocr_spaces",
            "description": "Nettoyage de {} espace(s) redondant(s)".format(diff),
            "count": diff,
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
