#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 15:10:32 2026

@author: clemenceneve
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List
import logging

# =============================================================
# CONFIGURATION DES LOGS
# =============================================================
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s | %(funcName)s | %(message)s"
)
log = logging.getLogger(__name__)

# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Arrete:
    """
    Représente un arrêté extrait du RAA.
    """

    index: int
    titre: str
    contenu: str
    score_validation: int


# ============================================================
# NORMALISATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Nettoie et normalise le texte OCR/PDF.

    Pourquoi ?
    ----------
    Les RAA issus d'OCR contiennent souvent :
    - des espaces multiples
    - des caractères Unicode incohérents
    - des retours chariot Windows
    - des sauts de ligne excessifs

    Cette étape améliore énormément la robustesse des regex.
    """

    # Normalisation unicode
    text = unicodedata.normalize("NFKC", text)

    # Uniformisation des retours ligne
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Suppression espaces multiples
    text = re.sub(r"[ \t]+", " ", text)

    # Réduction des lignes vides multiples
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# REGEX DE DÉTECTION DES ARRÊTÉS
# ============================================================

"""
IMPORTANT :
------------
On détecte UNIQUEMENT les titres plausibles d'arrêtés.

On veut éviter :
    "Vu l'arrêté du ..."
dans le corps du texte.

Donc :
- début de ligne obligatoire
- mot en majuscule
- structure administrative
"""

ARRETE_HEADER_REGEX = re.compile(
    r"""
    ^                           # Début de ligne obligatoire
    \s*                         # Espaces optionnels
    (
        ARR[ÊE]T[ÉE]            # ARRÊTÉ / ARRETE
        (?:
            \s+N[°º]?\s*\S+     # ARRÊTÉ N°2025-123
            |
            \s+DU\s+\d          # ARRÊTÉ DU 12 JANVIER
            |
            \s+PORTANT\b        # ARRÊTÉ PORTANT ...
            |
            \s+RELATIF\b        # ARRÊTÉ RELATIF ...
            |
            \s+FIXANT\b         # ARRÊTÉ FIXANT ...
            |
            \s*$                # ARRÊTÉ seul sur sa ligne (dispositif)
        )
    )
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE
)


# ============================================================
# VALIDATION HEURISTIQUE
# ============================================================

def compute_validation_score(segment: str) -> int:
    patterns = {
        "article":      r"Article\s+1",
        "vu":           r"^\s*Vu\b",
        "considerant":  r"Considérant",
        "prefet":       r"Préfet",
        "maire":        r"Maire",
        "arrete_verbe": r"^\s*ARR[ÊE]T[ÉE]\s*$",
        "signature":    r"Fait\s+[àa]\b",
    }

    score = 0
    for nom, pattern in patterns.items():
        if re.search(pattern, segment, re.IGNORECASE | re.MULTILINE):
            score += 1
            log.debug(f"  ✅ Pattern '{nom}' trouvé (+1)")
        else:
            log.debug(f"  ❌ Pattern '{nom}' absent")

    return score


def is_valid_arrete(segment: str, min_score: int = 2) -> bool:
    score = compute_validation_score(segment)

    if len(segment) < 300:
        log.debug(f"Segment rejeté : trop court ({len(segment)} chars < 300)")
        return False

    if score < min_score:
        log.debug(f"Segment rejeté : score {score} < {min_score}")
        return False

    log.debug(f"Segment accepté : score={score}, longueur={len(segment)}")
    return True


# ============================================================
# EXTRACTION DU TITRE
# ============================================================

def extract_title(segment: str) -> str:
    lines = segment.splitlines()

    for line in lines[:10]:
        cleaned = line.strip()
        if len(cleaned) > 10:
            log.debug(f"Titre extrait : '{cleaned[:80]}'")
            return cleaned

    log.warning("Titre non détecté dans les 10 premières lignes")
    return "TITRE_NON_DETECTE"



# ============================================================
# SEGMENTATION PRINCIPALE
# ============================================================

def split_arretes(text: str) -> List[Arrete]:
    """
    Fonction principale de segmentation.
    """
    log.info("=== Début split_arretes ===")

    text = normalize_text(text)

    matches = list(ARRETE_HEADER_REGEX.finditer(text))
    log.info(f"Nombre de headers détectés par regex : {len(matches)}")

    for i, m in enumerate(matches):
        log.debug(f"  Header #{i+1} à pos {m.start()} : '{m.group().strip()[:80]}'")

    arretes = []

    if not matches:
        log.warning("Aucun header d'arrêté détecté. Vérifiez la regex ou le contenu du fichier.")
        return arretes

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[start:end].strip()

        log.debug(f"\n--- Segment #{i+1} ---")
        log.debug(f"Position : {start} → {end} ({len(segment)} chars)")
        log.debug(f"Début : '{segment[:100]}'")

        score = compute_validation_score(segment)

        if not is_valid_arrete(segment):
            log.info(f"Segment #{i+1} ignoré (score={score}, longueur={len(segment)})")
            continue

        titre = extract_title(segment)

        arrete = Arrete(
            index=len(arretes) + 1,
            titre=titre,
            contenu=segment,
            score_validation=score
        )
        arretes.append(arrete)
        log.info(f"✅ Arrêté #{arrete.index} accepté : '{titre[:60]}' (score={score})")

    log.info(f"=== Fin split_arretes : {len(arretes)} arrêté(s) extrait(s) ===")
    return arretes


# ============================================================
# EXTRACTION ENTÊTE GLOBAL RAA
# ============================================================

def extract_header(text: str) -> str:
    """
    Extrait l'en-tête global du RAA.

    On prend tout ce qui précède :
    - le SOMMAIRE
    OU
    - le premier arrêté détecté
    """

    log.info("=== Début extract_header ===")

    # ========================================================
    # Cas 1 : découpe au SOMMAIRE
    # ========================================================

    sommaire_match = re.search(
        r"\bSOMMAIRE\b",
        text,
        re.IGNORECASE
    )

    if sommaire_match:

        header = text[:sommaire_match.start()].strip()

        log.info("En-tête détecté via SOMMAIRE")

        return header

    # ========================================================
    # Cas 2 : découpe au premier arrêté
    # ========================================================

    first_arrete = ARRETE_HEADER_REGEX.search(text)

    if first_arrete:

        header = text[:first_arrete.start()].strip()

        log.info("En-tête détecté via premier arrêté")

        return header

    # ========================================================
    # Fallback
    # ========================================================

    log.warning("Aucun en-tête détecté")

    return ""


# ============================================================
# EXTRACTION SOMMAIRE RAA
# ============================================================


def extract_sommaire(text: str) -> str:
    """
    Extrait le sommaire du RAA.

    On prend :
    - depuis 'SOMMAIRE'
    - jusqu'au premier arrêté détecté
    """

    log.info("=== Début extract_sommaire ===")

    sommaire_match = re.search(
        r"\bSOMMAIRE\b",
        text,
        re.IGNORECASE
    )

    if not sommaire_match:

        log.warning("Aucun SOMMAIRE détecté")

        return ""

    start = sommaire_match.start()

    # ========================================================
    # Recherche du premier arrêté APRÈS le sommaire
    # ========================================================

    first_arrete = ARRETE_HEADER_REGEX.search(
        text,
        pos=start
    )

    if first_arrete:

        end = first_arrete.start()

        sommaire = text[start:end].strip()

        log.info("Sommaire extrait avec succès")

        return sommaire

    # ========================================================
    # Fallback
    # ========================================================

    sommaire = text[start:].strip()

    log.warning(
        "Sommaire extrait sans fin détectée"
    )

    return sommaire

# ============================================================
# EXPORT
# ============================================================

def export_arretes(
    arretes: List[Arrete],
    source_text: str,
    output_dir="output"
):
    """
    Sauvegarde chaque arrêté dans un fichier texte
    avec l'en-tête complet du RAA.
    """

    from pathlib import Path

    log.info("=== Début export_arretes ===")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # ========================================================
    # Extraction de l'en-tête global
    # ========================================================

    header = extract_header(source_text)

    log.info("En-tête ajouté aux arrêtés")
    
    sommaire = extract_sommaire(source_text)
    
    log.info("Sommaire ajouté aux arrêtés")

    # ========================================================
    # Export des arrêtés
    # ========================================================

    for arrete in arretes:

        filename = f"arrete_{arrete.index:03d}.txt"

        filepath = output_path / filename

        contenu_final = (
            f"{header}\n\n"
            f"{sommaire}\n\n"
            f"{arrete.contenu}"
        )

        with open(filepath, "w", encoding="utf-8") as f:

            f.write(contenu_final)

        log.info(f"📄 Fichier écrit : {filepath}")

    log.info(
        f"=== Export terminé : "
        f"{len(arretes)} fichier(s) ==="
    )

    print(
        f"{len(arretes)} arrêtés exportés dans "
        f"'{output_dir}/'"
    )




