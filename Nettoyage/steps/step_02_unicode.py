"""
Etape 2 du pipeline : Normalisation Unicode NFC + remplacement des homoglyphes.

Cette etape assure que tous les caracteres du texte sont dans une forme
canonique Unicode (NFC) et remplace les caracteres visuellement identiques
mais techniquement differents (homoglyphes) par leurs equivalents standard.

Pourquoi c'est important pour les RAA :
    Les documents issus de PDF, OCR ou copier-coller contiennent souvent :
    1. Des caracteres decomposes (NFC vs NFD) :
       - NFD : "e" = "e" + accent combine (2 code points : U+0065 + U+0301)
       - NFC : "e" = un seul code point (U+00E9)
       Les deux sont visuellement identiques mais different en memoire.
       Cela cause des bugs dans les recherches, comparaisons, et regex.

    2. Des homoglyphes (caracteres qui se ressemblent mais sont differents) :
       - Espace insecable fine (U+202F) vs espace insecable (U+00A0)
       - Tiret cadratin (U+2014) vs tiret long (U+2015)
       - Apostrophe typographique (U+2019) vs apostrophe droite (U+0027)
       - Guillemets anglais vs guillemets francais

    3. Des caracteres exotiques provenant de polices non-standard :
       - Lettres cyrilliques qui ressemblent au latin (а/a, е/e, о/o)
       - Chiffres pleine largeur (０１２) vs chiffres normaux (012)
"""

import re
import unicodedata


# =================================================================
# BLOC : Table des homoglyphes
# =================================================================
# Chaque entree mappe un caractere "imposteur" vers son equivalent
# standard. Les homoglyphes les plus courants dans les documents
# administratifs francais sont :
#
# 1. Les espaces : il existe plus de 20 types d'espaces en Unicode !
# 2. Les tirets : au moins 6 types courants
# 3. Les apostrophes/guillemets : simples et doubles, droits et courbes
# 4. Les lettres cyrilliques qui ressemblent au latin
# =================================================================

HOMOGLYPH_MAP = {
    # ── Espaces exotiques → espace normale ou insecable ──
    # U+2000 EN QUAD → espace
    '\u2000': ' ',
    # U+2001 EM QUAD → espace
    '\u2001': ' ',
    # U+2002 EN SPACE → espace
    '\u2002': ' ',
    # U+2003 EM SPACE → espace
    '\u2003': ' ',
    # U+2004 THREE-PER-EM SPACE → espace
    '\u2004': ' ',
    # U+2005 FOUR-PER-EM SPACE → espace
    '\u2005': ' ',
    # U+2006 SIX-PER-EM SPACE → espace
    '\u2006': ' ',
    # U+2007 FIGURE SPACE → espace
    '\u2007': ' ',
    # U+2008 PUNCTUATION SPACE → espace
    '\u2008': ' ',
    # U+2009 THIN SPACE → espace fine insecable (typographie fr.)
    '\u2009': '\u202f',
    # U+200A HAIR SPACE → espace fine insecable
    '\u200a': '\u202f',
    # U+205F MEDIUM MATHEMATICAL SPACE → espace
    '\u205f': ' ',
    # U+3000 IDEOGRAPHIC SPACE → espace
    '\u3000': ' ',

    # ── Espaces de largeur nulle (invisibles, parasites) ──
    # U+200B ZERO WIDTH SPACE → supprime
    '\u200b': '',
    # U+200C ZERO WIDTH NON-JOINER → supprime
    '\u200c': '',
    # U+200D ZERO WIDTH JOINER → supprime
    '\u200d': '',
    # U+FEFF BOM / ZERO WIDTH NO-BREAK SPACE → supprime
    '\ufeff': '',

    # ── Tirets → tiret demi-cadratin (U+2013) ou cadratin (U+2014) ──
    # U+2010 HYPHEN → trait d'union standard
    '\u2010': '-',
    # U+2011 NON-BREAKING HYPHEN → trait d'union
    '\u2011': '-',
    # U+2012 FIGURE DASH → tiret demi-cadratin
    '\u2012': '\u2013',
    # U+2015 HORIZONTAL BAR → tiret cadratin
    '\u2015': '\u2014',
    # U+FE58 SMALL EM DASH → tiret cadratin
    '\ufe58': '\u2014',
    # U+FE63 SMALL HYPHEN-MINUS → trait d'union
    '\ufe63': '-',
    # U+FF0D FULLWIDTH HYPHEN-MINUS → trait d'union
    '\uff0d': '-',

    # ── Apostrophes ──
    # U+2018 LEFT SINGLE QUOTATION MARK → apostrophe typographique
    '\u2018': '\u2019',
    # U+201B SINGLE HIGH-REVERSED-9 QUOTATION MARK → apostrophe
    '\u201b': '\u2019',
    # U+FF07 FULLWIDTH APOSTROPHE → apostrophe typographique
    '\uff07': '\u2019',
    # U+02BC MODIFIER LETTER APOSTROPHE → apostrophe typographique
    '\u02bc': '\u2019',
    # U+02BB MODIFIER LETTER TURNED COMMA → apostrophe typographique
    '\u02bb': '\u2019',

    # ── Guillemets doubles ──
    # U+201C LEFT DOUBLE QUOTATION → guillemet ouvrant francais
    '\u201c': '\u00ab',
    # U+201D RIGHT DOUBLE QUOTATION → guillemet fermant francais
    '\u201d': '\u00bb',
    # U+201E DOUBLE LOW-9 QUOTATION → guillemet ouvrant francais
    '\u201e': '\u00ab',
    # U+FF02 FULLWIDTH QUOTATION MARK → guillemet fermant
    '\uff02': '\u00bb',

    # ── Lettres cyrilliques sosies du latin ──
    # Ces caracteres sont visuellement identiques mais ont des
    # code points differents. Ils apparaissent quand un document
    # a ete saisi avec le mauvais clavier ou OCRise avec une
    # police mixte.
    #
    # Minuscules cyrilliques → latin
    '\u0430': 'a',   # а → a
    '\u0435': 'e',   # е → e
    '\u043e': 'o',   # о → o
    '\u0440': 'p',   # р → p
    '\u0441': 'c',   # с → c
    '\u0443': 'y',   # у → y
    '\u0445': 'x',   # х → x
    '\u0456': 'i',   # і → i
    # Majuscules cyrilliques → latin
    '\u0410': 'A',   # А → A
    '\u0412': 'B',   # В → B
    '\u0415': 'E',   # Е → E
    '\u041a': 'K',   # К → K
    '\u041c': 'M',   # М → M
    '\u041d': 'H',   # Н → H
    '\u041e': 'O',   # О → O
    '\u0420': 'P',   # Р → P
    '\u0421': 'C',   # С → C
    '\u0422': 'T',   # Т → T
    '\u0425': 'X',   # Х → X

    # ── Chiffres pleine largeur → chiffres ASCII ──
    '\uff10': '0',
    '\uff11': '1',
    '\uff12': '2',
    '\uff13': '3',
    '\uff14': '4',
    '\uff15': '5',
    '\uff16': '6',
    '\uff17': '7',
    '\uff18': '8',
    '\uff19': '9',

    # ── Symboles courants ──
    # U+2026 HORIZONTAL ELLIPSIS → trois points
    '\u2026': '...',
    # U+00AD SOFT HYPHEN → supprime (invisible, parasite)
    '\u00ad': '',
}

# =================================================================
# Pre-compiler la regex de remplacement pour la performance.
# On construit un pattern qui matche n'importe quel caractere
# de la table d'homoglyphes, puis on remplace via une fonction.
# =================================================================
_HOMOGLYPH_PATTERN = re.compile(
    '[' + re.escape(''.join(HOMOGLYPH_MAP.keys())) + ']'
)


def fix_unicode(text: str) -> dict:
    """
    Normalise le texte en NFC et remplace les homoglyphes.

    Parametres :
        text : Le texte a normaliser (str)

    Retourne :
        Un dictionnaire contenant :
        - 'text'  : le texte normalise (str)
        - 'corrections' : liste des corrections effectuees
        - 'stats' : statistiques de l'etape

    Exemples :
        >>> result = fix_unicode("l\\u2019arr\\u00eaté")  # apostrophe typographique
        >>> result['text']  # inchange car U+2019 est deja standard
        "l\\u2019arrêté"

        >>> # Caractere cyrillique "а" (U+0430) au lieu de "a" latin
        >>> result = fix_unicode("\\u0430rticle 1er")
        >>> result['text']
        'article 1er'
    """
    corrections = []

    # =================================================================
    # Etape 1 : Normalisation NFC (Canonical Decomposition + Composition)
    # =================================================================
    # NFC est la forme recommandee pour le stockage et l'echange de
    # texte. Elle garantit que chaque caractere accentue est represente
    # par un seul code point quand c'est possible.
    #
    # Exemple :
    #   NFD : "é" = U+0065 (e) + U+0301 (accent aigu combine) = 2 code points
    #   NFC : "é" = U+00E9 (e accent aigu precompose) = 1 code point
    # =================================================================
    text_before_nfc = text
    text = unicodedata.normalize('NFC', text)

    if text != text_before_nfc:
        diff = _count_char_diff(text_before_nfc, text)
        corrections.append({
            "type": "nfc_normalization",
            "description": "Normalisation Unicode NFC ({} caract\u00e8re(s) recompos\u00e9(s))".format(diff),
            "count": diff,
        })

    # =================================================================
    # Etape 2 : Remplacement des homoglyphes
    # =================================================================
    # On parcourt le texte et remplace chaque caractere "imposteur"
    # par son equivalent standard. La regex pre-compilee assure
    # une bonne performance meme sur de gros documents.
    # =================================================================
    text_before_homoglyphs = text
    homoglyph_counts = {}

    def _replace_homoglyph(match):
        char = match.group(0)
        replacement = HOMOGLYPH_MAP[char]
        # Compter par type pour le rapport
        name = unicodedata.name(char, 'U+{:04X}'.format(ord(char)))
        homoglyph_counts[name] = homoglyph_counts.get(name, 0) + 1
        return replacement

    text = _HOMOGLYPH_PATTERN.sub(_replace_homoglyph, text)

    if text != text_before_homoglyphs:
        total_replaced = sum(homoglyph_counts.values())
        corrections.append({
            "type": "homoglyphs",
            "description": "Remplacement de {} homoglyphe(s) ({} type(s))".format(
                total_replaced, len(homoglyph_counts)
            ),
            "count": total_replaced,
        })

    # =================================================================
    # Etape 3 : Nettoyage des caracteres de formatage Unicode parasites
    # =================================================================
    # Certains caracteres de controle Unicode sont invisibles mais
    # perturbent le traitement (marques directionnelles, etc.)
    #
    # U+200E LEFT-TO-RIGHT MARK
    # U+200F RIGHT-TO-LEFT MARK
    # U+202A LEFT-TO-RIGHT EMBEDDING
    # U+202B RIGHT-TO-LEFT EMBEDDING
    # U+202C POP DIRECTIONAL FORMATTING
    # U+202D LEFT-TO-RIGHT OVERRIDE
    # U+202E RIGHT-TO-LEFT OVERRIDE
    # U+2066 LEFT-TO-RIGHT ISOLATE
    # U+2067 RIGHT-TO-LEFT ISOLATE
    # U+2068 FIRST STRONG ISOLATE
    # U+2069 POP DIRECTIONAL ISOLATE
    # =================================================================
    text_before_bidi = text
    text = re.sub(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]', '', text)

    if text != text_before_bidi:
        diff = len(text_before_bidi) - len(text)
        corrections.append({
            "type": "bidi_marks",
            "description": "Suppression de {} marque(s) directionnelle(s)".format(diff),
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


def _count_char_diff(a: str, b: str) -> int:
    """Compte le nombre de positions differentes entre deux chaines."""
    count = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            count += 1
    count += abs(len(a) - len(b))
    return count
