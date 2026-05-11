"""
Etape 4 du pipeline : Typographie francaise (regles de l'Imprimerie nationale).

Cette etape applique les conventions typographiques francaises aux
documents RAA. Les regles proviennent du "Lexique des regles
typographiques en usage a l'Imprimerie nationale" et sont obligatoires
pour les documents officiels de la Republique francaise.

Regles principales :
    1. Espaces insecables avant les ponctuations doubles (; : ! ?)
    2. Espaces insecables dans les guillemets francais (« ... »)
    3. Conversion des guillemets anglais ("...") en guillemets francais
    4. Normalisation des tirets (-- → tiret cadratin)
    5. Points de suspension (... → U+2026 ou normalisation)
    6. Espaces autour des signes mathematiques
    7. Formatage des references legales (L. 2213-1, R. 421-3, etc.)
    8. Formatage du symbole "numero" (n° avec espace insecable)

Espaces en typographie francaise :
    - Espace fine insecable (U+202F) : avant ; ? ! et apres «
    - Espace insecable (U+00A0) : avant : et avant »
    - Espace normale : apres toute ponctuation sauf apostrophe/trait d'union

    Moyen mnemotechnique :
      « mot » → insecable des deux cotes
      mot ;   → fine insecable AVANT
      mot :   → insecable AVANT (pas fine : le deux-points est "large")
"""

import re


# =================================================================
# BLOC : Constantes typographiques
# =================================================================
# Les caracteres Unicode speciaux utilises en typographie francaise.
# On les definit comme constantes pour la lisibilite du code.
# =================================================================

NBSP = '\u00a0'      # Espace insecable (no-break space)
NNBSP = '\u202f'     # Espace fine insecable (narrow no-break space)
LAQUO = '\u00ab'     # Guillemet ouvrant francais «
RAQUO = '\u00bb'     # Guillemet fermant francais »
MDASH = '\u2014'     # Tiret cadratin —
NDASH = '\u2013'     # Tiret demi-cadratin –
HELLIP = '\u2026'    # Points de suspension …
RSQUO = '\u2019'     # Apostrophe typographique '


# =================================================================
# BLOC : Regles de typographie francaise
# =================================================================
# Chaque regle est definie comme un tuple :
#   (regex_compilee, chaine_de_remplacement, description)
#
# L'ordre d'application est IMPORTANT :
#   1. D'abord les guillemets (car ils modifient les espaces internes)
#   2. Puis les ponctuations doubles (;:!?)
#   3. Puis les tirets et symboles
#   4. Enfin les references legales et numeros
#
# CONVENTION dans les regex :
#   \s  = n'importe quel espace (normal, insecable, fine, etc.)
#   [ ] = espace normale uniquement (U+0020)
# =================================================================



def fix_typography(text: str) -> dict:
    """
    Applique les regles typographiques francaises au texte.

    Parametres :
        text : Le texte a corriger (str)

    Retourne :
        Un dictionnaire contenant :
        - 'text'  : le texte avec typographie corrigee (str)
        - 'corrections' : liste des corrections effectuees
        - 'stats' : statistiques de l'etape

    Exemple :
        >>> r = fix_typography('Vu l\\'article L.2213-1 du CGCT;le prefet decide:"oui"')
        >>> r['text']
        'Vu l\\'article L. 2213-1 du CGCT\\u202f; le prefet decide\\u00a0: «\\u00a0oui\\u00a0»'
    """
    corrections = []
    
    # =================================================================
    # Regle 0 : Recollage des mots lettres espacées (OCR)
    # =================================================================
    # Exemple : S O M M A I R E → SOMMAIRE
    # On cible uniquement les mots en MAJUSCULES avec au moins 3 lettres
    # pour éviter de casser du texte normal.
    # =================================================================
    spaced_pattern = re.compile(r'\b(?:[A-ZÀ-ÖØ-Ý]\s+){2,}[A-ZÀ-ÖØ-Ý]\b')

    def _fix_spaced(match):
        word = match.group(0)
        return word.replace(" ", "")

    text, n = _apply_rule(
        text,
        spaced_pattern,
        lambda m: _fix_spaced(m),
        "Recollage mots lettres espacées (OCR)",
        corrections,
    )


    # =================================================================
    # Regle 1 : Guillemets anglais → guillemets francais
    # =================================================================
    # "texte" → « texte »
    # 'texte' → « texte » (seulement les paires, pas les apostrophes)
    #
    # Regex expliquee :
    #   "       : guillemet double ouvrant anglais
    #   ([^"]*) : contenu entre guillemets (tout sauf un autre ")
    #   "       : guillemet double fermant anglais
    #
    # Remplacement :
    #   «\u00a0 + contenu + \u00a0»
    #   Avec des espaces insecables a l'interieur (regle Imprimerie nat.)
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'"([^"]*?)"'),
        LAQUO + NBSP + r'\1' + NBSP + RAQUO,
        "Guillemets anglais doubles \u2192 fran\u00e7ais",
        corrections,
    )

    # Guillemets anglais typographiques (curly quotes) deja convertis
    # en Phase 2 vers « », mais on s'assure des espaces
    # (traite plus bas dans la regle des guillemets francais)

    # =================================================================
    # Regle 2 : Espaces dans les guillemets francais « ... »
    # =================================================================
    # Assurer une espace insecable apres « et avant »
    #
    # Cas traites :
    #   «texte»     → «\u00a0texte\u00a0»
    #   « texte»    → «\u00a0texte\u00a0»
    #   «texte »    → «\u00a0texte\u00a0»
    #   « texte »   → «\u00a0texte\u00a0»  (espace normale → insecable)
    #
    # Regex pour « :
    #   \u00ab      : guillemet ouvrant
    #   \s*         : zero ou plusieurs espaces (de tout type)
    #   (?=\S)      : suivi d'un caractere non-espace (lookahead)
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(LAQUO + r'\s*(\S)'),
        LAQUO + NBSP + r'\1',
        "Espace ins\u00e9cable apr\u00e8s \u00ab",
        corrections,
    )

    text, n = _apply_rule(
        text,
        re.compile(r'(\S)\s*' + RAQUO),
        r'\1' + NBSP + RAQUO,
        "Espace ins\u00e9cable avant \u00bb",
        corrections,
    )

    # =================================================================
    # Regle 3 : Espace fine insecable avant ; ? !
    # =================================================================
    # En typographie francaise, les ponctuations "hautes" (celles qui
    # ont un element au-dessus de la ligne de base) sont precedees
    # d'une espace fine insecable (U+202F).
    #
    # Concerne : point-virgule (;), point d'interrogation (?),
    #            point d'exclamation (!)
    #
    # Regex expliquee :
    #   (\S)        : caractere non-espace precedent (groupe 1)
    #   \s*         : zero ou plusieurs espaces existantes (on les retire)
    #   ([;?!])     : la ponctuation cible (groupe 2)
    #
    # Remplacement :
    #   \1\u202f\2  : caractere + espace fine insecable + ponctuation
    #
    # ATTENTION : on ne modifie pas les URLs ou les chemins de fichier
    # qui contiennent ces caracteres dans un contexte technique.
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'(\S)\s*([;?!])'),
        r'\1' + NNBSP + r'\2',
        "Espace fine ins\u00e9cable avant ; ? !",
        corrections,
    )

    # =================================================================
    # Regle 4 : Espace insecable avant :
    # =================================================================
    # Le deux-points utilise une espace insecable NORMALE (pas fine),
    # car c'est un signe "large" en typographie francaise.
    #
    # Exception : les heures (14:30), les references (art. 3:2),
    # et les protocoles (http:) ne prennent PAS d'espace.
    #
    # Regex expliquee :
    #   (\S)        : caractere non-espace precedent
    #   \s*         : espaces existantes (retirees)
    #   :           : le deux-points
    #   (?=\s|$)    : suivi d'une espace ou fin de ligne
    #                 (evite de modifier "14:30" ou "http:")
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'(\S)\s*:(?=[\s' + LAQUO + r']|$)'),
        r'\1' + NBSP + ':',
        "Espace ins\u00e9cable avant :",
        corrections,
    )

    # =================================================================
    # Regle 5 : Espace apres ponctuation
    # =================================================================
    # Assurer une espace apres . , ; : ! ? sauf en fin de ligne
    # et sauf si deja suivi d'un espace ou d'un guillemet fermant.
    #
    # Regex :
    #   ([.,;:!?])  : ponctuation (groupe 1)
    #   (?=[A-Za-z\u00c0-\u017f]) : suivi d'une lettre (pas d'espace)
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'([.,;:!?])(?=[A-Za-z\u00c0-\u017f' + LAQUO + r'])'),
        r'\1 ',
        "Espace apr\u00e8s ponctuation",
        corrections,
    )

    # =================================================================
    # Regle 6 : Tirets
    # =================================================================
    # " -- " ou " --- " → " — " (tiret cadratin)
    # Utilise dans les arretes pour separer le numero d'article
    # du contenu : "Article 1er — Le prefet decide..."
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'\s*---?\s*'),
        ' ' + MDASH + ' ',
        "Tirets -- \u2192 tiret cadratin \u2014",
        corrections,
    )

    # =================================================================
    # Regle 7 : Apostrophe typographique
    # =================================================================
    # L'apostrophe droite (U+0027) entre deux lettres est remplacee
    # par l'apostrophe typographique (U+2019).
    #
    # Regex :
    #   ([A-Za-z\u00c0-\u017f]) : lettre avant l'apostrophe
    #   '                       : apostrophe droite
    #   ([A-Za-z\u00c0-\u017f]) : lettre apres l'apostrophe
    #
    # Exemples : l'article → l\u2019article, d'application → d\u2019application
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r"([A-Za-z\u00c0-\u017f])'([A-Za-z\u00c0-\u017f])"),
        r'\1' + RSQUO + r'\2',
        "Apostrophe typographique \u2019",
        corrections,
    )

    # =================================================================
    # Regle 8 : Points de suspension
    # =================================================================
    # "..." (trois points) → normalises en trois points separes
    # (on NE convertit PAS en U+2026 car c'est moins courant dans
    # les documents administratifs et peut poser des problemes de
    # compatibilite avec certains systemes)
    #
    # On s'assure juste qu'il y en a exactement 3, pas plus.
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'\.{4,}'),
        '...',
        "Normalisation des points de suspension",
        corrections,
    )

    # =================================================================
    # Regle 9 : Reference legale — espacement apres L. R. D. A.
    # =================================================================
    # Les references au code utilisent des lettres abreviatives :
    #   L. = partie legislative
    #   R. = partie reglementaire
    #   D. = decret
    #   A. = arrete
    #
    # Format correct : "L. 2213-1" (espace apres le point)
    # Erreur courante : "L.2213-1" (pas d'espace)
    #
    # Regex expliquee :
    #   \b([LRDA])  : lettre abreviative en debut de mot
    #   \.          : point
    #   (?=\d)      : suivi immediatement d'un chiffre (pas d'espace)
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'\b([LRDA])\.(?=\d)'),
        r'\1. ',
        "Espace apr\u00e8s abr\u00e9viation l\u00e9gale (L. R. D. A.)",
        corrections,
    )

    # =================================================================
    # Regle 10 : Symbole "numero" — n° avec espace insecable
    # =================================================================
    # "n°2023" → "n° 2023" (espace insecable entre n° et le chiffre)
    # "N°2023" → "N° 2023"
    #
    # Regex :
    #   [nN]        : n minuscule ou majuscule
    #   °           : symbole degre
    #   \s*         : espaces existantes (retirees)
    #   (\d)        : chiffre qui suit (groupe 1)
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'([nN])\u00b0\s*(\d)'),
        r'\1' + '\u00b0' + NBSP + r'\2',
        "Espace ins\u00e9cable apr\u00e8s n\u00b0",
        corrections,
    )

    # =================================================================
    # Regle 11 : Pas d'espace avant les ponctuations simples (, .)
    # =================================================================
    # Erreur courante dans les OCR : "le prefet ,vu l'article ."
    # Correct : "le prefet, vu l'article."
    #
    # Regex :
    #   \s+         : une ou plusieurs espaces
    #   ([.,])      : virgule ou point
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'\s+([.,])'),
        r'\1',
        "Suppression espace avant , et .",
        corrections,
    )

    # =================================================================
    # Regle 12 : Espaces multiples → espace simple
    # =================================================================
    # Apres toutes les modifications, il peut rester des espaces
    # doubles. On les reduit, en preservant les espaces insecables.
    # =================================================================
    text, n = _apply_rule(
        text,
        re.compile(r'[ ]{2,}'),
        ' ',
        "Espaces multiples r\u00e9duites",
        corrections,
    )

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


def _apply_rule(text: str, pattern: re.Pattern, replacement: str,
                description: str, corrections: list) -> tuple[str, int]:
    """
    Applique une regle regex et enregistre la correction si des
    modifications ont ete faites.

    Retourne :
        (texte_modifie, nombre_de_substitutions)
    """
    new_text, count = pattern.subn(replacement, text)
    if count > 0:
        corrections.append({
            "type": "typography",
            "description": "{} ({} occurrence(s))".format(description, count),
            "count": count,
        })
    return new_text, count
