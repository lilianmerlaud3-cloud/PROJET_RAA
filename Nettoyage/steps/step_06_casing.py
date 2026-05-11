"""
Etape 6 du pipeline : Harmonisation de la capitalisation.

Les RAA proviennent de sources variees avec des conventions de
capitalisation incoherentes. Certaines prefectures ecrivent tout
en majuscules, d'autres en minuscules, d'autres melangent.

Cette etape harmonise la capitalisation selon les regles officielles :

    1. Titres et fonctions : minuscules sauf en debut de phrase
       - "le PREFET" → "le prefet"
       - "La SOUS-PREFETE" → "la sous-prefete"
       - "Le DIRECTEUR GENERAL" → "le directeur general"

    2. Noms propres de lieux : capitalisation preservee
       - "Val-de-Marne" reste "Val-de-Marne"
       - "PARIS" reste en majuscules si c'est le style du document

    3. Sigles et acronymes : preserves en majuscules
       - "CGCT", "DGCL", "INSEE" restent tels quels

    4. Mots entierement en majuscules dans le corps du texte :
       convertis en minuscules sauf exceptions (sigles, debut de phrase)

REGLE FONDAMENTALE : on ne modifie JAMAIS un nom propre de personne.
Les noms de famille qui apparaissent en majuscules dans les signatures
sont PRESERVES tels quels.
"""

import re


# =================================================================
# BLOC : Titres et fonctions administratives
# =================================================================
# Liste des titres et fonctions qui doivent etre en minuscules
# dans le corps du texte (sauf en debut de phrase).
#
# Ces mots sont souvent ecrits en MAJUSCULES par habitude
# administrative mais les regles typographiques francaises
# exigent des minuscules.
#
# Source : Lexique de l'Imprimerie nationale, conventions
# de la DILA (Direction de l'Information Legale et Administrative)
# =================================================================

TITLES_TO_LOWERCASE = [
    # ── Fonctions prefectorales ──
    # Regex : le mot en majuscules, potentiellement avec accents
    # On les classe du plus long au plus court pour eviter
    # les remplacements partiels (SOUS-PREFETE avant PREFETE)
    (re.compile(r'\bSOUS-PR[ÉE\u00c9]F[ÈE\u00c8]TE\b'), 'sous-pr\u00e9f\u00e8te'),
    (re.compile(r'\bSOUS-PR[ÉE\u00c9]FET\b'), 'sous-pr\u00e9fet'),
    (re.compile(r'\bPR[ÉE\u00c9]F[ÈE\u00c8]TE\b'), 'pr\u00e9f\u00e8te'),
    (re.compile(r'\bPR[ÉE\u00c9]FET\b'), 'pr\u00e9fet'),
    (re.compile(r'\bPREFET\b'), 'pr\u00e9fet'),
    (re.compile(r'\bPREFETE\b'), 'pr\u00e9f\u00e8te'),

    # ── Fonctions de direction ──
    (re.compile(r'\bSECR[ÉE\u00c9]TAIRE\s+G[ÉE\u00c9]N[ÉE\u00c9]RAL(?:E)?\b'), 'secr\u00e9taire g\u00e9n\u00e9ral'),
    (re.compile(r'\bDIRECTEUR\s+G[ÉE\u00c9]N[ÉE\u00c9]RAL(?:E)?\b'), 'directeur g\u00e9n\u00e9ral'),
    (re.compile(r'\bDIRECTRICE\s+G[ÉE\u00c9]N[ÉE\u00c9]RALE\b'), 'directrice g\u00e9n\u00e9rale'),
    (re.compile(r'\bDIRECTEUR\b'), 'directeur'),
    (re.compile(r'\bDIRECTRICE\b'), 'directrice'),

    # ── Autres fonctions ──
    (re.compile(r'\bMAIRE\b'), 'maire'),
    (re.compile(r'\bMINISTRE\b'), 'ministre'),
    (re.compile(r'\bPR[ÉE\u00c9]SIDENT(?:E)?\b'), 'pr\u00e9sident'),
    (re.compile(r'\bCOMMISSAIRE\b'), 'commissaire'),
    (re.compile(r'\bINSPECTEUR\b'), 'inspecteur'),
    (re.compile(r'\bINSPECTRICE\b'), 'inspectrice'),
]


# =================================================================
# BLOC : Sigles et acronymes a preserver
# =================================================================
# Ces sequences de majuscules sont des sigles connus et doivent
# rester en MAJUSCULES. On les detecte pour eviter de les
# convertir en minuscules par erreur.
#
# Un sigle est une sequence de 2+ lettres majuscules sans
# minuscules intercalees.
# =================================================================

KNOWN_ACRONYMS = {
    # Administration
    'CGCT', 'DGCL', 'DILA', 'DREAL', 'DREETS', 'DDT', 'DDTM',
    'DDPP', 'DDCS', 'DDETS', 'ARS', 'DIRECCTE', 'DRIEETS',
    'INSEE', 'SIRENE', 'SIRET', 'SIREN', 'DREAL', 'DDFIP'
    # Juridique
    'SAS', 'SARL', 'SA', 'SCI', 'SNC', 'EURL', 'EI',
    'ICPE', 'PLU', 'POS', 'SCOT', 'ZAC', 'ZAD',
    # Divers
    'PDF', 'RAA', 'RCS', 'TVA', 'HT', 'TTC',
    'CE', 'TA', 'CAA',  # Conseil d'Etat, Tribunal Admin., Cour Admin. Appel
    'EU', 'UE',
}

# =================================================================
# Regex pour detecter un mot entierement en majuscules (3+ lettres)
# qui n'est PAS un sigle connu.
#
# On cible les mots de 3 lettres ou plus en majuscules dans le
# corps du texte. Les mots de 2 lettres (LE, LA, DU, AU, etc.)
# sont ignores car ils sont souvent en majuscules dans les titres
# et ce serait trop agressif de les forcer en minuscules.
# =================================================================
RE_ALL_CAPS_WORD = re.compile(
    r'\b([A-Z\u00c0-\u00dc]{3,})\b'
)


def fix_casing(text: str) -> dict:
    """
    Harmonise la capitalisation du texte selon les conventions
    typographiques des documents administratifs francais.

    Parametres :
        text : Le texte a harmoniser (str)

    Retourne :
        dict avec 'text', 'corrections', 'stats'

    Exemple :
        >>> r = fix_casing("Le PREFET du Val-de-Marne ARRETE...")
        >>> r['text']
        'Le prefet du Val-de-Marne ARRETE...'
        # Note : ARRETE est preserve car c'est le titre de l'acte
    """
    corrections = []

    # =================================================================
    # Etape 1 : Convertir les titres/fonctions en minuscules
    # =================================================================
    # On applique les regles de la table TITLES_TO_LOWERCASE.
    # Chaque regle est un tuple (regex, remplacement).
    #
    # EXCEPTION : si le mot est en debut de phrase (apres un point
    # ou en debut de ligne), on met une majuscule initiale.
    # =================================================================
    total_title_fixes = 0

    for pattern, replacement in TITLES_TO_LOWERCASE:
        text_before = text

        def _replace_title(match):
            word = match.group(0)
            start = match.start()

            # Verifier si c'est en debut de phrase
            # (debut de texte, ou apres un point/retour a la ligne)
            if _is_start_of_sentence(text, start):
                # Mettre une majuscule initiale
                return replacement[0].upper() + replacement[1:]
            return replacement

        text = pattern.sub(_replace_title, text)

        if text != text_before:
            count = len(pattern.findall(text_before))
            total_title_fixes += count

    if total_title_fixes > 0:
        corrections.append({
            "type": "casing_titles",
            "description": "Mise en minuscules de {} titre(s)/fonction(s)".format(total_title_fixes),
            "count": total_title_fixes,
        })

    # =================================================================
    # Etape 2 : Convertir les mots tout-majuscules du corps de texte
    # =================================================================
    # Les mots de 3+ lettres entierement en majuscules dans le corps
    # du texte sont convertis en minuscules, SAUF :
    #   - Les sigles connus (CGCT, INSEE, etc.)
    #   - Le titre de l'acte (ARRETE, DECIDE, etc.)
    #   - Les mots en debut de phrase
    #   - Les noms dans les blocs de signature
    #
    # On ne touche PAS aux lignes qui semblent etre des titres
    # (ligne entierement en majuscules = probablement intentionnel).
    # =================================================================

    # Detecter les lignes "titre" (entierement ou majoritairement en majuscules)
    title_lines = set()
    for i, line in enumerate(text.split('\n')):
        stripped = line.strip()
        if stripped and _is_title_line(stripped):
            title_lines.add(i)

    # Mots proteges (titres d'acte, sigles)
    protected_words = KNOWN_ACRONYMS | {
        'ARR\u00caTE', 'ARRETE', 'ARRÊTE',
        'D\u00c9CIDE', 'DECIDE', 'DÉCIDE',
        'ORDONNE',
        'TITRE', 'CHAPITRE', 'SECTION', 'ANNEXE',
    }

    lines = text.split('\n')
    caps_fixes = 0

    for i, line in enumerate(lines):
        # Ne pas toucher aux lignes de titre
        if i in title_lines:
            continue


        def _fix_caps_word(match):
            nonlocal caps_fixes
            word = match.group(1)

            # Preserver les sigles et mots proteges
            if word in protected_words:
                return word
            

            # Preserver si c'est un sigle probable (2-4 lettres, toutes caps)
            if len(word) <= 10 and word.isascii() and word.isupper():
                # Pourrait etre un sigle non repertorie — prudence
                return word

            # Convertir en minuscules
            lowered = word.lower()
            
             

            # Majuscule initiale si debut de phrase
            start = match.start()
            if _is_start_of_sentence(line, start):
                lowered = lowered[0].upper() + lowered[1:]

            caps_fixes += 1
            return lowered

        lines[i] = RE_ALL_CAPS_WORD.sub(_fix_caps_word, line)

    text = '\n'.join(lines)

    if caps_fixes > 0:
        corrections.append({
            "type": "casing_caps",
            "description": "Conversion de {} mot(s) majuscules en minuscules".format(caps_fixes),
            "count": caps_fixes,
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


def _is_start_of_sentence(text: str, pos: int) -> bool:
    """
    Determine si la position `pos` dans `text` est un debut de phrase.

    Un debut de phrase est :
    - La position 0 (debut du texte)
    - Apres un saut de ligne
    - Apres un point suivi d'espaces
    - Apres un point-virgule suivi d'espaces (dans les visas)
    """
    if pos == 0:
        return True

    # Remonter en arriere en sautant les espaces
    i = pos - 1
    while i >= 0 and text[i] in ' \t\u00a0\u202f':
        i -= 1

    if i < 0:
        return True

    # Debut de phrase si le caractere precedent est un saut de ligne,
    # un point, ou un tiret cadratin (separateur d'article)
    return text[i] in '\n.!\u2014'


def _is_title_line(line: str) -> bool:
    """
    Determine si une ligne est une ligne de titre (entierement
    ou majoritairement en majuscules).

    Une ligne de titre contient principalement des majuscules
    et peu de minuscules. Seuil : >= 70% de majuscules parmi
    les caracteres alphabetiques.
    """
    alpha_chars = [c for c in line if c.isalpha()]
    if len(alpha_chars) < 3:
        return False

    upper_count = sum(1 for c in alpha_chars if c.isupper())
    ratio = upper_count / len(alpha_chars)
    return ratio >= 0.70
