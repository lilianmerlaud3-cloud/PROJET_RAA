"""
Detecteur d'encodage multi-strategie pour RAA-NORM.

Ce module detecte l'encodage d'un fichier texte brut en combinant
plusieurs strategies. Les RAA francais proviennent de sources
variees (scans OCR, copier-coller de PDF, exports Word) et
arrivent souvent en Latin-1, Windows-1252, ou UTF-8 casse.

Strategie de detection :
    1. Verifier la presence d'un BOM (Byte Order Mark) UTF-8/UTF-16
    2. Tenter un decodage UTF-8 strict (le plus courant aujourd'hui)
    3. Utiliser charset-normalizer pour une detection statistique
    4. En dernier recours, supposer Windows-1252 (courant en France)
"""

from charset_normalizer import from_bytes


def detect_encoding(raw_bytes: bytes) -> str:
    """
    Detecte l'encodage d'un contenu binaire.

    Parametres :
        raw_bytes : Le contenu brut du fichier (bytes)

    Retourne :
        Le nom de l'encodage detecte (str), par exemple 'utf-8',
        'windows-1252', 'iso-8859-1', etc.

    Exemples :
        >>> detect_encoding(b'Arr\\xc3\\xaat\\xc3\\xa9')   # UTF-8 valide
        'utf-8'
        >>> detect_encoding(b'Arr\\xeat\\xe9')              # Latin-1
        ... # retourne 'windows-1252' ou 'iso-8859-1'
    """

    # =================================================================
    # Strategie 1 : Verifier le BOM (Byte Order Mark)
    # Le BOM est une sequence d'octets en debut de fichier qui indique
    # explicitement l'encodage. C'est la detection la plus fiable.
    #
    #   BOM UTF-8    : EF BB BF (3 octets)
    #   BOM UTF-16 LE: FF FE    (2 octets, little-endian)
    #   BOM UTF-16 BE: FE FF    (2 octets, big-endian)
    # =================================================================
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    if raw_bytes.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if raw_bytes.startswith(b'\xfe\xff'):
        return 'utf-16-be'

    # =================================================================
    # Strategie 2 : Tenter un decodage UTF-8 strict
    # Si le fichier se decode sans erreur en UTF-8, c'est tres
    # probablement du UTF-8. C'est le cas le plus frequent pour
    # les fichiers recents.
    # =================================================================
    try:
        raw_bytes.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    # =================================================================
    # Strategie 3 : Detection statistique avec charset-normalizer
    # La bibliotheque analyse la distribution des octets et compare
    # avec des modeles statistiques de langues. On demande un
    # resultat pour le francais en priorite.
    # =================================================================
    results = from_bytes(raw_bytes)
    best = results.best()

    if best is not None:
        encoding = best.encoding
        # =============================================================
        # Normaliser les noms d'encodage :
        #   - 'iso-8859-1' et 'latin-1' sont equivalents
        #   - En pratique, les fichiers francais etiquetes 'iso-8859-1'
        #     utilisent souvent des caracteres Windows-1252 (guillemets
        #     typographiques, tirets cadratins, etc.)
        # =============================================================
        if encoding.lower() in ('iso-8859-1', 'latin-1', 'iso8859-1'):
            return 'windows-1252'
        return encoding.lower()

    # =================================================================
    # Strategie 4 : Dernier recours — Windows-1252
    # C'est l'encodage le plus courant pour les documents francais
    # provenant de systemes Windows (Word, Acrobat, etc.)
    # =================================================================
    return 'windows-1252'


def decode_bytes(raw_bytes: bytes) -> tuple[str, str]:
    """
    Decode un contenu binaire en texte Unicode.

    Parametres :
        raw_bytes : Le contenu brut (bytes)

    Retourne :
        Un tuple (texte_decode, encodage_detecte)

    Exemple :
        >>> text, enc = decode_bytes(b'Arr\\xeat\\xe9')
        >>> text
        'Arrte'  # ... en windows-1252
        >>> enc
        'windows-1252'
    """
    encoding = detect_encoding(raw_bytes)

    # =================================================================
    # Decoder avec l'encodage detecte.
    # En cas d'erreur (fichier corrompu), on remplace les caracteres
    # invalides par le caractere de remplacement Unicode U+FFFD.
    # =================================================================
    text = raw_bytes.decode(encoding, errors='replace')

    # =================================================================
    # Retirer le BOM s'il est present dans le texte decode
    # (le BOM UTF-8 se decode en U+FEFF, un espace insecable
    # de largeur nulle qui peut perturber le traitement)
    # =================================================================
    if text.startswith('\ufeff'):
        text = text[1:]

    return text, encoding
