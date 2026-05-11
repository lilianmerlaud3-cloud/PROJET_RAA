"""
Etape 1 du pipeline : Correction d'encodage et reparation mojibake.

Cette etape est la premiere et la plus critique du pipeline.
Les RAA proviennent de sources multiples (PDF, OCR, Word, web)
et souffrent frequemment de problemes d'encodage :

1. Mojibake : du texte UTF-8 mal interprete en Latin-1/Windows-1252
   Exemple : "ArrÃªtÃ©" au lieu de "Arrete"
   Cause : un fichier UTF-8 ouvert comme s'il etait en Latin-1

2. Double encodage : le texte a ete converti deux fois

3. Caracteres de remplacement : U+FFFD ou '?' insertes lors d'une
   conversion ratee

La bibliotheque ftfy (fixes text for you) est specialisee dans
la detection et la reparation automatique de ces problemes.
"""

import re
import ftfy


# =================================================================
# BLOC : Nettoyage des caracteres de controle
# =================================================================
# Les fichiers OCR et les copier-coller depuis PDF contiennent
# parfois des caracteres de controle invisibles qui perturbent
# le traitement. On les supprime, sauf les retours a la ligne
# et les tabulations.
#
# Regex expliquee :
#   [\x00-\x08]   : caracteres de controle 0 a 8 (NUL, SOH, etc.)
#   [\x0b]         : tabulation verticale
#   [\x0e-\x1f]   : caracteres de controle 14 a 31
#   [\x7f]         : DEL (delete)
#
# On preserve :
#   \x09 = tabulation horizontale (TAB)
#   \x0a = saut de ligne (LF)
#   \x0d = retour chariot (CR)
# =================================================================
RE_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0e-\x1f\x7f]')


def fix_encoding(text: str) -> dict:
    """
    Corrige les problemes d'encodage et de mojibake dans un texte.

    Cette fonction est la premiere etape du pipeline. Elle :
    1. Applique ftfy pour reparer automatiquement le mojibake
    2. Supprime les caracteres de controle parasites
    3. Normalise les fins de ligne en LF (Unix)
    4. Reduit les lignes vides excessives

    Parametres :
        text : Le texte brut (deja decode en str Python)

    Retourne :
        Un dictionnaire contenant :
        - 'text'  : le texte corrige (str)
        - 'corrections' : liste des corrections effectuees
        - 'stats' : statistiques de l'etape

    Exemple :
        >>> result = fix_encoding("Arr\\xc3\\xaatÃ© prÃ©fectoral")
        >>> # ftfy corrige automatiquement le mojibake
    """
    corrections = []
    original = text

    # =================================================================
    # Etape 1 : Reparation automatique avec ftfy
    # =================================================================
    # ftfy detecte et corrige automatiquement les patterns de mojibake
    # les plus courants. C'est notre premiere ligne de defense.
    #
    # Options :
    #   fix_encoding=True    : reparer le mojibake
    #   fix_entities=True    : convertir &amp; -> &, etc.
    #   fix_latin_ligatures=False : garder les ligatures (oe, ae)
    #   fix_character_width=True : normaliser les caracteres pleine largeur
    #   uncurl_quotes=False  : on garde les guillemets typographiques
    #   fix_line_breaks=True : normaliser les retours a la ligne
    # =================================================================
    text = ftfy.fix_text(
        text,
        fix_encoding=True,
        fix_entities=True,
        fix_latin_ligatures=False,
        fix_character_width=True,
        uncurl_quotes=False,
        fix_line_breaks=True,
    )

    if text != original:
        corrections.append({
            "type": "ftfy_auto",
            "description": "R\u00e9paration automatique mojibake (ftfy)",
            "count": _count_differences(original, text),
        })

    # =================================================================
    # Etape 2 : Nettoyage du caractere "Â" isole
    # =================================================================
    # Apres la correction ftfy, il reste parfois des "Â" isoles
    # qui sont des artefacts de double encodage. On les supprime
    # uniquement quand ils apparaissent devant un espace insecable
    # ou seuls (pas dans un mot).
    #
    # Pattern : "\u00c2" suivi d'un espace ou d'un caractere special
    # =================================================================
    text_before_cleanup = text
    # "Â " (Â + espace insecable U+00A0 mal decode) -> espace insecable
    text = text.replace('\u00c2\u00a0', '\u00a0')
    # "Â" isole (suivi d'un espace normal) -> supprime
    text = re.sub(r'\u00c2(?=\s)', '', text)
    if text != text_before_cleanup:
        diff = _count_differences(text_before_cleanup, text)
        if diff > 0:
            corrections.append({
                "type": "cleanup_artefacts",
                "description": "Nettoyage artefacts d'encodage r\u00e9siduels",
                "count": diff,
            })
            
    # =================================================================
    # Etape 2 bis : Suppression des caracteres corrompus (�, �, etc.)
    # =================================================================
    # Certains caracteres ne peuvent pas etre recuperes (perte definitive
    # lors d'un mauvais encodage). Ils apparaissent sous forme de :
    #
    #   - U+FFFD : caractere de remplacement Unicode "�"
    #   - Symboles inconnus affiches comme "?" dans un carre
    #
    # On les supprime ou remplace proprement pour eviter de polluer
    # le texte final.
    # =================================================================
    
    text_before_corrupted = text
    
    # Supprimer le caractere de remplacement Unicode
    text = text.replace('\uFFFD', '')
    
    # Supprimer variantes visibles possibles
    text = text.replace('�', '')
    
    # Normalisation de quelques caracteres frequents (optionnel mais utile RAA)
    replacements = {
        '\u2019': "'",   # apostrophe typographique
        '\u2018': "'",
        '\u201c': '"',   # guillemets
        '\u201d': '"',
        '\u2013': '-',   # tiret long
        '\u2014': '-',
    }
    
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    if text != text_before_corrupted:
        diff = _count_differences(text_before_corrupted, text)
        if diff > 0:
            corrections.append({
                "type": "corrupted_chars",
                "description": "Suppression / normalisation des caracteres corrompus",
                "count": diff,
            })

    
    # =================================================================
    # Etape 2 ter : Suppression des glyphes non Unicode standards
    # =================================================================
    # Certains PDF injectent des caracteres issus de zones privees Unicode
    # (Private Use Area) ou des symboles inutilisables (ex: ).
    # On les supprime.
    # =================================================================
    
    text_before_private = text
    
    # Supprimer les caracteres de la Private Use Area (PUA)
    # U+E000 à U+F8FF
    text = re.sub(r'[\uE000-\uF8FF]', '', text)
    
    # Supprimer les symboles "bizarres" fréquents (ex: , , )
    # (souvent dans les plages suivantes)
    text = re.sub(r'[\uF000-\uF0FF]', '', text)
    
    # Optionnel : supprimer les caractères non imprimables restants
    text = re.sub(r'[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF\n\t]', '', text)
    
    if text != text_before_private:
        diff = _count_differences(text_before_private, text)
        if diff > 0:
            corrections.append({
                "type": "private_unicode",
                "description": "Suppression des glyphes non standards (PUA, symboles PDF)",
                "count": diff,
            })
    

    # =================================================================
    # Etape 3 : Suppression des caracteres de controle
    # =================================================================
    cleaned = RE_CONTROL_CHARS.sub('', text)
    if cleaned != text:
        diff_count = len(text) - len(cleaned)
        corrections.append({
            "type": "control_chars",
            "description": "Suppression de {} caract\u00e8re(s) de contr\u00f4le".format(diff_count),
            "count": diff_count,
        })
        text = cleaned

    # =================================================================
    # Etape 4 : Normalisation des fins de ligne
    # =================================================================
    # Les fichiers Windows utilisent \r\n (CRLF), Mac classique \r (CR),
    # Unix/Mac moderne \n (LF). On unifie tout en LF.
    # =================================================================
    text_before_crlf = text
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if text != text_before_crlf:
        corrections.append({
            "type": "line_endings",
            "description": "Normalisation des fins de ligne en LF",
            "count": 1,
        })

    # =================================================================
    # Etape 5 : Supprimer les lignes vides excessives
    # =================================================================
    # Les RAA issus de PDF contiennent souvent des dizaines de lignes
    # vides consecutives. On les reduit a maximum 2.
    # =================================================================
    text_before_blank = text
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    if text != text_before_blank:
        corrections.append({
            "type": "blank_lines",
            "description": "R\u00e9duction des lignes vides excessives",
            "count": 1,
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


def _count_differences(a: str, b: str) -> int:
    """
    Compte approximativement le nombre de caracteres differents
    entre deux chaines. Utilise pour les statistiques.
    """
    count = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            count += 1
    count += abs(len(a) - len(b))
    return count

