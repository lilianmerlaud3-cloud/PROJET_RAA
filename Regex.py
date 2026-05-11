import re
import json
 
# ─────────────────────────────────────────────
# Patterns de détection
# ─────────────────────────────────────────────
PATTERNS = {
    "fonction_auteur": r"(?i)sign[ée]\s*:\s*(.+?)(?=\s*:)",
    "date_acte": r"(?:du|en date du|signé le)\s+(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
    "base_legale": r"[Vv]u\s+(.+?)(?=\n\s*\n|\n[A-Z]|\Z)",
    "objet_large": r"[Aa]rr[eê]t[eé]\s+n[°o]?\s*[\w\-]+\s+du\s+[^\n]+?portant\s+(.*)",
    "prefecture": r"((?:SOUS[- ]?)?PREFECTURE\s+D(?:E|U|['’])\s+[A-Z\- ]+?)(?=\.{3}|\n|$)",
    "numero_acte": r"\b(?:n°\s*)?(\d{4}[/\-]\d{2,4}(?:[/\-]\d{2,4})?|\d{2}[/\-]\d{4}[/\-]\d{3})\b",
}
 
# Balises XML pour chaque champ
TAG_MAP = {
    "fonction_auteur": "FONCTION_AUTEUR",
    "date_acte":       "DATE_ACTE",
    "base_legale":     "BASE_LEGALE",
    "objet_large":     "OBJET",
    "prefecture":      "PREFECTURE",
    "numero_acte":     "NUMERO_ACTE",
}
 
# ─────────────────────────────────────────────
# Extraction des valeurs
# ─────────────────────────────────────────────
def extraire_valeurs(texte: str) -> dict:
    resultats = {}
    for champ, pattern in PATTERNS.items():
        flags = re.DOTALL if champ == "base_legale" else 0
        match = re.search(pattern, texte, flags)
        if match:
            valeur = match.group(1).strip()
            resultats[champ] = valeur
        else:
            resultats[champ] = None
    return resultats
 
# ─────────────────────────────────────────────
# Construction d'un objet JSON pour un arrêté
# ─────────────────────────────────────────────
def construire_objet_arrete(index: int, texte_bloc: str, resultats: dict) -> dict:
    """Construit un dictionnaire structuré représentant un arrêté."""
    return {
        "id":             index + 1,
        "numero_acte":    resultats.get("numero_acte"),
        "date":           resultats.get("date_acte"),
        "prefecture":     resultats.get("prefecture"),
        "auteur":         resultats.get("fonction_auteur"),
        "objet":          resultats.get("objet_large"),
        "base_legale":    resultats.get("base_legale"),
        "contenu":        texte_bloc.strip(),  # ← Texte intégral du bloc
    }
 
# ─────────────────────────────────────────────
# Balisage dans le texte original
# ─────────────────────────────────────────────
def baliser_texte(texte: str, resultats: dict) -> str:
    texte_balise = texte
    for champ, valeur in resultats.items():
        if not valeur:
            continue
        tag = TAG_MAP[champ]
        valeur_escaped = re.escape(valeur)
        texte_balise = re.sub(
            valeur_escaped,
            f"<{tag}>{valeur}</{tag}>",
            texte_balise,
            count=1
        )
    return texte_balise
 
# ─────────────────────────────────────────────
# Rapport structuré (console)
# ─────────────────────────────────────────────
def afficher_rapport(index: int, resultats: dict):
    print(f"\n{'='*60}")
    print(f"  ARRÊTÉ N°{index + 1} — RAPPORT D'EXTRACTION")
    print("="*60)
    for champ, valeur in resultats.items():
        tag = TAG_MAP[champ]
        print(f"\n[{tag}]")
        if valeur:
            print(f"  → {valeur}")
        else:
            print("  → (non trouvé)")
    print("="*60 + "\n")
 

# ─────────────────────────────────────────────
# Lecture du fichier source
# ─────────────────────────────────────────────
with open("arrete_083.txt", encoding="utf-8") as f:
    TEXTE = f.read()
 
# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print("\n📄 1 acte détecté.\n")

    # Extraction directe sur tout le texte
    resultats = extraire_valeurs(TEXTE)

    # Affichage console
    afficher_rapport(0, resultats)

    # Construction JSON
    arrete_obj = construire_objet_arrete(0, TEXTE, resultats)

    sortie_json = {
        "source": "arrete_083.txt",
        "total_arretes": 1,
        "arretes": [arrete_obj],
    }

    with open("arretes.json", "w", encoding="utf-8") as f:
        json.dump(sortie_json, f, ensure_ascii=False, indent=2)

    print("✔ Fichier 'arretes.json' généré.")

    # Texte balisé
    texte_balise = baliser_texte(TEXTE, resultats)

    with open("acte_balise.txt", "w", encoding="utf-8") as f:
        f.write(texte_balise)

    print("✔ Fichier 'acte_balise.txt' généré.")

   