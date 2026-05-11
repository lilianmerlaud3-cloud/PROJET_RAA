import argparse
import re
from pathlib import Path


MASK = "XXX"


PATTERNS = [
    # Monsieur Frédéric PINGRET-KERJEAN
    # Madame Marie DURAND
    # M. Pierre CHAULEUR
    # Mme Jeanne MARTIN
    (
        re.compile(
            r"\b(Monsieur|Madame|M\.|Mme)\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+"
            r"(?:-[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+)*"
            r"\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,}"
            r"(?:[-'][A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,})*"
            r"\b"
        ),
        r"\1 XXX",
    ),

    # Monsieur PINGRET-KERJEAN Frédéric
    # Madame DURAND Marie
    # M. CHAULEUR Pierre
    (
        re.compile(
            r"\b(Monsieur|Madame|M\.|Mme)\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,}"
            r"(?:[-'][A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,})*"
            r"\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+"
            r"(?:-[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+)*"
            r"\b"
        ),
        r"\1 XXX",
    ),

    # Monsieur Frédéric Jean PINGRET-KERJEAN
    # Madame Marie Claire DURAND
    (
        re.compile(
            r"\b(Monsieur|Madame|M\.|Mme)\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+"
            r"(?:-[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+)*"
            r"(?:\s+[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+"
            r"(?:-[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ][a-zéèàùâêîôûäëïöüç'’-]+)*){1,3}"
            r"\s+"
            r"[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,}"
            r"(?:[-'][A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ]{2,})*"
            r"\b"
        ),
        r"\1 XXX",
    ),
]


def read_text_file(path: Path) -> str:
    encodings = ["utf-8", "utf-8-sig", "cp1252"]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            pass

    raise UnicodeDecodeError(
        "unknown",
        b"",
        0,
        1,
        f"Impossible de lire le fichier : {path}",
    )


def anonymize_text(text: str) -> str:
    result = text

    for pattern, replacement in PATTERNS:
        result = pattern.sub(replacement, result)

    return result


def process_file(input_file: Path, output_file: Path) -> None:
    text = read_text_file(input_file)
    anonymized = anonymize_text(text)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(anonymized, encoding="utf-8")


def collect_txt_files(input_path: Path):
    if input_path.is_file():
        if input_path.suffix.lower() != ".txt":
            raise ValueError("Le fichier fourni doit être un fichier .txt")
        return [input_path]

    if input_path.is_dir():
        return sorted(input_path.rglob("*.txt"))

    raise FileNotFoundError(f"Chemin introuvable : {input_path}")


def build_output_path(input_file: Path, input_root: Path, output_root: Path) -> Path:
    if input_root.is_file():
        return output_root / f"{input_file.stem}_anonymise.txt"

    relative_path = input_file.relative_to(input_root)
    return output_root / relative_path.with_name(
        f"{relative_path.stem}_anonymise.txt"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Anonymisation prudente des noms et prénoms dans des fichiers TXT de RAA."
    )

    parser.add_argument(
        "input",
        help="Chemin vers un fichier .txt ou vers un dossier contenant des .txt",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="sortie_anonymisee",
        help="Dossier de sortie. Par défaut : sortie_anonymisee",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_root = Path(args.output)

    txt_files = collect_txt_files(input_path)

    for txt_file in txt_files:
        output_file = build_output_path(txt_file, input_path, output_root)
        process_file(txt_file, output_file)

    print("Traitement terminé.")
    print(f"Nombre de fichiers traités : {len(txt_files)}")
    print(f"Dossier de sortie : {output_root}")


if __name__ == "__main__":
    main()