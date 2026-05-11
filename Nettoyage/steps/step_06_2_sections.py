"""
Etape 6 du pipeline : Segmentation structurelle d'un arrêté préfectoral.

Un arrêté préfectoral suit toujours cette structure juridique canonique :

    1. ENTETE        → Identification de l'autorité (préfecture, service...)
    2. TITRE         → Objet de l'arrêté
    3. VISAS         → Références légales commençant par "Vu..."
    4. CONSIDERANTS  → Motifs commençant par "Considérant...", "Attendu..."
    5. DISPOSITIF    → Le mot "ARRÊTE" / "DÉCIDE" seul sur sa ligne
    6. ARTICLES      → Les articles numérotés (Article 1, Article 2...)
    7. ANNEXES       → Sections commençant par "ANNEXE"
    8. SIGNATURE     → Formule finale + lieu + date + signataires

Principe fondamental : on ne modifie JAMAIS le contenu,
on attribue uniquement un label à chaque bloc détecté.
"""

import re

# =================================================================
# BLOC : Définition des sections possibles
# =================================================================

SECTIONS = [
    "ENTETE",
    "TITRE",
    "VISAS",
    "CONSIDERANTS",
    "DISPOSITIF",
    "ARTICLES",
    "ANNEXES",
    "SIGNATURE",
    "INCONNU",
]

# =================================================================
# BLOC : Patterns de détection des frontières de sections
# =================================================================

RE_VISA_START = re.compile(
    r'^\s*(?:VU|Vu|vu)\b',
    re.MULTILINE
)

RE_CONSIDERANT_START = re.compile(
    r'^\s*(?:CONSID[ÉEe]RANT|Consid[ée]rant|ATTENDU|Attendu)\b',
    re.MULTILINE
)

RE_DISPOSITIF = re.compile(
    r'^\s*(?:ARR[ÊE]T[ÉE]|D[ÉE]CIDE|ORDONNE)\s*$',
    re.IGNORECASE | re.MULTILINE
)

RE_ARTICLE_START = re.compile(
    r'^\s*(?:ARTICLE|Article|Art\.?)\s*(?:\d+|PREMIER|premier|UNIQUE|unique)',
    re.MULTILINE
)

RE_ANNEXE_START = re.compile(
    r'^\s*ANNEXE\b',
    re.IGNORECASE | re.MULTILINE
)

RE_SIGNATURE_START = re.compile(
    r'''^\s*(?:
        Fait\s+[àa]\b |
        Pour\s+le\s+[Pp]r[ée]fet |
        Le\s+[Pp]r[ée]fet |
        P\.?\s*O\.?\b |
        Par\s+délégation |
        Sign[ée]?\b |                # signé / signe / signée
        Signature[s]?\b              # signature / signatures
    )''',
    re.MULTILINE | re.VERBOSE | re.IGNORECASE
)

    


# =================================================================
# FONCTION PRINCIPALE
# =================================================================

def segment_arrete(text: str) -> dict:
    """
    Segmente un arrêté préfectoral en sections nommées.

    Paramètres :
        text : Le texte nettoyé de l'arrêté (str)

    Retourne :
        dict avec :
            - 'segments' : liste de dicts {label, content, start, end}
            - 'stats'    : statistiques de segmentation
            - 'success'  : True si les sections clés ont été trouvées
    """
    RE_SIGNATURE = re.compile(r'\b(SIGN[ÉE]|SIGNE|SIGNÉE)\b', re.I)
    
    lines = text.split("\n")

    segments = []
    current_label = "ENTETE"
    buffer = []

    def flush():
        nonlocal buffer, segments, current_label
        if buffer:
            segments.append({
                "label": current_label,
                "content": "\n".join(buffer).strip()
            })
            buffer = []
            
    sommaire_done = False 
    in_sommaire = False  

    global_entete_done = False
    
    # casse les mots-clés importants même s’ils sont collés
    text = re.sub(r'(SIGN[ÉE]|SIGNE|SIGNÉE)(?=[A-Z])', r'\1\n', text, flags=re.I)
    
    text = re.sub(r'(ARR[ÊE]T[ÉE]\s*n°?\s*\d+)', r'\n\1', text, flags=re.I)

    for line in lines:
        
        lines = text.split("\n")
        
         # Détection ENTETE
        if not global_entete_done:
            if re.match(r'^\s*(SOMMAIRE|VU|ARTICLE|CONSID|ARR[ÊE]T[ÉE])', line, re.I):
                global_entete_done = True
            else:
                current_label = "ENTETE_GLOBAL"

         # Détection SOMMAIRE
        if not sommaire_done and re.match(r'^\s*SOMMAIRE\b', line, re.I):
            flush()
            current_label = "SOMMAIRE"
            buffer.append(line)
            sommaire_done = True
            in_sommaire = True
            continue
        
        
        if re.match(r'^\s*(ARR[ÊE]T[ÉE]|ARRETE)\b', line, re.I):
            if in_sommaire:
                buffer.append(line)
                continue
            flush()
            current_label = "ARRETE_TITRE"
            buffer.append(line)
            continue
        
        # 👉 Détection VISA
        if re.match(r'^\s*(VU|Vu|vu)\b', line):
            if current_label != "VISAS":
                flush()
                current_label = "VISAS"
            buffer.append(line)
            continue

        # 👉 Détection CONSIDERANT
        if re.match(r'^\s*(CONSID[ÉE]RANT|ATTENDU)', line, re.I):
            if current_label != "CONSIDERANTS":
                flush()
                current_label = "CONSIDERANTS"
            buffer.append(line)
            continue
        
        # 👉 Détection DISPOSITIF
        if re.match(r'^\s*(ARR[ÊE]T[ÉE]|D[ÉE]CIDE)\s*$', line, re.I):
            flush()
            current_label = "DISPOSITIF"
            buffer.append(line)
            continue

        # 👉 Détection ARTICLES (UNE SEULE FOIS)
        if current_label != "ARTICLES" and re.match(r'^\s*ARTICLE\s+\d+', line, re.I):
            flush()
            current_label = "ARTICLES"
        
        # toujours append dans le buffer
        if current_label == "ARTICLES":
            buffer.append(line)
            continue

        # 👉 Détection SIGNATURE
        if RE_SIGNATURE.search(line):
            flush()
            current_label = "SIGNATURE"
            buffer.append(line)
            continue
                
        # 👉 Détection ANNEXE
        if re.match(r'^\s*ANNEXE', line, re.I):
            flush()
            current_label = "ANNEXES"
            buffer.append(line)
            continue

        buffer.append(line)

    flush()

    return {
        "segments": segments,
        "as_dict": {s["label"]: s["content"] for s in segments},
        "stats": {
            "total_segments": len(segments),
            "labels_trouves": list(set(s["label"] for s in segments))
        },
        "success": True
    }
# =================================================================
# FONCTIONS UTILITAIRES
# =================================================================

def is_new_act(line: str) -> bool:
    return re.match(r'^\s*(ARR[ÊE]T[ÉE]|ARRETE)\b', line, re.I)



def _split_entete_titre(bloc: str) -> tuple:
    """
    Sépare le bloc initial en EN-TÊTE et TITRE.
    """
    lignes = bloc.split('\n')

    RE_TITRE_LIGNE = re.compile(
        r'(?:^[A-Z\s\d]{10,}$|Objet\s*:|portant\b|relatif\b|fixant\b)',
        re.IGNORECASE
    )

    idx_titre = None
    for i, ligne in enumerate(lignes):
        if RE_TITRE_LIGNE.search(ligne.strip()) and i > 0:
            idx_titre = i
            break

    if idx_titre is None:
        return bloc, ""

    entete = '\n'.join(lignes[:idx_titre]).strip()
    titre = '\n'.join(lignes[idx_titre:]).strip()
    return entete, titre


def _build_result(segments: list, success: bool) -> dict:
    """
    Construit le dictionnaire de résultat final.
    """
    labels_trouves = [s["label"] for s in segments]

    return {
        "segments": segments,
        "as_dict": {s["label"]: s["content"] for s in segments},
        "stats": {
            "total_segments": len(segments),
            "labels_trouves": labels_trouves,
            "labels_manquants": [
                l for l in ["VISAS", "DISPOSITIF", "ARTICLES", "SIGNATURE"]
                if l not in labels_trouves
            ],
        },
        "success": success,
    }


# =================================================================
# Wrapper pour compatibilité avec le pipeline
# =================================================================

def fix_segmentation(text: str) -> dict:
    """
    Wrapper pour compatibilité avec le pipeline RAA-NORM.
    Ajoute des titres de sections dans le texte.
    """

    result = segment_arrete(text)
    segments = result["segments"]

    # 🔥 reconstruction du texte avec labels
    new_text_parts = []

    for seg in segments:
        label = seg["label"]
        content = seg["content"].strip()

        # on ignore INCONNU vide
        if not content:
            continue

        # on injecte le label comme titre
        if label != "INCONNU":
            new_text_parts.append(f"\n=== {label} ===\n")

        new_text_parts.append(content)

    new_text = "\n".join(new_text_parts)

    return {
        "text": new_text,  # ✅ IMPORTANT : texte modifié maintenant
        "corrections": [{
            "type": "segmentation",
            "description": "Segmentation injectée dans le texte ({}) sections".format(
                result["stats"]["total_segments"]
            ),
            "count": result["stats"]["total_segments"],
        }],
        "stats": result["stats"],
        "segments": result["segments"],
        "as_dict": result["as_dict"],
    }













