"""
Moteur de diff pour RAA-NORM.

Ce module genere un diff colore entre le texte original et le texte
corrige, au format HTML. Le diff est envoye via WebSocket au frontend
pour un affichage en temps reel.

Le diff est calcule ligne par ligne avec difflib, puis enrichi
d'informations sur le type de correction (encodage, typo, structure...).
"""

import difflib
import json


def compute_diff(original: str, corrected: str, step_name: str = "") -> list[dict]:
    """
    Calcule un diff ligne par ligne entre deux textes.

    Parametres :
        original  : Texte avant correction
        corrected : Texte apres correction
        step_name : Nom de l'etape du pipeline (pour l'etiquette)

    Retourne :
        Liste de dictionnaires, chacun representant une ligne modifiee :
        {
            "line": numero_de_ligne,
            "type": "replace" | "insert" | "delete",
            "before": texte_original,
            "after": texte_corrige,
            "step": nom_etape
        }
    """
    diff_entries = []

    original_lines = original.splitlines(keepends=True)
    corrected_lines = corrected.splitlines(keepends=True)

    # =================================================================
    # Utiliser SequenceMatcher de difflib pour trouver les differences.
    # get_opcodes() retourne des tuples (tag, i1, i2, j1, j2) :
    #   - 'equal'   : les lignes i1:i2 et j1:j2 sont identiques
    #   - 'replace' : les lignes i1:i2 ont ete remplacees par j1:j2
    #   - 'insert'  : des lignes j1:j2 ont ete inserees
    #   - 'delete'  : les lignes i1:i2 ont ete supprimees
    # =================================================================
    matcher = difflib.SequenceMatcher(
        None, original_lines, corrected_lines, autojunk=False
    )

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        if tag == 'replace':
            # ==========================================================
            # Remplacement : on associe les lignes une a une
            # S'il y a plus de lignes d'un cote, les extras sont
            # traitees comme des insertions ou suppressions.
            # ==========================================================
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                entry = {
                    "line": i1 + k + 1,
                    "type": "replace",
                    "before": original_lines[i1 + k].rstrip('\n') if i1 + k < i2 else "",
                    "after": corrected_lines[j1 + k].rstrip('\n') if j1 + k < j2 else "",
                    "step": step_name,
                }
                diff_entries.append(entry)

        elif tag == 'insert':
            for k in range(j1, j2):
                diff_entries.append({
                    "line": i1 + 1,
                    "type": "insert",
                    "before": "",
                    "after": corrected_lines[k].rstrip('\n'),
                    "step": step_name,
                })

        elif tag == 'delete':
            for k in range(i1, i2):
                diff_entries.append({
                    "line": k + 1,
                    "type": "delete",
                    "before": original_lines[k].rstrip('\n'),
                    "after": "",
                    "step": step_name,
                })

    return diff_entries


def diff_to_json(diff_entries: list[dict]) -> str:
    """Serialise les entrees diff en JSON pour envoi WebSocket."""
    return json.dumps(diff_entries, ensure_ascii=False)
