from pathlib import Path

from config import INPUT_DIRS, OUTPUT_FOLDER_NAME
from pipeline import run_pipeline
from utils.segmentation_arrete import export_arretes
from utils.segmentation_arrete import split_arretes


def process_file(file_path, output_dir):
    raw = file_path.read_text(encoding="utf-8", errors="ignore")

    cleaned = run_pipeline(raw)
    
    arretes = split_arretes(cleaned)
    
    print(f"{len(arretes)} arrêtés détectés")
    
    export_arretes(
    arretes,
    source_text=cleaned,
    output_dir=output_dir
    )

    print(f"{file_path.name}")


def process_folder(folder: Path):
    if not folder.exists():
        print(f" Dossier introuvable : {folder}")
        return

    # ✅ création automatique
    output_dir = folder / OUTPUT_FOLDER_NAME
    output_dir.mkdir(exist_ok=True)

    files = list(folder.glob("*.txt"))

    if not files:
        print(f"⚠️ Aucun .txt dans {folder}")
        return

    print(f"\n Traitement : {folder} ({len(files)} fichiers)")

    for file in files:
        process_file(file, output_dir)


def main():
    print(" RAA Cleaner V2\n")

    for folder in INPUT_DIRS:
        process_folder(folder)

    print("\n Terminé.")


if __name__ == "__main__":
    main()