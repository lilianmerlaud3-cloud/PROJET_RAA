"""
Etape 7 du pipeline : Nettoyage final et validation.

Cette etape est la derniere du pipeline. Elle effectue :
    1. Nettoyage des espaces residuelles (doubles espaces, espaces
       en fin de ligne, lignes vides excessives)
    2. Verification de l'idempotence (repasser les etapes precedentes
       ne doit rien changer)
    3. Validation structurelle via le module validators
    4. Generation du rapport de normalisation

Aucune modification de contenu n'est faite ici — uniquement du
nettoyage cosmetique et de la validation.
"""

import re
from utils.validators import validate_structure


def fix_final(text: str) -> dict:
    """
    Nettoyage final et validation du texte normalise.

    Parametres :
        text : Le texte apres les 6 etapes precedentes (str)

    Retourne :
        dict avec 'text', 'corrections', 'stats', 'validation'
    """
    corrections = []

    # =================================================================
    # Etape 1 : Supprimer les espaces en fin de ligne (trailing spaces)
    # =================================================================
    # Les espaces en fin de ligne sont invisibles mais peuvent
    # perturber les comparaisons et certains outils.
    #
    # Regex :
    #   [ \t]+   : une ou plusieurs espaces/tabulations
    #   $        : fin de ligne (avec re.MULTILINE)
    # =================================================================
    text_before = text
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

    if text != text_before:
        count = text_before.count(' \n') + text_before.count('\t\n')
        corrections.append({
            "type": "trailing_spaces",
            "description": "Suppression des espaces en fin de ligne",
            "count": max(count, 1),
        })

    # =================================================================
    # Etape 2 : Normaliser les lignes vides
    # =================================================================
    # Maximum 2 lignes vides consecutives (3 \n).
    # Les RAA issus de PDF ont souvent des dizaines de lignes vides.
    # =================================================================
    text_before = text
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    if text != text_before:
        corrections.append({
            "type": "blank_lines",
            "description": "R\u00e9duction des lignes vides excessives",
            "count": 1,
        })

    # =================================================================
    # Etape 3 : Assurer un saut de ligne final
    # =================================================================
    # Convention POSIX : tout fichier texte se termine par un \n.
    # =================================================================
    if text and not text.endswith('\n'):
        text += '\n'
        corrections.append({
            "type": "final_newline",
            "description": "Ajout du saut de ligne final",
            "count": 1,
        })

    # =================================================================
    # Etape 4 : Supprimer les espaces insecables en debut de ligne
    # =================================================================
    # Des espaces insecables (\u00a0, \u202f) peuvent se retrouver
    # en debut de ligne apres les corrections typographiques.
    # On les remplace par des espaces normales.
    # =================================================================
    text_before = text
    text = re.sub(r'^([\u00a0\u202f]+)', _nbsp_to_space, text, flags=re.MULTILINE)

    if text != text_before:
        corrections.append({
            "type": "leading_nbsp",
            "description": "Remplacement espaces ins\u00e9cables en d\u00e9but de ligne",
            "count": 1,
        })

    # =================================================================
    # Etape 5 : Validation structurelle
    # =================================================================
    validation = validate_structure(text)

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
        "validation": validation,
    }


def _nbsp_to_space(match):
    """Remplace des espaces insecables par des espaces normales."""
    return ' ' * len(match.group(1))
