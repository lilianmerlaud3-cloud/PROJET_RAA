"""
Validateurs de structure juridique pour RAA-NORM.

Ce module fournit des fonctions de validation pour verifier
la coherence structurelle d'un arrete prefectoral apres
normalisation.

Validations effectuees :
    1. Sequence des articles (1, 2, 3... sans trou)
    2. Presence du titre de l'acte (ARRETE / DECIDE / ORDONNE)
    3. Equilibre des guillemets (« ... »)
    4. Presence d'au moins un visa (Vu)
"""

import re


# =================================================================
# BLOC : Patterns de detection
# =================================================================

RE_ARTICLE_NUM = re.compile(
    r'^(?:\s*)Article\s+(\d+|1er|unique)\s',
    re.MULTILINE
)

RE_TITLE = re.compile(
    r'^\s*(ARR[\u00ca\u00c9E]TE|D[\u00c9E]CIDE|ORDONNE)\s*$',
    re.MULTILINE | re.IGNORECASE
)

RE_VU = re.compile(r'^\s*Vu\b', re.MULTILINE)

RE_GUILLEMET_OPEN = re.compile(r'\u00ab')
RE_GUILLEMET_CLOSE = re.compile(r'\u00bb')


def validate_structure(text: str) -> dict:
    """
    Valide la structure d'un arrete prefectoral normalise.

    Retourne un dictionnaire avec :
        - 'valid'    : True si tout est coherent
        - 'errors'   : liste d'erreurs bloquantes
        - 'warnings' : liste d'avertissements non bloquants
        - 'info'     : informations de structure detectees
    """
    errors = []
    warnings = []
    info = {}

    # =================================================================
    # Validation 1 : Titre de l'acte
    # =================================================================
    title_match = RE_TITLE.search(text)
    if title_match:
        info['title'] = title_match.group(1).strip()
    else:
        warnings.append("Aucun titre d\u2019acte d\u00e9tect\u00e9 (ARR\u00caTE, D\u00c9CIDE, ORDONNE)")

    # =================================================================
    # Validation 2 : Sequence des articles
    # =================================================================
    articles = []
    for match in RE_ARTICLE_NUM.finditer(text):
        raw = match.group(1)
        if raw == '1er':
            articles.append(1)
        elif raw == 'unique':
            articles.append('unique')
        else:
            articles.append(int(raw))

    info['article_count'] = len(articles)

    if articles:
        if articles[0] == 'unique':
            # Article unique : pas de sequence a verifier
            info['article_type'] = 'unique'
        else:
            info['article_type'] = 'numbered'
            # Verifier la sequence
            expected = 1
            for i, num in enumerate(articles):
                if isinstance(num, int) and num != expected:
                    warnings.append(
                        "Rupture de s\u00e9quence\u00a0: article {} attendu, article {} trouv\u00e9".format(
                            expected, num
                        )
                    )
                if isinstance(num, int):
                    expected = num + 1

    # =================================================================
    # Validation 3 : Equilibre des guillemets
    # =================================================================
    open_count = len(RE_GUILLEMET_OPEN.findall(text))
    close_count = len(RE_GUILLEMET_CLOSE.findall(text))

    if open_count != close_count:
        warnings.append(
            "Guillemets d\u00e9s\u00e9quilibr\u00e9s\u00a0: {} ouvrants (\u00ab) vs {} fermants (\u00bb)".format(
                open_count, close_count
            )
        )

    info['guillemets'] = {'open': open_count, 'close': close_count}

    # =================================================================
    # Validation 4 : Presence de visas
    # =================================================================
    vu_count = len(RE_VU.findall(text))
    info['visa_count'] = vu_count

    if vu_count == 0:
        warnings.append("Aucun visa (Vu) d\u00e9tect\u00e9")

    # =================================================================
    # Resultat
    # =================================================================
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'info': info,
    }
